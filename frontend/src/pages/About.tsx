import CampusGallery from '../components/CampusGallery'
import { CAMPUS } from '../data/campusPhotos'

const values = [
  {
    title: 'Made for Campus Life',
    text: 'Every piece is chosen for how students actually live: early classes, late study sessions, and everything in between.',
  },
  {
    title: 'Pride You Can Wear',
    text: 'From residential college crests to rivalry-game graphics, our designs celebrate the traditions that make this place home.',
  },
  {
    title: 'Comfort First',
    text: 'Soft fleece, easy fits, and fabrics that hold up wash after wash, so your favorite hoodie stays your favorite.',
  },
]

export default function About() {
  return (
    <>
      <section className="page-hero page-hero-photo" style={{ backgroundImage: `url(${CAMPUS.branfordHarkness.src})` }}>
        <h1>About Us</h1>
        <p>Local roots. Campus spirit. Gear that feels like home.</p>
      </section>

      <section className="section narrow">
        <h2>Our Story</h2>
        <p>
          Campus Customs started with a simple idea: the clothes you wear on
          campus should say something about where you belong. We're a
          New Haven shop that outfits students, alumni, families, and fans with
          apparel that's comfortable enough for every day and meaningful
          enough to keep for years.
        </p>
        <p>
          Whether you're moving in for your first semester, cheering at the
          big game, or coming back for reunion weekend, we want you to find
          something that brings you right back to campus.
        </p>
      </section>

      <section className="section">
        <div className="values-grid">
          {values.map((v) => (
            <div key={v.title} className="value-card">
              <h3>{v.title}</h3>
              <p>{v.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <p className="eyebrow">Our campus</p>
        <h2>Where Our Gear Lives</h2>
        <CampusGallery
          photos={[CAMPUS.crossCampusPath, CAMPUS.killingworthSpring, CAMPUS.sterlingLibrary, CAMPUS.phelpsGateSpring]}
        />
      </section>

      <section className="section narrow">
        <h2>Visit the Shop</h2>
        <p>
          Come see us in person at <strong>57 Broadway, New Haven, CT 06511</strong>.
          Our team is happy to help you find the right fit, the right color,
          and the right gift.
        </p>
      </section>
    </>
  )
}
