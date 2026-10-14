import { SectionTag } from '@/components/SectionTag'

export default function About() {
  return (
    <section className="page-about">
      <div className="container">
        <div className="about-hero-block reveal">
          <SectionTag icon="fa-solid fa-shield-halved">About the Project</SectionTag>
          <h1>AI-Powered Federated Learning Intrusion Detection</h1>
          <p>AIPFL-IDS is a privacy-preserving cybersecurity solution that combines AI, Deep Learning, and Federated Learning to detect malicious network traffic without requiring organizations to share their raw data.</p>
        </div>

        <div className="about-stats">
          {[
            { value: '13M', label: 'Dataset Records' },
            { value: '79.85%', label: 'Test Accuracy' },
            { value: '10', label: 'Attack Classes' },
            { value: '10', label: 'Global Rounds' },
          ].map((s, i) => (
            <div key={i} className="about-stat reveal">
              <h3>{s.value}</h3>
              <p>{s.label}</p>
            </div>
          ))}
        </div>

        <div className="section-header reveal">
          <SectionTag>Overview</SectionTag>
          <h2>The Problem We Solve</h2>
          <p>Traditional IDS rely on centralized datasets where all network traffic is collected into one server. This introduces serious privacy, security, scalability, and legal challenges.</p>
        </div>
        <div className="grid-2" style={{ marginBottom: 70 }}>
          <div className="card-feature reveal-left">
            <h3>Traditional IDS Challenges</h3>
            <p>Centralized IDS systems require sensitive network traffic to be transferred and stored centrally. This creates data privacy risks, single points of failure, and regulatory compliance issues.</p>
          </div>
          <div className="card-feature reveal-right">
            <h3>Our Federated Solution</h3>
            <p>AIPFL-IDS uses Federated Learning where each client trains a model locally and shares only anonymized model parameters — never raw network data. Privacy is preserved while achieving high detection accuracy.</p>
          </div>
        </div>

        <div className="section-header reveal">
          <SectionTag>Architecture</SectionTag>
          <h2>How It Works</h2>
          <p>A complete AI pipeline that transforms raw IoT traffic into intelligent cyber attack predictions.</p>
        </div>
        <div className="timeline" style={{ marginBottom: 70 }}>
          {[
            { num: '01', title: 'Data Collection & Balancing', desc: 'IoT network traffic is collected from distributed devices. The NF-ToN-IoT-V2 dataset contains over 13 million records with 43 features. Each attack category is sampled up to 50,000 records to create a balanced dataset.' },
            { num: '02', title: 'Preprocessing & Feature Engineering', desc: 'Unstable features are removed, infinite values are handled via median imputation, constant features are eliminated using VarianceThreshold, and all features are standardized using StandardScaler.' },
            { num: '03', title: 'Federated Training', desc: 'The dataset is split among 10 simulated clients. Each client trains a deep neural network locally for 3 epochs per global round. Only model weights — never data — are shared with the central server.' },
            { num: '04', title: 'Federated Averaging (FedAvg)', desc: 'The central server aggregates client updates using weighted Federated Averaging. Larger client datasets contribute proportionally more. Invalid updates are discarded for stability.' },
            { num: '05', title: 'AI Prediction & Evaluation', desc: 'The global model achieves 79.85% test accuracy across 10 attack types including DDoS, DoS, Ransomware, Injection, XSS, and more.' },
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

        <div className="section-header reveal">
          <SectionTag>Model Architecture</SectionTag>
          <h2>Deep Neural Network Design</h2>
          <p>The model is implemented as a fully connected neural network using TensorFlow Keras.</p>
        </div>
        <div className="grid-2" style={{ marginBottom: 70 }}>
          <div className="card-feature reveal-left">
            <h3>Network Structure</h3>
            <ul className="check-list" style={{ marginTop: 14 }}>
              <li><i className="fa-solid fa-check" /> Input: 39 features after preprocessing</li>
              <li><i className="fa-solid fa-check" /> Hidden: 512 → 256 → 128 → 64 neurons</li>
              <li><i className="fa-solid fa-check" /> Output: 10 classes (Softmax activation)</li>
              <li><i className="fa-solid fa-check" /> Batch Normalization after each hidden layer</li>
              <li><i className="fa-solid fa-check" /> Dropout (0.30, 0.30, 0.20) for regularization</li>
              <li><i className="fa-solid fa-check" /> L2 regularization on all dense layers</li>
            </ul>
          </div>
          <div className="card-feature reveal-right">
            <h3>Training Configuration</h3>
            <ul className="check-list" style={{ marginTop: 14 }}>
              <li><i className="fa-solid fa-check" /> Optimizer: Adam (lr=0.0005, clipnorm=1.0)</li>
              <li><i className="fa-solid fa-check" /> Loss: Sparse Categorical Crossentropy</li>
              <li><i className="fa-solid fa-check" /> 10 clients, 10 global communication rounds</li>
              <li><i className="fa-solid fa-check" /> 3 local epochs per round per client</li>
              <li><i className="fa-solid fa-check" /> Mixed Precision (float16) for GPU efficiency</li>
              <li><i className="fa-solid fa-check" /> EarlyStopping & ReduceLROnPlateau callbacks</li>
            </ul>
          </div>
        </div>

        <div className="section-header reveal">
          <SectionTag>Performance</SectionTag>
          <h2>Detection Capabilities</h2>
          <p>The AIPFL-IDS model achieves industry-leading performance while maintaining privacy.</p>
        </div>
        <div className="grid-4">
          {[
            { value: '79.85', suffix: '%', label: 'Test Accuracy' },
            { value: '377', suffix: 'K', label: 'Training Samples' },
            { value: '39', suffix: '', label: 'Input Features' },
            { value: '10', suffix: '', label: 'Fed Clients' },
          ].map((s, i) => (
            <div key={i} className="stat-card reveal">
              <h2 className="stat-number" data-count-to={s.value} data-count-suffix={s.suffix}>{s.value}{s.suffix}</h2>
              <p className="stat-label">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
