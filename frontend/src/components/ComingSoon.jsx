/** Placeholder card used by pages that are delivered in a later sprint. */
export default function ComingSoon({ sprint, features = [] }) {
  return (
    <section className="card empty">
      <h2>Arrives in Sprint {sprint}</h2>
      <p>This page is part of the product backlog and is built in Sprint {sprint}.</p>
      {features.length > 0 && (
        <ul className="feature-list">
          {features.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      )}
    </section>
  )
}
