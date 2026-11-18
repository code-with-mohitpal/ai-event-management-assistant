CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
  reg_no TEXT, department TEXT, phone TEXT, password_hash TEXT NOT NULL,
  role_id INTEGER NOT NULL REFERENCES roles(id), created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS venues (
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(capacity>0),
  location TEXT, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS event_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT,
  category_id INTEGER NOT NULL REFERENCES event_categories(id),
  organizer_id INTEGER NOT NULL REFERENCES users(id),
  venue_id INTEGER NOT NULL REFERENCES venues(id),
  event_date TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL,
  max_participants INTEGER NOT NULL CHECK(max_participants>0),
  registration_deadline TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('DRAFT','PENDING','APPROVED','REJECTED','CANCELLED','COMPLETED')),
  reject_reason TEXT, poster TEXT,
  CHECK(end_time > start_time));
CREATE INDEX IF NOT EXISTS idx_venue_slot ON events(venue_id,event_date,start_time,end_time);
CREATE INDEX IF NOT EXISTS idx_status_date ON events(status,event_date);
CREATE TABLE IF NOT EXISTS registrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, registration_code TEXT UNIQUE NOT NULL,
  event_id INTEGER NOT NULL REFERENCES events(id), user_id INTEGER NOT NULL REFERENCES users(id),
  status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK(status IN ('CONFIRMED','CANCELLED')),
  qr_token TEXT UNIQUE NOT NULL, registered_at TEXT DEFAULT CURRENT_TIMESTAMP, cancelled_at TEXT,
  UNIQUE(event_id,user_id));
CREATE TABLE IF NOT EXISTS academic_calendar (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('EXAM','HOLIDAY','MAINTENANCE')),
  start_date TEXT NOT NULL, end_date TEXT NOT NULL, hard_block INTEGER NOT NULL DEFAULT 1,
  venue_id INTEGER REFERENCES venues(id));
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, event_id INTEGER NOT NULL,
  type TEXT NOT NULL, subject TEXT, body TEXT,
  status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','SENT','FAILED')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, sent_at TEXT,
  UNIQUE(user_id,event_id,type));
CREATE TABLE IF NOT EXISTS attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT, registration_id INTEGER NOT NULL UNIQUE REFERENCES registrations(id),
  event_id INTEGER NOT NULL, scanned_by INTEGER NOT NULL, scanned_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
  rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), comments TEXT, suggestions TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(event_id,user_id));
CREATE TABLE IF NOT EXISTS feedback_analysis (
  id INTEGER PRIMARY KEY AUTOINCREMENT, feedback_id INTEGER NOT NULL UNIQUE REFERENCES feedback(id),
  sentiment TEXT NOT NULL, confidence REAL, topics TEXT, complaints TEXT, model_version TEXT);
CREATE TABLE IF NOT EXISTS scheduling_recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, requested_by INTEGER, venue_id INTEGER, slot_date TEXT,
  start_time TEXT, end_time TEXT, conflict INTEGER NOT NULL, conflict_reason TEXT,
  score REAL, explanation TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
