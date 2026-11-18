import React, { useEffect, useState } from 'react'
import { api, err } from '../api'
import { useAuth } from '../App'
import { Head, Msg } from './ui'
export default function Profile() {
  const { user, setUser } = useAuth(); const [f, setF] = useState({ name: user.name, department: user.department || '', phone: user.phone || '' }); const [p, setP] = useState({ current: '', new: '' }); const [m, setM] = useState(); const [n, setN] = useState([])
  useEffect(() => { api.get('/notifications').then(r => setN(r.data)) }, [])
  const save = async e => { e.preventDefault(); try { const r = await api.put('/me', f); setUser(r.data); setM({ t: 'ok', text: 'Profile updated' }) } catch (x) { setM({ t: 'bad', text: err(x) }) } }
  const pw = async e => { e.preventDefault(); try { await api.put('/me/password', p); setP({ current: '', new: '' }); setM({ t: 'ok', text: 'Password changed' }) } catch (x) { setM({ t: 'bad', text: err(x) }) } }
  return <><Head title="My profile" sub="View and update your personal details and password." /><Msg m={m} />
    <div className="grid g21" style={{ alignItems: 'start' }}><div><form className="card" onSubmit={save}><h2 style={{ marginBottom: 14 }}>Personal details</h2>
      <div className="row"><div className="f"><label>Full name</label><input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} /></div><div className="f"><label>Email</label><input value={user.email} disabled /></div></div>
      <div className="row"><div className="f"><label>Registration no.</label><input value={user.reg_no || '—'} disabled /></div><div className="f"><label>Role</label><input value={user.role} disabled /></div></div>
      <div className="row"><div className="f"><label>Department</label><input value={f.department} onChange={e => setF({ ...f, department: e.target.value })} /></div><div className="f"><label>Phone</label><input value={f.phone} onChange={e => setF({ ...f, phone: e.target.value })} /></div></div><button className="btn">Save changes</button></form>
      <form className="card" onSubmit={pw}><h2 style={{ marginBottom: 14 }}>Change password</h2><div className="row"><div className="f"><label>Current password</label><input type="password" value={p.current} onChange={e => setP({ ...p, current: e.target.value })} required /></div><div className="f"><label>New password</label><input type="password" minLength={8} value={p.new} onChange={e => setP({ ...p, new: e.target.value })} required /></div></div><button className="btn dark">Update password</button></form></div>
      <div className="card"><h2 style={{ marginBottom: 8 }}>Recent notifications</h2>{n.map((x, i) => <div key={i} className="kv" style={{ gridTemplateColumns: '1fr auto' }}><span style={{ color: 'var(--ink)' }}>{x.subject}<div className="muted" style={{ fontSize: 12 }}>{x.type} · {x.created_at?.slice(0, 16)}</div></span><span className={'badge b-' + x.status}>{x.status}</span></div>)}{!n.length && <span className="muted">No notifications.</span>}</div></div></>
}
