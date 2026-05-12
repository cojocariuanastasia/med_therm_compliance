REGULATORY_RULES = {
    "REG-TEMP-1": {
        "code": "REG-TEMP-1",
        "title": "Operating Temperature Range",
        "text": "The device shall maintain internal storage temperature within: 2C <= T <= 8C at all times during active operation.",
        "severity": "critical",
        "category": "thermal"
    },
    "REG-TEMP-2": {
        "code": "REG-TEMP-2",
        "title": "Excursion Limits",
        "text": "Temperature excursions outside the allowed range shall comply with: Maximum duration per event: 5 minutes, Maximum cumulative duration per 24h: 10 minutes. Any exceedance is considered a critical violation.",
        "severity": "critical",
        "category": "thermal"
    },
    "REG-TEMP-3": {
        "code": "REG-TEMP-3",
        "title": "Stabilization Requirement",
        "text": "After any disturbance (e.g., door opening), the system must return to stable operating range within: t_recovery <= 3 minutes.",
        "severity": "major",
        "category": "thermal"
    },
    "REG-TEMP-4": {
        "code": "REG-TEMP-4",
        "title": "Sampling Frequency",
        "text": "Temperature must be recorded at intervals of: delta_t <= 30 seconds.",
        "severity": "major",
        "category": "thermal"
    },
    "REG-SENS-1": {
        "code": "REG-SENS-1",
        "title": "Redundant Sensing",
        "text": "The system shall include: at least one primary sensor, at least one redundant secondary sensor. Failure of redundancy constitutes a critical violation.",
        "severity": "critical",
        "category": "sensor"
    },
    "REG-SENS-2": {
        "code": "REG-SENS-2",
        "title": "Sensor Placement Constraint",
        "text": "Sensors must not be placed within: d < 15 cm from airflow outlet to prevent airflow bias interference.",
        "severity": "major",
        "category": "sensor"
    },
    "REG-SENS-3": {
        "code": "REG-SENS-3",
        "title": "Sensor Agreement",
        "text": "Sensor readings must satisfy: |T1 - T2| <= 0.5C.",
        "severity": "major",
        "category": "sensor"
    },
    "REG-ALARM-1": {
        "code": "REG-ALARM-1",
        "title": "Activation Delay",
        "text": "Alarm shall activate if temperature remains outside range for: t >= 2 minutes.",
        "severity": "critical",
        "category": "alarm"
    },
    "REG-ALARM-2": {
        "code": "REG-ALARM-2",
        "title": "Notification Latency",
        "text": "System notifications must be delivered within: t_notify <= 10 seconds.",
        "severity": "major",
        "category": "alarm"
    },
    "REG-ALARM-3": {
        "code": "REG-ALARM-3",
        "title": "Alarm Types",
        "text": "The system must support: audible alarm, visual dashboard alert, remote mobile notification. Failure to support any channel is non-compliant.",
        "severity": "major",
        "category": "alarm"
    },
    "REG-DATA-1": {
        "code": "REG-DATA-1",
        "title": "Immutable Audit Log",
        "text": "The system must maintain an immutable log of: temperature readings, alarms, configuration changes, sensor status events.",
        "severity": "major",
        "category": "data"
    },
    "REG-DATA-2": {
        "code": "REG-DATA-2",
        "title": "Logging Continuity",
        "text": "Data gaps in telemetry must not exceed: delta_t_gap <= 90 seconds.",
        "severity": "major",
        "category": "data"
    },
    "REG-DATA-3": {
        "code": "REG-DATA-3",
        "title": "Retention Requirement",
        "text": "Local data must be retained for at least: t_retention >= 72 hours in case of cloud sync failure.",
        "severity": "major",
        "category": "data"
    },
    "REG-POWER-1": {
        "code": "REG-POWER-1",
        "title": "Minimum Runtime",
        "text": "Battery backup must support continuous operation for: t_battery >= 4 hours.",
        "severity": "critical",
        "category": "power"
    },
    "REG-POWER-2": {
        "code": "REG-POWER-2",
        "title": "Degraded Mode Compliance",
        "text": "Even in battery mode, temperature must remain compliant with REG-TEMP-1.",
        "severity": "critical",
        "category": "power"
    },
    "REG-COOL-1": {
        "code": "REG-COOL-1",
        "title": "Redundant Airflow",
        "text": "Cooling system must include at least: n >= 2 airflow paths.",
        "severity": "major",
        "category": "cooling"
    },
    "REG-COOL-2": {
        "code": "REG-COOL-2",
        "title": "Failure Tolerance",
        "text": "Single-point failure in cooling airflow shall not result in temperature excursion beyond allowed range for more than 3 minutes.",
        "severity": "critical",
        "category": "cooling"
    },
    "REG-INS-1": {
        "code": "REG-INS-1",
        "title": "Minimum Insulation Thickness",
        "text": "All chamber walls must have insulation thickness: t_insulation >= 4 cm.",
        "severity": "major",
        "category": "insulation"
    },
    "REG-INS-2": {
        "code": "REG-INS-2",
        "title": "Thermal Isolation",
        "text": "Battery compartment must be physically and thermally isolated from storage chamber.",
        "severity": "major",
        "category": "insulation"
    },
    "REG-OPS-1": {
        "code": "REG-OPS-1",
        "title": "Door Event Impact",
        "text": "After a door opening event, system must: stabilize within 3 minutes (REG-TEMP-3), not exceed 8C during recovery window.",
        "severity": "major",
        "category": "operational"
    },
    "REG-OPS-2": {
        "code": "REG-OPS-2",
        "title": "Access Frequency",
        "text": "Excessive access is defined as: f_door > 10 events/hour and must trigger operational warning.",
        "severity": "warning",
        "category": "operational"
    }
}

def get_rule(code):
    return REGULATORY_RULES.get(code)

def get_all_rules():
    return REGULATORY_RULES
