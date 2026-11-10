const LABELS = { HEALTHY: 'Healthy', OK: 'OK', WARNING: 'Warning', CRITICAL: 'Critical' }
const CLASSES = { HEALTHY: 'badge-healthy', OK: 'badge-ok', WARNING: 'badge-warning', CRITICAL: 'badge-critical' }

/** Runway status with text (never colour alone) and the days left. */
export default function RunwayBadge({ runway }) {
  if (!runway) return null
  const days = runway.days === null ? 'no spending in 30 days' : `${runway.days} days left`
  return (
    <span className={`badge ${CLASSES[runway.status]}`} title={`Runway: ${days}`}>
      {LABELS[runway.status]} · {days}
    </span>
  )
}
