import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, err } from '../api'
import { useAuth } from '../App'
import { Msg } from './ui'
export function Login() {
  const { login } = useAuth(); const nav = useNavigate(); const [f, setF] = useState({ email: '', password: '' }); const [m, setM] = useState()
  const go = async e => { e.preventDefault(); try { const r = await api.post('/auth/login', f); login(r.data.token, r.data.user); nav('/dashboard') } catch (x) { setM({ t: 'bad', text: err(x) }) } }
  return <div className="auth"><form className="card" onSubmit={go}><div className="logo" style={{ color: '#14213d', padding: 0, marginBottom: 20 }}><i>🎓</i><span>AI Event Assistant</span></div>
    <h1 style={{ marginBottom: 4 }}>Welcome back</h1><p className="muted" style={{ marginTop: 0 }}>Log in with your university account.</p><Msg m={m} />
    <div className="f"><label>Email</label><input type="email" value={f.email} onChange={e => setF({ ...f, email: e.target.value })} placeholder="you@lpu.in" required /></div>
    <div className="f"><label>Password</label><input type="password" value={f.password} onChange={e => setF({ ...f, password: e.target.value })} required /></div>
    <button className="btn" style={{ width: '100%', justifyContent: 'center' }}>Log in</button>
    <p className="muted" style={{ textAlign: 'center' }}>New student? <Link to="/register" style={{ color: 'var(--brand)', fontWeight: 700 }}>Create an account</Link></p>
    <div className="alert warn" style={{ fontSize: 12, marginBottom: 0 }}>Demo logins — admin@lpu.in / Admin@123 · organizer@lpu.in / Organizer@123 · student@lpu.in / Student@123</div></form></div>
}
export function Register() {
  const { login } = useAuth(); const nav = useNavigate(); const [f, setF] = useState({ name: '', email: '', reg_no: '', department: '', password: '' }); const [m, setM] = useState()
  const set = k => e => setF({ ...f, [k]: e.target.value })
  const go = async e => { e.preventDefault(); try { const r = await api.post('/auth/signup', f); login(r.data.token, r.data.user); nav('/dashboard') } catch (x) { setM({ t: 'bad', text: err(x) }) } }
  return <div className="auth"><form className="card" onSubmit={go}><h1 style={{ marginBottom: 4 }}>Create student account</h1><p className="muted" style={{ marginTop: 0 }}>Organisers and admins are created by an administrator.</p><Msg m={m} />
    <div className="f"><label>Full name</label><input value={f.name} onChange={set('name')} required /></div>
    <div className="row"><div className="f"><label>Registration no.</label><input value={f.reg_no} onChange={set('reg_no')} /></div><div className="f"><label>Department</label><input value={f.department} onChange={set('department')} /></div></div>
    <div className="f"><label>Email</label><input type="email" value={f.email} onChange={set('email')} required /></div>
    <div className="f"><label>Password (min 8 characters)</label><input type="password" minLength={8} value={f.password} onChange={set('password')} required /></div>
    <button className="btn" style={{ width: '100%', justifyContent: 'center' }}>Register</button>
    <p className="muted" style={{ textAlign: 'center' }}>Already registered? <Link to="/login" style={{ color: 'var(--brand)', fontWeight: 700 }}>Log in</Link></p></form></div>
}
