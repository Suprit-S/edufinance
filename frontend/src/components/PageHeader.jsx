/** Standard page heading: small eyebrow label, serif title, optional lead and actions. */
export default function PageHeader({ eyebrow, title, lead, actions }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {lead && <p className="lead">{lead}</p>}
      </div>
      {actions && <div>{actions}</div>}
    </div>
  )
}
