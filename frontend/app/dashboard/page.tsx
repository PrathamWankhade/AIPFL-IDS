'use client'

import { useEffect, useState } from 'react'
import { SectionTag } from '@/components/SectionTag'
import { DashboardMetric } from '@/components/DashboardMetric'
import api from '@/lib/api'

interface StatusData {
  status?: string
  timestamp?: string
  datasets?: Record<string, { model_loaded: boolean; num_classes: number; input_dim: number }>
}

function ZoneLabel({ kind, children }: { kind: 'live' | 'stored' | 'illustrative'; children?: React.ReactNode }) {
  const styles: Record<string, React.CSSProperties> = {
    live: { background: 'var(--turquoise)', color: 'var(--black-pure)' },
    stored: { background: 'var(--blue)', color: 'var(--white-pure)' },
    illustrative: { background: 'transparent', color: 'var(--text-muted)', borderStyle: 'dashed' },
  }
  return (
    <span className="tag" style={{ ...styles[kind], fontSize: '0.6rem' }}>
      {kind === 'live' ? 'Live API' : kind === 'stored' ? 'Stored evaluation' : 'Illustrative reference'}
      {children ? ` · ${children}` : ''}
    </span>
  )
}

export default function Dashboard() {
  const [status, setStatus] = useState<StatusData | null>(null)
  const [models, setModels] = useState<{ models: { name: string; dataset: string; size_bytes: number }[] } | null>(null)
  const [metrics, setMetrics] = useState<Record<string, { training_summary: any; release: any }> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.getStatus().catch((e) => { throw e }),
      api.getModels().catch(() => null),
      api.getMetrics().catch(() => null),
    ])
      .then(([s, m, met]) => {
        if (cancelled) return
        setStatus(s)
        if (m) setModels(m)
        if (met?.metrics) setMetrics(met.metrics)
        setLoading(false)
      })
      .catch((e: any) => {
        if (cancelled) return
        setError(e.message || 'Backend unreachable')
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const cici = status?.datasets?.CICIoT2023
  const nfton = status?.datasets?.['NF-ToN-IoT-V2']
  const anyLoaded = Boolean(cici?.model_loaded || nfton?.model_loaded)
  const mCici = metrics?.CICIoT2023?.training_summary
  const mNfton = metrics?.['NF-ToN-IoT-V2']?.training_summary
  const fmt = (v: any, digits = 2) => (typeof v === 'number' ? (v * 100).toFixed(digits) : '—')
  const fmtMacro = (m: any) => (m?.macro_f1 != null ? `${(m.macro_f1 * 100).toFixed(1)}%` : 'Not measured')

  const events: { text: string; time: string }[] = []
  if (status?.timestamp) events.push({ text: `Backend status fetched (${status.status || 'online'})`, time: status.timestamp })
  if (cici) events.push({ text: `CICIoT2023 model ${cici.model_loaded ? 'loaded' : 'not loaded'} — ${cici.num_classes} classes, ${cici.input_dim} features`, time: 'live' })
  if (nfton) events.push({ text: `NF-ToN-IoT-V2 model ${nfton.model_loaded ? 'loaded' : 'not loaded'} — ${nfton.num_classes} classes, ${nfton.input_dim} features`, time: 'live' })
  if (models?.models?.length) {
    for (const m of models.models.slice(0, 6)) {
      events.push({ text: `${m.name} (${m.dataset}, ${(m.size_bytes / 1024).toFixed(0)} KB)`, time: 'artifact' })
    }
  }

  return (
    <section className="page-dashboard">
      <div className="container">
        <div className="reveal" style={{ marginBottom: 36 }}>
          <SectionTag icon="fa-solid fa-chart-line">Operations Dashboard</SectionTag>
          <h1 style={{ marginTop: 10 }}>System Status &amp; Model Evaluation</h1>
          <p style={{ maxWidth: 640, marginTop: 6 }}>
            Live backend state, stored evaluation metrics, and illustrative reference data are shown in
            separate labeled zones. Nothing here monitors live network traffic.
          </p>
        </div>

        <div className="dash-header">
          <h1>Backend Status</h1>
          <span className={`tag ${anyLoaded ? 'tag-turquoise' : 'tag-orange'}`}>
            {loading ? 'Checking backend…' : anyLoaded ? 'Backend Reachable' : 'Backend Unreachable'}
          </span>
        </div>

        {loading && <div className="alert" role="status">Loading live status…</div>}
        {error && <div className="alert alert-danger" role="alert">Backend unreachable: {error}. Live values below show “Not measured”.</div>}

        {/* Zone A — live API state */}
        <h2 style={{ fontSize: '1rem', marginBottom: 12 }}><ZoneLabel kind="live">from /api/status</ZoneLabel></h2>
        <div className="grid-4" style={{ marginBottom: 36 }}>
          <DashboardMetric label="Models loaded" value={loading ? '…' : anyLoaded ? '1–2' : '0'} change={anyLoaded ? 'At least one model ready' : 'Not measured'} />
          <DashboardMetric label="CICIoT2023" value={cici ? String(cici.num_classes) : '—'} change={cici ? (cici.model_loaded ? `Loaded · ${cici.input_dim} features` : 'Not loaded') : 'Not measured'} />
          <DashboardMetric label="NF-ToN-V2" value={nfton ? String(nfton.num_classes) : '—'} change={nfton ? (nfton.model_loaded ? `Loaded · ${nfton.input_dim} features` : 'Not loaded') : 'Not measured'} />
          <DashboardMetric label="Artifacts" value={models?.models?.length != null ? String(models.models.length) : '—'} change={models ? 'From /api/models' : 'Not measured'} />
        </div>

        {/* Zone B — stored evaluation metrics */}
        <h2 style={{ fontSize: '1rem', marginBottom: 12 }}><ZoneLabel kind="stored">from /api/metrics · historical test runs</ZoneLabel></h2>
        <div className="grid-4" style={{ marginBottom: 36 }}>
          <DashboardMetric label="CICIoT2023 test acc" value={mCici ? fmt(mCici.test_accuracy) : '—'} change={mCici ? `macro-F1 ${fmtMacro(mCici)} · ${mCici.partition || 'iid'}` : 'Not measured'}>%</DashboardMetric>
          <DashboardMetric label="NF-ToN-V2 test acc" value={mNfton ? fmt(mNfton.test_accuracy) : '—'} change={mNfton ? `macro-F1 ${fmtMacro(mNfton)} · ${mNfton.partition || 'iid'}` : 'Not measured'}>%</DashboardMetric>
          <DashboardMetric label="CICIoT2023 ECE" value={mCici?.ece != null ? mCici.ece.toFixed(3) : '—'} change={mCici ? 'Lower is better calibrated' : 'Not measured'} />
          <DashboardMetric label="NF-ToN-V2 ECE" value={mNfton?.ece != null ? mNfton.ece.toFixed(3) : '—'} change={mNfton ? 'Lower is better calibrated' : 'Not measured'} />
        </div>

        <div className="dash-main-grid">
          {/* Zone C — illustrative reference, visually distinct */}
          <div className="dash-card dash-card-full dash-illustrative">
            <h3>Attack Distribution <ZoneLabel kind="illustrative">demo data, not live incidents</ZoneLabel></h3>
            <div className="dash-list">
              {[
                { name: 'DDOS Attacks', count: '10 types' },
                { name: 'DOS Attacks', count: '4 types' },
                { name: 'MIRAI Variants', count: '3 types' },
                { name: 'RECON Attacks', count: '4 types' },
                { name: 'Web Attacks', count: '4 types' },
                { name: 'Other', count: '9 types' },
              ].map((a, i) => (
                <div key={i} className="dash-list-item">
                  <span>{a.name}</span>
                  <span>{a.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="dash-card">
            <h3>Model Readiness <small><ZoneLabel kind="live" /></small></h3>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 6, fontFamily: 'var(--font-mono)', letterSpacing: '0.08em', color: anyLoaded ? 'var(--turquoise)' : 'var(--orange)' }}>
                {loading ? '…' : anyLoaded ? 'READY' : 'NOT READY'}
              </div>
              <small>{loading ? 'Checking…' : anyLoaded ? 'At least one model loaded' : 'No model loaded'}</small>
            </div>
          </div>

          <div className="dash-card dash-card-full">
            <h3>Recent API Events <small><ZoneLabel kind="live">not security incidents</ZoneLabel></small></h3>
            <div className="dash-list">
              {events.length === 0 && (
                <div className="dash-list-item"><span>{loading ? 'Loading…' : 'No live events — backend unreachable'}</span><span /></div>
              )}
              {events.map((a, i) => (
                <div key={i} className="dash-list-item">
                  <span>{a.text}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{a.time}</span>
                </div>
              ))}
            </div>
            <small style={{ color: 'var(--text-muted)' }}>Predictions are uncalibrated model outputs, not confirmed incidents. Confirm alerts before action.</small>
          </div>
        </div>
      </div>
    </section>
  )
}
