export function SectionTag({ icon, children }: { icon?: string; children: React.ReactNode }) {
  return (
    <span className="section-tag">
      {icon && <i className={icon} style={{ fontSize: '0.65rem' }} />}
      {children}
    </span>
  )
}
