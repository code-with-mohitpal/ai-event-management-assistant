// Captures REAL screenshots of the running app. Usage: node capture.cjs  (app on :5173, API on :8000)
const { chromium } = require('playwright'); const path = require('path')
const URL = 'http://localhost:5173', OUT = __dirname
const D = n => { const d = new Date(); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10) }
const U = { admin: ['admin@lpu.in', 'Admin@123'], org: ['organizer@lpu.in', 'Organizer@123'], stu: ['student@lpu.in', 'Student@123'] }
;(async () => {
  const b = await chromium.launch()
  const shot = async (p, name) => { await p.waitForTimeout(900); await p.screenshot({ path: path.join(OUT, name + '.png') }); console.log('saved', name) }
  const ctx = async role => { const c = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 }); const p = await c.newPage()
    if (role) { await p.goto(URL + '/login'); await p.fill('input[type=email]', U[role][0]); await p.fill('input[type=password]', U[role][1]); await p.click('button.btn'); await p.waitForURL('**/dashboard') } return p }
  let p = await ctx(); await p.goto(URL + '/'); await shot(p, '01_landing')
  await p.goto(URL + '/login'); await shot(p, '02_login')
  await p.goto(URL + '/register'); await p.fill('input >> nth=0', 'Demo Student'); await shot(p, '03_register')
  p = await ctx('admin'); await p.waitForSelector('text=Approval queue'); await p.waitForTimeout(800); await p.screenshot({ path: path.join(OUT, '04_admin_dashboard.png'), fullPage: true }); console.log('saved admin')
  p = await ctx('org'); await p.waitForSelector('text=My pending requests'); await shot(p, '05_organizer_dashboard')
  p = await ctx('stu'); await p.waitForSelector('text=My QR passes'); await p.waitForTimeout(800); await p.screenshot({ path: path.join(OUT, '06_student_dashboard.png'), fullPage: true })
  await p.goto(URL + '/events'); await p.click('text=Startup Pitch Day'); await p.waitForSelector('text=Registration'); await shot(p, '07_event_details')
  p = await ctx('org'); await p.goto(URL + '/events/new'); await p.fill('input >> nth=0', 'Tech Talk: Generative AI'); await p.fill('textarea', 'Guest lecture on generative AI for campus students.')
  await p.fill('input[type=date]', D(20)); await p.waitForSelector('.alert.bad'); await shot(p, '08_event_creation')
  await p.goto(URL + '/scheduling'); await p.click('text=Recommend slots'); await p.waitForSelector('.slot'); await p.waitForTimeout(500); await p.screenshot({ path: path.join(OUT, '09_smart_scheduling.png'), fullPage: true })
  await p.goto(URL + '/registrations'); await p.waitForSelector('tbody tr'); await shot(p, '10_registration_management')
  await p.goto(URL + '/attendance'); await p.waitForSelector('text=Scanner'); await p.waitForTimeout(500)
  const tok = '11111111-2222-3333-4444-555555555555'; await p.fill('input[placeholder^="QR token"]', tok); await p.click('text=Mark present'); await p.waitForSelector('.alert.ok'); await shot(p, '11_attendance_qr')
  await p.goto(URL + '/feedback'); await p.waitForSelector('text=AI summary'); await p.waitForTimeout(800); await shot(p, '12_feedback_analysis')
  await p.goto(URL + '/archive'); await p.waitForSelector('tbody tr'); await shot(p, '13_archive')
  await p.goto(URL + '/profile'); await shot(p, '14_profile')
  await b.close()
})().catch(e => { console.error(e); process.exit(1) })
