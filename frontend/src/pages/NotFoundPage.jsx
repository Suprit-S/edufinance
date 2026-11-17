import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section className="card empty">
      <h2>Page not found</h2>
      <p>The page you are looking for does not exist.</p>
      <p style={{ marginTop: 16 }}>
        <Link className="btn btn-primary" to="/">
          Back to dashboard
        </Link>
      </p>
    </section>
  )
}
