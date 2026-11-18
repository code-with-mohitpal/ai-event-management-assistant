"""Smart scheduling: stage 1 hard-conflict filter (database driven), stage 2 weighted ranking."""
from datetime import date, datetime, timedelta
from .db import q, q1

WEIGHTS = {"venue_fit": 25, "calendar": 25, "load": 20, "preference": 15, "availability": 10, "buffer": 5}
ACTIVE = ("PENDING", "APPROVED")
GRID = ["09:00", "11:00", "14:00", "16:00"]
DURATION_MIN = 120

def hm(t): h, m = t.split(":")[:2]; return int(h) * 60 + int(m)
def fmt(mins): return f"{mins // 60:02d}:{mins % 60:02d}"

def overlaps(s1, e1, s2, e2):
    return s1 < e2 and e1 > s2      # new.start < existing.end and new.end > existing.start

def find_venue_conflicts(c, venue_id, d, start, end, exclude_id=None):
    return q(c, f"""SELECT * FROM events WHERE venue_id=? AND event_date=? AND status IN ('PENDING','APPROVED')
        AND start_time < ? AND end_time > ? AND (? IS NULL OR id<>?)""", (venue_id, d, end, start, exclude_id, exclude_id))

def hard_conflict(c, venue, d, start, end, exclude_id=None):
    """Return a reason string if the slot violates a hard constraint, else None."""
    if not venue["active"]:
        return "Venue is inactive"
    ev = find_venue_conflicts(c, venue["id"], d, start, end, exclude_id)
    if ev:
        return f"Venue already booked by '{ev[0]['title']}' ({ev[0]['start_time']}-{ev[0]['end_time']})"
    for cal in q(c, "SELECT * FROM academic_calendar WHERE hard_block=1 AND start_date<=? AND end_date>=?", (d, d)):
        if cal["kind"] in ("EXAM", "HOLIDAY"):
            return f"{cal['kind'].title()} period: {cal['title']}"
        if cal["kind"] == "MAINTENANCE" and cal["venue_id"] == venue["id"]:
            return f"Venue blocked for maintenance: {cal['title']}"
    return None

def venue_fit(expected, capacity):
    if capacity < expected: return 0.0
    return min(1.0, (expected / capacity) / 0.8)

def calendar_score(c, d):
    dd = date.fromisoformat(d); best = 3
    for cal in q(c, "SELECT start_date,end_date FROM academic_calendar WHERE kind='EXAM'"):
        s, e = date.fromisoformat(cal["start_date"]), date.fromisoformat(cal["end_date"])
        gap = 0 if s <= dd <= e else min(abs((s - dd).days), abs((dd - e).days))
        best = min(best, gap)
    return 1.0 if best >= 3 else best / 3.0, best

def load_score(c, d):
    n = q1(c, "SELECT COUNT(*) n FROM events WHERE event_date=? AND status IN ('PENDING','APPROVED')", (d,))["n"]
    return 1.0 / (1 + n), n

def preference_score(slot, req):
    s = 0.0
    if req.get("preferred_venue_id") == slot["venue_id"]: s += 0.4
    if req.get("preferred_date") == slot["date"]: s += 0.3
    pt = req.get("preferred_time")
    if pt and abs(hm(pt) - hm(slot["start_time"])) <= 60: s += 0.3
    return s if (req.get("preferred_venue_id") or req.get("preferred_date") or pt) else 0.5

def availability_score(c, slot, category_id):
    rows = q(c, """SELECT e.event_date, e.start_time, COUNT(a.id)*1.0/MAX(COUNT(r.id),1) AS rate FROM events e
        JOIN registrations r ON r.event_id=e.id AND r.status='CONFIRMED'
        LEFT JOIN attendance a ON a.registration_id=r.id
        WHERE e.category_id=? AND e.status='COMPLETED' GROUP BY e.id""", (category_id,))
    wd = date.fromisoformat(slot["date"]).weekday()
    hits = [r["rate"] for r in rows if date.fromisoformat(r["event_date"]).weekday() == wd
            and abs(hm(r["start_time"]) - hm(slot["start_time"])) <= 120]
    return sum(hits) / len(hits) if hits else 0.5       # neutral when no data

def buffer_score(c, slot):
    ev = q(c, "SELECT start_time,end_time FROM events WHERE venue_id=? AND event_date=? AND status IN ('PENDING','APPROVED')",
           (slot["venue_id"], slot["date"]))
    if not ev: return 1.0
    s, e = hm(slot["start_time"]), hm(slot["end_time"])
    gap = min(min(abs(s - hm(x["end_time"])), abs(hm(x["start_time"]) - e)) for x in ev)
    return min(1.0, gap / 60)

def score_slot(c, slot, req):
    cal, days = calendar_score(c, slot["date"]); ld, n = load_score(c, slot["date"])
    f = {"venue_fit": venue_fit(req["expected"], slot["capacity"]), "calendar": cal, "load": ld,
         "preference": preference_score(slot, req),
         "availability": availability_score(c, slot, req.get("category_id")), "buffer": buffer_score(c, slot)}
    total = sum(WEIGHTS[k] * f[k] for k in WEIGHTS)
    notes = []
    notes.append(f"Venue capacity {slot['capacity']} suits {req['expected']} expected participants" if f["venue_fit"] >= .8
                 else f"Venue capacity {slot['capacity']} vs {req['expected']} expected (fit {f['venue_fit']:.0%})")
    notes.append("no examination within 3 days" if days >= 3 else f"examination only {days} day(s) away")
    notes.append("no other events that day" if n == 0 else f"{n} other event(s) that day")
    if f["preference"] >= .7: notes.append("matches organiser preference")
    return {"score": round(total, 1), "factors": {k: round(v, 3) for k, v in f.items()},
            "explanation": "; ".join(notes).capitalize() + "."}

def recommend(c, req, user_id=None, limit=10):
    d0 = date.fromisoformat(req["date_from"]); d1 = date.fromisoformat(req["date_to"])
    if (d1 - d0).days > 60: d1 = d0 + timedelta(days=60)
    dur = int(req.get("duration_min") or DURATION_MIN)
    venues = q(c, "SELECT * FROM venues WHERE capacity>=? ORDER BY id", (req["expected"],))
    inactive = q(c, "SELECT * FROM venues WHERE capacity>=? AND active=0", (req["expected"],))
    ok, conflicts = [], []
    d = d0
    while d <= d1:
        for v in venues:
            for st in GRID:
                start = st; end = fmt(hm(st) + dur); ds = d.isoformat()
                reason = hard_conflict(c, v, ds, start, end)
                slot = {"venue_id": v["id"], "venue": v["name"], "capacity": v["capacity"], "date": ds,
                        "start_time": start, "end_time": end}
                if reason: conflicts.append({**slot, "conflict": True, "reason": reason})
                else: ok.append(slot)
        d += timedelta(days=1)
    ranked = []
    for s in ok:                         # only conflict-free slots are ever scored
        ranked.append({**s, "conflict": False, **score_slot(c, s, req)})
    ranked.sort(key=lambda s: s["score"], reverse=True)
    top = ranked[:limit]
    for s in top:
        c.execute("""INSERT INTO scheduling_recommendations(requested_by,venue_id,slot_date,start_time,end_time,conflict,score,explanation)
                     VALUES(?,?,?,?,?,0,?,?)""", (user_id, s["venue_id"], s["date"], s["start_time"], s["end_time"], s["score"], s["explanation"]))
    for s in conflicts[:30]:
        c.execute("""INSERT INTO scheduling_recommendations(requested_by,venue_id,slot_date,start_time,end_time,conflict,conflict_reason)
                     VALUES(?,?,?,?,?,1,?)""", (user_id, s["venue_id"], s["date"], s["start_time"], s["end_time"], s["reason"]))
    # de-duplicate conflict report to the most informative entries
    seen, rep = set(), []
    for s in conflicts:
        k = ("*", s["venue_id"], s["reason"]) if "inactive" in s["reason"] else (s["date"], s["reason"])
        if k not in seen: seen.add(k); rep.append(s)
    return {"recommendations": top, "conflicts": rep[:25], "candidates": len(ok) + len(conflicts),
            "conflict_count": len(conflicts), "weights": WEIGHTS}
