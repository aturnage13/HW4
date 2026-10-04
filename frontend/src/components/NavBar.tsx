import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const mainLinks = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const guestLinks = [
  { to: '/login', label: 'Log In' },
  { to: '/create-account', label: 'Create Account' },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const close = () => setOpen(false)

  async function handleLogout() {
    close()
    await logout()
    navigate('/')
  }

  const linkClass =
    (to: string) =>
    ({ isActive }: { isActive: boolean }) =>
      ['nav-link', to === '/create-account' ? 'nav-cta' : '', isActive ? 'active' : ''].join(' ')

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="brand" onClick={close} aria-label="Campus Customs home">
          {/* Official Yale wordmark (public domain, Wikimedia Commons), tinted white in CSS */}
          <img src="/brand/yale-logo.svg" alt="Yale" className="brand-logo" />
          <span className="brand-divider" aria-hidden="true" />
          <span className="brand-name">
            Campus <span>Customs</span>
          </span>
        </Link>
        <button
          className="nav-toggle"
          aria-label="Toggle navigation"
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          ☰
        </button>
        <nav className={open ? 'nav-links open' : 'nav-links'}>
          {mainLinks.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === '/'} className={linkClass(link.to)} onClick={close}>
              {link.label}
            </NavLink>
          ))}
          {user ? (
            <>
              <span className="nav-greeting">Hi, {user.firstName}</span>
              <button className="nav-link nav-cta nav-button" onClick={handleLogout}>
                Log Out
              </button>
            </>
          ) : (
            guestLinks.map((link) => (
              <NavLink key={link.to} to={link.to} className={linkClass(link.to)} onClick={close}>
                {link.label}
              </NavLink>
            ))
          )}
        </nav>
      </div>
    </header>
  )
}
