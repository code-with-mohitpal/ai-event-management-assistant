import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, fmtDate } from '../api'
import { Badge, Head } from './ui'
export default function Archive() {
  const [rows, setRows] = useState([]); const [cats, setCats] = useState([]); const [f, setF] = useState({ search: '', category_id: 0, organizer: '', date_from: '', date_to: '' })
  useEffect(() => { api.get('/categories').then(r => setCats(r.data)) }, [])
  useEffect(() => { api.get('/archive', { params: f }).then(r => setRows(r.data)) }, [f])
  const set = k => e => setF({ ...f, [k]: k === 'category_id' ? +e.target.value : e.target.value })
  return <><Head title="Historical event archive" sub="Past events with attendance statistics and feedback ratings." />
    <div className="card row" style={{ marginBottom: 16 }}><input placeholder="Search title…" value={f.search} onChange={set('search')} /><select value={f.category_id} onChange={set('category_id')}><option value={0}>All categories</option>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select><input placeholder="Organiser" value={f.organizer} onChange={set('organizer')} /><input type="date" value={f.date_from} onChange={set('date_from')} /><input type="date" value={f.date_to} onChange={set('date_to')} /></div>
    <div className="card"><table><thead><tr><th>Event</th><th>Date</th><th>Category</th><th>Organiser</th><th>Registered</th><th>Attended</th><th>Attendance</th><th>Rating</th><th>Status</th></tr></thead><tbody>
      {rows.map(r => <tr key={r.id}><td><Link to={'/events/' + r.id}><b>{r.title}</b></Link><div className="muted" style={{ fontSize: 12 }}>{r.venue}</div></td><td>{fmtDate(r.event_date)}</td><td><span className="tag">{r.category}</span></td><td>{r.organizer}</td><td>{r.registered}</td><td>{r.attended}</td>
        <td style={{ minWidth: 110 }}><div className="bar"><i style={{ width: (r.registered ? 100 * r.attended / r.registered : 0) + '%' }} /></div><span className="muted" style={{ fontSize: 12 }}>{r.registered ? Math.round(100 * r.attended / r.registered) : 0}%</span></td>
        <td>{r.avg_rating ? <span className="stars">★ <b style={{ color: 'var(--ink)' }}>{r.avg_rating}</b></span> : '—'}</td><td><Badge s={r.status} /></td></tr>)}
      {!rows.length && <tr><td colSpan={9} className="muted">No past events match.</td></tr>}</tbody></table></div></>
}
