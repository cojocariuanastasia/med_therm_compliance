import os
import json
import csv
import io
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from models import db, UploadedFile, AnalysisResult, Violation, LogEntry
from log_analyzer import ComplianceAnalyzer
from report_generator import ReportGenerator
from compliance_rules import get_all_rules
from gemini_client import GeminiClient
from ark_client import ArkClient

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

analyzer = ComplianceAnalyzer()
gemini_model_cfg = app.config.get('GEMINI_MODEL') or ''
gemini_client = GeminiClient(app.config.get('GEMINI_API_KEY'), gemini_model_cfg)

ark_api_key = app.config.get('ARK_API_KEY')
ark_base_url = app.config.get('ARK_BASE_URL')
ark_vision_model = app.config.get('ARK_VISION_MODEL')
ark_text_model = app.config.get('ARK_TEXT_MODEL')
ark_client = None
if ark_api_key and ark_vision_model:
    ark_client = ArkClient(ark_api_key, ark_base_url, ark_vision_model, ark_text_model)


def extract_csv_from_image(image_path, mime_type):
    if ark_client:
        return ark_client.analyze_image_as_csv(image_path, mime_type)
    return gemini_client.analyze_image_as_csv(image_path, mime_type)


def generate_logs_from_csv(csv_data):
    if ark_client:
        return ark_client.generate_simulated_logs(csv_data)
    return gemini_client.generate_simulated_logs(csv_data)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'txt':
        return 'log'
    elif ext in ['png', 'jpg', 'jpeg']:
        return 'image'
    return 'unknown'


def get_mime_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'png':
        return 'image/png'
    if ext in ['jpg', 'jpeg']:
        return 'image/jpeg'
    return 'application/octet-stream'

with app.app_context():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/files', methods=['GET'])
def get_files():
    files = UploadedFile.query.order_by(UploadedFile.uploaded_at.desc()).all()
    return jsonify({
        'success': True,
        'files': [f.to_dict() for f in files]
    })

@app.route('/api/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    return jsonify({
        'success': True,
        'file': file.to_dict()
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    original_filename = secure_filename(file.filename)
    filename = f"{timestamp}_{original_filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    file.save(filepath)
    
    uploaded_file = UploadedFile(
        filename=filename,
        original_filename=original_filename,
        file_type=get_file_type(original_filename),
        file_size=file_size,
        uploaded_by=request.form.get('uploaded_by', 'system'),
        file_path=filepath
    )
    db.session.add(uploaded_file)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'File uploaded successfully',
        'file': uploaded_file.to_dict()
    })

@app.route('/api/analyze/<int:file_id>', methods=['POST'])
def analyze_file(file_id):
    uploaded_file = UploadedFile.query.get_or_404(file_id)
    
    existing_analysis = AnalysisResult.query.filter_by(file_id=file_id).first()
    if existing_analysis:
        return jsonify({
            'success': True,
            'analysis': existing_analysis.to_dict(),
            'violations': [v.to_dict() for v in existing_analysis.violations]
        })
    
    if uploaded_file.file_type == 'log':
        with open(uploaded_file.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        result = analyzer.analyze_log_file(content)
        
        analysis_result = AnalysisResult(
            file_id=file_id,
            analysis_type='log',
            compliant=result['compliant'],
            summary=result['summary'],
            raw_data=json.dumps(result['stats'])
        )
        db.session.add(analysis_result)
        db.session.flush()
        
        for violation_data in result['violations']:
            violation = Violation(
                analysis_result_id=analysis_result.id,
                regulation_code=violation_data['regulation_code'],
                regulation_title=violation_data['regulation_title'],
                regulation_text=violation_data['regulation_text'],
                severity=violation_data['severity'],
                description=violation_data['description'],
                evidence=violation_data['evidence'],
                timestamp=violation_data.get('timestamp'),
                line_number=violation_data.get('line_number')
            )
            db.session.add(violation)
        
        for entry in result['entries']:
            if entry.get('timestamp'):
                log_entry = LogEntry(
                    analysis_result_id=analysis_result.id,
                    timestamp=entry['timestamp'],
                    entry_type=entry['entry_type'],
                    value=str(entry['value']) if entry.get('value') else None,
                    raw_line=entry['raw_line'],
                    line_number=entry['line_number']
                )
                db.session.add(log_entry)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'analysis': analysis_result.to_dict(),
            'violations': [v.to_dict() for v in analysis_result.violations],
            'stats': result['stats']
        })
    
    elif uploaded_file.file_type == 'image':
        try:
            mime_type = get_mime_type(uploaded_file.original_filename)
            csv_output = extract_csv_from_image(uploaded_file.file_path, mime_type)
        except Exception as exc:
            return jsonify({
                'success': False,
                'error': f'Image analysis failed: {str(exc)}'
            }), 500

        # Validate CSV header and extract rows
        parsed_rows = []
        reader = csv.reader(io.StringIO(csv_output))
        try:
            header = next(reader)
        except StopIteration:
            header = []

        header = [h.strip().lower() for h in header]

        if header[:2] != ['time_min', 'temp_c']:
            analysis_result = AnalysisResult(
                file_id=file_id,
                analysis_type='image',
                compliant=False,
                summary='Output did not match expected CSV header (time_min,temp_c).',
                gemini_csv=csv_output,
                raw_data=json.dumps({'gemini_csv': csv_output, 'parsed_count': len(parsed_rows)})
            )
            db.session.add(analysis_result)
            db.session.commit()

            return jsonify({
                'success': False,
                'error': 'Output did not contain expected CSV header time_min,temp_c.',
                'analysis': analysis_result.to_dict()
            }), 500

        for row_num, row in enumerate(reader, start=2):
            if not row or len(row) < 2:
                continue
            try:
                time_min = float(row[0])
                temp_c = float(row[1])
                parsed_rows.append({'time_min': time_min, 'temp_c': temp_c, 'row': row_num})
            except Exception:
                continue

        # Generate simulated transport logs from CSV data
        try:
            simulated_logs = generate_logs_from_csv(csv_output)
        except Exception as exc:
            return jsonify({
                'success': False,
                'error': f'Log generation failed: {str(exc)}'
            }), 500

        # Analyze the simulated logs using the full log analyzer
        result = analyzer.analyze_log_file(simulated_logs)

        analysis_result = AnalysisResult(
            file_id=file_id,
            analysis_type='image',
            compliant=result['compliant'],
            summary=result['summary'],
            gemini_csv=csv_output,
            simulated_logs=simulated_logs,
            raw_data=json.dumps({
                'parsed_count': len(parsed_rows),
                'stats': result['stats']
            })
        )
        db.session.add(analysis_result)
        db.session.flush()

        for violation_data in result['violations']:
            violation = Violation(
                analysis_result_id=analysis_result.id,
                regulation_code=violation_data['regulation_code'],
                regulation_title=violation_data['regulation_title'],
                regulation_text=violation_data['regulation_text'],
                severity=violation_data['severity'],
                description=violation_data['description'],
                evidence=violation_data['evidence'],
                timestamp=violation_data.get('timestamp'),
                line_number=violation_data.get('line_number')
            )
            db.session.add(violation)

        for entry in result['entries']:
            if entry.get('timestamp'):
                log_entry = LogEntry(
                    analysis_result_id=analysis_result.id,
                    timestamp=entry['timestamp'],
                    entry_type=entry['entry_type'],
                    value=str(entry['value']) if entry.get('value') else None,
                    raw_line=entry['raw_line'],
                    line_number=entry['line_number']
                )
                db.session.add(log_entry)

        db.session.commit()

        return jsonify({
            'success': True,
            'analysis': analysis_result.to_dict(),
            'violations': [v.to_dict() for v in analysis_result.violations],
            'stats': result['stats'],
            'simulated_logs_generated': True
        })
    
    return jsonify({'success': False, 'error': 'Unsupported file type'}), 400

@app.route('/api/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    analysis = AnalysisResult.query.get_or_404(analysis_id)
    
    return jsonify({
        'success': True,
        'analysis': analysis.to_dict(),
        'violations': [v.to_dict() for v in analysis.violations],
        'file': analysis.uploaded_file.to_dict()
    })

@app.route('/api/analysis/<int:analysis_id>/timeline', methods=['GET'])
def get_timeline(analysis_id):
    analysis = AnalysisResult.query.get_or_404(analysis_id)
    
    entries = LogEntry.query.filter_by(analysis_result_id=analysis_id).order_by(LogEntry.timestamp).all()
    
    timeline_data = {
        'temperature': [],
        'door_events': [],
        'alarm_events': [],
        'fan_speed': [],
        'voltage': [],
        'battery_level': [],
        'humidity': [],
        'sensor_timeout': [],
        'sync_failed': []
    }
    
    for entry in entries:
        entry_type = entry.entry_type
        ts = entry.timestamp.isoformat() if entry.timestamp else None
        
        if entry_type == 'TEMP_READING':
            try:
                val = float(entry.value)
                timeline_data['temperature'].append({'timestamp': ts, 'value': val, 'line': entry.line_number})
            except:
                pass
        elif entry_type in ['DOOR_OPEN', 'DOOR_CLOSE']:
            timeline_data['door_events'].append({
                'timestamp': ts, 
                'type': entry_type,
                'line': entry.line_number
            })
        elif entry_type == 'ALARM_TRIGGERED':
            timeline_data['alarm_events'].append({'timestamp': ts, 'line': entry.line_number})
        elif entry_type == 'FAN_SPEED':
            try:
                val = float(entry.value)
                timeline_data['fan_speed'].append({'timestamp': ts, 'value': val, 'line': entry.line_number})
            except:
                pass
        elif entry_type == 'VOLTAGE':
            try:
                val = float(entry.value)
                timeline_data['voltage'].append({'timestamp': ts, 'value': val, 'line': entry.line_number})
            except:
                pass
        elif entry_type == 'BATTERY_LEVEL':
            try:
                val = float(entry.value)
                timeline_data['battery_level'].append({'timestamp': ts, 'value': val, 'line': entry.line_number})
            except:
                pass
        elif entry_type == 'HUMIDITY':
            try:
                val = float(entry.value)
                timeline_data['humidity'].append({'timestamp': ts, 'value': val, 'line': entry.line_number})
            except:
                pass
        elif entry_type == 'SENSOR_TIMEOUT':
            timeline_data['sensor_timeout'].append({
                'timestamp': ts, 
                'sensor': entry.value,
                'line': entry.line_number
            })
        elif entry_type == 'TELEMETRY_SYNC_FAILED':
            timeline_data['sync_failed'].append({'timestamp': ts, 'line': entry.line_number})
    
    return jsonify({
        'success': True,
        'timeline': timeline_data
    })

@app.route('/api/rules', methods=['GET'])
def get_rules():
    return jsonify({
        'success': True,
        'rules': get_all_rules()
    })

@app.route('/api/download/csv/<int:analysis_id>', methods=['GET'])
def download_csv(analysis_id):
    analysis = AnalysisResult.query.get_or_404(analysis_id)

    if analysis.analysis_type == 'image':
        csv_content = analysis.gemini_csv
        if not csv_content and analysis.raw_data:
            raw_payload = json.loads(analysis.raw_data)
            csv_content = raw_payload.get('gemini_csv', '')
        if csv_content:
            from flask import make_response
            response = make_response(csv_content)
            response.headers["Content-Disposition"] = f"attachment; filename=gemini_extracted_data_{analysis_id}.csv"
            response.headers["Content-type"] = "text/csv"
            return response
    
    csv_content = ReportGenerator.generate_csv(
        {'compliant': analysis.compliant, 'stats': json.loads(analysis.raw_data) if analysis.raw_data else {}},
        [v.to_dict() for v in analysis.violations],
        [e.to_dict() for e in analysis.log_entries]
    )
    
    from flask import make_response
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = f"attachment; filename=compliance_report_{analysis_id}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/api/analysis/<int:analysis_id>/generate-logs', methods=['POST'])
def generate_simulated_logs(analysis_id):
    analysis = AnalysisResult.query.get_or_404(analysis_id)
    
    if analysis.analysis_type != 'image':
        return jsonify({
            'success': False,
            'error': 'Simulated logs can only be generated for image analyses.'
        }), 400

    uploaded_file = analysis.uploaded_file

    raw_payload = {}
    if analysis.raw_data:
        raw_payload = json.loads(analysis.raw_data)

    csv_output = analysis.gemini_csv or raw_payload.get('gemini_csv', '')

    if not csv_output:
        try:
            mime_type = get_mime_type(uploaded_file.original_filename)
            csv_output = extract_csv_from_image(uploaded_file.file_path, mime_type)
            analysis.gemini_csv = csv_output
            raw_payload['gemini_csv'] = csv_output
        except Exception as exc:
            return jsonify({
                'success': False,
                'error': f'Image analysis failed: {str(exc)}'
            }), 500

    try:
        simulated_logs_txt = generate_logs_from_csv(csv_output)
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f'Gemini log generation failed: {str(exc)}'
        }), 500

    result = analyzer.analyze_log_file(simulated_logs_txt)

    Violation.query.filter_by(analysis_result_id=analysis.id).delete()
    LogEntry.query.filter_by(analysis_result_id=analysis.id).delete()

    for violation_data in result['violations']:
        violation = Violation(
            analysis_result_id=analysis.id,
            regulation_code=violation_data['regulation_code'],
            regulation_title=violation_data['regulation_title'],
            regulation_text=violation_data['regulation_text'],
            severity=violation_data['severity'],
            description=violation_data['description'],
            evidence=violation_data['evidence'],
            timestamp=violation_data.get('timestamp'),
            line_number=violation_data.get('line_number')
        )
        db.session.add(violation)

    for entry in result['entries']:
        if entry.get('timestamp'):
            log_entry = LogEntry(
                analysis_result_id=analysis.id,
                timestamp=entry['timestamp'],
                entry_type=entry['entry_type'],
                value=str(entry['value']) if entry.get('value') else None,
                raw_line=entry['raw_line'],
                line_number=entry['line_number']
            )
            db.session.add(log_entry)

    analysis.simulated_logs = simulated_logs_txt
    raw_payload['simulated_logs'] = simulated_logs_txt
    raw_payload['stats'] = result['stats']
    analysis.raw_data = json.dumps(raw_payload)
    analysis.compliant = result['compliant']
    analysis.summary = result['summary']
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        'success': True,
        'analysis': analysis.to_dict(),
        'violations': [v.to_dict() for v in analysis.violations],
        'stats': result['stats'],
        'simulated_logs_generated': True
    })

@app.route('/api/analysis/<int:analysis_id>/has-logs', methods=['GET'])
def check_has_simulated_logs(analysis_id):
    analysis = AnalysisResult.query.get_or_404(analysis_id)
    
    has_logs = False
    if analysis.analysis_type == 'image':
        has_logs = bool(analysis.simulated_logs)
        if not has_logs and analysis.raw_data:
            raw_payload = json.loads(analysis.raw_data)
            has_logs = bool(raw_payload.get('simulated_logs', ''))
    
    return jsonify({
        'success': True,
        'has_simulated_logs': has_logs
    })

@app.route('/api/download/logs/<int:analysis_id>', methods=['GET'])
def download_simulated_logs(analysis_id):
    analysis = AnalysisResult.query.get_or_404(analysis_id)

    if analysis.analysis_type == 'image':
        logs_content = analysis.simulated_logs
        if not logs_content and analysis.raw_data:
            raw_payload = json.loads(analysis.raw_data)
            logs_content = raw_payload.get('simulated_logs', '')
        if logs_content:
            from flask import make_response
            response = make_response(logs_content)
            response.headers["Content-Disposition"] = f"attachment; filename=simulated_transport_logs_{analysis_id}.txt"
            response.headers["Content-type"] = "text/plain"
            return response

    return jsonify({
        'success': False,
        'error': 'No simulated logs available for this analysis.'
    }), 404

@app.route('/api/download/pdf/<int:analysis_id>', methods=['GET'])
def download_pdf(analysis_id):
    analysis = AnalysisResult.query.get_or_404(analysis_id)
    
    pdf_content = ReportGenerator.generate_pdf(
        {'compliant': analysis.compliant, 'stats': json.loads(analysis.raw_data) if analysis.raw_data else {}},
        [v.to_dict() for v in analysis.violations],
        [e.to_dict() for e in analysis.log_entries]
    )
    
    from flask import make_response
    response = make_response(pdf_content)
    response.headers["Content-Disposition"] = f"attachment; filename=compliance_report_{analysis_id}.pdf"
    response.headers["Content-type"] = "application/pdf"
    return response

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    uploaded_file = UploadedFile.query.get_or_404(file_id)
    
    try:
        if os.path.exists(uploaded_file.file_path):
            os.remove(uploaded_file.file_path)
    except:
        pass
    
    db.session.delete(uploaded_file)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'File deleted successfully'
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
