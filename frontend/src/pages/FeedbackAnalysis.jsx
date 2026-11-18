import React, { useEffect, useState } from 'react'
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from 'recharts'
import { api } from '../api'
import { Head, Stat } from './ui'
const COL = { Positive: '#16a34a', Neutral: '#d97706', Negative: '#dc2626' }
export default function FeedbackAnalysis() {
  const [ev, setEv] = useState([]); const [id, setId] = useState(''); const [a, setA] = useState(null); const [ml, setMl] = useState(null)
  useEffect(() => { api.get('/events', { params: { mine: true } }).then(r => { const c = r.data.filter(e => e.status === 'COMPLETED'); setEv(c); if (c.length) setId(String(c[0].id)) }); api.get('/ml/metrics').then(r => setMl(r.data)) }, [])
  useEffect(() => { if (id) api.get(`/events/${id}/feedback-analysis`).then(r => setA(r.data)) }, [id])
  const pie = a ? Object.entries(a.sentiment).map(([name, value]) => ({ name, value })) : []
  return <><Head title="AI feedback analysis" sub="TF-IDF sentiment classification, topic extraction and complaint detection."><select value={id} onChange={x => setId(x.target.value)} style={{ minWidth: 280 }}>{ev.map(x => <option key={x.id} value={x.id}>{x.title}</option>)}</select></Head>
    {a && <><div className="grid g4" style={{ marginBottom: 16 }}><Stat label="Responses" value={a.count} /><Stat label="Average rating" value={a.average_rating + ' ★'} color="#f59e0b" /><Stat label="Satisfaction" value={a.satisfaction_pct + '%'} color="var(--ok)" /><Stat label="Complaint topics" value={a.complaints.length} color="var(--bad)" /></div>
      <div className="card" style={{ marginBottom: 16, background: '#fff7ed', borderColor: '#fed7aa' }}><b>AI summary</b><div style={{ marginTop: 4 }}>{a.summary}</div></div>
      <div className="grid g3" style={{ marginBottom: 16 }}>
        <div className="card"><h2>Sentiment split</h2><ResponsiveContainer height={220}><PieChart><Pie data={pie} dataKey="value" nameKey="name" innerRadius={45} outerRadius={78} label>{pie.map(p => <Cell key={p.name} fill={COL[p.name]} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div>
        <div className="card"><h2>Most appreciated</h2><ResponsiveContainer height={220}><BarChart data={a.appreciated} layout="vertical"><XAxis type="number" allowDecimals={false} fontSize={11} /><YAxis type="category" dataKey="topic" width={90} fontSize={12} /><Tooltip /><Bar dataKey="count" fill="#16a34a" radius={[0, 6, 6, 0]} /></BarChart></ResponsiveContainer></div>
        <div className="card"><h2>Common complaints</h2><ResponsiveContainer height={220}><BarChart data={a.complaints} layout="vertical"><XAxis type="number" allowDecimals={false} fontSize={11} /><YAxis type="category" dataKey="topic" width={90} fontSize={12} /><Tooltip /><Bar dataKey="count" fill="#dc2626" radius={[0, 6, 6, 0]} /></BarChart></ResponsiveContainer></div></div>
      <div className="grid g2"><div className="card"><h2 style={{ marginBottom: 8 }}>Improvement suggestions</h2>{a.suggestions.map((s, i) => <div key={i} className="kv" style={{ gridTemplateColumns: '1fr' }}>“{s}”</div>)}{!a.suggestions.length && <span className="muted">None.</span>}
        {!!a.nmf_topics.length && <><div className="sep" /><b>Discovered topics (NMF)</b><div className="fac">{a.nmf_topics.map((t, i) => <span key={i} className="tag">{t.join(' · ')}</span>)}</div></>}</div>
        {ml && <div className="card"><h2 style={{ marginBottom: 8 }}>Model evaluation (held-out test set)</h2><table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead><tbody>
          {ml.labels.map(l => <tr key={l}><td>{l}</td>{['precision', 'recall', 'f1-score'].map(k => <td key={k}>{ml.report[l][k].toFixed(3)}</td>)}<td>{ml.report[l].support}</td></tr>)}
          <tr><td><b>Macro avg</b></td>{['precision', 'recall', 'f1-score'].map(k => <td key={k}><b>{ml.report['macro avg'][k].toFixed(3)}</b></td>)}<td>{ml.test_size}</td></tr></tbody></table>
          <p className="muted" style={{ fontSize: 12, marginBottom: 0 }}>Accuracy {ml.accuracy.toFixed(3)}. Trained on {ml.dataset}; real feedback will score lower.</p></div>}</div></>}</>
}
