import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from models import db, UploadedFile, AnalysisResult, Violation, LogEntry
from log_analyzer import ComplianceAnalyzer
from report_generator import ReportGenerator
from compliance_rules import get_all_rules

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

analyzer = ComplianceAnalyzer()

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
        return jsonify({
            'success': False,
            'error': 'Image analysis requires additional OCR/VLM setup. For this PoC, please use log files.'
        }), 501
    
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
