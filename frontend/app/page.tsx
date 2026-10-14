import Link from 'next/link'
import { SectionTag } from '@/components/SectionTag'

const ciciotAttacks = ['BACKDOOR_MALWARE', 'BROWSERHIJACKING', 'COMMANDINJECTION', 'DDOS-HTTP_FLOOD', 'DDOS-ICMP_FLOOD', 'DDOS-SYN_FLOOD', 'DDOS-TCP_FLOOD', 'DDOS-UDP_FLOOD', 'DICTIONARYBRUTEFORCE', 'DNS_SPOOFING', 'DOS-HTTP_FLOOD', 'DOS-SYN_FLOOD', 'DOS-TCP_FLOOD', 'DOS-UDP_FLOOD', 'MIRAI-GREETH_FLOOD', 'MIRAI-GREIP_FLOOD', 'MIRAI-UDPPLAIN', 'MITM-ARPSPOOFING', 'RECON-HOSTDISCOVERY', 'RECON-OSSCAN', 'RECON-PORTSCAN', 'SQLINJECTION', 'UPLOADING_ATTACK', 'VULNERABILITYSCAN', 'XSS']
const nftoniotAttacks = ['DDoS', 'DoS', 'Injection', 'Ransomware', 'Scanning', 'XSS', 'Backdoor', 'Password', 'MITM', 'Benign']

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
                  {[...ciciotAttacks, ...nftoniotAttacks].map((a) => <span key={a}>{a}</span>)}
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
                  <small>NF-ToN-V2 Accuracy</small>
                  <h2 data-count-to="79.92" data-count-suffix="%">79.92%</h2>
                  <div style={{ marginTop: 6, display: 'flex', justifyContent: 'center', gap: 14 }}>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>CICIoT2023: <strong style={{ color: 'var(--black)' }}>71.35%</strong></span>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>Classes: <strong style={{ color: 'var(--black)' }}>34+10</strong></span>
                  </div>
                </div>
                <div className="metric-grid">
                  <div className="metric-card"><small>Attack Classes</small><h3>34+10</h3></div>
                  <div className="metric-card"><small>Features</small><h3>39+41</h3></div>
                  <div className="metric-card"><small>Training Samples</small><h3>537K</h3></div>
                  <div className="metric-card"><small>Fed Clients</small><h3>10</h3></div>
                </div>
                <div className="dashboard-graph">
                  <svg viewBox="0 0 280 60" preserveAspectRatio="none" style={{ width: '100%', height: '100%', display: 'block' }}>
                    <rect x="5" y="30" width="28" height="30" fill="var(--blue)" className="graph-bar" style={{ animationDelay: '0.05s' }} />
                    <rect x="38" y="18" width="28" height="42" fill="var(--blue)" className="graph-bar" style={{ animationDelay: '0.10s' }} />
                    <rect x="71" y="6" width="28" height="54" fill="var(--blue)" className="graph-bar" style={{ animationDelay: '0.15s' }} />
                    <rect x="104" y="21" width="28" height="39" fill="var(--turquoise)" className="graph-bar" style={{ animationDelay: '0.20s' }} />
                    <rect x="137" y="3" width="28" height="57" fill="var(--blue)" className="graph-bar" style={{ animationDelay: '0.25s' }} />
                    <rect x="170" y="15" width="28" height="45" fill="var(--blue)" className="graph-bar" style={{ animationDelay: '0.30s' }} />
                    <rect x="203" y="24" width="28" height="36" fill="var(--blue)" className="graph-bar" style={{ animationDelay: '0.35s' }} />
                    <rect x="236" y="36" width="28" height="24" fill="var(--blue)" className="graph-bar" style={{ animationDelay: '0.40s' }} />
                  </svg>
                </div>
                <div className="dashboard-footer">
                  <small>Datasets</small>
                  <strong>CICIoT2023 + NF-ToN-IoT-V2</strong>
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
              { num: '01', icon: 'fa-solid fa-database', title: 'Streaming Load', desc: '45M + 13M records from CICIoT2023 and NF-ToN-IoT-V2' },
              { num: '02', icon: 'fa-solid fa-scale-balanced', title: 'Per-Class Balance', desc: '50K max/class, 10+10 classes, 814K total balanced' },
              { num: '03', icon: 'fa-solid fa-sliders', title: 'Standard Scaling', desc: '39 + 41 features normalized per dataset' },
              { num: '04', icon: 'fa-solid fa-network-wired', title: 'FedAvg Training', desc: '10 clients, 10 rounds, 3 epochs each' },
              { num: '05', icon: 'fa-solid fa-chart-bar', title: 'Evaluation', desc: '71.35% / 79.92% accuracy, confusion matrices' },
              { num: '06', icon: 'fa-solid fa-shield-halved', title: 'Inference', desc: 'Dual-model API with dataset selection' },
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
              { icon: 'fa-solid fa-brain', title: 'TensorFlow / Keras', desc: 'DNN: 512 → 256 → 128 → 10 classes per dataset.' },
              { icon: 'fa-solid fa-flask', title: 'Flask API', desc: '6 REST endpoints for prediction, status, config.' },
              { icon: 'fa-solid fa-network-wired', title: 'Federated Averaging', desc: 'FedAvg aggregates client weights privately.' },
              { icon: 'fa-solid fa-table', title: 'Parquet / Pandas', desc: '58M records from two datasets loaded in batches.' },
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
              { num: '01', title: 'Collect & Load', desc: 'CICIoT2023 (45M rows, 10 cls) + NF-ToN-IoT-V2 (13M rows, 10 cls) loaded in streaming batches.' },
              { num: '02', title: 'Preprocess & Balance', desc: '39 / 41 features standardized, class-balanced at 5K / 50K max per class.' },
              { num: '03', title: 'Federated Training', desc: '10 simulated clients train locally (3 epochs each) — raw data never leaves.' },
              { num: '04', title: 'Global Aggregation', desc: 'FedAvg merges local weight updates into a global DNN model.' },
              { num: '05', title: 'Evaluate & Deploy', desc: '71.35% / 79.92% accuracy. Confusion matrices, precision, recall computed.' },
              { num: '06', title: 'Real-Time Inference', desc: 'Flask API serves predictions with dataset selectable via query param.' },
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
                  <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
                    <div style={{ flex: 1, textAlign: 'center', padding: 10, background: 'var(--yellow)', border: 'var(--border-thick)' }}>
                      <small style={{ display: 'block', fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--black)', fontWeight: 700, marginBottom: 2 }}>NF-ToN-V2</small>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.6rem', fontWeight: 700, letterSpacing: '0.04em' }}>79.92%</span>
                    </div>
                    <div style={{ flex: 1, textAlign: 'center', padding: 10, background: 'var(--bg)', border: 'var(--border-thick)' }}>
                      <small style={{ display: 'block', fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', fontWeight: 700, marginBottom: 2 }}>CICIoT2023</small>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.6rem', fontWeight: 700, letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>71.35%</span>
                    </div>
                  </div>
                  <svg viewBox="0 0 260 80" style={{ width: '100%', display: 'block', marginBottom: 14 }}>
                    <line x1="20" y1="70" x2="250" y2="70" stroke="var(--black)" strokeWidth="2" />
                    <line x1="20" y1="10" x2="20" y2="70" stroke="var(--black)" strokeWidth="2" />
                    <text x="22" y="24" fontSize="5" fill="var(--text-muted)" fontFamily="monospace">80%</text>
                    <text x="22" y="47" fontSize="5" fill="var(--text-muted)" fontFamily="monospace">60%</text>
                    <text x="22" y="68" fontSize="5" fill="var(--text-muted)" fontFamily="monospace">40%</text>
                    <polyline points="43,60 66,52 89,44 112,36 135,30 158,26 181,22 204,20 227,18 250,17" fill="none" stroke="var(--magenta)" strokeWidth="2" strokeLinejoin="round" className="chart-line" />
                    <polyline points="43,64 66,58 89,52 112,47 135,43 158,39 181,37 204,35 227,34 250,33" fill="none" stroke="var(--blue)" strokeWidth="2" strokeLinejoin="round" className="chart-line" />
                    <circle cx="250" cy="17" r="3" fill="var(--magenta)" stroke="var(--black)" strokeWidth="1.5" />
                    <circle cx="250" cy="33" r="3" fill="var(--blue)" stroke="var(--black)" strokeWidth="1.5" />
                    <text x="225" y="10" fontSize="4.5" fill="var(--magenta)" fontFamily="monospace" fontWeight="700">NF-ToN</text>
                    <text x="225" y="46" fontSize="4.5" fill="var(--blue)" fontFamily="monospace" fontWeight="700">CICIoT</text>
                    <text x="15" y="82" fontSize="5" fill="var(--text-muted)" fontFamily="monospace">R1</text>
                    <text x="60" y="82" fontSize="5" fill="var(--text-muted)" fontFamily="monospace">R3</text>
                    <text x="108" y="82" fontSize="5" fill="var(--text-muted)" fontFamily="monospace">R5</text>
                    <text x="155" y="82" fontSize="5" fill="var(--text-muted)" fontFamily="monospace">R7</text>
                    <text x="200" y="82" fontSize="5" fill="var(--text-muted)" fontFamily="monospace">R10</text>
                  </svg>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                    {[{ l: 'CICIoT Acc', v: '71.35%' }, { l: 'NF-ToN Acc', v: '79.92%' }, { l: 'Classes', v: '10+10' }, { l: 'Clients', v: '10' }].map((c, i) => (
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
            <p>Actual results from two trained federated DNN models — CICIoT2023 (10 merged classes) and NF-ToN-IoT-V2 (10 classes).</p>
          </div>
          <div className="grid-4">
            {[
              { value: '79.92', suffix: '%', label: 'NF-ToN-V2 Accuracy' },
              { value: '71.35', suffix: '%', label: 'CICIoT2023 Accuracy' },
              { value: '537', suffix: 'K', label: 'Total Samples' },
              { value: '44', suffix: '', label: 'Total Classes' },
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
