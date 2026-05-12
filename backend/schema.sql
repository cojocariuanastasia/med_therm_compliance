-- MED-THERM-2026 Compliance Analyzer Database Schema

CREATE TABLE IF NOT EXISTS uploaded_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_by VARCHAR(100) DEFAULT 'system',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500) NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    compliant BOOLEAN DEFAULT FALSE,
    summary TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data TEXT,
    FOREIGN KEY (file_id) REFERENCES uploaded_files(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS violations (
    id SERIAL PRIMARY KEY,
    analysis_result_id INTEGER NOT NULL,
    regulation_code VARCHAR(50) NOT NULL,
    regulation_title VARCHAR(200),
    regulation_text TEXT,
    severity VARCHAR(20) DEFAULT 'warning',
    description TEXT,
    evidence TEXT,
    timestamp TIMESTAMP,
    line_number INTEGER,
    FOREIGN KEY (analysis_result_id) REFERENCES analysis_results(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS log_entries (
    id SERIAL PRIMARY KEY,
    analysis_result_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    entry_type VARCHAR(50),
    value VARCHAR(200),
    raw_line TEXT,
    line_number INTEGER,
    FOREIGN KEY (analysis_result_id) REFERENCES analysis_results(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_uploaded_files_uploaded_at ON uploaded_files(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_analysis_results_file_id ON analysis_results(file_id);
CREATE INDEX IF NOT EXISTS idx_violations_analysis_result_id ON violations(analysis_result_id);
CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity);
CREATE INDEX IF NOT EXISTS idx_log_entries_analysis_result_id ON log_entries(analysis_result_id);
CREATE INDEX IF NOT EXISTS idx_log_entries_timestamp ON log_entries(timestamp);
