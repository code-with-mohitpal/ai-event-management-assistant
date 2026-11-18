import os, tempfile
os.environ["EVENTS_DB"] = os.path.join(tempfile.mkdtemp(), "t.db"); os.environ["DISABLE_JOBS"] = "1"
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app import seed, sentiment
from app.main import app
seed.run()
cl = TestClient(app)
D = lambda n: (date.today() + timedelta(days=n)).isoformat()

def auth(email, pw):
    r = cl.post("/api/auth/login", json={"email": email, "password": pw}); assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}
ORG = lambda: auth("organizer@lpu.in", "Organizer@123")
STU = lambda: auth("student@lpu.in", "Student@123")
ADM = lambda: auth("admin@lpu.in", "Admin@123")
def ev(**k):
    b = dict(title="Test Event", description="d", category_id=1, venue_id=1, event_date=D(25), start_time="10:00", end_time="12:00", max_participants=50, registration_deadline=D(24) + " 10:00:00"); b.update(k); return b

def test_01_overlap_rejected():
    d = D(60)  # outside exam/holiday windows
    assert cl.post("/api/events", json=ev(event_date=d, start_time="10:00", end_time="12:00"), headers=ORG()).status_code == 201
    r = cl.post("/api/events", json=ev(event_date=d, start_time="11:00", end_time="13:00", title="Overlap"), headers=ORG())  # draft does not block...
    assert r.status_code == 201
    # submit + approve first, then overlapping must be rejected
    ids = [e["id"] for e in cl.get("/api/events", headers=ADM()).json() if e["event_date"] == d]
    first = min(ids); cl.post(f"/api/events/{first}/submit", headers=ORG()); assert cl.post(f"/api/events/{first}/approve", headers=ADM()).status_code == 200
    assert cl.post("/api/events", json=ev(event_date=d, start_time="11:00", end_time="13:00", title="Overlap2"), headers=ORG()).status_code == 409
    assert cl.post("/api/events", json=ev(event_date=d, start_time="12:00", end_time="14:00", title="Adjacent"), headers=ORG()).status_code == 201

def test_02_exam_hard_conflict():
    r = cl.post("/api/events", json=ev(event_date=D(20)), headers=ORG()); assert r.status_code == 409 and "Exam" in r.text
    s = cl.post("/api/scheduling/recommend", json=dict(expected=50, date_from=D(17), date_to=D(34)), headers=ORG()).json()
    assert all(not (D(18) <= x["date"] <= D(32)) for x in s["recommendations"])
    assert any("Exam" in x["reason"] for x in s["conflicts"])

def test_03_venue_unavailable():
    assert cl.post("/api/events", json=ev(venue_id=7, event_date=D(62), max_participants=50), headers=ORG()).status_code == 409
    s = cl.post("/api/scheduling/recommend", json=dict(expected=50, date_from=D(60), date_to=D(62)), headers=ORG()).json()
    assert all(x["venue_id"] != 7 for x in s["recommendations"]) and any("inactive" in x["reason"] for x in s["conflicts"])
    s = cl.post("/api/scheduling/recommend", json=dict(expected=50, date_from=D(9), date_to=D(10)), headers=ORG()).json()
    assert all(not (x["venue_id"] == 1 and x["date"] in (D(9), D(10))) for x in s["recommendations"])

def test_recommendations_sorted_scored_explained():
    s = cl.post("/api/scheduling/recommend", json=dict(expected=100, date_from=D(1), date_to=D(14), category_id=1), headers=ORG()).json()
    sc = [x["score"] for x in s["recommendations"]]; assert sc == sorted(sc, reverse=True) and all(0 <= v <= 100 for v in sc)
    assert all(x["explanation"] and not x["conflict"] for x in s["recommendations"])

def _open_event(cap):
    eid = cl.post("/api/events", json=ev(event_date=D(70), venue_id=6, max_participants=cap, title=f"Cap{cap}"), headers=ORG()).json()["id"]
    cl.post(f"/api/events/{eid}/submit", headers=ORG()); assert cl.post(f"/api/events/{eid}/approve", headers=ADM()).status_code == 200; return eid

def test_04_capacity_and_05_duplicate():
    eid = _open_event(2)
    for i, e in enumerate(["s1@lpu.in", "s2@lpu.in"]): assert cl.post(f"/api/events/{eid}/register", headers=auth(e, "Student@123")).status_code == 201
    assert cl.post(f"/api/events/{eid}/register", headers=auth("s3@lpu.in", "Student@123")).status_code == 400   # full
    assert cl.post(f"/api/events/{eid}/register", headers=auth("s1@lpu.in", "Student@123")).status_code == 409   # duplicate
    # cancel frees seat and can be re-activated
    assert cl.delete(f"/api/events/{eid}/register", headers=auth("s1@lpu.in", "Student@123")).status_code == 200
    assert cl.post(f"/api/events/{eid}/register", headers=auth("s3@lpu.in", "Student@123")).status_code == 201

def test_06_duplicate_qr_scan():
    regs = cl.get("/api/my/registrations", headers=STU()).json(); r = [x for x in regs if x["registration_code"] == "EVT-DEMO-0001"][0]
    assert cl.post("/api/attendance/scan", json={"token": "bad"}, headers=ORG()).status_code == 400
    a = cl.post("/api/attendance/scan", json={"token": r["qr_token"]}, headers=ORG()); assert a.status_code == 200
    assert cl.post("/api/attendance/scan", json={"token": r["qr_token"]}, headers=ORG()).status_code == 409
    rep = cl.get(f"/api/events/{r['event_id']}/attendance", headers=ORG()).json(); assert rep["attended"] == 1 and rep["percentage"] > 0
    assert cl.post("/api/attendance/scan", json={"token": r["qr_token"]}, headers=auth("arjun@lpu.in", "Organizer@123")).status_code in (403, 409)

def test_auth_rules():
    assert cl.get("/api/events").status_code == 401
    assert cl.post("/api/auth/login", json={"email": "student@lpu.in", "password": "wrong"}).status_code == 401
    assert cl.post("/api/events", json=ev(), headers=STU()).status_code == 403
    assert cl.get("/api/admin/users", headers=ORG()).status_code == 403
    assert "password" not in cl.get("/api/me", headers=STU()).text

def test_signup_duplicate_and_short_password():
    ok = dict(name="New Student", email="new@lpu.in", password="Password123"); assert cl.post("/api/auth/signup", json=ok).status_code == 201
    assert cl.post("/api/auth/signup", json=ok).status_code == 409
    assert cl.post("/api/auth/signup", json={**ok, "email": "x@lpu.in", "password": "short"}).status_code == 422

def test_feedback_rules():
    done = [e for e in cl.get("/api/events", headers=STU()).json() if e["status"] == "COMPLETED"]
    mine = [r for r in cl.get("/api/my/registrations", headers=STU()).json() if r["event_status"] == "COMPLETED" and not r["feedback_given"]]
    if mine:
        r = cl.post(f"/api/events/{mine[0]['event_id']}/feedback", json=dict(rating=5, comments="The speaker was excellent and very well handled."), headers=STU()); assert r.status_code == 201
        assert r.json()["analysis"]["sentiment"] == "Positive"
        assert cl.post(f"/api/events/{mine[0]['event_id']}/feedback", json=dict(rating=5), headers=STU()).status_code == 409
    assert cl.post(f"/api/events/{done[0]['id']}/feedback", json=dict(rating=9), headers=STU()).status_code == 422

def test_07_08_09_sentiment_model():
    for text, lab in [("The speaker was excellent and I really enjoyed the session, great work.", "Positive"),
                      ("The venue was terrible and the whole event was very disappointing.", "Negative"),
                      ("The schedule was okay, nothing special, just average.", "Neutral")]:
        assert sentiment.analyse_one(text)["sentiment"] == lab
    m = sentiment.metrics(); assert m["test_size"] == 124 and 0 <= m["accuracy"] <= 1

def test_analytics_and_archive():
    a = cl.get("/api/analytics", headers=ADM()).json(); assert a["totals"]["events"] > 0 and a["sentiment"]
    assert all(r["status"] in ("COMPLETED", "CANCELLED") for r in cl.get("/api/archive?search=Workshop", headers=STU()).json())
