import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, err, fmtDate } from '../api'
import { useAuth } from '../App'
import { Badge, EventCard, Head, Msg, Stat } from './ui'
const COL = { Positive: '#16a34a', Neutral: '#d97706', Negative: '#dc2626' }
const PAL = ['#e8590c', '#14213d', '#2563eb', '#16a34a', '#d97706', '#7c3aed']

function Analytics({ admin }) {
  const [a, setA] = useState(null); const [m, setM] = useState()
  const load = () => api.get('/analytics').then(r => setA(r.data))
  useEffect(() => { load() }, [])
  const act = async (id, k, body) => { try { await api.post(`/events/${id}/${k}`, body); setM({ t: 'ok', text: 'Event ' + k + 'd' }); load() } catch (e) { setM({ t: 'bad', text: err(e) }) } }
  if (!a) return null
  return <><Msg m={m} />
    <div className="grid g4" style={{ marginBottom: 16 }}><Stat label="Events" value={a.totals.events} /><Stat label="Registrations" value={a.totals.registrations} color="var(--blue)" /><Stat label="Attendance scans" value={a.totals.attendance} color="var(--ok)" />{admin ? <Stat label="Users" value={a.totals.users} /> : <Stat label="Pending approval" value={a.totals.pending} color="var(--warn)" />}</div>
    <div className="grid g2" style={{ marginBottom: 16 }}>
      <div className="card"><h2>Events per month</h2><ResponsiveContainer height={230}><LineChart data={a.monthly}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="month" fontSize={12} /><YAxis allowDecimals={false} fontSize={12} /><Tooltip /><Line dataKey="events" stroke="#e8590c" strokeWidth={3} dot={{ r: 4 }} /></LineChart></ResponsiveContainer></div>
      <div className="card"><h2>Category popularity (registrations)</h2><ResponsiveContainer height={230}><BarChart data={a.categories}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="name" fontSize={11} /><YAxis fontSize={12} /><Tooltip /><Bar dataKey="registrations" radius={[6, 6, 0, 0]}>{a.categories.map((c, i) => <Cell key={i} fill={PAL[i % 6]} />)}</Bar></BarChart></ResponsiveContainer></div></div>
    <div className="grid g3" style={{ marginBottom: 16 }}>
      <div className="card"><h2>Events by status</h2><ResponsiveContainer height={220}><PieChart><Pie data={a.by_status} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80}>{a.by_status.map((c, i) => <Cell key={i} fill={PAL[i % 6]} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div>
      <div className="card"><h2>Feedback sentiment</h2><ResponsiveContainer height={220}><PieChart><Pie data={a.sentiment} dataKey="value" nameKey="name" outerRadius={80} label>{a.sentiment.map(c => <Cell key={c.name} fill={COL[c.name]} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div>
      <div className="card"><h2>Registered vs attended</h2><ResponsiveContainer height={220}><BarChart data={a.attendance.map(x => ({ ...x, title: x.title.slice(0, 12) }))}><XAxis dataKey="title" fontSize={10} /><YAxis fontSize={11} /><Tooltip /><Bar dataKey="registered" fill="#14213d" radius={[4, 4, 0, 0]} /><Bar dataKey="attended" fill="#e8590c" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></div>
    <div className="card"><h2 style={{ marginBottom: 8 }}>{admin ? 'Approval queue' : 'My pending requests'}</h2>
      <table><thead><tr><th>Event</th><th>Date</th><th>Venue</th><th>Organiser</th><th>Status</th>{admin && <th></th>}</tr></thead><tbody>
        {a.pending_events.map(e => <tr key={e.id}><td><Link to={'/events/' + e.id}><b>{e.title}</b></Link></td><td>{fmtDate(e.event_date)}</td><td>{e.venue}</td><td>{e.organizer}</td><td><Badge s={e.status} /></td>
          {admin && <td style={{ display: 'flex', gap: 6 }}><button className="btn ok sm" onClick={() => act(e.id, 'approve')}>Approve</button><button className="btn bad sm" onClick={() => { const r = prompt('Reason for rejection?'); if (r) act(e.id, 'reject', { reason: r }) }}>Reject</button></td>}</tr>)}
        {!a.pending_events.length && <tr><td colSpan={6} className="muted">Nothing pending.</td></tr>}</tbody></table></div></>
}

function Student() {
  const [regs, setRegs] = useState([]); const [ev, setEv] = useState([]); const [fb, setFb] = useState(null); const [m, setM] = useState(); const [f, setF] = useState({ rating: 5, comments: '', suggestions: '' })
  const load = () => { api.get('/my/registrations').then(r => setRegs(r.data)); api.get('/events').then(r => setEv(r.data.filter(e => e.status === 'APPROVED'))) }
  useEffect(load, [])
  const send = async () => { try { const r = await api.post(`/events/${fb}/feedback`, f); setM({ t: 'ok', text: `Thanks! Your comment was analysed as ${r.data.analysis.sentiment}.` }); setFb(null); load() } catch (e) { setM({ t: 'bad', text: err(e) }) } }
  const up = regs.filter(r => r.status === 'CONFIRMED' && r.event_status === 'APPROVED'); const past = regs.filter(r => r.status === 'CONFIRMED' && r.event_status === 'COMPLETED')
  return <><Msg m={m} /><div className="grid g3" style={{ marginBottom: 16 }}><Stat label="Upcoming registrations" value={up.length} color="var(--brand)" /><Stat label="Events attended" value={regs.filter(r => r.attended).length} color="var(--ok)" /><Stat label="Open events to join" value={ev.length} color="var(--blue)" /></div>
    <div className="grid g21" style={{ alignItems: 'start' }}><div>
      <div className="card"><h2 style={{ marginBottom: 12 }}>My QR passes</h2><div className="grid g2">{up.map(r => <div key={r.id} className="card" style={{ display: 'flex', gap: 14, alignItems: 'center' }}><QR id={r.id} /><div><b>{r.title}</b><div className="muted">{fmtDate(r.event_date)} · {r.start_time}</div><div className="tag" style={{ marginTop: 6, display: 'inline-block' }}>{r.registration_code}</div></div></div>)}{!up.length && <span className="muted">Register for an event to get a QR pass.</span>}</div></div>
      <div className="card"><h2 style={{ marginBottom: 8 }}>Participation history</h2><table><thead><tr><th>Event</th><th>Date</th><th>Attended</th><th></th></tr></thead><tbody>{past.map(r => <tr key={r.id}><td>{r.title}</td><td>{fmtDate(r.event_date)}</td><td>{r.attended ? <Badge s="Positive" /> : <span className="muted">No</span>}{''}</td>
        <td>{r.feedback_given ? <span className="muted">Feedback sent</span> : <button className="btn sm" onClick={() => setFb(r.event_id)}>Give feedback</button>}</td></tr>)}{!past.length && <tr><td colSpan={4} className="muted">No past events yet.</td></tr>}</tbody></table></div></div>
      <div>{fb ? <div className="card"><h2>Submit feedback</h2><div className="f" style={{ marginTop: 12 }}><label>Rating</label><select value={f.rating} onChange={e => setF({ ...f, rating: +e.target.value })}>{[5, 4, 3, 2, 1].map(n => <option key={n} value={n}>{'★'.repeat(n)} ({n})</option>)}</select></div>
        <div className="f"><label>Comments</label><textarea rows={3} value={f.comments} onChange={e => setF({ ...f, comments: e.target.value })} /></div><div className="f"><label>Suggestions</label><textarea rows={2} value={f.suggestions} onChange={e => setF({ ...f, suggestions: e.target.value })} /></div>
        <div style={{ display: 'flex', gap: 8 }}><button className="btn" onClick={send}>Submit</button><button className="btn sec" onClick={() => setFb(null)}>Cancel</button></div></div>
        : <div className="card"><h2 style={{ marginBottom: 10 }}>Recommended for you</h2>{ev.slice(0, 3).map(e => <Link key={e.id} to={'/events/' + e.id} className="kv" style={{ gridTemplateColumns: '1fr auto' }}><b>{e.title}</b><span>{fmtDate(e.event_date).slice(0, 10)}</span></Link>)}</div>}</div></div></>
}
function QR({ id }) {
  const [src, setSrc] = useState('')
  useEffect(() => { let u; api.get(`/registrations/${id}/qr`, { responseType: 'blob' }).then(r => { u = URL.createObjectURL(r.data); setSrc(u) }); return () => u && URL.revokeObjectURL(u) }, [id])
  return <img className="qr" src={src} alt="QR pass" width={110} height={110} style={{ width: 110, height: 110 }} />
}
export { QR }
export default function Dashboard() {
  const { user } = useAuth()
  const T = { ADMIN: ['Admin dashboard', 'Campus-wide analytics, approvals and settings.'], ORGANIZER: ['Organizer dashboard', 'Your events, requests and audience insights.'], STUDENT: ['Student dashboard', 'Your passes, registrations and feedback.'] }[user.role]
  return <><Head title={T[0]} sub={T[1]}>{user.role !== 'STUDENT' && <Link to="/events/new" className="btn">＋ Create event</Link>}</Head>
    {user.role === 'STUDENT' ? <Student /> : <><Analytics admin={user.role === 'ADMIN'} />{user.role === 'ADMIN' && <AdminTools />}</>}</>
}
function AdminTools() {
  const [u, setU] = useState([]); const [v, setV] = useState([]); const [cal, setCal] = useState([]); const [m, setM] = useState(); const [nc, setNc] = useState({ title: '', kind: 'EXAM', start_date: '', end_date: '' })
  const load = () => { api.get('/admin/users').then(r => setU(r.data)); api.get('/venues').then(r => setV(r.data)); api.get('/calendar').then(r => setCal(r.data)) }
  useEffect(load, [])
  const role = async (id, role) => { await api.put(`/admin/users/${id}/role`, { role }); setM({ t: 'ok', text: 'Role updated' }); load() }
  const toggle = async x => { await api.put('/venues/' + x.id, { ...x, active: !x.active }); load() }
  const addCal = async e => { e.preventDefault(); try { await api.post('/calendar', nc); setNc({ title: '', kind: 'EXAM', start_date: '', end_date: '' }); load() } catch (x) { setM({ t: 'bad', text: err(x) }) } }
  return <div className="grid g3" style={{ marginTop: 16, alignItems: 'start' }}>
    <div className="card"><h2 style={{ marginBottom: 8 }}>Users & roles</h2><Msg m={m} /><table><tbody>{u.slice(0, 7).map(x => <tr key={x.id}><td><b>{x.name}</b><div className="muted" style={{ fontSize: 12 }}>{x.email}</div></td><td><select value={x.role} onChange={e => role(x.id, e.target.value)} style={{ padding: 6 }}><option>ADMIN</option><option>ORGANIZER</option><option>STUDENT</option></select></td></tr>)}</tbody></table></div>
    <div className="card"><h2 style={{ marginBottom: 8 }}>Venues</h2><table><tbody>{v.map(x => <tr key={x.id}><td><b>{x.name}</b><div className="muted" style={{ fontSize: 12 }}>Capacity {x.capacity}</div></td><td><button className={'btn sm ' + (x.active ? 'ok' : 'bad')} onClick={() => toggle(x)}>{x.active ? 'Active' : 'Inactive'}</button></td></tr>)}</tbody></table></div>
    <div className="card"><h2 style={{ marginBottom: 8 }}>Academic calendar</h2>{cal.map(x => <div key={x.id} className="kv" style={{ gridTemplateColumns: '1fr auto' }}><span style={{ color: 'var(--ink)' }}>{x.title}<div className="muted" style={{ fontSize: 12 }}>{x.start_date} → {x.end_date}</div></span><Badge s={x.kind === 'EXAM' ? 'REJECTED' : x.kind === 'HOLIDAY' ? 'COMPLETED' : 'PENDING'} /></div>)}
      <form onSubmit={addCal} style={{ marginTop: 12 }}><input placeholder="Title" value={nc.title} onChange={e => setNc({ ...nc, title: e.target.value })} required style={{ marginBottom: 8 }} /><div className="row" style={{ marginBottom: 8 }}><select value={nc.kind} onChange={e => setNc({ ...nc, kind: e.target.value })}><option>EXAM</option><option>HOLIDAY</option><option>MAINTENANCE</option></select><input type="date" value={nc.start_date} onChange={e => setNc({ ...nc, start_date: e.target.value })} required /><input type="date" value={nc.end_date} onChange={e => setNc({ ...nc, end_date: e.target.value })} required /></div><button className="btn sm">Add block</button></form></div></div>
}
