import base64
import json
import urllib.error
import urllib.request


GEMINI_IMAGE_PROMPT = """You are a precision data extraction tool. Your task is to analyze the provided image of a temperature profile graph and extract the data points represented by the markers on the line.

CRITICAL INSTRUCTIONS:

DO NOT guess, assume, or generate generic timelines.

First, carefully read the X-axis (Time) and Y-axis (Temperature) labels to determine the exact numerical scale and the step value of the gridlines.

Identify each distinct circular marker on the plotted line.

Map each marker to the axes to determine its exact (X, Y) coordinates.

OUTPUT FORMAT:
Return the extracted data STRICTLY as a valid CSV (Comma Separated Values) string.

The first row must be the header: time_min,temp_c

Do not include any extra conversational text, greetings, or explanations.

Do not wrap the output in markdown code blocks (e.g., avoid ```csv). Output ONLY the raw comma-separated text."""


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

OUTPUT ONLY THE RAW LOG LINES, ONE PER LINE. NO extra text."""


class GeminiClient:
    def __init__(self, api_key, model_or_models):
        self.api_key = api_key
        # Accept a single model string or a comma-separated/list of models
        if isinstance(model_or_models, str):
            self.models = [m.strip() for m in model_or_models.split(',') if m.strip()]
        elif isinstance(model_or_models, (list, tuple)):
            self.models = [str(m).strip() for m in model_or_models if str(m).strip()]
        else:
            self.models = []

    def analyze_image_as_csv(self, image_path, mime_type='image/png'):
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY is not set. Add it to backend/.env.')

        if not self.models:
            raise ValueError('No GEMINI_MODEL configured. Set GEMINI_MODEL in backend/.env')

        with open(image_path, 'rb') as img_file:
            image_bytes = img_file.read()

        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        payload = {
            'contents': [
                {
                    'parts': [
                        {'text': GEMINI_IMAGE_PROMPT},
                        {
                            'inline_data': {
                                'mime_type': mime_type,
                                'data': encoded_image,
                            }
                        },
                    ]
                }
            ]
        }

        last_error = None
        for model in self.models:
            endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}'

            request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )

            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    csv_text = self._extract_text(response_data)
                    if csv_text:
                        return csv_text.strip()
                    else:
                        last_error = RuntimeError('Gemini response did not include text output.')
                        # try next model
            except urllib.error.HTTPError as error:
                try:
                    error_body = error.read().decode('utf-8', errors='ignore')
                except Exception:
                    error_body = ''

                # If model is unavailable (503 / UNAVAILABLE) or quota exceeded (429 / RESOURCE_EXHAUSTED) or not found (404 / NOT_FOUND), try next model
                if error.code == 503 or error.code == 429 or error.code == 404 or 'UNAVAILABLE' in error_body or 'RESOURCE_EXHAUSTED' in error_body or 'NOT_FOUND' in error_body:
                    last_error = RuntimeError(f'Model {model} failed (HTTP {error.code}). Trying next model.')
                    continue
                else:
                    # Other HTTP errors should be raised
                    raise RuntimeError(f'Gemini API HTTP {error.code}: {error_body}') from error
            except urllib.error.URLError as error:
                # network error - keep as last_error and try next model
                last_error = RuntimeError(f'Gemini API request failed: {error.reason}')
                continue

        if last_error:
            raise last_error
        raise RuntimeError('Gemini image analysis failed: no models responded successfully')

    def generate_simulated_logs(self, csv_data):
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY is not set. Add it to backend/.env.')

        if not self.models:
            raise ValueError('No GEMINI_MODEL configured. Set GEMINI_MODEL in backend/.env')

        prompt = GEMINI_LOG_SIMULATION_PROMPT.format(csv_data=csv_data)

        payload = {
            'contents': [
                {
                    'parts': [
                        {'text': prompt},
                    ]
                }
            ],
            'generationConfig': {
                'temperature': 0.7,
                'maxOutputTokens': 8192,
            }
        }

        last_error = None
        for model in self.models:
            endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}'

            request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )

            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    log_text = self._extract_text(response_data)
                    if log_text:
                        return log_text.strip()
                    else:
                        last_error = RuntimeError('Gemini response did not include text output.')
            except urllib.error.HTTPError as error:
                try:
                    error_body = error.read().decode('utf-8', errors='ignore')
                except Exception:
                    error_body = ''

                if error.code == 503 or error.code == 429 or error.code == 404 or 'UNAVAILABLE' in error_body or 'RESOURCE_EXHAUSTED' in error_body or 'NOT_FOUND' in error_body:
                    last_error = RuntimeError(f'Model {model} failed (HTTP {error.code}). Trying next model.')
                    continue
                else:
                    raise RuntimeError(f'Gemini API HTTP {error.code}: {error_body}') from error
            except urllib.error.URLError as error:
                last_error = RuntimeError(f'Gemini API request failed: {error.reason}')
                continue

        if last_error:
            raise last_error
        raise RuntimeError('Gemini log generation failed: no models responded successfully')

    @staticmethod
    def _extract_text(response_data):
        candidates = response_data.get('candidates', [])
        for candidate in candidates:
            content = candidate.get('content', {})
            parts = content.get('parts', [])
            for part in parts:
                text = part.get('text')
                if text:
                    return text
        return None
