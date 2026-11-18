import React, { createContext, useContext, useEffect, useState } from 'react'
import { Link, NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { api } from './api'
import Landing from './pages/Landing'
import { Login, Register } from './pages/Auth'
import Dashboard from './pages/Dashboard'
import { EventDetails, EventForm } from './pages/Events'
import Scheduling from './pages/Scheduling'
import Registrations from './pages/Registrations'
import Attendance from './pages/Attendance'
import FeedbackAnalysis from './pages/FeedbackAnalysis'
import Archive from './pages/Archive'
import Profile from './pages/Profile'
import Browse from './pages/Browse'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

const NAV = {
  ADMIN: [['/dashboard', '▦', 'Dashboard'], ['/events', '📅', 'All Events'], ['/events/new', '＋', 'Create Event'], ['/scheduling', '✨', 'Smart Scheduling'], ['/registrations', '👥', 'Registrations'], ['/attendance', '▣', 'Attendance'], ['/feedback', '💬', 'Feedback Analysis'], ['/archive', '🗂', 'Archive'], ['/profile', '◉', 'Profile']],
  ORGANIZER: [['/dashboard', '▦', 'Dashboard'], ['/events', '📅', 'My Events'], ['/events/new', '＋', 'Create Event'], ['/scheduling', '✨', 'Smart Scheduling'], ['/registrations', '👥', 'Registrations'], ['/attendance', '▣', 'Attendance'], ['/feedback', '💬', 'Feedback Analysis'], ['/archive', '🗂', 'Archive'], ['/profile', '◉', 'Profile']],
  STUDENT: [['/dashboard', '▦', 'Dashboard'], ['/events', '📅', 'Browse Events'], ['/archive', '🗂', 'Archive'], ['/profile', '◉', 'Profile']],
}

function Shell({ children }) {
  const { user, logout } = useAuth(); const nav = useNavigate()
  return <div className="app"><aside className="side">
    <Link to="/" className="logo"><i>🎓</i><span>AI Event<br />Assistant</span></Link>
    {NAV[user.role].map(([to, ic, t]) => <NavLink key={to} to={to} end className={({ isActive }) => isActive ? 'on' : ''}><span>{ic}</span>{t}</NavLink>)}
    <div className="who"><b>{user.name}</b>{user.role}<br /><a style={{ padding: 0, marginTop: 8, cursor: 'pointer', color: '#fdba74' }} onClick={() => { logout(); nav('/') }}>Sign out</a></div>
  </aside><main className="main">{children}</main></div>
}

export default function App() {
  const [user, setUser] = useState(null); const [ready, setReady] = useState(false)
  useEffect(() => { if (localStorage.getItem('token')) api.get('/me').then(r => setUser(r.data)).catch(() => localStorage.removeItem('token')).finally(() => setReady(true)); else setReady(true) }, [])
  const login = (token, u) => { localStorage.setItem('token', token); setUser(u) }
  const logout = () => { localStorage.removeItem('token'); setUser(null) }
  if (!ready) return null
  const P = (el, roles) => !user ? <Navigate to="/login" /> : roles && !roles.includes(user.role) ? <Navigate to="/dashboard" /> : <Shell>{el}</Shell>
  const staff = ['ADMIN', 'ORGANIZER']
  return <Ctx.Provider value={{ user, setUser, login, logout }}><Routes>
    <Route path="/" element={<Landing />} /><Route path="/login" element={<Login />} /><Route path="/register" element={<Register />} />
    <Route path="/dashboard" element={P(<Dashboard />)} />
    <Route path="/events" element={P(<Browse />)} />
    <Route path="/events/new" element={P(<EventForm />, staff)} />
    <Route path="/events/:id/edit" element={P(<EventForm />, staff)} />
    <Route path="/events/:id" element={P(<EventDetails />)} />
    <Route path="/scheduling" element={P(<Scheduling />, staff)} />
    <Route path="/registrations" element={P(<Registrations />, staff)} />
    <Route path="/attendance" element={P(<Attendance />, staff)} />
    <Route path="/feedback" element={P(<FeedbackAnalysis />, staff)} />
    <Route path="/archive" element={P(<Archive />)} />
    <Route path="/profile" element={P(<Profile />)} />
    <Route path="*" element={<Navigate to="/" />} />
  </Routes></Ctx.Provider>
}
