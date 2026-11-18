import axios from 'axios'
export const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api`
})
api.interceptors.request.use(c => { const t = localStorage.getItem('token'); if (t) c.headers.Authorization = 'Bearer ' + t; return c })
export const err = e => e?.response?.data?.detail ? (typeof e.response.data.detail === 'string' ? e.response.data.detail : e.response.data.detail.map(d => d.msg).join(', ')) : 'Something went wrong'
export const fmtDate = d => new Date(d + 'T00:00:00').toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
export const today = () => new Date().toISOString().slice(0, 10)
export const addDays = n => { const d = new Date(); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10) }
