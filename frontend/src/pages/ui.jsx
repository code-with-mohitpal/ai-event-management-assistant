import React from 'react'
import { Link } from 'react-router-dom'
export const Badge = ({ s }) => <span className={'badge b-' + s}>{s}</span>
export const Head = ({ title, sub, children }) => <div className="head"><div><h1>{title}</h1>{sub && <p>{sub}</p>}</div><div style={{ display: 'flex', gap: 8 }}>{children}</div></div>
export const Stat = ({ label, value, color }) => <div className="card stat"><span>{label}</span><b style={{ color }}>{value}</b></div>
export const Msg = ({ m }) => m ? <div className={'alert ' + m.t}>{m.text}</div> : null
export const EventCard = ({ e }) => {
  const d = new Date(e.event_date + 'T00:00:00'); const pct = Math.min(100, Math.round(100 * e.registered / e.max_participants))
  return <Link to={'/events/' + e.id} className="card evcard">
    <div className="top"><div className="date"><b>{d.getDate()}</b><small>{d.toLocaleString('en', { month: 'short' }).toUpperCase()}</small></div><Badge s={e.status} /></div>
    <h3 style={{ fontSize: 16 }}>{e.title}</h3><div className="muted">{e.start_time}–{e.end_time} · {e.venue}</div>
    <div style={{ display: 'flex', gap: 6 }}><span className="tag">{e.category}</span><span className="tag">{e.organizer}</span></div>
    <div className="bar"><i style={{ width: pct + '%' }} /></div><div className="muted" style={{ fontSize: 12 }}>{e.registered} / {e.max_participants} registered</div></Link>
}
