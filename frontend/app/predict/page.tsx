'use client'

import { useState, useRef } from 'react'
import { SectionTag } from '@/components/SectionTag'
import api from '@/lib/api'

const MAX_MB = 50

interface PredictionItem {
  prediction: string
  confidence: number
  top_predictions: { class: string; probability: number }[]
}

interface PredictionData {
  results: PredictionItem[]
  total: number
  distribution: Record<string, number>
  mean_confidence: number
  dataset?: string
}

const STAGES = ['Configure', 'Upload & validate', 'Run detection', 'Review results'] as const

function formatMB(bytes: number) {
  return `${(bytes / 1048576).toFixed(1)} MB`
}

function PredictionRow({ item }: { item: PredictionItem }) {
  const isAttack = item.prediction !== 'Benign'
  return (
    <div style={{ padding: 12, background: 'var(--bg)', border: 'var(--border-thick)', marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span className={`tag ${isAttack ? 'tag-magenta' : 'tag-turquoise'}`}>{isAttack ? 'Attack' : 'Normal'}</span>
        <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{item.prediction}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <small style={{ color: 'var(--text-muted)', minWidth: 60 }}>{(item.confidence * 100).toFixed(1)}%</small>
        <div style={{ flex: 1, height: 6, background: 'var(--bg)', border: '2px solid var(--black)' }}>
          <div style={{ height: '100%', width: `${item.confidence * 100}%`, background: isAttack ? 'var(--magenta)' : 'var(--turquoise)' }} />
        </div>
      </div>
    </div>
  )
}

function PaginatedPredictions({ results, distribution }: { results: PredictionItem[]; distribution: Record<string, number> }) {
  const [page, setPage] = useState(0)
  const [query, setQuery] = useState('')
  const PAGE = 50
  const filtered = query
    ? results.filter((r) => r.prediction.toLowerCase().includes(query.toLowerCase()))
    : results
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE))
  const safePage = Math.min(page, pages - 1)
  const slice = filtered.slice(safePage * PAGE, safePage * PAGE + PAGE)
  const download = () => {
    const rows = ['prediction,confidence', ...filtered.map((r) => `${r.prediction},${r.confidence}`)].join('\n')
    const blob = new Blob([rows], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'predictions.csv'
    a.click()
    URL.revokeObjectURL(a.href)
  }
  return (
    <div>
      <h4 style={{ marginBottom: 10 }}>All Predictions ({filtered.length}{query ? ` matching “${query}”` : ''})</h4>
      <small style={{ color: 'var(--text-muted)' }}>Class distribution: {Object.entries(distribution).map(([k, v]) => `${k}: ${v}`).join(', ')}</small>
      <div className="form-group" style={{ marginTop: 10 }}>
        <label htmlFor="pred-search" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: 6 }}>Filter by class</label>
        <input
          id="pred-search"
          className="form-input"
          type="search"
          placeholder="e.g. DDoS"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setPage(0) }}
        />
      </div>
      {filtered.length === 0 && <div className="alert">No predictions match this filter.</div>}
      <div style={{ margin: '10px 0' }}>{slice.map((item, i) => <PredictionRow key={i} item={item} />)}</div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <button type="button" className="btn btn-sm" disabled={safePage === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>Prev</button>
        <small>Page {safePage + 1} / {pages}</small>
        <button type="button" className="btn btn-sm" disabled={safePage + 1 >= pages} onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}>Next</button>
        <button type="button" className="btn btn-sm" onClick={download}>Download CSV</button>
      </div>
      <small style={{ color: 'var(--text-muted)' }}>Scores are uncalibrated model outputs; confirm before action.</small>
    </div>
  )
}

export default function Predict() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<PredictionData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dataset, setDataset] = useState('CICIoT2023')
  const fileRef = useRef<HTMLInputElement>(null)

  const ext = file ? file.name.split('.').pop()?.toLowerCase() : null
  const extOk = !file || ext === 'csv' || ext === 'parquet'
  const sizeOk = !file || file.size <= MAX_MB * 1024 * 1024
  const fileError = !file
    ? null
    : !extOk
      ? `“${file.name}” has an unsupported extension. Use .csv or .parquet.`
      : !sizeOk
        ? `File is ${formatMB(file.size)}; server limit is ${MAX_MB} MB. Choose a smaller file.`
        : null
  const canRun = Boolean(file) && !fileError && !loading
  const stage: 1 | 2 | 3 | 4 = data ? 4 : loading ? 3 : file && !fileError ? 3 : file ? 2 : 1

  const handleFile = (f: File) => {
    setFile(f)
    setData(null)
    setError(null)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0])
  }

  const openPicker = () => fileRef.current?.click()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || fileError) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.predictFile(file, dataset)
      setData(res)
    } catch (err: any) {
      setError(err.message || 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  const retry = () => {
    setError(null)
    setData(null)
    if (file && !fileError) {
      const f = file
      setLoading(true)
      api.predictFile(f, dataset)
        .then(setData)
        .catch((err: any) => setError(err.message || 'Prediction failed'))
        .finally(() => setLoading(false))
    }
  }

  const first = data?.results?.[0]
  const isAttack = first?.prediction !== 'Benign'

  return (
    <section className="page-predict">
      <div className="container">
        <div className="reveal" style={{ marginBottom: 36 }}>
          <SectionTag icon="fa-solid fa-microchip">AI Prediction Engine</SectionTag>
          <h1 style={{ marginTop: 10 }}>Detect Network Threats Instantly</h1>
          <p style={{ maxWidth: 600, marginTop: 6 }}>Upload network traffic data to detect cyber attacks using our Federated Learning model.</p>
        </div>

        <ol style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }} aria-label="Prediction workflow stages">
          {STAGES.map((s, i) => (
            <li key={s} className="tag" style={{ opacity: stage === i + 1 ? 1 : 0.55 }} aria-current={stage === i + 1 ? 'step' : undefined}>
              {`0${i + 1} · ${s}`}
            </li>
          ))}
        </ol>

        <div className="predict-grid">
          <div>
            <div className="card-feature" style={{ padding: 32 }}>
              <h2>01 · Configure</h2>
              <p style={{ marginBottom: 20 }}>Select the model trained on matching feature format.</p>

              <form onSubmit={handleSubmit}>
                <div className="form-group" style={{ marginBottom: 14 }}>
                  <label htmlFor="dataset-select" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: 6 }}>Target Model</label>
                  <select id="dataset-select" className="form-input" value={dataset} onChange={(e) => setDataset(e.target.value)} style={{ width: '100%', padding: '10px 12px', fontFamily: 'var(--font-mono)' }}>
                    <option value="CICIoT2023">CICIoT2023 (10 classes, 39 features)</option>
                    <option value="NF-ToN-IoT-V2">NF-ToN-IoT-V2 (10 classes, 41 features)</option>
                  </select>
                </div>

                <h2 style={{ marginTop: 20 }}>02 · Upload &amp; validate</h2>
                <div className="form-group">
                  <div
                    className="form-input"
                    role="button"
                    tabIndex={0}
                    aria-label="Select a CSV or Parquet file. Press Enter to browse."
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openPicker() } }}
                    style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 36, cursor: 'pointer', textAlign: 'center', minHeight: 160, justifyContent: 'center' }}
                    onClick={openPicker}
                    onDragOver={(e) => { e.preventDefault(); (e.currentTarget as HTMLDivElement).style.background = 'var(--yellow)' }}
                    onDragLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = '' }}
                    onDrop={handleDrop}
                  >
                    <i className="fa-solid fa-cloud-arrow-up" style={{ fontSize: '2.2rem', color: 'var(--blue)', marginBottom: 14 }} aria-hidden="true" />
                    <h4 style={{ marginBottom: 4 }}>Drop file here or press Enter to browse</h4>
                    <small>Supports .csv and .parquet files (max {MAX_MB} MB)</small>
                    <input ref={fileRef} type="file" accept=".csv,.parquet" style={{ display: 'none' }} onChange={(e) => e.target.files?.length && handleFile(e.target.files[0])} aria-hidden="true" tabIndex={-1} />
                  </div>
                  {file && (
                    <div style={{ marginTop: 10, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                      <span className="tag"><i className="fa-solid fa-file" /> {file.name} · {formatMB(file.size)}</span>
                      <button type="button" className="btn btn-sm" onClick={() => { setFile(null); setData(null); setError(null) }}>Remove</button>
                    </div>
                  )}
                  {fileError && <div className="alert alert-danger" role="alert" style={{ marginTop: 10 }}>{fileError}</div>}
                </div>

                <h2 style={{ marginTop: 20 }}>03 · Run detection</h2>
                <button type="submit" className="btn btn-blue btn-lg" disabled={!canRun} style={{ width: '100%', opacity: !canRun ? 0.5 : 1 }} aria-disabled={!canRun}>
                  {loading ? <><i className="fa-solid fa-spinner fa-spin" /> Analyzing...</> : <><i className="fa-solid fa-shield-halved" /> Run Detection</>}
                </button>
                {loading && <div className="alert" role="status" style={{ marginTop: 10 }}>Analyzing… large files may take a minute.</div>}
              </form>

              <div style={{ marginTop: 16, paddingTop: 16, borderTop: '2px solid var(--bg)' }}>
                <small><i className="fa-solid fa-info-circle" /> The selected file is sent to the configured AIPFL-IDS server for analysis and deleted after prediction. See deployment docs for retention, logging, and transport security.</small>
              </div>
            </div>
          </div>

          <div className="predict-result-card">
            <h3>04 · Review results</h3>
            <p style={{ fontSize: '0.88rem', marginBottom: 16 }}>Prediction output will appear here.</p>

            {!data && !error && !loading && (
              <div style={{ textAlign: 'center', padding: 36 }}>
                <i className="fa-solid fa-microchip" style={{ fontSize: '2.5rem', color: 'var(--text-muted)', marginBottom: 14 }} />
                <p style={{ color: 'var(--text-muted)' }}>Upload traffic data and run detection to see results.</p>
              </div>
            )}

            {error && (
              <div className="alert alert-danger" role="alert">
                <p style={{ marginBottom: 10 }}>{error}</p>
                <p style={{ fontSize: '0.8rem', marginBottom: 10 }}>Common causes: missing required columns, wrong dataset selected, or an oversized file.</p>
                <button type="button" className="btn btn-sm" onClick={retry} disabled={!file || Boolean(fileError) || loading}>Retry</button>
              </div>
            )}

            {data && first && (
              <>
                <div style={{ padding: 20, background: 'var(--bg)', border: 'var(--border-thick)', marginBottom: 16 }}>
                  <div style={{ marginBottom: 12 }}>
                    <small style={{ display: 'block', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', marginBottom: 4 }}>Prediction</small>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', letterSpacing: '0.1em', marginBottom: 6 }}>{first.prediction}</div>
                    <small style={{ color: 'var(--text-secondary)' }}>Confidence: {(first.confidence * 100).toFixed(1)}% (uncalibrated)</small>
                  </div>
                  <span className={`tag ${isAttack ? 'tag-magenta' : 'tag-turquoise'}`} style={{ padding: '6px 18px' }}>
                    {isAttack ? 'Threat Detected' : 'Normal Traffic'}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                  <div style={{ flex: 1, padding: 14, background: 'var(--bg)', border: 'var(--border-thick)', textAlign: 'center' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.6rem', letterSpacing: '0.06em', color: 'var(--blue)' }}>{data.total}</div>
                    <small style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Rows</small>
                  </div>
                  <div style={{ flex: 1, padding: 14, background: 'var(--bg)', border: 'var(--border-thick)', textAlign: 'center' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.6rem', letterSpacing: '0.06em', color: 'var(--blue)' }}>{(data.mean_confidence * 100).toFixed(1)}%</div>
                    <small style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Avg Conf</small>
                  </div>
                </div>

                {first.top_predictions && (
                  <div style={{ marginBottom: 16 }}>
                    <h4 style={{ marginBottom: 10 }}>Top Classes</h4>
                    {first.top_predictions.map((p, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                        <span style={{ minWidth: 90, fontWeight: 600, fontSize: '0.82rem' }}>{p.class}</span>
                        <div style={{ flex: 1, height: 6, background: 'var(--bg)', border: '2px solid var(--black)' }}>
                          <div style={{ height: '100%', width: `${p.probability * 100}%`, background: 'var(--blue)' }} />
                        </div>
                        <small style={{ color: 'var(--text-muted)', minWidth: 45, textAlign: 'right' }}>{(p.probability * 100).toFixed(1)}%</small>
                      </div>
                    ))}
                  </div>
                )}

                {data.results.length > 1 && (
                  <PaginatedPredictions results={data.results} distribution={data.distribution} />
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
