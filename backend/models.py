from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    uploaded_by = db.Column(db.String(100), default='system')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500), nullable=False)
    
    analysis_results = db.relationship('AnalysisResult', backref='uploaded_file', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'file_path': self.file_path
        }

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)
    compliant = db.Column(db.Boolean, default=False)
    summary = db.Column(db.Text)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_data = db.Column(db.Text)
    gemini_csv = db.Column(db.Text)
    simulated_logs = db.Column(db.Text)
    
    violations = db.relationship('Violation', backref='analysis_result', lazy=True, cascade='all, delete-orphan')
    log_entries = db.relationship('LogEntry', backref='analysis_result', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'analysis_type': self.analysis_type,
            'compliant': self.compliant,
            'summary': self.summary,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
            'violation_count': len(self.violations)
        }

class Violation(db.Model):
    __tablename__ = 'violations'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_result_id = db.Column(db.Integer, db.ForeignKey('analysis_results.id'), nullable=False)
    regulation_code = db.Column(db.String(50), nullable=False)
    regulation_title = db.Column(db.String(200))
    regulation_text = db.Column(db.Text)
    severity = db.Column(db.String(20), default='warning')
    description = db.Column(db.Text)
    evidence = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    line_number = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'regulation_code': self.regulation_code,
            'regulation_title': self.regulation_title,
            'regulation_text': self.regulation_text,
            'severity': self.severity,
            'description': self.description,
            'evidence': self.evidence,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'line_number': self.line_number
        }

class LogEntry(db.Model):
    __tablename__ = 'log_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_result_id = db.Column(db.Integer, db.ForeignKey('analysis_results.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    entry_type = db.Column(db.String(50))
    value = db.Column(db.String(200))
    raw_line = db.Column(db.Text)
    line_number = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'entry_type': self.entry_type,
            'value': self.value,
            'line_number': self.line_number
        }
