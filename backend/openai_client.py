import json
import urllib.error
import urllib.request


GEMINI_LOG_SIMULATION_PROMPT = """You are a medical device transport log simulator. Generate realistic transport log entries based on the provided temperature profile CSV data.

INPUT CSV DATA (time in minutes, temperature in Celsius):
{csv_data}

CRITICAL EVENT ORDERING RULES - THESE MUST BE FOLLOWED EXACTLY:

RULE 1 - DOOR OPENING DETECTION:
- If temperature raises by AT LEAST 1.0°C from the starting temperature, this indicates a DOOR_OPEN event.
- Event ORDER must be: DOOR_OPEN → temperature raises → HUMIDITY changes → ... → DOOR_CLOSE
- When door opens, humidity typically changes (drops or raises depending on ambient conditions).

RULE 2 - COOLING RECOVERY:
- If temperature starts to COOL DOWN after being elevated, the fan must have started working FASTER BEFORE the temperature drop.
- The COOLING_RECOVERY_START event must be triggered BEFORE the fan speeds up.
- Event ORDER must be: temperature raises → COOLING_RECOVERY_START → FAN_SPEED increases → temperature drops
- Base fan speed is approximately 1800-2200 RPM. Cooling fan speed is approximately 2800-3800 RPM.

RULE 3 - BATTERY DRAIN:
- When the fan works at a FASTER pace (higher RPM), the battery percentage DROPS FASTER.
- Event ORDER must be: FAN_SPEED (faster) → BATTERY_LEVEL drops
- Battery starts around 99.9% and gradually decreases. Normal drain is ~0.1-0.2% per entry. Fast drain (during cooling) is ~0.3-0.5% per entry.

RULE 4 - LOG FORMAT:
- Each line must be formatted exactly like:
  YYYY-MM-DD HH:MM:SS EVENT_TYPE [VALUE][UNIT]
  
- Examples of valid log lines:
  2026-05-14 14:00:10 TEMP_READING 4.3C
  2026-05-14 14:00:20 FAN_SPEED 2029RPM
  2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED
  2026-05-14 14:01:20 DOOR_CLOSE
  2026-05-14 14:01:30 COOLING_RECOVERY_START
  2026-05-14 14:02:10 HUMIDITY 77%
  2026-05-14 14:07:40 BATTERY_LEVEL 99.9%
  2026-05-14 14:06:00 VOLTAGE 12.56V
  2026-05-14 14:00:50 DEVICE_START
  2026-05-14 14:00:40 ALARM_TRIGGERED
  2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR

RULE 5 - OUTPUT REQUIREMENTS:
- Generate about 200 log lines.
- Start timestamp: 2026-05-14 14:00:00
- Each log entry should be spaced 10 seconds apart.
- Include a mix of: TEMP_READING, FAN_SPEED, HUMIDITY, BATTERY_LEVEL, VOLTAGE, DOOR_OPEN, DOOR_CLOSE, COOLING_RECOVERY_START, ALARM_TRIGGERED, TELEMETRY_SYNC_FAILED, SENSOR_TIMEOUT, DEVICE_START, TEMP_WARNING
- Temperature readings should follow the pattern from input CSV.
- Humidity: 30-85%
- Voltage: ~12.0-12.8V

OUTPUT ONLY THE RAW LOG LINES, ONE PER LINE. NO extra text, NO explanations, NO markdown."""


class OpenAIClient:
    def __init__(self, api_key, base_url, model):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model

    def generate_simulated_logs(self, csv_data):
        if not self.api_key:
            raise ValueError('ARK_API_KEY is not set. Add it to backend/.env.')

        if not self.model:
            raise ValueError('ARK_MODEL is not set. Set ARK_MODEL in backend/.env')

        prompt = GEMINI_LOG_SIMULATION_PROMPT.format(csv_data=csv_data)

        endpoint = f'{self.base_url}/chat/completions'

        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 8192,
            'temperature': 0.7,
        }

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
            },
            method='POST',
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                text = self._extract_text(response_data)
                if text:
                    return text.strip()
                else:
                    raise RuntimeError('API response did not include text output.')
        except urllib.error.HTTPError as error:
            try:
                error_body = error.read().decode('utf-8', errors='ignore')
            except Exception:
                error_body = ''
            raise RuntimeError(f'API HTTP {error.code}: {error_body}') from error
        except urllib.error.URLError as error:
            raise RuntimeError(f'API request failed: {error.reason}') from error

    @staticmethod
    def _extract_text(response_data):
        choices = response_data.get('choices', [])
        for choice in choices:
            message = choice.get('message', {})
            content = message.get('content')
            if content:
                return content
        return None
