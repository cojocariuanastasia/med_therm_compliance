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

                # If model is unavailable (503 / UNAVAILABLE) try next model
                if error.code == 503 or 'UNAVAILABLE' in error_body:
                    last_error = RuntimeError(f'Model {model} unavailable (HTTP 503). Trying next model.')
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
