'use client'

import { useEffect, useState } from 'react'
import { SectionTag } from '@/components/SectionTag'
import { DashboardMetric } from '@/components/DashboardMetric'
import api from '@/lib/api'

export default function Dashboard() {
  const [modelLoaded, setModelLoaded] = useState<boolean | null>(null)

  useEffect(() => {
    api.getStatus()
      .then((d) => setModelLoaded(d.model_loaded))
      .catch(() => setModelLoaded(false))
  }, [])

  return (
    <section className="page-dashboard">
      <div className="container">
        <div className="reveal" style={{ marginBottom: 36 }}>
          <SectionTag icon="fa-solid fa-chart-line">Live Dashboard</SectionTag>
          <h1 style={{ marginTop: 10 }}>Monitor Your Network Security</h1>
          <p style={{ maxWidth: 600, marginTop: 6 }}>Real-time AI-powered threat monitoring with Federated Learning metrics.</p>
        </div>

        <div className="dash-header">
          <h1>Security Overview</h1>
          <span className={`tag ${modelLoaded ? 'tag-turquoise' : 'tag-orange'}`}>
            {modelLoaded ? 'System Online' : 'Model Unavailable'}
          </span>
        </div>

        <div className="grid-4" style={{ marginBottom: 36 }}>
          <DashboardMetric label="Detection Accuracy" value="98.7" change="↑ 0.3% from last round">%</DashboardMetric>
          <DashboardMetric label="Active Clients" value="10" change="All clients online" />
          <DashboardMetric label="Global Rounds" value="20" change="Training completed" />
          <DashboardMetric label="Avg Latency" value="18" change="Fast inference">ms</DashboardMetric>
        </div>

        <div className="dash-main-grid">
          <div className="dash-card dash-card-full">
            <h3>Threat Monitor <small>Real-time analysis</small></h3>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 140, marginBottom: 16 }}>
              {[30, 55, 85, 65, 95, 70, 45, 60].map((h, i) => (
                <div key={i} style={{ flex: 1, background: 'var(--blue)', height: `${h}%`, animation: `bar-rise 0.4s ease-out ${i * 0.08}s both, bar-pulse 2s ease-in-out ${i * 0.3 + 2}s infinite`, transformOrigin: 'bottom' }} />
              ))}
            </div>
            <span className="threat-level low"><span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--black)' }} /> Low Threat Level</span>
          </div>

          <div className="dash-card">
            <h3>Attack Distribution</h3>
            <div className="dash-list">
              {[
                { name: 'Benign', count: '180K' },
                { name: 'DDoS', count: '50K' },
                { name: 'DoS', count: '50K' },
                { name: 'Scanning', count: '50K' },
                { name: 'Injection', count: '12K' },
                { name: 'Ransomware', count: '3.4K' },
              ].map((a, i) => (
                <div key={i} className="dash-list-item">
                  <span>{a.name}</span>
                  <span>{a.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="dash-card">
            <h3>Federated Learning Progress</h3>
            <div className="dash-list">
              <div className="dash-list-item"><span>Global Rounds</span><span>20 / 20</span></div>
              <div className="dash-list-item"><span>Clients Participated</span><span>10 / 10</span></div>
              <div className="dash-list-item"><span>Best Accuracy</span><span>98.7%</span></div>
            </div>
          </div>

          <div className="dash-card">
            <h3>Model Status</h3>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 6, fontFamily: 'var(--font-mono)', letterSpacing: '0.08em', color: modelLoaded ? 'var(--turquoise)' : 'var(--orange)' }}>
                {modelLoaded ? 'ACTIVE' : 'OFFLINE'}
              </div>
              <small>{modelLoaded ? 'Federated Model v1.0' : 'Not Loaded'}</small>
            </div>
          </div>

          <div className="dash-card dash-card-full">
            <h3>Activity Feed <small>Recent events</small></h3>
            <div className="dash-list">
              {[
                { text: 'Model prediction completed — Normal traffic', time: 'Just now' },
                { text: 'Federated round 20 aggregated successfully', time: '2 min ago' },
                { text: 'DDoS pattern detected on client 07', time: '5 min ago' },
                { text: 'Client 03 joined federated round', time: '8 min ago' },
                { text: 'Model accuracy improved to 98.7%', time: '15 min ago' },
                { text: 'System health check: All clients online', time: '20 min ago' },
              ].map((a, i) => (
                <div key={i} className="dash-list-item">
                  <span>{a.text}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{a.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
