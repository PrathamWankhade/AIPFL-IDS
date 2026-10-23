'use client'

import { SectionTag } from '@/components/SectionTag'

const REPO = 'https://github.com/PrathamWankhade/AIPFL-IDS'

const CHANNELS = [
  {
    icon: 'fa-solid fa-bug',
    label: 'Bug Reports',
    value: 'Open a GitHub issue',
    href: `${REPO}/issues/new`,
    desc: 'Crashes, wrong predictions, docs gaps.',
  },
  {
    icon: 'fa-solid fa-lightbulb',
    label: 'Feature Requests',
    value: 'Start a discussion',
    href: `${REPO}/issues`,
    desc: 'Model, pipeline, or UI improvements.',
  },
  {
    icon: 'fa-brands fa-github',
    label: 'Source',
    value: 'github.com/PrathamWankhade',
    href: 'https://github.com/PrathamWankhade',
    desc: 'Code, commit history, CI status.',
  },
  {
    icon: 'fa-solid fa-scale-balanced',
    label: 'License',
    value: 'MIT',
    href: `${REPO}/blob/main/LICENSE`,
    desc: 'Open-source; datasets keep their own terms.',
  },
]

export default function Contact() {
  return (
    <section className="page-contact">
      <div className="container">
        <div className="reveal" style={{ marginBottom: 36 }}>
          <SectionTag icon="fa-solid fa-envelope">Get In Touch</SectionTag>
          <h1 style={{ marginTop: 10 }}>Let&apos;s Talk About Network Security</h1>
          <p style={{ maxWidth: 640, marginTop: 6 }}>
            AIPFL-IDS is an open-source research prototype. This project has no
            backend contact service, so messages go through GitHub — every
            channel below is a real, live destination.
          </p>
        </div>

        <div className="contact-grid">
          <div className="reveal-left">
            <h2 style={{ marginBottom: 10 }}>Reach the Project</h2>
            <p style={{ marginBottom: 28 }}>
              Whether you are reproducing the training run, auditing the
              federated simulation, or reviewing the security posture, open an
              issue with enough detail to reproduce what you saw.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {CHANNELS.map((c) => (
                <a
                  key={c.label}
                  href={c.href}
                  target="_blank"
                  rel="noreferrer"
                  className="contact-item"
                  style={{ display: 'flex', gap: 14, alignItems: 'center', textDecoration: 'none', color: 'inherit' }}
                >
                  <i className={c.icon} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>{c.label}</div>
                    <div style={{ fontWeight: 600 }}>{c.value}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{c.desc}</div>
                  </div>
                </a>
              ))}
            </div>
          </div>

          <div className="contact-form-card reveal-right">
            <h3 style={{ marginBottom: 12 }}>Before You Open an Issue</h3>
            <p style={{ fontSize: '0.88rem', marginBottom: 16 }}>
              Useful reports include the dataset, the command you ran, and the
              exact error or screenshot. Keep these in mind:
            </p>
            <ul className="check-list" style={{ marginBottom: 20 }}>
              <li><i className="fa-solid fa-circle-info" /> Trained models and raw datasets are not committed — train first (see README).</li>
              <li><i className="fa-solid fa-circle-info" /> Published accuracy figures are historical and pending a clean retrain.</li>
              <li><i className="fa-solid fa-circle-info" /> Federated training is an in-process simulation; no secure aggregation or DP.</li>
              <li><i className="fa-solid fa-circle-info" /> Predictions are uncalibrated model outputs, not confirmed incidents.</li>
            </ul>
            <a href={`${REPO}/issues/new`} target="_blank" rel="noreferrer" className="btn btn-blue btn-lg" style={{ width: '100%', textAlign: 'center' }}>
              <i className="fa-solid fa-paper-plane" /> Open a GitHub Issue
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
