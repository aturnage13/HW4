import { useState } from 'react'
import type { FormEvent } from 'react'
import { CAMPUS } from '../data/campusPhotos'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, authApi } from '../api/auth'
import { useAuth } from '../auth/AuthContext'

export default function LogIn() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [unverifiedEmail, setUnverifiedEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const email = String(form.get('email'))
    setError('')
    setNotice('')
    setUnverifiedEmail('')
    setSubmitting(true)
    try {
      await login(email, String(form.get('password')))
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      if (err instanceof ApiError && err.status === 403) setUnverifiedEmail(email)
    } finally {
      setSubmitting(false)
    }
  }

  async function resend() {
    const { message } = await authApi.resendVerification(unverifiedEmail)
    setError('')
    setNotice(message)
  }

  return (
    <section className="section auth auth-split">
      <figure className="auth-photo" style={{ backgroundImage: `url(${CAMPUS.crossCampusLeaves.src})` }}>
        <figcaption>Welcome back to campus.</figcaption>
      </figure>
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Welcome back</h1>
        <p className="muted">Log in to your Campus Customs account.</p>
        {error && <p className="form-error" role="alert">{error}</p>}
        {notice && <p className="form-notice">{notice}</p>}
        {unverifiedEmail && !notice && (
          <button type="button" className="link-button" onClick={resend}>
            Resend confirmation email
          </button>
        )}
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input type="password" name="password" autoComplete="current-password" required />
        </label>
        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Logging in…' : 'Log In'}
        </button>
        <p className="muted small">
          New here? <Link to="/create-account">Create an account</Link>
        </p>
      </form>
    </section>
  )
}
