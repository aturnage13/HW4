import { Link } from 'react-router-dom'
import CampusGallery from '../components/CampusGallery'
import ProductCard from '../components/ProductCard'
import { CAMPUS } from '../data/campusPhotos'
import { getProduct, imageUrl, products, toCard } from '../data/products'

const featuredIds = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'benjamin-franklin-1-4-zip',
  'baseball-left-chest-crewneck',
]

const categories = [
  { label: 'Hoodies', blurb: 'Warm layers for long library nights.', image: 'basic-hoodie-big-yale' },
  { label: 'Crewnecks', blurb: 'The classic campus sweatshirt.', image: 'baseball-left-chest-crewneck' },
  { label: 'T-Shirts', blurb: 'Easy everyday school spirit.', image: 'morse-logo-t-shirt' },
  { label: 'Quarter-Zips & Jackets', blurb: 'Sharp enough for game day and beyond.', image: 'benjamin-franklin-1-4-zip' },
]

export default function Home() {
  const featured = featuredIds.map((id) => getProduct(id)).filter((p) => p !== undefined)

  return (
    <>
      <section className="hero hero-photo" style={{ backgroundImage: `url(${CAMPUS.harknessAutumn.src})` }}>
        <div className="hero-inner">
          <div className="hero-copy">
            <p className="eyebrow">New Haven's campus outfitter</p>
            <h1>Wear your colors. Live your campus.</h1>
            <p className="hero-sub">
              Hoodies, crewnecks, tees, and layers made for the people who call
              this campus home: students, alumni, families, and fans.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-primary">
                Shop the Collection
              </Link>
              <Link to="/about" className="btn btn-ghost">
                Our Story
              </Link>
            </div>
            <p className="hero-hint">
              Psst, ask our bulldog assistant in the corner for help finding your size.
            </p>
          </div>
        </div>
        <p className="photo-caption">{CAMPUS.harknessAutumn.caption}</p>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Shop favorites</p>
            <h2>Fan Favorites</h2>
          </div>
          <Link to="/products" className="text-link">
            View all {products.length} →
          </Link>
        </div>
        <div className="product-grid">
          {featured.map((p) => (
            <ProductCard key={p.productId} product={toCard(p)} />
          ))}
        </div>
      </section>

      <section className="section">
        <p className="eyebrow">Browse by style</p>
        <h2>Gear for Every Season</h2>
        <div className="category-grid">
          {categories.map((c) => {
            const p = getProduct(c.image)
            return (
              <Link to="/products" key={c.label} className="category-tile">
                {p && <img src={imageUrl(p)} alt="" />}
                <div>
                  <h3>{c.label}</h3>
                  <p>{c.blurb}</p>
                </div>
              </Link>
            )
          })}
        </div>
      </section>

      <section className="section">
        <p className="eyebrow">Our campus</p>
        <h2>The View Never Gets Old</h2>
        <p className="muted section-lede">
          Neither does the gear. Wear your colors from Old Campus to Science Hill.
        </p>
        <CampusGallery photos={[CAMPUS.killingworthSpring, CAMPUS.sterlingLibrary, CAMPUS.phelpsGateSpring]} />
      </section>

      <section className="band band-photo" style={{ backgroundImage: `url(${CAMPUS.oldCampusCourtyard.src})` }}>
        <div className="band-inner">
          <div>
            <h2>Stop by the shop</h2>
            <p>
              Try it on, find your size, and say hello. We're right in the
              heart of New Haven at 57 Broadway.
            </p>
          </div>
          <Link to="/about" className="btn btn-light">
            Plan Your Visit
          </Link>
        </div>
      </section>
    </>
  )
}
