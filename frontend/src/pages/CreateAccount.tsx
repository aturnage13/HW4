import { useState } from 'react'
import type { FormEvent } from 'react'
import { CAMPUS } from '../data/campusPhotos'
import { Link } from 'react-router-dom'
import { authApi } from '../api/auth'

export default function CreateAccount() {
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sentTo, setSentTo] = useState('')

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const email = String(form.get('email'))
    setError('')
    setSubmitting(true)
    try {
      await authApi.register({
        first_name: String(form.get('firstName')),
        last_name: String(form.get('lastName')),
        email,
        password: String(form.get('password')),
      })
      setSentTo(email)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  if (sentTo) {
    return (
      <section className="section auth auth-split">
        <figure className="auth-photo" style={{ backgroundImage: `url(${CAMPUS.crossCampusLeaves.src})` }}>
          <figcaption>Join the Campus Customs family.</figcaption>
        </figure>
        <div className="auth-card">
          <h1>Check your email</h1>
          <p>
            We sent a confirmation link to <strong>{sentTo}</strong>. Open it to
            activate your account, then log in.
          </p>
          <p className="muted small">The link expires in 24 hours.</p>
          <Link to="/login" className="btn btn-primary btn-block">
            Go to Log In
          </Link>
        </div>
      </section>
    )
  }

  return (
    <section className="section auth auth-split">
      <figure className="auth-photo" style={{ backgroundImage: `url(${CAMPUS.crossCampusLeaves.src})` }}>
        <figcaption>Join the Campus Customs family.</figcaption>
      </figure>
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Create your account</h1>
        <p className="muted">Save your favorites and chat with our assistant.</p>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="field-row">
          <label>
            First name
            <input type="text" name="firstName" autoComplete="given-name" required />
          </label>
          <label>
            Last name
            <input type="text" name="lastName" autoComplete="family-name" required />
          </label>
        </div>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            minLength={8}
            maxLength={128}
            required
          />
          <span className="hint">At least 8 characters.</span>
        </label>
        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create Account'}
        </button>
        <p className="muted small">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </section>
  )
}
