async function fetchJson(path: string, init?: RequestInit, timeoutMs = 30000) {
  const ctrl = new AbortController()
  const t = setTimeout(() => ctrl.abort(), timeoutMs)
  try {
    const res = await fetch(path, { ...init, signal: ctrl.signal })
    const ctype = res.headers.get('content-type') || ''
    if (!ctype.includes('application/json')) {
      const text = await res.text()
      throw new Error(`Server returned ${res.status} (non-JSON). ${text.slice(0, 120)}`)
    }
    const json = await res.json()
    if (!res.ok || !json.success) {
      const err: any = new Error(json.error || `Request failed (${res.status})`)
      err.status = res.status
      throw err
    }
    return json.data
  } catch (e: any) {
    if (e?.name === 'AbortError') throw new Error('Request timed out')
    throw e
  } finally {
    clearTimeout(t)
  }
}

const api = {
  getStatus() {
    return fetchJson('/api/status')
  },
  getHealth() {
    return fetchJson('/api/health')
  },
  getReadiness() {
    return fetchJson('/api/readyz')
  },
  getModels() {
    return fetchJson('/api/models')
  },
  getConfig() {
    return fetchJson('/api/config')
  },
  getMetrics() {
    return fetchJson('/api/metrics')
  },
  predictFile(file: File, dataset = 'CICIoT2023') {
    const formData = new FormData()
    formData.append('file', file)
    return fetchJson(`/api/predict?dataset=${encodeURIComponent(dataset)}`, {
      method: 'POST',
      body: formData,
    }, 120000)
  },
  predictBatch(features: Record<string, any>[]) {
    return fetchJson('/api/predict-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ features }),
    })
  },
}

export default api
