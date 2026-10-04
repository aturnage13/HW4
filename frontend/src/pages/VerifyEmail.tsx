import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { authApi } from '../api/auth'

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [status, setStatus] = useState<'working' | 'done' | 'error'>(token ? 'working' : 'error')
  const [message, setMessage] = useState(token ? '' : 'This confirmation link is missing its token.')
  const sent = useRef(false)

  useEffect(() => {
    // Tokens are single-use, so guard against StrictMode's double effect run.
    if (!token || sent.current) return
    sent.current = true
    authApi
      .verifyEmail(token)
      .then(({ message }) => {
        setStatus('done')
        setMessage(message)
      })
      .catch((err: Error) => {
        setStatus('error')
        setMessage(err.message)
      })
  }, [token])

  return (
    <section className="section auth">
      <div className="auth-card">
        <h1>
          {status === 'working' && 'Confirming your email…'}
          {status === 'done' && 'Email confirmed'}
          {status === 'error' && "We couldn't confirm your email"}
        </h1>
        {message && <p>{message}</p>}
        {status !== 'working' && (
          <Link to="/login" className="btn btn-primary btn-block">
            Go to Log In
          </Link>
        )}
      </div>
    </section>
  )
}
