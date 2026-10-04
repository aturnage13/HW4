import { Link } from 'react-router-dom'
import { ALL_CAMPUS_PHOTOS } from '../data/campusPhotos'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <img src="/brand/yale-logo.svg" alt="Yale" className="brand-logo" />
          <div>
            <p className="brand-name">
              Campus <span>Customs</span>
            </p>
            <p className="muted">57 Broadway, New Haven, CT 06511</p>
          </div>
        </div>
        <nav className="footer-links">
          <Link to="/products">Shop</Link>
          <Link to="/about">About Us</Link>
          <Link to="/login">Log In</Link>
        </nav>
      </div>
      <p className="footer-credit">
        Yale wordmark and the 1889 photo of Handsome Dan are public domain. Campus photos:{' '}
        {ALL_CAMPUS_PHOTOS.map((p) => `${p.caption} by ${p.credit} (${p.license})`).join(' · ')}. All via
        Wikimedia Commons.
      </p>
    </footer>
  )
}
