import Link from 'next/link'

const REPO = 'https://github.com/PrathamWankhade/AIPFL-IDS'

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
              AI-powered Intrusion Detection System research demo for IoT
              environments. Federated training is simulated in one process;
              see the threat model for privacy limitations.
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
              <a href={`${REPO}#readme`}>Documentation</a>
              <a href={`${REPO}/actions`}>CI Status</a>
              <a href={REPO}>GitHub</a>
            </div>
            <div>
              <h4>Project</h4>
              <a href={`${REPO}/blob/main/docs/THREAT_MODEL.md`}>Threat Model</a>
              <a href={`${REPO}/blob/main/docs/DEPLOYMENT.md`}>Deployment</a>
              <a href={REPO}>GitHub</a>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2026 AIPFL-IDS. All Rights Reserved.</p>
          <div className="footer-socials">
            <a href={REPO} aria-label="GitHub repository"><i className="fa-brands fa-github" /></a>
          </div>
        </div>
      </div>
    </footer>
  )
}
