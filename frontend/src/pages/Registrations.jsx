import React, { useEffect, useState } from 'react'
import { api, fmtDate } from '../api'
import { Badge, Head, Stat } from './ui'
export function useMyEvents() { const [ev, setEv] = useState([]); useEffect(() => { api.get('/events', { params: { mine: true } }).then(r => setEv(r.data.filter(e => ['APPROVED', 'COMPLETED'].includes(e.status) && e.registered > 0))) }, []); return ev }
export default function Registrations() {
  const ev = useMyEvents(); const [id, setId] = useState(''); const [rows, setRows] = useState([])
  useEffect(() => { if (!id && ev.length) setId(String((ev.find(e => e.status === 'APPROVED') || ev[0]).id)) }, [ev])
  useEffect(() => { if (id) api.get(`/events/${id}/registrations`).then(r => setRows(r.data)) }, [id])
  const e = ev.find(x => String(x.id) === id); const conf = rows.filter(r => r.status === 'CONFIRMED').length
  return <><Head title="Registration management" sub="Participants, capacity and registration statistics per event.">
    <select value={id} onChange={x => setId(x.target.value)} style={{ minWidth: 280 }}>{ev.map(x => <option key={x.id} value={x.id}>{x.title}</option>)}</select></Head>
    {e && <div className="grid g4" style={{ marginBottom: 16 }}><Stat label="Confirmed" value={conf} color="var(--ok)" /><Stat label="Cancelled" value={rows.length - conf} color="var(--bad)" /><Stat label="Capacity" value={e.max_participants} /><Stat label="Seats left" value={Math.max(0, e.max_participants - conf)} color="var(--brand)" /></div>}
    <div className="card"><table><thead><tr><th>Registration ID</th><th>Student</th><th>Reg. no</th><th>Dept</th><th>Registered</th><th>Status</th><th>Attended</th></tr></thead><tbody>
      {rows.map(r => <tr key={r.id}><td><code>{r.registration_code}</code></td><td><b>{r.name}</b><div className="muted" style={{ fontSize: 12 }}>{r.email}</div></td><td>{r.reg_no}</td><td>{r.department}</td><td>{r.registered_at?.slice(0, 10)}</td><td><Badge s={r.status} /></td><td>{r.attended_at ? '✓ ' + r.attended_at.slice(11, 16) : '—'}</td></tr>)}</tbody></table></div></>
}
