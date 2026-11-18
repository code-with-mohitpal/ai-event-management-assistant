import React, { useEffect, useState } from 'react'
import { api, err } from '../api'
import { Head, Msg, Stat } from './ui'
import { useMyEvents } from './Registrations'
export default function Attendance() {
  const ev = useMyEvents(); const [id, setId] = useState(''); const [rep, setRep] = useState(null); const [tok, setTok] = useState(''); const [m, setM] = useState()
  const load = () => id && api.get(`/events/${id}/attendance`).then(r => setRep(r.data))
  useEffect(() => { if (!id && ev.length) setId(String((ev.find(e => e.event_date === new Date().toISOString().slice(0, 10)) || ev[0]).id)) }, [ev]); useEffect(() => { load() }, [id])
  const scan = async e => { e.preventDefault(); try { const r = await api.post('/attendance/scan', { token: tok }); setM({ t: 'ok', text: `✓ ${r.data.student} (${r.data.reg_no || '—'}) marked present for ${r.data.event}` }); setTok(''); load() } catch (x) { setM({ t: 'bad', text: '✕ ' + err(x) }) } }
  return <><Head title="QR attendance" sub="Scan a student pass. Each pass can be used once."><select value={id} onChange={x => setId(x.target.value)} style={{ minWidth: 280 }}>{ev.map(x => <option key={x.id} value={x.id}>{x.title} · {x.event_date}</option>)}</select></Head>
    <div className="grid g21" style={{ alignItems: 'start' }}><div>
      {rep && <div className="grid g3" style={{ marginBottom: 16 }}><Stat label="Confirmed" value={rep.confirmed} /><Stat label="Present" value={rep.attended} color="var(--ok)" /><Stat label="Attendance" value={rep.percentage + '%'} color="var(--brand)" /></div>}
      <div className="card"><h2 style={{ marginBottom: 8 }}>Scan log</h2><table><thead><tr><th>Student</th><th>Reg. no</th><th>Scanned at</th></tr></thead><tbody>{rep?.records.map((r, i) => <tr key={i}><td><b>{r.name}</b></td><td>{r.reg_no}</td><td>{r.scanned_at}</td></tr>)}{rep && !rep.records.length && <tr><td colSpan={3} className="muted">No scans yet.</td></tr>}</tbody></table></div></div>
      <form className="scan" onSubmit={scan}><h2>Scanner</h2><div className="frame">▣ Point camera at QR<br /><small>or paste token below</small></div>
        <input value={tok} onChange={e => setTok(e.target.value)} placeholder="QR token (from scanner)" style={{ marginBottom: 10 }} /><button className="btn" style={{ width: '100%', justifyContent: 'center' }}>Mark present</button><div style={{ marginTop: 12, textAlign: 'left' }}><Msg m={m} /></div></form></div></>
}
