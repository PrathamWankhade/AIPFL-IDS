import Link from 'next/link'

export function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-top">
          <div className="footer-brand">
            <div className="footer-logo">
              <i className="fa-solid fa-shield-halved" />
              AIPFL-IDS
            </div>
            <p>
              AI Powered Federated Learning Intrusion Detection System
              for secure IoT environments. Privacy-preserving network security.
            </p>
          </div>

          <div className="footer-links">
            <div>
              <h4>Navigation</h4>
              <Link href="/">Home</Link>
              <Link href="/about">About</Link>
              <Link href="/dashboard">Dashboard</Link>
              <Link href="/predict">Predict</Link>
            </div>
            <div>
              <h4>Resources</h4>
              <a href="#">Documentation</a>
              <a href="#">Research</a>
              <a href="#">Dataset</a>
              <a href="#">GitHub</a>
            </div>
            <div>
              <h4>Contact</h4>
              <a href="mailto:hello@aipfl-ids.io">Email</a>
              <a href="#">LinkedIn</a>
              <a href="#">GitHub</a>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2026 AIPFL-IDS. All Rights Reserved.</p>
          <div className="footer-socials">
            <a href="#" aria-label="GitHub"><i className="fa-brands fa-github" /></a>
            <a href="#" aria-label="LinkedIn"><i className="fa-brands fa-linkedin-in" /></a>
            <a href="#" aria-label="Twitter"><i className="fa-brands fa-x-twitter" /></a>
          </div>
        </div>
      </div>
    </footer>
  )
}
