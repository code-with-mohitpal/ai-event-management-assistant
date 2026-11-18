import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { EventCard } from './ui'
import { useAuth } from '../App'
export default function Landing() {
  const [ev, setEv] = useState([]); const { user } = useAuth()
  useEffect(() => { api.get('/public/events').then(r => setEv(r.data)) }, [])
  return <div><div className="top"><div className="logo" style={{ color: '#14213d', padding: 0 }}><i>🎓</i><span>AI Event Assistant</span></div>
    <div style={{ display: 'flex', gap: 8 }}>{user ? <Link className="btn" to="/dashboard">Open dashboard</Link> : <><Link className="btn sec" to="/login">Log in</Link><Link className="btn" to="/register">Register</Link></>}</div></div>
    <div className="pub"><div className="hero"><h1>Plan campus events without a single clash.</h1>
      <p>One platform for scheduling, registration, QR attendance and AI feedback analysis. Slots that collide with an exam, a holiday or another event are never recommended.</p>
      <div style={{ display: 'flex', gap: 10 }}><Link className="btn" to="/register">Get started</Link><a className="btn sec" href="#up">See upcoming events</a></div></div>
      <div className="grid g4" style={{ marginBottom: 30 }}>{[['🛡', 'Conflict-free scheduling', 'Hard constraints filter every slot before ranking.'], ['🎟', 'Smart registration', 'Capacity and duplicate checks with unique QR passes.'], ['▣', 'QR attendance', 'Scan once, never twice. Attendance % in real time.'], ['💬', 'AI feedback insight', 'Sentiment and topics from student comments.']].map(([i, t, d]) => <div key={t} className="card"><div style={{ fontSize: 24 }}>{i}</div><h3 style={{ margin: '8px 0 4px' }}>{t}</h3><span className="muted">{d}</span></div>)}</div>
      <h2 id="up" style={{ marginBottom: 14 }}>Upcoming public events</h2>
      <div className="grid g4">{ev.slice(0, 4).map(e => <EventCard key={e.id} e={e} />)}</div></div></div>
}
