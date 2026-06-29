import Link from 'next/link'
import { SectionTag } from '@/components/SectionTag'

const attackTypes = ['DDoS', 'DoS', 'Injection', 'Ransomware', 'Scanning', 'XSS', 'Backdoor', 'Password', 'MITM', 'Benign']

export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="hero-container">
          <div className="hero-grid">
            <div className="hero-content">
              <div className="hero-badge reveal">
                <span className="live-dot-pulse" />
                <span className="cycle-text" style={{ minWidth: 80 }}>
                  {attackTypes.map((a) => <span key={a}>{a}</span>)}
                </span>
                <span>&nbsp;Detection Active</span>
              </div>
              <h1 className="hero-title reveal">
                <span
                  className="typewriter"
                  data-text="Detect IoT Attacks"
                  data-speed="50"
                  style={{ visibility: 'hidden' }}
                />
                <span className="hl-underline">
                  <span className="hl-blue">With</span>{' '}
                  <span className="hl-magenta">Federated</span>{' '}
                  <span className="hl-orange">Learning</span>
                </span>
              </h1>
              <p className="hero-description reveal">
                AIPFL-IDS is an AI-powered Intrusion Detection System for
                modern IoT environments. It combines Deep Learning and
                Federated Learning to detect cyber attacks while preserving
                user privacy.
              </p>
              <div className="hero-buttons reveal">
                <Link href="/predict" className="btn btn-yellow">
                  <i className="fa-solid fa-bolt" /> Start Detection
                </Link>
                <a href="https://github.com" target="_blank" rel="noreferrer" className="btn">
                  <i className="fa-brands fa-github" /> GitHub
                </a>
              </div>
              <div className="hero-trust reveal">
                <span className="hero-trust-item"><i className="fa-solid fa-circle-check" /> Privacy Preserving</span>
                <span className="hero-trust-item"><i className="fa-solid fa-circle-check" /> Federated Learning</span>
                <span className="hero-trust-item"><i className="fa-solid fa-circle-check" /> Deep Learning</span>
              </div>
            </div>
            <div className="hero-visual reveal">
              <div className="hero-dashboard">
                <div className="dashboard-header">
                  <h3 className="dashboard-title">AI Security Monitor</h3>
                  <div className="dashboard-live"><span className="live-dot" /> Online</div>
                </div>
                <div className="dashboard-status">
                  <small>Model Accuracy</small>
                  <h2 data-count-to="79.85" data-count-suffix="%">79.85%</h2>
                </div>
                <div className="metric-grid">
                  <div className="metric-card"><small>Attack Classes</small><h3>10</h3></div>
                  <div className="metric-card"><small>Features</small><h3>39</h3></div>
                  <div className="metric-card"><small>Training Samples</small><h3>377K</h3></div>
                  <div className="metric-card"><small>Fed Clients</small><h3>10</h3></div>
                </div>
                <div className="dashboard-graph">
                  <div style={{ height: '50%' }} /><div style={{ height: '70%' }} /><div style={{ height: '90%' }} /><div style={{ height: '60%' }} /><div style={{ height: '80%' }} /><div style={{ height: '45%' }} /><div style={{ height: '75%' }} /><div style={{ height: '55%' }} />
                </div>
                <div className="dashboard-footer">
                  <small>Dataset</small>
                  <strong>NF-ToN-IoT-V2</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="section-header reveal">
            <SectionTag>Pipeline</SectionTag>
            <h2>End-to-End ML Pipeline</h2>
            <p>From raw IoT traffic to intelligent threat detection — every stage of the pipeline uses real data and trained models.</p>
          </div>
          <div className="pipeline">
            {[
              { num: '01', icon: 'fa-solid fa-database', title: 'Streaming Load', desc: '13M records loaded in batches from NF-ToN-IoT-V2' },
              { num: '02', icon: 'fa-solid fa-scale-balanced', title: 'Per-Class Balance', desc: '50K max per class, 377K total training samples' },
              { num: '03', icon: 'fa-solid fa-sliders', title: 'Standard Scaling', desc: '39 features normalized, label encoded' },
              { num: '04', icon: 'fa-solid fa-network-wired', title: 'FedAvg Training', desc: '10 clients, 10 rounds, 3 epochs each' },
              { num: '05', icon: 'fa-solid fa-chart-bar', title: 'Evaluation', desc: '79.85% accuracy, confusion matrix, per-class metrics' },
              { num: '06', icon: 'fa-solid fa-shield-halved', title: 'Inference', desc: 'Real-time prediction via Flask API' },
            ].map((s, i) => (
              <div key={i} className="pipeline-step reveal">
                <div className="step-count">{s.num}</div>
                <div className="step-icon"><i className={s.icon} /></div>
                <h4>{s.title}</h4>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="section-header reveal">
            <SectionTag>Technology Stack</SectionTag>
            <h2>Built With Real AI Components</h2>
            <p>Every technology listed here is actually used in the backend training pipeline and frontend interface.</p>
          </div>
          <div className="grid-3">
            {[
              { icon: 'fa-brands fa-python', title: 'Python 3.11+', desc: 'Core language for data processing and model training.' },
              { icon: 'fa-solid fa-brain', title: 'TensorFlow / Keras', desc: 'DNN architecture: 512 → 256 → 128 → 64 → 10.' },
              { icon: 'fa-solid fa-flask', title: 'Flask API', desc: '6 REST endpoints for prediction, status, config.' },
              { icon: 'fa-solid fa-network-wired', title: 'Federated Averaging', desc: 'FedAvg aggregates client weights privately.' },
              { icon: 'fa-solid fa-table', title: 'Parquet / Pandas', desc: '13M records loaded via streaming batches.' },
              { icon: 'fa-brands fa-react', title: 'Next.js 14', desc: 'App router, server components, API proxy.' },
            ].map((t, i) => (
              <div key={i} className="card-feature reveal">
                <div className="card-icon"><i className={t.icon} /></div>
                <h3>{t.title}</h3>
                <p>{t.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="section-header reveal">
            <SectionTag>Workflow</SectionTag>
            <h2>How AIPFL-IDS Works</h2>
            <p>A complete AI pipeline that transforms raw IoT traffic into intelligent predictions while preserving privacy through Federated Learning.</p>
          </div>
          <div className="timeline">
            {[
              { num: '01', title: 'Collect & Load', desc: '13M records from NF-ToN-IoT-V2 loaded in streaming 200K-row batches.' },
              { num: '02', title: 'Preprocess & Balance', desc: '39 features standardized, 10 classes balanced at 50K max per class.' },
              { num: '03', title: 'Federated Training', desc: '10 simulated clients train locally (3 epochs each) — raw data never leaves.' },
              { num: '04', title: 'Global Aggregation', desc: 'FedAvg merges local weight updates into a global DNN model.' },
              { num: '05', title: 'Evaluate & Deploy', desc: '79.85% accuracy. Confusion matrix, precision, recall computed.' },
              { num: '06', title: 'Real-Time Inference', desc: 'Flask API serves predictions on uploaded CSV/Parquet files.' },
            ].map((s, i) => (
              <div key={i} className="timeline-item reveal">
                <div className="timeline-number">{s.num}</div>
                <div className="timeline-content">
                  <h3>{s.title}</h3>
                  <p>{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="grid-2" style={{ alignItems: 'center', gap: 50 }}>
            <div className="reveal-left">
              <SectionTag>Dashboard</SectionTag>
              <h2 style={{ marginBottom: 12 }}>Monitor Every Network From One Dashboard</h2>
              <p style={{ marginBottom: 24 }}>View live AI predictions, model performance, attack statistics and network activity.</p>
              <ul className="check-list">
                <li><i className="fa-solid fa-check" /> Live Traffic Monitoring</li>
                <li><i className="fa-solid fa-check" /> Attack Classification</li>
                <li><i className="fa-solid fa-check" /> Federated Learning Progress</li>
                <li><i className="fa-solid fa-check" /> AI Performance Metrics</li>
              </ul>
            </div>
            <div className="reveal-right">
              <div style={{ background: 'var(--white)', border: 'var(--border-thick)', boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
                <div style={{ display: 'flex', gap: 6, padding: '12px 18px', background: 'var(--yellow)', borderBottom: 'var(--border-thick)' }}>
                  {[...Array(3)].map((_, i) => (
                    <span key={i} style={{ width: 12, height: 12, borderRadius: '50%', background: i === 0 ? 'var(--black)' : 'var(--text-muted)' }} />
                  ))}
                </div>
                <div style={{ padding: 22 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 90, marginBottom: 16 }}>
                    {[35, 55, 80, 65, 95, 70].map((h, i) => (
                      <div key={i} style={{ flex: 1, height: `${h}%`, background: 'var(--blue)', animation: `bar-rise 0.4s ease-out ${i * 0.08}s both` }} />
                    ))}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                    {[{ l: 'Accuracy', v: '79.85%' }, { l: 'Classes', v: '10' }, { l: 'Features', v: '39' }, { l: 'Clients', v: '10' }].map((c, i) => (
                      <div key={i} style={{ padding: 12, background: 'var(--bg)', border: 'var(--border-thick)', textAlign: 'center' }}>
                        <small style={{ display: 'block', fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', marginBottom: 2 }}>{c.l}</small>
                        <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', letterSpacing: '0.06em' }}>{c.v}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div className="section-header reveal">
            <SectionTag>Performance</SectionTag>
            <h2>Real Training Metrics</h2>
            <p>Actual results from the federated DNN trained on NF-ToN-IoT-V2 with 10 clients and 10 communication rounds.</p>
          </div>
          <div className="grid-4">
            {[
              { value: '79.85', suffix: '%', label: 'Test Accuracy' },
              { value: '377', suffix: 'K', label: 'Training Samples' },
              { value: '13', suffix: 'M', label: 'Raw Records' },
              { value: '10', suffix: '', label: 'Attack Classes' },
            ].map((s, i) => (
              <div key={i} className="stat-card reveal">
                <h2 className="stat-number" data-count-to={s.value} data-count-suffix={s.suffix}>{s.value}{s.suffix}</h2>
                <p className="stat-label">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="container">
          <div style={{ padding: 50, background: 'var(--blue)', border: 'var(--border-thick)', boxShadow: 'var(--shadow)', textAlign: 'center' }}>
            <SectionTag>Get Started</SectionTag>
            <h2 style={{ color: 'white', marginBottom: 12 }}>Ready to Protect Your IoT Network?</h2>
            <p style={{ color: 'rgba(255,255,255,0.85)', fontSize: '1rem', maxWidth: 500, margin: '0 auto 28px' }}>
              Experience privacy-preserving intrusion detection powered by AI and Federated Learning.
            </p>
            <div style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link href="/predict" className="btn btn-yellow btn-lg">
                <i className="fa-solid fa-bolt" /> Launch Detection
              </Link>
              <Link href="/dashboard" className="btn" style={{ background: 'var(--white)' }}>
                <i className="fa-solid fa-chart-line" /> Open Dashboard
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
