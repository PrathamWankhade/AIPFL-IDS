export function DashboardMetric({ label, value, change, children }: {
  label: string
  value: string
  change?: string
  children?: React.ReactNode
}) {
  return (
    <div className="stat-card">
      <div className="stat-label" style={{ marginBottom: 6 }}>{label}</div>
      <div className="stat-number" data-count-to={value}>{value}{children}</div>
      {change && <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4, fontWeight: 600 }}>{change}</div>}
    </div>
  )
}
