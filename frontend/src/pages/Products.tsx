import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import type { CardData } from '../components/ProductCard'
import type { ChatProductCard } from '../api/chat'
import { usePageResults } from '../chat/PageResultsContext'
import { DanSays, SorryDan } from '../components/HandsomeDan'
import { CANT_FIND_SAYINGS, FOUND_SAYINGS, randomSaying } from '../data/danSayings'
import { CAMPUS } from '../data/campusPhotos'
import { products, toCard } from '../data/products'

function chatCard(p: ChatProductCard): CardData {
  return {
    productId: p.productId,
    name: p.name,
    price: p.price,
    imageUrl: p.imageUrl,
    blurb: p.shortDescription,
  }
}

export default function Products() {
  const [params] = useSearchParams()
  const { results } = usePageResults()
  const fromChat = params.get('view') === 'chat' && results
  // A fresh one-liner from Dan for each new set of chat results.
  const saying = useMemo(
    () => randomSaying(results && results.totalMatches > 0 ? FOUND_SAYINGS : CANT_FIND_SAYINGS),
    [results],
  )

  if (fromChat) {
    const count = results.totalMatches
    return (
      <>
        <section className="page-hero page-hero-photo" style={{ backgroundImage: `url(${CAMPUS.oldCampusFall.src})` }}>
          <p className="eyebrow">From the Campus Customs assistant</p>
          <h1>{results.heading}</h1>
          <p>
            {count === 0 ? 'No matches' : `${count} ${count === 1 ? 'match' : 'matches'}`} ·{' '}
            <Link to="/products">Show all products</Link>
          </p>
        </section>
        <section className="section">
          {count === 0 ? (
            <div className="empty-state">
              <SorryDan message={saying} />
              <p className="muted">Try asking the assistant for something else, or browse everything we carry.</p>
              <Link to="/products" className="btn btn-primary">
                Browse All Products
              </Link>
            </div>
          ) : (
            <>
              <div className="found-dan">
                <DanSays mood="found" compact message={saying} />
              </div>
              <div className="product-grid">
                {results.products.map((p) => (
                  <ProductCard key={p.productId} product={chatCard(p)} />
                ))}
              </div>
            </>
          )}
        </section>
      </>
    )
  }

  return (
    <>
      <section className="page-hero page-hero-photo" style={{ backgroundImage: `url(${CAMPUS.oldCampusFall.src})` }}>
        <h1>Shop All Products</h1>
        <p>{products.length} styles of hoodies, crewnecks, tees, and layers.</p>
      </section>
      <section className="section">
        <div className="product-grid">
          {products.map((p) => (
            <ProductCard key={p.productId} product={toCard(p)} />
          ))}
        </div>
      </section>
    </>
  )
}
