"""Seeds demo data (clearly sample data). Run: python -m app.seed"""
import json, os, random, uuid
from datetime import date, datetime, timedelta
from . import db, sentiment
from .main import hash_pw
from .db import q1

def run(reset=True):
    if reset and os.path.exists(db.DB_PATH): os.remove(db.DB_PATH)
    db.init(); c = db.conn(); rnd = random.Random(11); today = date.today(); D = lambda n: (today + timedelta(days=n)).isoformat()
    c.execute("BEGIN")
    def user(name, email, pw, role, reg=None, dept="CSE"):
        c.execute("INSERT INTO users(name,email,reg_no,department,password_hash,role_id) VALUES(?,?,?,?,?,?)", (name, email, reg, dept, hash_pw(pw), role)); return c.execute("SELECT last_insert_rowid()").fetchone()[0]
    admin = user("Dr. Rakesh Sharma", "admin@lpu.in", "Admin@123", 1, None, "Event Coordination Office")
    org1 = user("Priya Verma", "organizer@lpu.in", "Organizer@123", 2, None, "Robotics Club")
    org2 = user("Arjun Mehta", "arjun@lpu.in", "Organizer@123", 2, None, "Cultural Committee")
    stu = user("Mohit Pal", "student@lpu.in", "Student@123", 3, "12413686")
    first = ["Aman", "Riya", "Karan", "Neha", "Rohit", "Sneha", "Vikram", "Anjali", "Deepak", "Pooja", "Harsh", "Simran", "Yash", "Isha", "Nikhil", "Kavya", "Sahil", "Tanvi", "Rahul", "Meera"]
    last = ["Singh", "Kumar", "Gupta", "Patel", "Joshi", "Nair", "Reddy", "Khan", "Das", "Roy"]
    students = [stu]
    for i in range(44): students.append(user(f"{rnd.choice(first)} {rnd.choice(last)}", f"s{i+1}@lpu.in", "Student@123", 3, str(12400000 + i * 37), rnd.choice(["CSE", "ECE", "ME", "BBA"])))
    for n, cap, loc, act in [("Main Auditorium", 600, "Block 34", 1), ("Seminar Hall A", 150, "Block 32", 1), ("Seminar Hall B", 120, "Block 32", 1),
                             ("Innovation Lab", 60, "Block 38", 1), ("Open Air Theatre", 400, "Central Lawn", 1), ("Conference Room 1", 40, "Admin Block", 1), ("Old Gymnasium", 200, "Sports Complex", 0)]:
        c.execute("INSERT INTO venues(name,capacity,location,active) VALUES(?,?,?,?)", (n, cap, loc, act))
    cats = ["Technical", "Cultural", "Workshop", "Seminar", "Sports", "Career"]
    for n in cats: c.execute("INSERT INTO event_categories(name) VALUES(?)", (n,))
    cal = [("End Semester Examinations", "EXAM", D(18), D(32), 1, None), ("Mid-term Examinations", "EXAM", D(-70), D(-60), 1, None),
           ("Winter Break", "HOLIDAY", D(40), D(55), 1, None), ("Guru Nanak Jayanti", "HOLIDAY", D(6), D(6), 1, None),
           ("Auditorium stage repair", "MAINTENANCE", D(9), D(10), 1, 1)]
    for r in cal: c.execute("INSERT INTO academic_calendar(title,kind,start_date,end_date,hard_block,venue_id) VALUES(?,?,?,?,?,?)", r)
    def event(title, desc, cat, org, ven, d, st, en, mx, status, dl_days=1):
        dl = (datetime.fromisoformat(f"{d} {st}") - timedelta(days=dl_days)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO events(title,description,category_id,organizer_id,venue_id,event_date,start_time,end_time,max_participants,registration_deadline,status) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                  (title, desc, cat, org, ven, d, st, en, mx, dl, status)); return c.execute("SELECT last_insert_rowid()").fetchone()[0]
    def regs(eid, n, attend=0.0, d=None):
        ids = []
        for s in rnd.sample(students, min(n, len(students))):
            c.execute("INSERT INTO registrations(registration_code,event_id,user_id,qr_token,registered_at) VALUES(?,?,?,?,?)", (f"EVT{eid:03d}-{len(ids)+1:04d}-{uuid.uuid4().hex[:4].upper()}", eid, s, str(uuid.uuid4()), (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")))
            rid = c.execute("SELECT last_insert_rowid()").fetchone()[0]; ids.append((rid, s))
            if rnd.random() < attend and d: c.execute("INSERT INTO attendance(registration_id,event_id,scanned_by,scanned_at) VALUES(?,?,?,?)", (rid, eid, org1, f"{d} 10:05:00"))
        return ids
    pos = ["The speaker was excellent and very well handled.", "Loved the content, truly outstanding work.", "Great organisation, I would recommend this event to everyone.", "The venue was amazing and exceeded my expectations.", "Fantastic workshop, very helpful and engaging."]
    neu = ["The timing was okay, nothing special.", "The food was average and acceptable.", "The registration process was fine, neither good nor bad."]
    neg = ["The sound system was terrible and very disappointing.", "The timing was bad, the event started late and ran too long.", "Poor food arrangements, I would not attend again.", "The venue was crowded and the seating was poor."]
    sugg = ["Start on time and add more seating.", "Please improve the sound system.", "More hands-on sessions next time.", "Provide refreshments.", ""]
    past = [("AI & Machine Learning Workshop", 1, -63, "10:00", "13:00", 3, 60, "Technical", .86, 5), ("Inter-College Cultural Night", 2, -49, "17:00", "20:00", 5, 300, "Cultural", .78, 2),
            ("Career Guidance Seminar", 1, -35, "11:00", "13:00", 2, 120, "Career", .72, 5), ("Hackathon Kickoff", 1, -21, "09:00", "11:00", 4, 55, "Technical", .8, 4),
            ("Public Speaking Workshop", 2, -12, "14:00", "16:00", 6, 38, "Workshop", .65, 3), ("Cyber Security Seminar", 1, -5, "11:00", "13:00", 2, 110, "Seminar", .82, 4)]
    cid = {n: i + 1 for i, n in enumerate(cats)}
    for t, o, dd, st, en, v, mx, cat, ar, mood in past:
        d = D(dd); eid = event(t, f"{t} organised for university students.", cid[cat], org1 if o == 1 else org2, v, d, st, en, mx + 10, "COMPLETED", 2)
        for rid, s in regs(eid, rnd.randint(28, 40), ar, d):
            if rnd.random() < .6 and q1(c, "SELECT 1 FROM attendance WHERE registration_id=?", (rid,)):
                k = rnd.random(); good = .7 if mood >= 4 else .35
                text, rating = (rnd.choice(pos), rnd.choice([4, 5])) if k < good else ((rnd.choice(neu), 3) if k < good + .15 else (rnd.choice(neg), rnd.choice([1, 2])))
                sg = rnd.choice(sugg)
                c.execute("INSERT INTO feedback(event_id,user_id,rating,comments,suggestions) VALUES(?,?,?,?,?)", (eid, s, rating, text, sg)); fid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
                a = sentiment.analyse_one(text + " " + sg)
                c.execute("INSERT INTO feedback_analysis(feedback_id,sentiment,confidence,topics,complaints,model_version) VALUES(?,?,?,?,?,?)", (fid, a["sentiment"], a["confidence"], json.dumps(a["topics"]), json.dumps(a["complaints"]), sentiment.VERSION))
    # today's event for QR demo
    e = event("Robotics Showcase 2026", "Live demos of student robotics projects, followed by a Q&A with the jury.", cid["Technical"], org1, 2, D(0), "16:00", "18:00", 100, "APPROVED", 0)
    c.execute("UPDATE events SET registration_deadline=? WHERE id=?", ((datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"), e)); regs(e, 30, .0)
    c.execute("INSERT OR IGNORE INTO registrations(registration_code,event_id,user_id,qr_token) VALUES('EVT-DEMO-0001',?,?,?)", (e, stu, "11111111-2222-3333-4444-555555555555"))
    for t, desc, cat, o, v, dd, st, en, mx, stt, n in [("Full-Stack Web Dev Bootcamp", "Hands-on React and APIs bootcamp.", "Workshop", org1, 4, 4, "10:00", "13:00", 50, "APPROVED", 38),
        ("Startup Pitch Day", "Student founders pitch to alumni investors.", "Career", org1, 2, 7, "14:00", "16:00", 140, "APPROVED", 70),
        ("Spring Fest Dance Auditions", "Auditions for the cultural fest.", "Cultural", org2, 5, 8, "16:00", "18:00", 300, "APPROVED", 120),
        ("Inter-Department Cricket League", "T20 knockout round.", "Sports", org2, 5, 12, "09:00", "13:00", 200, "APPROVED", 40),
        ("Quantum Computing Seminar", "Introduction to quantum algorithms.", "Seminar", org1, 3, 15, "11:00", "13:00", 100, "PENDING", 0),
        ("Photography Masterclass", "Composition and editing workshop.", "Workshop", org2, 6, 16, "14:00", "16:00", 35, "PENDING", 0),
        ("Alumni Meet Draft", "Planning draft for alumni meet.", "Career", org1, 1, 20, "10:00", "12:00", 300, "DRAFT", 0)]:
        eid = event(t, desc, cid[cat], o, v, D(dd), st, en, mx, stt, 2)
        if n: regs(eid, n)
    c.execute("COMMIT"); c.close(); print("seeded")

if __name__ == "__main__": run()
