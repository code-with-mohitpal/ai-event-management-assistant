import json
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
R = Path('/home/claude/event-assistant'); SS = R/'screenshots'; MEDIA = Path('/tmp/claude-0/rep/media/media'); TMP = Path('/tmp/claude-0/crops'); TMP.mkdir(exist_ok=True)
NAVY, ORG, INK, MUTE, BG = RGBColor(0x14,0x21,0x3d), RGBColor(0xe8,0x59,0x0c), RGBColor(0x14,0x21,0x3d), RGBColor(0x64,0x74,0x8b), RGBColor(0xf4,0xf6,0xfb)
m = json.load(open(R/'backend/models/metrics.json'))
p = Presentation(); p.slide_width, p.slide_height = Inches(13.333), Inches(7.5)
blank = p.slide_layouts[6]
def rect(s, x, y, w, h, c, shape=MSO_SHAPE.RECTANGLE):
    r = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h)); r.fill.solid(); r.fill.fore_color.rgb = c; r.line.fill.background(); return r
def text(s, t, x, y, w, h, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    for i, line in enumerate(t if isinstance(t, list) else [t]):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); para.alignment = align
        r = para.add_run(); r.text = line; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = 'Calibri'; para.space_after = Pt(6)
    return tb
def slide(title, sub=None, n=[0]):
    s = p.slides.add_slide(blank); n[0] += 1; rect(s, 0, 0, 13.333, 7.5, BG); rect(s, 0, 0, 0.18, 7.5, ORG)
    text(s, title, 0.6, 0.35, 12, 0.8, 30, True)
    if sub: text(s, sub, 0.6, 1.05, 12, 0.5, 15, False, MUTE)
    text(s, f'AI-Based Event Management and Scheduling Assistant · CSEAIML2026-P37 · {n[0]+1}', 0.6, 7.05, 12, 0.3, 10, False, MUTE); return s
def bullets(s, items, x=0.6, y=1.7, w=12, size=18, gap=0.62):
    for i, t in enumerate(items):
        rect(s, x, y + i*gap + 0.1, 0.14, 0.14, ORG, MSO_SHAPE.OVAL); text(s, t, x + 0.35, y + i*gap - 0.05, w - 0.4, 0.6, size)
def cards(s, items, y=1.8, cols=3, h=1.9):
    w = (12.1 - 0.3*(cols-1))/cols
    for i, (t, d) in enumerate(items):
        x = 0.6 + (i % cols)*(w+0.3); yy = y + (i//cols)*(h+0.3); rect(s, x, yy, w, h, RGBColor(255,255,255), MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.06
        rect(s, x, yy+0.25, 0.08, 0.5, ORG); text(s, t, x+0.25, yy+0.2, w-0.4, 0.5, 17, True); text(s, d, x+0.25, yy+0.75, w-0.4, h-0.8, 13, False, MUTE)
def img(s, path, x, y, w, h):
    im = Image.open(path); r = im.width/im.height; bw, bh = (w, w/r) if w/h < r else (h*r, h)
    s.shapes.add_picture(str(path), Inches(x+(w-bw)/2), Inches(y+(h-bh)/2), Inches(bw), Inches(bh))
def crop(path, ratio=16/9.6):
    im = Image.open(path).convert('RGB'); h = int(im.width/ratio); out = TMP/path.name
    im.crop((0, 0, im.width, min(h, im.height))).save(out); return out
def shot(title, f, note, caption):
    s = slide(title); path = crop(SS/f)
    img(s, path, 0.6, 1.2, 8.3, 5.7); rect(s, 9.2, 1.2, 3.55, 5.7, RGBColor(255,255,255), MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.04
    text(s, 'What it shows', 9.45, 1.4, 3.1, 0.4, 14, True, ORG); text(s, note, 9.45, 1.85, 3.1, 4.8, 14); text(s, caption, 0.6, 6.7, 8.3, 0.3, 10, False, MUTE)

# 1 title
s = p.slides.add_slide(blank); rect(s, 0, 0, 13.333, 7.5, NAVY); rect(s, 0, 5.2, 13.333, 0.08, ORG)
text(s, 'CSE472 · CA2 · Project ID CSEAIML2026-P37', 0.8, 1.3, 11, 0.4, 16, True, ORG)
text(s, 'AI-Based Event Management\nand Scheduling Assistant'.split('\n'), 0.8, 1.9, 11.5, 2.2, 46, True, RGBColor(255,255,255))
text(s, 'Conflict-free scheduling · Smart registration · QR attendance · NLP feedback analysis', 0.8, 4.3, 11.5, 0.5, 18, False, RGBColor(0xcb,0xd5,0xe1))
text(s, ['Mohit Pal (12413686) · Apoorv Suryawanshi (12412593) · Kumar Harsh (12400938)', 'Guide: Amandeep Kaur, Professor · Lovely Professional University, Phagwara · Nov 2026'], 0.8, 5.5, 12, 1, 15, False, RGBColor(0xcb,0xd5,0xe1))

s = slide('Problem and motivation', 'Campus events still run on spreadsheets, e-mail and informal approvals')
cards(s, [('Clashes', 'Venues promised twice; events placed inside examination weeks.'), ('Manual work', 'External forms, paper attendance, no link to student identity.'), ('Lost insight', 'Feedback is rarely analysed beyond an average star rating.')])
text(s, 'Goal: one secure, role-based platform that prevents conflicts before they occur, automates registration, reminders and attendance, and turns feedback into insight.', 0.6, 4.4, 12, 1.2, 20, True)
s = slide('Objectives'); bullets(s, ['JWT authentication with Admin, Organizer and Student roles', 'Event lifecycle with approval workflow, venues and academic calendar', 'Smart scheduling: hard-conflict filter, then explained weighted ranking', 'Registration with duplicate and capacity checks, unique IDs, e-mail reminders', 'QR attendance with duplicate-scan prevention and attendance %', 'TF-IDF sentiment and topic analysis, evaluated on held-out data', 'Analytics and searchable historical archive from stored records'], y=1.4, size=19, gap=0.78)
s = slide('System architecture', 'React SPA → REST API (JWT) → database; ML service for ranking and feedback')
img(s, MEDIA/'image2.png', 0.6, 1.5, 7.6, 5.3)
rect(s, 8.5, 1.5, 4.25, 5.3, RGBColor(255,255,255), MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.04
text(s, 'As built in this repository', 8.75, 1.7, 3.8, 0.4, 15, True, ORG)
text(s, ['Front end: React 18, Vite, Recharts', 'API: FastAPI with JWT + bcrypt', 'Database: SQLite, MySQL-style schema (12 tables)', 'ML: scikit-learn TF-IDF + Logistic Regression, NMF', 'Mail: SMTP/MailHog or logged outbox', 'QR: python-qrcode', '', 'The report’s design names Spring Boot + MySQL; this build keeps the same layers and rules.'], 8.75, 2.2, 3.8, 4.5, 13)
s = slide('Database design', 'Normalised schema with integrity enforced in the database'); img(s, MEDIA/'image3.png', 0.6, 1.4, 5.2, 5.5)
text(s, ['UNIQUE(event_id, user_id) on registrations and feedback', 'UNIQUE(registration_id) on attendance', 'UNIQUE(user_id, event_id, type) makes reminders idempotent', 'CHECK(end_time > start_time), CHECK(rating BETWEEN 1 AND 5)', 'Composite index (venue_id, event_date, start_time, end_time) for the overlap query'], 6.3, 1.8, 6.4, 5, 17)
s = slide('Smart scheduling pipeline', 'Hard constraints are a filter, so a conflicting slot can never be ranked'); img(s, MEDIA/'image4.png', 0.6, 1.5, 6, 5.3)
cards(s, [('Stage 1: hard filter', 'Venue overlap, exam period, holiday, inactive or maintenance venue.'), ('Stage 2: weighted score', 'Venue fit 25 · Calendar 25 · Load 20 · Preference 15 · Availability 10 · Buffer 5.')], y=1.6, cols=1, h=1.9) if False else None
for i, (t, d) in enumerate([('Stage 1: hard filter', 'Overlap, exam period, holiday, inactive or maintenance venue.'), ('Stage 2: weighted score', 'Venue fit 25 · Calendar 25 · Load 20 · Preference 15 · Availability 10 · Buffer 5.'), ('Explained output', 'Every slot stores its score and a plain-language reason.')]):
    y = 1.6 + i*1.75; rect(s, 7, y, 5.75, 1.55, RGBColor(255,255,255), MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.06; rect(s, 7, y+0.25, 0.08, 0.5, ORG); text(s, t, 7.25, y+0.15, 5.3, 0.4, 16, True); text(s, d, 7.25, y+0.7, 5.3, 0.8, 13, False, MUTE)
s = slide('Registration, QR attendance and notifications')
cards(s, [('Registration', 'Transaction with write lock; checks approval, deadline, duplicate and capacity. Cancelled rows re-activate.'), ('QR attendance', 'Random UUID token per registration. Scan checks owner, date and duplicates, then stores a timestamp.'), ('Notifications', 'Confirmation, 24-hour and 1-hour reminders, cancellation and schedule-change mails.')], h=2.4)
text(s, 'Attendance % = attendance records ÷ confirmed registrations', 0.6, 4.7, 12, 0.5, 20, True, ORG)
s = slide('NLP feedback analysis', 'TF-IDF (1–2 grams) + Logistic Regression, NMF topics, keyword complaint lexicon')
rows = [['Class', 'Precision', 'Recall', 'F1', 'Support']] + [[l] + [f"{m['report'][l][k]:.3f}" for k in ('precision', 'recall', 'f1-score')] + [str(int(m['report'][l]['support']))] for l in m['labels']] + [['Macro avg'] + [f"{m['report']['macro avg'][k]:.3f}" for k in ('precision', 'recall', 'f1-score')] + [str(m['test_size'])]]
t = s.shapes.add_table(len(rows), 5, Inches(0.6), Inches(1.8), Inches(7.2), Inches(2.6)).table
for i, r in enumerate(rows):
    for j, v in enumerate(r):
        c = t.cell(i, j); c.text = v; c.text_frame.paragraphs[0].runs[0].font.size = Pt(15); c.text_frame.paragraphs[0].runs[0].font.bold = (i == 0 or i == len(rows)-1)
text(s, f"Accuracy {m['accuracy']:.3f} on {m['test_size']} held-out samples ({m['train_size']} train, stratified 80/20, seed 42).", 0.6, 4.7, 7.2, 0.8, 15, True)
text(s, 'Honest note: the dataset is 620 synthetic template sentences, far more regular than real comments. These figures show the pipeline works end to end, not expected accuracy on real feedback.', 8.2, 1.8, 4.5, 3, 14, False, MUTE)
s = slide('Testing', 'Automated pytest suite: 11 tests, all passing'); 
cases = [('Overlapping events in one venue', 'Rejected 409; adjacent slot allowed'), ('Event during examinations', 'Hard conflict, never recommended'), ('Venue inactive / under maintenance', 'Hard conflict, never recommended'), ('Registration beyond capacity', 'Refused; cancel frees a seat'), ('Duplicate registration', 'Refused 409'), ('Duplicate QR scan', 'Refused; first timestamp kept'), ('Positive / Negative / Neutral text', 'Classified correctly'), ('Auth, roles, signup validation', 'Enforced')]
for i, (a, b) in enumerate(cases):
    y = 1.6 + i*0.62; rect(s, 0.6, y, 12.1, 0.54, RGBColor(255,255,255), MSO_SHAPE.ROUNDED_RECTANGLE); text(s, a, 0.8, y+0.08, 6, 0.4, 15, True); text(s, b, 6.9, y+0.08, 4.8, 0.4, 14, False, MUTE); text(s, '✓ Pass', 11.5, y+0.08, 1.1, 0.4, 14, True, RGBColor(0x16,0xa3,0x4a))

S = [('Landing page', '01_landing.png', 'Public introduction with upcoming approved events and links to log in or register.'),
 ('Login page', '02_login.png', 'JWT login. Wrong credentials return a generic error; passwords are bcrypt hashed.'),
 ('Registration page', '03_register.png', 'Student sign-up with validation (8+ character password, unique email). Organisers and admins are promoted by an admin.'),
 ('Admin dashboard', '04_admin_dashboard.png', 'Live SQL analytics: events, registrations, scans, users, monthly trend, category popularity, status, sentiment, and the approval queue.'),
 ('Organizer dashboard', '05_organizer_dashboard.png', 'Same analytics limited to the organiser’s own events, with their pending approval requests.'),
 ('Student dashboard', '06_student_dashboard.png', 'QR passes for upcoming events, participation history and feedback submission.'),
 ('Event details', '07_event_details.png', 'Full event information, seat count, and one-click registration with a generated QR pass.'),
 ('Event creation', '08_event_creation.png', 'Live availability check. Here an exam period is detected and the slot is flagged before saving.'),
 ('Smart scheduling', '09_smart_scheduling.png', 'Ranked slots with scores and explanations, plus the conflict report of slots removed by hard constraints.'),
 ('Registration management', '10_registration_management.png', 'Participants, registration IDs, seats left and attendance status for an event.'),
 ('QR attendance', '11_attendance_qr.png', 'Scanning a pass marks the student present once; attendance % updates immediately.'),
 ('AI feedback analysis', '12_feedback_analysis.png', 'Sentiment split, appreciated topics, complaints, suggestions, summary and measured model metrics.'),
 ('Historical archive', '13_archive.png', 'Search and filter past events by title, category, organiser and date, with attendance and rating.'),
 ('User profile', '14_profile.png', 'Update details, change password and view recent e-mail notifications.')]
for i, (t, f, n) in enumerate(S): shot(f'Figure 10.{i+1}: {t}', f, n, 'Real screenshot of the running application (sample data).')

s = slide('Conclusion and future scope')
cards(s, [('Delivered', 'Working full-stack platform with 14 pages, 11 passing tests and conflict-free explained scheduling.'), ('Future scope', 'ERP / SSO import of timetables, Google and Outlook calendar sync, mobile app with offline QR.'), ('Next ML steps', 'Multilingual (Hindi, Punjabi) transformer models, attendance prediction, waiting lists.')], h=2.6)
text(s, 'Thank you · Questions?', 0.6, 5.2, 12, 0.8, 32, True, ORG)
p.save(R/'AI_Event_Management_Assistant.pptx'); print('slides', len(p.slides))
