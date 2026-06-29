'use client'

import { useState } from 'react'
import { SectionTag } from '@/components/SectionTag'

export default function Contact() {
  const [sent, setSent] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSent(true)
    setTimeout(() => setSent(false), 5000)
  }

  return (
    <section className="page-contact">
      <div className="container">
        <div className="reveal" style={{ marginBottom: 36 }}>
          <SectionTag icon="fa-solid fa-envelope">Get In Touch</SectionTag>
          <h1 style={{ marginTop: 10 }}>Let&apos;s Talk About Network Security</h1>
          <p style={{ maxWidth: 600, marginTop: 6 }}>Have questions about AIPFL-IDS? Want to contribute or deploy Federated Learning in your organization? Reach out to us.</p>
        </div>

        <div className="contact-grid">
          <div className="reveal-left">
            <h2 style={{ marginBottom: 10 }}>We&apos;re Here to Help</h2>
            <p style={{ marginBottom: 28 }}>AIPFL-IDS is an open-source project. Whether you&apos;re a researcher, a security professional, or an organization exploring privacy-preserving intrusion detection — we&apos;d love to hear from you.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { icon: 'fa-solid fa-envelope', label: 'Email', value: 'hello@aipfl-ids.io' },
                { icon: 'fa-brands fa-github', label: 'GitHub', value: 'github.com/aipfl-ids' },
                { icon: 'fa-solid fa-location-dot', label: 'Research', value: 'Open-source AI Security Project' },
                { icon: 'fa-solid fa-clock', label: 'Response Time', value: 'Typically within 24 hours' },
              ].map((c, i) => (
                <div key={i} className="contact-item">
                  <i className={c.icon} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>{c.label}</div>
                    <div style={{ fontWeight: 600 }}>{c.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="contact-form-card reveal-right">
            <h3 style={{ marginBottom: 20 }}>Send Us a Message</h3>
            {sent ? (
              <div style={{ textAlign: 'center', padding: '36px 0' }}>
                <i className="fa-solid fa-circle-check" style={{ fontSize: '2.2rem', color: 'var(--turquoise)', marginBottom: 14 }} />
                <p style={{ fontWeight: 700 }}>Message sent successfully!</p>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>We&apos;ll get back to you soon.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="name">Your Name</label>
                  <input type="text" id="name" className="form-input" placeholder="John Doe" required />
                </div>
                <div className="form-group">
                  <label htmlFor="email">Email Address</label>
                  <input type="email" id="email" className="form-input" placeholder="john@example.com" required />
                </div>
                <div className="form-group">
                  <label htmlFor="subject">Subject</label>
                  <input type="text" id="subject" className="form-input" placeholder="How can we help?" />
                </div>
                <div className="form-group">
                  <label htmlFor="message">Message</label>
                  <textarea id="message" className="form-input" placeholder="Tell us about your project or question..." required />
                </div>
                <button type="submit" className="btn btn-blue btn-lg" style={{ width: '100%' }}>
                  <i className="fa-solid fa-paper-plane" /> Send Message
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
