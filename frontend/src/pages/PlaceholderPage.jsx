import ComingSoon from '../components/ComingSoon'
import PageHeader from '../components/PageHeader'
import { PLACEHOLDERS } from './placeholders'

export default function PlaceholderPage({ page }) {
  const p = PLACEHOLDERS[page]
  return (
    <>
      <PageHeader eyebrow={p.eyebrow} title={p.title} lead={p.lead} />
      <ComingSoon sprint={p.sprint} features={p.features} />
    </>
  )
}
