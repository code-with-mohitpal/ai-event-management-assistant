import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, err, fmtDate, addDays } from '../api'
import { useAuth } from '../App'
import { Badge, Head, Msg } from './ui'
import { QR } from './Dashboard'

export function EventDetails() {
  const { id } = useParams(); const { user } = useAuth(); const nav = useNavigate(); const [e, setE] = useState(null); const [m, setM] = useState()
  const load = () => api.get('/events/' + id).then(r => setE(r.data)); useEffect(() => { load() }, [id])
  const act = async (k, method = 'post') => { try { await api[method](method === 'post' ? `/events/${id}/${k}` : `/events/${id}/register`); setM({ t: 'ok', text: 'Done' }); load() } catch (x) { setM({ t: 'bad', text: err(x) }) } }
  if (!e) return null
  const reg = e.my_registration?.status === 'CONFIRMED'; const staff = user.role !== 'STUDENT' && (user.role === 'ADMIN' || e.organizer_id === user.id)
  const full = e.registered >= e.max_participants
  return <><Head title={e.title} sub={`${fmtDate(e.event_date)} · ${e.start_time}–${e.end_time} · ${e.venue}`}><Badge s={e.status} /></Head><Msg m={m} />
    {e.reject_reason && <div className="alert bad">Rejected: {e.reject_reason}</div>}
    <div className="grid g21" style={{ alignItems: 'start' }}><div className="card"><h2>About this event</h2><p style={{ lineHeight: 1.6 }}>{e.description || 'No description provided.'}</p><div className="sep" />
      {[['Category', e.category], ['Organiser', e.organizer], ['Venue', `${e.venue} (capacity ${e.venue_capacity})`], ['Registration deadline', e.registration_deadline.slice(0, 16).replace('T', ' ')], ['Seats', `${e.registered} registered of ${e.max_participants}`]].map(([k, v]) => <div key={k} className="kv"><span>{k}</span><b>{v}</b></div>)}</div>
      <div className="card">{user.role === 'STUDENT' ? <>
        <h2 style={{ marginBottom: 12 }}>Registration</h2>
        {reg ? <><div className="alert ok">You are registered · {e.my_registration.registration_code}</div><div style={{ textAlign: 'center' }}><QR id={e.my_registration.id} /></div><button className="btn sec" style={{ width: '100%', marginTop: 12, justifyContent: 'center' }} onClick={() => act('', 'delete')}>Cancel registration</button></>
          : <button className="btn" style={{ width: '100%', justifyContent: 'center' }} disabled={e.status !== 'APPROVED' || full} onClick={() => act('register')}>{full ? 'Event full' : e.status !== 'APPROVED' ? 'Not open' : 'Register now'}</button>}</>
        : <><h2 style={{ marginBottom: 12 }}>Manage</h2><div style={{ display: 'grid', gap: 8 }}>
          {staff && ['DRAFT', 'PENDING', 'APPROVED'].includes(e.status) && <Link className="btn sec" to={`/events/${id}/edit`}>Edit event</Link>}
          {staff && ['DRAFT', 'REJECTED'].includes(e.status) && <button className="btn" onClick={() => act('submit')}>Submit for approval</button>}
          {user.role === 'ADMIN' && e.status === 'PENDING' && <><button className="btn ok" onClick={() => act('approve')}>Approve</button><button className="btn bad" onClick={async () => { const r = prompt('Reason?'); if (r) { try { await api.post(`/events/${id}/reject`, { reason: r }); load() } catch (x) { setM({ t: 'bad', text: err(x) }) } } }}>Reject</button></>}
          {staff && e.status === 'APPROVED' && <button className="btn dark" onClick={() => act('complete')}>Mark completed</button>}
          {staff && ['DRAFT', 'PENDING', 'APPROVED'].includes(e.status) && <button className="btn bad" onClick={() => act('cancel')}>Cancel event</button>}
          <Link className="btn sec" to="/registrations">Registrations</Link></div></>}</div></div></>
}

export function EventForm() {
  const { id } = useParams(); const nav = useNavigate(); const [cats, setCats] = useState([]); const [ven, setVen] = useState([]); const [m, setM] = useState(); const [chk, setChk] = useState()
  const [f, setF] = useState({ title: '', description: '', category_id: 1, venue_id: 1, event_date: addDays(30), start_time: '10:00', end_time: '12:00', max_participants: 50, registration_deadline: addDays(29) + 'T10:00' })
  useEffect(() => { api.get('/categories').then(r => setCats(r.data)); api.get('/venues').then(r => setVen(r.data)); if (id) api.get('/events/' + id).then(r => setF({ ...r.data, registration_deadline: r.data.registration_deadline.slice(0, 16).replace(' ', 'T') })) }, [id])
  const set = k => e => setF({ ...f, [k]: ['category_id', 'venue_id', 'max_participants'].includes(k) ? +e.target.value : e.target.value })
  const body = () => ({ title: f.title, description: f.description, category_id: f.category_id, venue_id: f.venue_id, event_date: f.event_date, start_time: f.start_time, end_time: f.end_time, max_participants: f.max_participants, registration_deadline: f.registration_deadline.replace('T', ' ') + (f.registration_deadline.length === 16 ? ':00' : '') })
  useEffect(() => { const t = setTimeout(() => api.post('/events/check', body()).then(r => setChk(r.data)).catch(() => setChk(null)), 300); return () => clearTimeout(t) }, [f.venue_id, f.event_date, f.start_time, f.end_time])
  const save = async e => { e.preventDefault(); try { const r = id ? await api.put('/events/' + id, body()) : await api.post('/events', body()); nav('/events/' + r.data.id) } catch (x) { setM({ t: 'bad', text: err(x) }) } }
  return <><Head title={id ? 'Edit event' : 'Create event'} sub="The venue is checked against events, exams, holidays and maintenance as you type."><Link className="btn sec" to="/scheduling">✨ Find best slot</Link></Head>
    <form className="card" onSubmit={save} style={{ maxWidth: 860 }}><Msg m={m} />
      {chk && <div className={'alert ' + (chk.available ? 'ok' : 'bad')}>{chk.available ? '✓ Venue is available for this slot' : '✕ ' + chk.reason}</div>}
      <div className="f"><label>Title</label><input value={f.title} onChange={set('title')} required minLength={3} /></div>
      <div className="f"><label>Description</label><textarea rows={3} value={f.description} onChange={set('description')} /></div>
      <div className="row"><div className="f"><label>Category</label><select value={f.category_id} onChange={set('category_id')}>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
        <div className="f"><label>Venue</label><select value={f.venue_id} onChange={set('venue_id')}>{ven.map(v => <option key={v.id} value={v.id}>{v.name} ({v.capacity}){v.active ? '' : ' – inactive'}</option>)}</select></div></div>
      <div className="row"><div className="f"><label>Date</label><input type="date" value={f.event_date} onChange={set('event_date')} required /></div><div className="f"><label>Start</label><input type="time" value={f.start_time} onChange={set('start_time')} required /></div><div className="f"><label>End</label><input type="time" value={f.end_time} onChange={set('end_time')} required /></div></div>
      <div className="row"><div className="f"><label>Max participants</label><input type="number" min={1} value={f.max_participants} onChange={set('max_participants')} /></div><div className="f"><label>Registration deadline</label><input type="datetime-local" value={f.registration_deadline} onChange={set('registration_deadline')} required /></div></div>
      <div style={{ display: 'flex', gap: 8 }}><button className="btn">{id ? 'Save changes' : 'Save as draft'}</button><Link className="btn sec" to="/events">Cancel</Link></div></form></>
}
