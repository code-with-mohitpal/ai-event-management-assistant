import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, err, fmtDate, addDays } from '../api'
import { Head, Msg } from './ui'
const LABEL = { venue_fit: 'Venue fit', calendar: 'Calendar', load: 'Campus load', preference: 'Preference', availability: 'Availability', buffer: 'Buffer' }
export default function Scheduling() {
  const [cats, setCats] = useState([]); const [ven, setVen] = useState([]); const [r, setR] = useState(null); const [m, setM] = useState(); const [busy, setBusy] = useState(false)
  const [f, setF] = useState({ expected: 100, date_from: addDays(14), date_to: addDays(40), category_id: 1, duration_min: 120, preferred_venue_id: '', preferred_time: '' })
  useEffect(() => { api.get('/categories').then(x => setCats(x.data)); api.get('/venues').then(x => setVen(x.data)) }, [])
  const set = k => e => setF({ ...f, [k]: e.target.value })
  const go = async e => { e.preventDefault(); setBusy(true); try { const x = await api.post('/scheduling/recommend', { ...f, expected: +f.expected, category_id: +f.category_id, duration_min: +f.duration_min, preferred_venue_id: f.preferred_venue_id ? +f.preferred_venue_id : null, preferred_time: f.preferred_time || null }); setR(x.data); setM(null) } catch (x) { setM({ t: 'bad', text: err(x) }) } setBusy(false) }
  return <><Head title="Smart scheduling" sub="Hard conflicts are filtered out first. The remaining slots are ranked by a weighted, explained score." />
    <form className="card row" onSubmit={go} style={{ alignItems: 'flex-end', marginBottom: 16 }}>
      <div><label>Expected participants</label><input type="number" min={1} value={f.expected} onChange={set('expected')} /></div>
      <div><label>Category</label><select value={f.category_id} onChange={set('category_id')}>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
      <div><label>From</label><input type="date" value={f.date_from} onChange={set('date_from')} /></div><div><label>To</label><input type="date" value={f.date_to} onChange={set('date_to')} /></div>
      <div><label>Preferred venue</label><select value={f.preferred_venue_id} onChange={set('preferred_venue_id')}><option value="">Any</option>{ven.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select></div>
      <div><label>Preferred time</label><input type="time" value={f.preferred_time} onChange={set('preferred_time')} /></div>
      <div style={{ flex: '0 0 auto' }}><button className="btn" disabled={busy}>{busy ? 'Analysing…' : '✨ Recommend slots'}</button></div></form>
    <Msg m={m} />
    {r && <div className="grid g21" style={{ alignItems: 'start' }}>
      <div className="card"><h2>Top recommended slots</h2><p className="muted" style={{ marginTop: 4 }}>{r.candidates} candidate slots checked · {r.conflict_count} removed by hard constraints · {r.recommendations.length} shown</p>
        {r.recommendations.map((s, i) => <div key={i} className="slot"><div className="rank">{i + 1}</div><div><b>{fmtDate(s.date)} · {s.start_time}–{s.end_time}</b> <span className="muted">· {s.venue} ({s.capacity})</span><div className="muted" style={{ marginTop: 3 }}>{s.explanation}</div>
          <div className="fac">{Object.entries(s.factors).map(([k, v]) => <span key={k} className="tag">{LABEL[k]} {Math.round(v * 100)}%</span>)}</div></div>
          <div><div className="score" style={{ color: i === 0 ? 'var(--brand)' : 'var(--ink)' }}>{s.score}</div><div className="muted" style={{ textAlign: 'right', fontSize: 11 }}>of 100</div></div></div>)}
        {!r.recommendations.length && <div className="alert warn">No conflict-free slot found in this window.</div>}</div>
      <div><div className="card"><h2>Conflict report</h2><p className="muted" style={{ marginTop: 4 }}>These slots were never ranked.</p>
        {r.conflicts.slice(0, 9).map((c, i) => <div key={i} className="kv" style={{ gridTemplateColumns: '1fr' }}><b style={{ fontSize: 13 }}>{fmtDate(c.date)} · {c.venue}</b><span style={{ color: 'var(--bad)' }}>✕ {c.reason}</span></div>)}</div>
        <div className="card"><h2 style={{ marginBottom: 10 }}>Score weights</h2>{Object.entries(r.weights).map(([k, v]) => <div key={k} style={{ marginBottom: 8 }}><div style={{ display: 'flex', justifyContent: 'space-between' }}><span>{LABEL[k]}</span><b>{v}</b></div><div className="bar"><i style={{ width: v * 4 + '%' }} /></div></div>)}
          <Link className="btn sec sm" to="/events/new" style={{ marginTop: 8 }}>Create event with a slot</Link></div></div></div>}</>
}
