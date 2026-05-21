CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(50),
    reminder_time VARCHAR(5) DEFAULT '21:00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    record_date DATE DEFAULT (DATE('now', 'localtime')),
    mood INTEGER CHECK (mood >= 1 AND mood <= 5),
    work_hours REAL CHECK (work_hours >= 0),
    sleep_hours REAL CHECK (sleep_hours >= 0),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, record_date)
);

CREATE INDEX IF NOT EXISTS idx_records_user_date ON records(user_id, record_date);