import re
from datetime import datetime, timedelta
from collections import defaultdict
from compliance_rules import REGULATORY_RULES, get_rule

class LogParser:
    def __init__(self):
        self.entry_patterns = [
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) TEMP_READING ([\d.]+)C$', 'TEMP_READING', 'temperature'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ALARM_TRIGGERED$', 'ALARM_TRIGGERED', 'alarm'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) FAN_SPEED (\d+)RPM$', 'FAN_SPEED', 'fan_speed'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) TELEMETRY_SYNC_FAILED$', 'TELEMETRY_SYNC_FAILED', 'sync_failed'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) DEVICE_START$', 'DEVICE_START', 'device_start'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) VOLTAGE ([\d.]+)V$', 'VOLTAGE', 'voltage'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) DOOR_CLOSE$', 'DOOR_CLOSE', 'door_close'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) DOOR_OPEN$', 'DOOR_OPEN', 'door_open'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) COOLING_RECOVERY_START$', 'COOLING_RECOVERY_START', 'cooling_recovery'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) HUMIDITY (\d+)%$', 'HUMIDITY', 'humidity'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) SENSOR_TIMEOUT (\w+)$', 'SENSOR_TIMEOUT', 'sensor_timeout'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) TEMP_WARNING$', 'TEMP_WARNING', 'temp_warning'),
            (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) BATTERY_LEVEL ([\d.]+)%$', 'BATTERY_LEVEL', 'battery_level'),
        ]
    
    def parse_line(self, line, line_number):
        line = line.strip()
        if not line:
            return None
        
        for pattern, entry_type, value_type in self.entry_patterns:
            match = re.match(pattern, line)
            if match:
                timestamp_str = match.group(1)
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                entry = {
                    'timestamp': timestamp,
                    'entry_type': entry_type,
                    'raw_line': line,
                    'line_number': line_number,
                    'value': None,
                    'value_type': value_type
                }
                
                if entry_type in ['TEMP_READING', 'VOLTAGE', 'HUMIDITY', 'BATTERY_LEVEL', 'FAN_SPEED']:
                    entry['value'] = float(match.group(2))
                elif entry_type == 'SENSOR_TIMEOUT':
                    entry['value'] = match.group(2)
                
                return entry
        
        return {
            'timestamp': None,
            'entry_type': 'UNKNOWN',
            'raw_line': line,
            'line_number': line_number,
            'value': None,
            'value_type': 'unknown'
        }
    
    def parse_file(self, content):
        entries = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            entry = self.parse_line(line, line_num)
            if entry:
                entries.append(entry)
        
        entries.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min)
        return entries


class ComplianceAnalyzer:
    def __init__(self):
        self.parser = LogParser()
    
    def analyze_log_file(self, content):
        entries = self.parser.parse_file(content)
        violations = []
        
        temp_readings = [e for e in entries if e['entry_type'] == 'TEMP_READING']
        door_events = [e for e in entries if e['entry_type'] in ['DOOR_OPEN', 'DOOR_CLOSE']]
        alarm_events = [e for e in entries if e['entry_type'] == 'ALARM_TRIGGERED']
        sensor_timeouts = [e for e in entries if e['entry_type'] == 'SENSOR_TIMEOUT']
        sync_failures = [e for e in entries if e['entry_type'] == 'TELEMETRY_SYNC_FAILED']
        
        violations.extend(self._check_temp_range(temp_readings))
        violations.extend(self._check_temp_excursions(temp_readings))
        violations.extend(self._check_sampling_frequency(temp_readings))
        violations.extend(self._check_sensor_redundancy(sensor_timeouts, entries))
        violations.extend(self._check_alarm_timing(temp_readings, alarm_events))
        violations.extend(self._check_data_gaps(entries))
        violations.extend(self._check_door_events(door_events, temp_readings))
        violations.extend(self._check_access_frequency(door_events))
        
        compliant = len(violations) == 0
        
        summary_parts = []
        critical_count = sum(1 for v in violations if v['severity'] == 'critical')
        major_count = sum(1 for v in violations if v['severity'] == 'major')
        warning_count = sum(1 for v in violations if v['severity'] == 'warning')
        
        if compliant:
            summary = "PASS: All regulatory compliance checks passed. No violations detected."
        else:
            summary = f"FAIL: {len(violations)} violations detected. "
            if critical_count > 0:
                summary += f"Critical: {critical_count}, "
            if major_count > 0:
                summary += f"Major: {major_count}, "
            if warning_count > 0:
                summary += f"Warnings: {warning_count}"
        
        return {
            'compliant': compliant,
            'violations': violations,
            'entries': entries,
            'summary': summary,
            'stats': {
                'total_entries': len(entries),
                'temp_readings': len(temp_readings),
                'door_events': len(door_events),
                'alarms': len(alarm_events),
                'violations_by_severity': {
                    'critical': critical_count,
                    'major': major_count,
                    'warning': warning_count
                }
            }
        }
    
    def _check_temp_range(self, temp_readings):
        violations = []
        rule = get_rule('REG-TEMP-1')
        
        for reading in temp_readings:
            temp = reading['value']
            if temp < 2.0 or temp > 8.0:
                violations.append({
                    'regulation_code': 'REG-TEMP-1',
                    'regulation_title': rule['title'],
                    'regulation_text': rule['text'],
                    'severity': rule['severity'],
                    'description': f"Temperature reading of {temp}C is outside the allowed range of 2C-8C.",
                    'evidence': f"Line {reading['line_number']}: {reading['raw_line']}",
                    'timestamp': reading['timestamp'],
                    'line_number': reading['line_number']
                })
        
        return violations
    
    def _check_temp_excursions(self, temp_readings):
        violations = []
        rule = get_rule('REG-TEMP-2')
        
        if len(temp_readings) < 2:
            return violations
        
        excursions = []
        current_excursion = None
        
        for reading in temp_readings:
            temp = reading['value']
            if temp < 2.0 or temp > 8.0:
                if current_excursion is None:
                    current_excursion = {
                        'start': reading['timestamp'],
                        'start_line': reading['line_number'],
                        'readings': [reading]
                    }
                else:
                    current_excursion['readings'].append(reading)
                    current_excursion['end'] = reading['timestamp']
                    current_excursion['end_line'] = reading['line_number']
            else:
                if current_excursion is not None:
                    excursions.append(current_excursion)
                    current_excursion = None
        
        if current_excursion is not None:
            excursions.append(current_excursion)
        
        for exc in excursions:
            if 'end' in exc:
                duration = (exc['end'] - exc['start']).total_seconds() / 60.0
            else:
                duration = 0.05
            
            if duration > 5:
                violations.append({
                    'regulation_code': 'REG-TEMP-2',
                    'regulation_title': rule['title'],
                    'regulation_text': rule['text'],
                    'severity': rule['severity'],
                    'description': f"Temperature excursion lasted {duration:.1f} minutes, exceeding maximum 5 minutes per event.",
                    'evidence': f"Lines {exc['start_line']}-{exc.get('end_line', exc['start_line'])}: Excursion of {duration:.1f} minutes",
                    'timestamp': exc['start'],
                    'line_number': exc['start_line']
                })
        
        return violations
    
    def _check_sampling_frequency(self, temp_readings):
        violations = []
        rule = get_rule('REG-TEMP-4')
        
        for i in range(1, len(temp_readings)):
            prev = temp_readings[i-1]
            curr = temp_readings[i]
            
            if prev['timestamp'] and curr['timestamp']:
                gap = (curr['timestamp'] - prev['timestamp']).total_seconds()
                
                if gap > 30:
                    violations.append({
                        'regulation_code': 'REG-TEMP-4',
                        'regulation_title': rule['title'],
                        'regulation_text': rule['text'],
                        'severity': rule['severity'],
                        'description': f"Temperature sampling gap of {gap} seconds exceeds maximum 30 seconds.",
                        'evidence': f"Between lines {prev['line_number']} and {curr['line_number']}: {gap} second gap",
                        'timestamp': prev['timestamp'],
                        'line_number': prev['line_number']
                    })
        
        return violations
    
    def _check_sensor_redundancy(self, sensor_timeouts, all_entries):
        violations = []
        rule = get_rule('REG-SENS-1')
        
        secondary_timeouts = [t for t in sensor_timeouts if t['value'] == 'SECONDARY_SENSOR']
        
        seen_violations = set()
        for timeout in secondary_timeouts:
            key = (timeout['timestamp'].replace(second=0, microsecond=0),)
            if key not in seen_violations:
                seen_violations.add(key)
                violations.append({
                    'regulation_code': 'REG-SENS-1',
                    'regulation_title': rule['title'],
                    'regulation_text': rule['text'],
                    'severity': rule['severity'],
                    'description': "Secondary sensor timeout detected - sensor redundancy may be compromised.",
                    'evidence': f"Line {timeout['line_number']}: {timeout['raw_line']}",
                    'timestamp': timeout['timestamp'],
                    'line_number': timeout['line_number']
                })
        
        return violations
    
    def _check_alarm_timing(self, temp_readings, alarm_events):
        violations = []
        rule = get_rule('REG-ALARM-1')
        
        out_of_range_periods = []
        current_period = None
        
        sorted_readings = sorted(temp_readings, key=lambda x: x['timestamp'])
        
        for reading in sorted_readings:
            temp = reading['value']
            if temp < 2.0 or temp > 8.0:
                if current_period is None:
                    current_period = {
                        'start': reading['timestamp'],
                        'start_line': reading['line_number'],
                        'start_temp': temp
                    }
                else:
                    current_period['end'] = reading['timestamp']
                    current_period['end_temp'] = temp
            else:
                if current_period is not None:
                    out_of_range_periods.append(current_period)
                    current_period = None
        
        if current_period is not None:
            out_of_range_periods.append(current_period)
        
        for period in out_of_range_periods:
            if 'end' in period:
                duration = (period['end'] - period['start']).total_seconds() / 60.0
            else:
                duration = 0.05
            
            if duration >= 2:
                has_alarm = False
                for alarm in alarm_events:
                    if period['start'] <= alarm['timestamp'] <= period.get('end', period['start'] + timedelta(minutes=duration)):
                        has_alarm = True
                        break
                
                if not has_alarm:
                    violations.append({
                        'regulation_code': 'REG-ALARM-1',
                        'regulation_title': rule['title'],
                        'regulation_text': rule['text'],
                        'severity': rule['severity'],
                        'description': f"Temperature out of range for {duration:.1f} minutes (>= 2 minutes) but no alarm was triggered.",
                        'evidence': f"Temperature out of range starting at line {period['start_line']} ({period['start_temp']}C) for {duration:.1f} minutes",
                        'timestamp': period['start'],
                        'line_number': period['start_line']
                    })
        
        return violations
    
    def _check_data_gaps(self, entries):
        violations = []
        rule = get_rule('REG-DATA-2')
        
        sorted_entries = sorted([e for e in entries if e['timestamp']], key=lambda x: x['timestamp'])
        
        for i in range(1, len(sorted_entries)):
            prev = sorted_entries[i-1]
            curr = sorted_entries[i]
            
            gap = (curr['timestamp'] - prev['timestamp']).total_seconds()
            
            if gap > 90:
                violations.append({
                    'regulation_code': 'REG-DATA-2',
                    'regulation_title': rule['title'],
                    'regulation_text': rule['text'],
                    'severity': rule['severity'],
                    'description': f"Data gap of {gap} seconds exceeds maximum 90 seconds allowed.",
                    'evidence': f"Between lines {prev['line_number']} and {curr['line_number']}: {gap} second gap",
                    'timestamp': prev['timestamp'],
                    'line_number': prev['line_number']
                })
        
        return violations
    
    def _check_door_events(self, door_events, temp_readings):
        violations = []
        rule = get_rule('REG-OPS-1')
        
        door_openings = [d for d in door_events if d['entry_type'] == 'DOOR_OPEN']
        
        for opening in door_openings:
            open_time = opening['timestamp']
            recovery_end = open_time + timedelta(minutes=3)
            
            temps_during_recovery = [
                t for t in temp_readings 
                if open_time <= t['timestamp'] <= recovery_end
            ]
            
            for temp_reading in temps_during_recovery:
                if temp_reading['value'] > 8.0:
                    violations.append({
                        'regulation_code': 'REG-OPS-1',
                        'regulation_title': rule['title'],
                        'regulation_text': rule['text'],
                        'severity': rule['severity'],
                        'description': f"Temperature exceeded 8C during door recovery window. Reading: {temp_reading['value']}C",
                        'evidence': f"Door opened at line {opening['line_number']}, temperature violation at line {temp_reading['line_number']}: {temp_reading['raw_line']}",
                        'timestamp': temp_reading['timestamp'],
                        'line_number': temp_reading['line_number']
                    })
        
        return violations
    
    def _check_access_frequency(self, door_events):
        violations = []
        rule = get_rule('REG-OPS-2')
        
        door_openings = sorted(
            [d for d in door_events if d['entry_type'] == 'DOOR_OPEN'],
            key=lambda x: x['timestamp']
        )
        
        if not door_openings:
            return violations
        
        start_time = door_openings[0]['timestamp']
        end_time = door_openings[-1]['timestamp']
        
        current_hour_start = start_time.replace(minute=0, second=0, microsecond=0)
        hour_bins = defaultdict(list)
        
        for opening in door_openings:
            hour_key = opening['timestamp'].replace(minute=0, second=0, microsecond=0)
            hour_bins[hour_key].append(opening)
        
        for hour_bin, openings in hour_bins.items():
            if len(openings) > 10:
                violations.append({
                    'regulation_code': 'REG-OPS-2',
                    'regulation_title': rule['title'],
                    'regulation_text': rule['text'],
                    'severity': rule['severity'],
                    'description': f"Excessive door access: {len(openings)} openings in one hour (limit: 10).",
                    'evidence': f"Hour starting {hour_bin}: {len(openings)} door open events",
                    'timestamp': hour_bin,
                    'line_number': openings[0]['line_number']
                })
        
        return violations
