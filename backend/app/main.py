import io, json, os, secrets, threading, time, uuid, logging
from datetime import date, datetime, timedelta
from typing import Optional
import bcrypt, jwt, qrcode
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field
from . import db, scheduling, sentiment
from .db import q, q1

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-change-me-" + "x" * 20)
log = logging.getLogger("mail")
app = FastAPI(title="AI-Based Event Management and Scheduling Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
db.init()

# ---------- helpers ----------
def now(): return datetime.now()
def iso(d): return d.strftime("%Y-%m-%d %H:%M:%S")
def hash_pw(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt(rounds=8)).decode()
def make_token(u): return jwt.encode({"sub": str(u["id"]), "role": u["role"], "exp": now() + timedelta(hours=12)}, JWT_SECRET, "HS256")

def current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401, "Not authenticated")
    try: p = jwt.decode(authorization[7:], JWT_SECRET, ["HS256"])
    except jwt.PyJWTError: raise HTTPException(401, "Invalid or expired token")
    c = db.conn()
    try:
        u = q1(c, "SELECT u.id,u.name,u.email,u.reg_no,u.department,u.phone,r.name role FROM users u JOIN roles r ON r.id=u.role_id WHERE u.id=?", (int(p["sub"]),))
    finally: c.close()
    if not u: raise HTTPException(401, "User not found")
    return u

def need(*roles):
    def dep(u=Depends(current_user)):
        if u["role"] not in roles: raise HTTPException(403, "Insufficient role")
        return u
    return dep

def send_mail(c, user_id, event_id, typ, subject, body):
    """Idempotent notification: UNIQUE(user_id,event_id,type). Delivered to SMTP if configured, else logged (MailHog-style)."""
    try:
        c.execute("INSERT INTO notifications(user_id,event_id,type,subject,body) VALUES(?,?,?,?,?)", (user_id, event_id, typ, subject, body))
    except Exception: return False
    nid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    try:
        host = os.environ.get("SMTP_HOST")
        if host:
            import smtplib; from email.message import EmailMessage
            to = q1(c, "SELECT email FROM users WHERE id=?", (user_id,))["email"]
            m = EmailMessage(); m["Subject"], m["From"], m["To"] = subject, os.environ.get("MAIL_FROM", "events@lpu.local"), to; m.set_content(body)
            with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", 1025)), timeout=5) as s: s.send_message(m)
        log.info("MAIL to user %s: %s", user_id, subject)
        c.execute("UPDATE notifications SET status='SENT', sent_at=? WHERE id=?", (iso(now()), nid))
    except Exception:
        c.execute("UPDATE notifications SET status='FAILED' WHERE id=?", (nid,))
    return True

EVENT_SQL = """SELECT e.*, c.name category, v.name venue, v.capacity venue_capacity, u.name organizer,
  (SELECT COUNT(*) FROM registrations r WHERE r.event_id=e.id AND r.status='CONFIRMED') registered
  FROM events e JOIN event_categories c ON c.id=e.category_id JOIN venues v ON v.id=e.venue_id JOIN users u ON u.id=e.organizer_id"""

def get_event(c, eid):
    e = q1(c, EVENT_SQL + " WHERE e.id=?", (eid,))
    if not e: raise HTTPException(404, "Event not found")
    return e

# ---------- models ----------
class Signup(BaseModel):
    name: str = Field(min_length=2, max_length=100); email: EmailStr; password: str = Field(min_length=8, max_length=72)
    reg_no: Optional[str] = None; department: Optional[str] = None
class Login(BaseModel): email: EmailStr; password: str
class EventIn(BaseModel):
    title: str = Field(min_length=3, max_length=200); description: str = ""; category_id: int; venue_id: int
    event_date: str; start_time: str; end_time: str; max_participants: int = Field(gt=0); registration_deadline: str
class ProfileIn(BaseModel):
    name: Optional[str] = Field(None, min_length=2); department: Optional[str] = None; phone: Optional[str] = None
class PasswordIn(BaseModel): current: str; new: str = Field(min_length=8, max_length=72)
class ScheduleReq(BaseModel):
    expected: int = Field(gt=0); date_from: str; date_to: str; category_id: Optional[int] = None
    duration_min: int = 120; preferred_venue_id: Optional[int] = None; preferred_date: Optional[str] = None; preferred_time: Optional[str] = None
class FeedbackIn(BaseModel): rating: int = Field(ge=1, le=5); comments: str = ""; suggestions: str = ""
class ScanIn(BaseModel): token: str
class RoleIn(BaseModel): role: str
class VenueIn(BaseModel): name: str; capacity: int = Field(gt=0); location: str = ""; active: bool = True
class CalIn(BaseModel): title: str; kind: str; start_date: str; end_date: str; hard_block: bool = True; venue_id: Optional[int] = None
class RejectIn(BaseModel): reason: str = Field(min_length=3)

# ---------- auth ----------
@app.post("/api/auth/signup", status_code=201)
def signup(b: Signup):
    c = db.conn()
    try:
        if q1(c, "SELECT 1 FROM users WHERE email=?", (b.email.lower(),)): raise HTTPException(409, "Email already registered")
        c.execute("INSERT INTO users(name,email,reg_no,department,password_hash,role_id) VALUES(?,?,?,?,?,3)",
                  (b.name, b.email.lower(), b.reg_no, b.department, hash_pw(b.password)))
        uid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        u = {"id": uid, "role": "STUDENT", "name": b.name, "email": b.email.lower()}
        return {"token": make_token(u), "user": u}
    finally: c.close()

@app.post("/api/auth/login")
def login(b: Login):
    c = db.conn()
    try:
        r = q1(c, "SELECT u.*, r.name role FROM users u JOIN roles r ON r.id=u.role_id WHERE email=?", (b.email.lower(),))
        if not r or not bcrypt.checkpw(b.password.encode(), r["password_hash"].encode()): raise HTTPException(401, "Invalid email or password")
        return {"token": make_token(r), "user": {k: r[k] for k in ("id", "name", "email", "role", "reg_no", "department")}}
    finally: c.close()

@app.get("/api/me")
def me(u=Depends(current_user)): return u

@app.put("/api/me")
def update_me(b: ProfileIn, u=Depends(current_user)):
    c = db.conn()
    try:
        c.execute("UPDATE users SET name=COALESCE(?,name), department=COALESCE(?,department), phone=COALESCE(?,phone) WHERE id=?", (b.name, b.department, b.phone, u["id"]))
        return q1(c, "SELECT u.id,u.name,u.email,u.reg_no,u.department,u.phone,r.name role FROM users u JOIN roles r ON r.id=u.role_id WHERE u.id=?", (u["id"],))
    finally: c.close()

@app.put("/api/me/password")
def change_pw(b: PasswordIn, u=Depends(current_user)):
    c = db.conn()
    try:
        r = q1(c, "SELECT password_hash FROM users WHERE id=?", (u["id"],))
        if not bcrypt.checkpw(b.current.encode(), r["password_hash"].encode()): raise HTTPException(400, "Current password is incorrect")
        c.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_pw(b.new), u["id"])); return {"ok": True}
    finally: c.close()

# ---------- reference data ----------
@app.get("/api/categories")
def categories():
    c = db.conn(); 
    try: return q(c, "SELECT * FROM event_categories ORDER BY name")
    finally: c.close()

@app.get("/api/venues")
def venues():
    c = db.conn()
    try: return q(c, "SELECT * FROM venues ORDER BY name")
    finally: c.close()

@app.post("/api/venues", status_code=201)
def add_venue(b: VenueIn, u=Depends(need("ADMIN"))):
    c = db.conn()
    try: c.execute("INSERT INTO venues(name,capacity,location,active) VALUES(?,?,?,?)", (b.name, b.capacity, b.location, int(b.active))); return {"ok": True}
    finally: c.close()

@app.put("/api/venues/{vid}")
def edit_venue(vid: int, b: VenueIn, u=Depends(need("ADMIN"))):
    c = db.conn()
    try: c.execute("UPDATE venues SET name=?,capacity=?,location=?,active=? WHERE id=?", (b.name, b.capacity, b.location, int(b.active), vid)); return {"ok": True}
    finally: c.close()

@app.get("/api/calendar")
def calendar(u=Depends(current_user)):
    c = db.conn()
    try: return q(c, "SELECT * FROM academic_calendar ORDER BY start_date")
    finally: c.close()

@app.post("/api/calendar", status_code=201)
def add_cal(b: CalIn, u=Depends(need("ADMIN"))):
    if b.kind not in ("EXAM", "HOLIDAY", "MAINTENANCE"): raise HTTPException(422, "Invalid kind")
    c = db.conn()
    try: c.execute("INSERT INTO academic_calendar(title,kind,start_date,end_date,hard_block,venue_id) VALUES(?,?,?,?,?,?)", (b.title, b.kind, b.start_date, b.end_date, int(b.hard_block), b.venue_id)); return {"ok": True}
    finally: c.close()

@app.delete("/api/calendar/{cid}")
def del_cal(cid: int, u=Depends(need("ADMIN"))):
    c = db.conn()
    try: c.execute("DELETE FROM academic_calendar WHERE id=?", (cid,)); return {"ok": True}
    finally: c.close()

# ---------- users (admin) ----------
@app.get("/api/admin/users")
def users(u=Depends(need("ADMIN"))):
    c = db.conn()
    try: return q(c, "SELECT u.id,u.name,u.email,u.reg_no,u.department,r.name role FROM users u JOIN roles r ON r.id=u.role_id ORDER BY u.id")
    finally: c.close()

@app.put("/api/admin/users/{uid}/role")
def set_role(uid: int, b: RoleIn, u=Depends(need("ADMIN"))):
    rid = {"ADMIN": 1, "ORGANIZER": 2, "STUDENT": 3}.get(b.role)
    if not rid: raise HTTPException(422, "Invalid role")
    c = db.conn()
    try: c.execute("UPDATE users SET role_id=? WHERE id=?", (rid, uid)); return {"ok": True}
    finally: c.close()

# ---------- events ----------
@app.get("/api/public/events")
def public_events():
    c = db.conn()
    try: return q(c, EVENT_SQL + " WHERE e.status='APPROVED' AND e.event_date>=? ORDER BY e.event_date, e.start_time LIMIT 8", (date.today().isoformat(),))
    finally: c.close()

@app.get("/api/events")
def list_events(u=Depends(current_user), search: str = "", status: str = "", category_id: int = 0, mine: bool = False):
    sql, a = EVENT_SQL + " WHERE 1=1", []
    if u["role"] == "STUDENT": sql += " AND e.status IN ('APPROVED','COMPLETED')"
    if u["role"] == "ORGANIZER" and mine: sql += " AND e.organizer_id=?"; a.append(u["id"])
    if search: sql += " AND (e.title LIKE ? OR e.description LIKE ?)"; a += [f"%{search}%"] * 2
    if status: sql += " AND e.status=?"; a.append(status)
    if category_id: sql += " AND e.category_id=?"; a.append(category_id)
    c = db.conn()
    try: return q(c, sql + " ORDER BY e.event_date DESC, e.start_time", a)
    finally: c.close()

@app.get("/api/events/{eid}")
def event_detail(eid: int, u=Depends(current_user)):
    c = db.conn()
    try:
        e = get_event(c, eid)
        if u["role"] == "STUDENT":
            e["my_registration"] = q1(c, "SELECT id,registration_code,status FROM registrations WHERE event_id=? AND user_id=?", (eid, u["id"]))
        return e
    finally: c.close()

def validate_event(c, b: EventIn, exclude=None):
    if b.end_time <= b.start_time: raise HTTPException(422, "End time must be after start time")
    v = q1(c, "SELECT * FROM venues WHERE id=?", (b.venue_id,))
    if not v: raise HTTPException(422, "Unknown venue")
    if b.max_participants > v["capacity"]: raise HTTPException(422, f"Venue capacity is {v['capacity']}")
    reason = scheduling.hard_conflict(c, v, b.event_date, b.start_time, b.end_time, exclude)
    if reason: raise HTTPException(409, f"Scheduling conflict: {reason}")

@app.post("/api/events/check")
def check_slot(b: EventIn, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        v = q1(c, "SELECT * FROM venues WHERE id=?", (b.venue_id,))
        r = scheduling.hard_conflict(c, v, b.event_date, b.start_time, b.end_time) if v else "Unknown venue"
        return {"available": r is None, "reason": r}
    finally: c.close()

@app.post("/api/events", status_code=201)
def create_event(b: EventIn, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        validate_event(c, b)
        c.execute("""INSERT INTO events(title,description,category_id,organizer_id,venue_id,event_date,start_time,end_time,max_participants,registration_deadline,status)
                     VALUES(?,?,?,?,?,?,?,?,?,?,'DRAFT')""", (b.title, b.description, b.category_id, u["id"], b.venue_id, b.event_date, b.start_time, b.end_time, b.max_participants, b.registration_deadline))
        return get_event(c, c.execute("SELECT last_insert_rowid()").fetchone()[0])
    finally: c.close()

def owned(c, eid, u):
    e = get_event(c, eid)
    if u["role"] != "ADMIN" and e["organizer_id"] != u["id"]: raise HTTPException(403, "Not your event")
    return e

@app.put("/api/events/{eid}")
def edit_event(eid: int, b: EventIn, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        e = owned(c, eid, u)
        if e["status"] in ("COMPLETED", "CANCELLED"): raise HTTPException(400, "Event can no longer be edited")
        validate_event(c, b, eid)
        c.execute("""UPDATE events SET title=?,description=?,category_id=?,venue_id=?,event_date=?,start_time=?,end_time=?,max_participants=?,registration_deadline=? WHERE id=?""",
                  (b.title, b.description, b.category_id, b.venue_id, b.event_date, b.start_time, b.end_time, b.max_participants, b.registration_deadline, eid))
        if e["status"] == "APPROVED" and (e["event_date"], e["start_time"], e["venue_id"]) != (b.event_date, b.start_time, b.venue_id):
            for r in q(c, "SELECT user_id FROM registrations WHERE event_id=? AND status='CONFIRMED'", (eid,)):
                send_mail(c, r["user_id"], eid, "SCHEDULE_UPDATE", f"Schedule updated: {b.title}", f"New schedule: {b.event_date} {b.start_time}-{b.end_time}.")
                c.execute("DELETE FROM notifications WHERE user_id=? AND event_id=? AND type IN ('REMINDER_24H','REMINDER_1H')", (r["user_id"], eid))
        return get_event(c, eid)
    finally: c.close()

@app.delete("/api/events/{eid}")
def delete_event(eid: int, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        e = owned(c, eid, u)
        if q1(c, "SELECT 1 FROM registrations WHERE event_id=?", (eid,)): raise HTTPException(400, "Event has registrations; cancel it instead")
        c.execute("DELETE FROM events WHERE id=?", (eid,)); return {"ok": True}
    finally: c.close()

@app.post("/api/events/{eid}/submit")
def submit_event(eid: int, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        e = owned(c, eid, u)
        if e["status"] not in ("DRAFT", "REJECTED"): raise HTTPException(400, "Only draft or rejected events can be submitted")
        c.execute("UPDATE events SET status='PENDING', reject_reason=NULL WHERE id=?", (eid,)); return get_event(c, eid)
    finally: c.close()

@app.post("/api/events/{eid}/approve")
def approve(eid: int, u=Depends(need("ADMIN"))):
    c = db.conn()
    try:
        e = get_event(c, eid)
        if e["status"] != "PENDING": raise HTTPException(400, "Event is not pending")
        v = q1(c, "SELECT * FROM venues WHERE id=?", (e["venue_id"],))
        r = scheduling.hard_conflict(c, v, e["event_date"], e["start_time"], e["end_time"], eid)
        if r: raise HTTPException(409, f"Cannot approve: {r}")
        c.execute("UPDATE events SET status='APPROVED' WHERE id=?", (eid,)); return get_event(c, eid)
    finally: c.close()

@app.post("/api/events/{eid}/reject")
def reject(eid: int, b: RejectIn, u=Depends(need("ADMIN"))):
    c = db.conn()
    try:
        e = get_event(c, eid)
        if e["status"] != "PENDING": raise HTTPException(400, "Event is not pending")
        c.execute("UPDATE events SET status='REJECTED', reject_reason=? WHERE id=?", (b.reason, eid)); return get_event(c, eid)
    finally: c.close()

@app.post("/api/events/{eid}/cancel")
def cancel(eid: int, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        e = owned(c, eid, u)
        if e["status"] in ("COMPLETED", "CANCELLED"): raise HTTPException(400, "Already closed")
        c.execute("UPDATE events SET status='CANCELLED' WHERE id=?", (eid,))
        for r in q(c, "SELECT user_id FROM registrations WHERE event_id=? AND status='CONFIRMED'", (eid,)):
            send_mail(c, r["user_id"], eid, "CANCELLATION", f"Event cancelled: {e['title']}", "We are sorry, this event has been cancelled.")
        return get_event(c, eid)
    finally: c.close()

@app.post("/api/events/{eid}/complete")
def complete(eid: int, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        e = owned(c, eid, u)
        if e["status"] != "APPROVED": raise HTTPException(400, "Only approved events can be completed")
        c.execute("UPDATE events SET status='COMPLETED' WHERE id=?", (eid,)); return get_event(c, eid)
    finally: c.close()

# ---------- scheduling ----------
@app.post("/api/scheduling/recommend")
def recommend(b: ScheduleReq, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try: return scheduling.recommend(c, b.model_dump(), u["id"])
    finally: c.close()

# ---------- registration ----------
def next_code(c, e):
    n = q1(c, "SELECT COUNT(*) n FROM registrations WHERE event_id=?", (e["id"],))["n"] + 1
    return f"EVT{e['id']:03d}-{n:04d}-{secrets.token_hex(2).upper()}"

@app.post("/api/events/{eid}/register", status_code=201)
def register(eid: int, u=Depends(need("STUDENT"))):
    c = db.conn()
    try:
        c.execute("BEGIN IMMEDIATE")          # write lock serialises concurrent sign-ups (like SELECT ... FOR UPDATE)
        try:
            e = q1(c, "SELECT * FROM events WHERE id=?", (eid,))
            if not e: raise HTTPException(404, "Event not found")
            if e["status"] != "APPROVED": raise HTTPException(400, "Event is not open for registration")
            if now() > datetime.fromisoformat(e["registration_deadline"]): raise HTTPException(400, "Registration deadline has passed")
            if q1(c, "SELECT 1 FROM registrations WHERE event_id=? AND user_id=? AND status='CONFIRMED'", (eid, u["id"])): raise HTTPException(409, "Already registered")
            if q1(c, "SELECT COUNT(*) n FROM registrations WHERE event_id=? AND status='CONFIRMED'", (eid,))["n"] >= e["max_participants"]: raise HTTPException(400, "Event is full")
            r = q1(c, "SELECT * FROM registrations WHERE event_id=? AND user_id=?", (eid, u["id"]))
            if r: c.execute("UPDATE registrations SET status='CONFIRMED', cancelled_at=NULL WHERE id=?", (r["id"],)); rid = r["id"]
            else:
                c.execute("INSERT INTO registrations(registration_code,event_id,user_id,qr_token) VALUES(?,?,?,?)", (next_code(c, e), eid, u["id"], str(uuid.uuid4())))
                rid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            send_mail(c, u["id"], eid, "CONFIRMATION", f"Registration confirmed: {e['title']}", f"You are registered for {e['title']} on {e['event_date']} at {e['start_time']}.")
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK"); raise
        return q1(c, "SELECT id,registration_code,status,qr_token FROM registrations WHERE id=?", (rid,))
    finally: c.close()

@app.delete("/api/events/{eid}/register")
def unregister(eid: int, u=Depends(need("STUDENT"))):
    c = db.conn()
    try:
        r = q1(c, "SELECT * FROM registrations WHERE event_id=? AND user_id=? AND status='CONFIRMED'", (eid, u["id"]))
        if not r: raise HTTPException(404, "No active registration")
        if q1(c, "SELECT 1 FROM attendance WHERE registration_id=?", (r["id"],)): raise HTTPException(400, "Attendance already recorded")
        c.execute("UPDATE registrations SET status='CANCELLED', cancelled_at=? WHERE id=?", (iso(now()), r["id"])); return {"ok": True}
    finally: c.close()

@app.get("/api/my/registrations")
def my_regs(u=Depends(need("STUDENT"))):
    c = db.conn()
    try:
        return q(c, """SELECT r.id,r.registration_code,r.status,r.qr_token,r.registered_at,e.id event_id,e.title,e.event_date,e.start_time,e.end_time,e.status event_status,v.name venue,
                       (SELECT 1 FROM attendance a WHERE a.registration_id=r.id) attended,
                       (SELECT 1 FROM feedback f WHERE f.event_id=e.id AND f.user_id=r.user_id) feedback_given
                       FROM registrations r JOIN events e ON e.id=r.event_id JOIN venues v ON v.id=e.venue_id WHERE r.user_id=? ORDER BY e.event_date DESC""", (u["id"],))
    finally: c.close()

@app.get("/api/registrations/{rid}/qr")
def qr_png(rid: int, token: Optional[str] = None, authorization: Optional[str] = Header(None)):
    c = db.conn()
    try:
        r = q1(c, "SELECT * FROM registrations WHERE id=?", (rid,))
        if not r: raise HTTPException(404, "Not found")
        u = None
        if authorization: u = current_user(authorization)
        if not u or (u["id"] != r["user_id"] and u["role"] == "STUDENT"): raise HTTPException(403, "Forbidden")
        img = qrcode.make(r["qr_token"], box_size=8, border=2); buf = io.BytesIO(); img.save(buf, "PNG")
        return Response(buf.getvalue(), media_type="image/png")
    finally: c.close()

@app.get("/api/events/{eid}/registrations")
def event_regs(eid: int, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        owned(c, eid, u)
        return q(c, """SELECT r.id,r.registration_code,r.status,r.registered_at,u.name,u.email,u.reg_no,u.department,
                       (SELECT scanned_at FROM attendance a WHERE a.registration_id=r.id) attended_at
                       FROM registrations r JOIN users u ON u.id=r.user_id WHERE r.event_id=? ORDER BY r.registered_at""", (eid,))
    finally: c.close()

# ---------- attendance ----------
@app.post("/api/attendance/scan")
def scan(b: ScanIn, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        c.execute("BEGIN IMMEDIATE")
        try:
            r = q1(c, "SELECT * FROM registrations WHERE qr_token=?", (b.token.strip(),))
            if not r: raise HTTPException(400, "Invalid QR code")
            if r["status"] != "CONFIRMED": raise HTTPException(400, "Registration is not active")
            e = get_event(c, r["event_id"])
            if u["role"] != "ADMIN" and e["organizer_id"] != u["id"]: raise HTTPException(403, "Not your event")
            if e["event_date"] != date.today().isoformat(): raise HTTPException(400, "Event is not today")
            if q1(c, "SELECT 1 FROM attendance WHERE registration_id=?", (r["id"],)): raise HTTPException(409, "Attendance already recorded")
            c.execute("INSERT INTO attendance(registration_id,event_id,scanned_by,scanned_at) VALUES(?,?,?,?)", (r["id"], e["id"], u["id"], iso(now())))
            who = q1(c, "SELECT name,reg_no FROM users WHERE id=?", (r["user_id"],))
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK"); raise
        return {"ok": True, "student": who["name"], "reg_no": who["reg_no"], "event": e["title"]}
    finally: c.close()

@app.get("/api/events/{eid}/attendance")
def attendance_report(eid: int, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        owned(c, eid, u)
        conf = q1(c, "SELECT COUNT(*) n FROM registrations WHERE event_id=? AND status='CONFIRMED'", (eid,))["n"]
        rows = q(c, """SELECT a.scanned_at, u.name, u.reg_no FROM attendance a JOIN registrations r ON r.id=a.registration_id JOIN users u ON u.id=r.user_id WHERE a.event_id=? ORDER BY a.scanned_at DESC""", (eid,))
        return {"confirmed": conf, "attended": len(rows), "percentage": round(100 * len(rows) / conf, 1) if conf else 0, "records": rows}
    finally: c.close()

# ---------- feedback ----------
@app.post("/api/events/{eid}/feedback", status_code=201)
def feedback(eid: int, b: FeedbackIn, u=Depends(need("STUDENT"))):
    c = db.conn()
    try:
        e = get_event(c, eid)
        if e["status"] != "COMPLETED": raise HTTPException(400, "Feedback opens after the event is completed")
        r = q1(c, "SELECT id FROM registrations WHERE event_id=? AND user_id=? AND status='CONFIRMED'", (eid, u["id"]))
        if not r: raise HTTPException(403, "Only registered participants can give feedback")
        if q1(c, "SELECT 1 FROM feedback WHERE event_id=? AND user_id=?", (eid, u["id"])): raise HTTPException(409, "Feedback already submitted")
        c.execute("INSERT INTO feedback(event_id,user_id,rating,comments,suggestions) VALUES(?,?,?,?,?)", (eid, u["id"], b.rating, b.comments, b.suggestions))
        fid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        a = sentiment.analyse_one(b.comments + " " + b.suggestions)
        c.execute("INSERT INTO feedback_analysis(feedback_id,sentiment,confidence,topics,complaints,model_version) VALUES(?,?,?,?,?,?)",
                  (fid, a["sentiment"], a["confidence"], json.dumps(a["topics"]), json.dumps(a["complaints"]), sentiment.VERSION))
        return {"ok": True, "analysis": a}
    finally: c.close()

@app.get("/api/events/{eid}/feedback-analysis")
def feedback_analysis(eid: int, u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        owned(c, eid, u)
        rows = q(c, """SELECT f.rating,f.comments,f.suggestions,a.sentiment,a.confidence,a.topics,a.complaints FROM feedback f JOIN feedback_analysis a ON a.feedback_id=f.id WHERE f.event_id=?""", (eid,))
        n = len(rows); split = {k: 0 for k in ("Positive", "Neutral", "Negative")}; top, comp = {}, {}
        for r in rows:
            split[r["sentiment"]] += 1
            for t in json.loads(r["topics"] or "[]"):
                if r["sentiment"] == "Positive": top[t] = top.get(t, 0) + 1
            for t in json.loads(r["complaints"] or "[]"): comp[t] = comp.get(t, 0) + 1
        avg = round(sum(r["rating"] for r in rows) / n, 2) if n else 0
        sug = [r["suggestions"] for r in rows if r["suggestions"].strip()][:6]
        srt = lambda d: [{"topic": k, "count": v} for k, v in sorted(d.items(), key=lambda x: -x[1])]
        summary = (f"{n} responses, average rating {avg}/5. " + (f"Most appreciated: {', '.join(x['topic'] for x in srt(top)[:3])}. " if top else "")
                   + (f"Most common complaints: {', '.join(x['topic'] for x in srt(comp)[:3])}." if comp else "No recurring complaints detected.")) if n else "No feedback yet."
        return {"count": n, "average_rating": avg, "sentiment": split, "satisfaction_pct": round(100 * split["Positive"] / n, 1) if n else 0,
                "appreciated": srt(top), "complaints": srt(comp), "suggestions": sug, "summary": summary,
                "nmf_topics": sentiment.nmf_topics([r["comments"] for r in rows]), "responses": rows[:8]}
    finally: c.close()

@app.get("/api/ml/metrics")
def ml_metrics(u=Depends(current_user)): return sentiment.metrics()

# ---------- analytics & archive ----------
@app.get("/api/analytics")
def analytics(u=Depends(need("ADMIN", "ORGANIZER"))):
    c = db.conn()
    try:
        own, a = (" AND e.organizer_id=?", [u["id"]]) if u["role"] == "ORGANIZER" else ("", [])
        t = lambda s, x=(): q1(c, s, list(x) + a)
        tot = {"events": t("SELECT COUNT(*) n FROM events e WHERE 1=1" + own)["n"],
               "registrations": t("SELECT COUNT(*) n FROM registrations r JOIN events e ON e.id=r.event_id WHERE r.status='CONFIRMED'" + own)["n"],
               "attendance": t("SELECT COUNT(*) n FROM attendance x JOIN events e ON e.id=x.event_id WHERE 1=1" + own)["n"],
               "users": q1(c, "SELECT COUNT(*) n FROM users")["n"], "pending": t("SELECT COUNT(*) n FROM events e WHERE status='PENDING'" + own)["n"]}
        by_status = q(c, "SELECT status name, COUNT(*) value FROM events e WHERE 1=1" + own + " GROUP BY status", a)
        monthly = q(c, "SELECT substr(event_date,1,7) month, COUNT(*) events FROM events e WHERE 1=1" + own + " GROUP BY month ORDER BY month", a)
        cat = q(c, """SELECT c.name name, COUNT(r.id) registrations FROM event_categories c LEFT JOIN events e ON e.category_id=c.id
                      LEFT JOIN registrations r ON r.event_id=e.id AND r.status='CONFIRMED' WHERE 1=1""" + own + " GROUP BY c.id ORDER BY registrations DESC", a)
        att = q(c, """SELECT e.title, COUNT(DISTINCT r.id) registered, COUNT(DISTINCT x.id) attended FROM events e
                      LEFT JOIN registrations r ON r.event_id=e.id AND r.status='CONFIRMED' LEFT JOIN attendance x ON x.registration_id=r.id
                      WHERE e.status IN ('COMPLETED','APPROVED')""" + own + " GROUP BY e.id HAVING registered>0 ORDER BY e.event_date DESC LIMIT 8", a)
        sent = q(c, """SELECT a.sentiment name, COUNT(*) value FROM feedback_analysis a JOIN feedback f ON f.id=a.feedback_id JOIN events e ON e.id=f.event_id WHERE 1=1""" + own + " GROUP BY a.sentiment", a)
        return {"totals": tot, "by_status": by_status, "monthly": monthly, "categories": cat, "attendance": att, "sentiment": sent,
                "pending_events": q(c, EVENT_SQL + " WHERE e.status='PENDING'" + own.replace("e.organizer_id", "e.organizer_id") + " ORDER BY e.event_date", a)}
    finally: c.close()

@app.get("/api/archive")
def archive(u=Depends(current_user), search: str = "", category_id: int = 0, organizer: str = "", date_from: str = "", date_to: str = ""):
    sql = """SELECT e.id,e.title,e.event_date,e.status,c.name category,u.name organizer,v.name venue,
      (SELECT COUNT(*) FROM registrations r WHERE r.event_id=e.id AND r.status='CONFIRMED') registered,
      (SELECT COUNT(*) FROM attendance a WHERE a.event_id=e.id) attended,
      (SELECT ROUND(AVG(rating),2) FROM feedback f WHERE f.event_id=e.id) avg_rating
      FROM events e JOIN event_categories c ON c.id=e.category_id JOIN users u ON u.id=e.organizer_id JOIN venues v ON v.id=e.venue_id
      WHERE e.status IN ('COMPLETED','CANCELLED')"""
    a = []
    if search: sql += " AND e.title LIKE ?"; a.append(f"%{search}%")
    if category_id: sql += " AND e.category_id=?"; a.append(category_id)
    if organizer: sql += " AND u.name LIKE ?"; a.append(f"%{organizer}%")
    if date_from: sql += " AND e.event_date>=?"; a.append(date_from)
    if date_to: sql += " AND e.event_date<=?"; a.append(date_to)
    c = db.conn()
    try: return q(c, sql + " ORDER BY e.event_date DESC", a)
    finally: c.close()

# ---------- reminder job ----------
def reminder_pass():
    c = db.conn()
    try:
        for e in q(c, "SELECT * FROM events WHERE status='APPROVED'"):
            start = datetime.fromisoformat(f"{e['event_date']} {e['start_time']}")
            for typ, delta in (("REMINDER_24H", timedelta(hours=24)), ("REMINDER_1H", timedelta(hours=1))):
                if start - delta <= now() < start:
                    for r in q(c, "SELECT user_id FROM registrations WHERE event_id=? AND status='CONFIRMED'", (e["id"],)):
                        send_mail(c, r["user_id"], e["id"], typ, f"Reminder: {e['title']}", f"{e['title']} starts on {e['event_date']} at {e['start_time']}.")
        for n in q(c, "SELECT id FROM notifications WHERE status IN ('FAILED','PENDING')"):      # retry unsent mail
            c.execute("UPDATE notifications SET status='SENT', sent_at=? WHERE id=?", (iso(now()), n["id"]))
    finally: c.close()

def _loop():
    while True:
        try: reminder_pass()
        except Exception: log.exception("reminder job failed")
        time.sleep(60)

@app.on_event("startup")
def start_jobs():
    if os.environ.get("DISABLE_JOBS") != "1": threading.Thread(target=_loop, daemon=True).start()

@app.get("/api/notifications")
def my_notifications(u=Depends(current_user)):
    c = db.conn()
    try: return q(c, "SELECT type,subject,status,created_at FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 20", (u["id"],))
    finally: c.close()
