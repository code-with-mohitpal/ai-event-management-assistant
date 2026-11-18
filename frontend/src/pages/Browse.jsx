import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../App'
import { EventCard, Head } from './ui'
export default function Browse() {
  const { user } = useAuth(); const [ev, setEv] = useState([]); const [cats, setCats] = useState([]); const [s, setS] = useState(''); const [c, setC] = useState(0); const [st, setSt] = useState('')
  useEffect(() => { api.get('/categories').then(r => setCats(r.data)) }, [])
  useEffect(() => { api.get('/events', { params: { search: s, category_id: c, status: st, mine: user.role === 'ORGANIZER' } }).then(r => setEv(r.data)) }, [s, c, st])
  return <><Head title={user.role === 'STUDENT' ? 'Browse events' : user.role === 'ORGANIZER' ? 'My events' : 'All events'} sub="Search, filter and open any event.">{user.role !== 'STUDENT' && <Link className="btn" to="/events/new">＋ Create event</Link>}</Head>
    <div className="card row" style={{ marginBottom: 16 }}><input placeholder="Search events…" value={s} onChange={e => setS(e.target.value)} />
      <select value={c} onChange={e => setC(+e.target.value)}><option value={0}>All categories</option>{cats.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
      <select value={st} onChange={e => setSt(e.target.value)}><option value="">All statuses</option>{['DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'COMPLETED'].filter(x => user.role !== 'STUDENT' || ['APPROVED', 'COMPLETED'].includes(x)).map(x => <option key={x}>{x}</option>)}</select></div>
    <div className="grid g3">{ev.map(e => <EventCard key={e.id} e={e} />)}</div>{!ev.length && <p className="muted">No events match.</p>}</>
}
