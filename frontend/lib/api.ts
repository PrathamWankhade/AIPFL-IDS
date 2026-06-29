const api = {
  async getStatus() {
    const res = await fetch('/api/status')
    if (!res.ok) throw new Error('Failed to fetch status')
    const json = await res.json()
    if (!json.success) throw new Error(json.error || 'Failed to fetch status')
    return json.data
  },

  async getHealth() {
    const res = await fetch('/api/health')
    if (!res.ok) throw new Error('Failed to fetch health')
    const json = await res.json()
    if (!json.success) throw new Error(json.error || 'Failed to fetch health')
    return json.data
  },

  async getModels() {
    const res = await fetch('/api/models')
    if (!res.ok) throw new Error('Failed to fetch models')
    const json = await res.json()
    if (!json.success) throw new Error(json.error || 'Failed to fetch models')
    return json.data
  },

  async getConfig() {
    const res = await fetch('/api/config')
    if (!res.ok) throw new Error('Failed to fetch config')
    const json = await res.json()
    if (!json.success) throw new Error(json.error || 'Failed to fetch config')
    return json.data
  },

  async predictFile(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('/api/predict', {
      method: 'POST',
      body: formData,
    })
    const json = await res.json()
    if (!json.success) throw new Error(json.error || 'Prediction failed')
    return json.data
  },

  async predictBatch(features: Record<string, any>[]) {
    const res = await fetch('/api/predict-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ features }),
    })
    const json = await res.json()
    if (!json.success) throw new Error(json.error || 'Batch prediction failed')
    return json.data
  },
}

export default api
