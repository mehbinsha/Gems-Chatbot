CREATE TABLE IF NOT EXISTS result_analysis_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rules TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS result_analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    total INTEGER NOT NULL,
    average REAL NOT NULL,
    subjects TEXT NOT NULL,
    strength_subjects TEXT NOT NULL,
    recommended_courses TEXT NOT NULL,
    source_filename TEXT,
    analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_result_analysis_history_analyzed_at
ON result_analysis_history (analyzed_at);
