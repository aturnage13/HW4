import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchStock } from '../api/chat'
import type { SizeStock } from '../api/chat'
import { formatPrice, getProduct, imageUrl } from '../data/products'
import NotFound from './NotFound'

const STATUS_LABEL: Record<SizeStock['status'], (q: number) => string> = {
  in_stock: () => 'In stock',
  low_stock: (q) => `Only ${q} left`,
  out_of_stock: () => 'Sold out',
}

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const product = getProduct(productId)
  const [stock, setStock] = useState<SizeStock[] | null>(null)
  const [stockError, setStockError] = useState(false)

  useEffect(() => {
    setStock(null)
    setStockError(false)
    fetchStock(productId)
      .then(setStock)
      .catch(() => setStockError(true))
  }, [productId])

  if (!product) return <NotFound />

  return (
    <section className="section">
      <Link to="/products" className="text-link back-link">
        ← Back to all products
      </Link>
      <div className="detail">
        <div className="detail-image">
          <img src={imageUrl(product)} alt={product.name} />
        </div>
        <div className="detail-info">
          <p className="eyebrow">{product.garmentType}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-desc">{product.description}</p>

          <h2 className="detail-label">Colors</h2>
          <ul className="chip-list">
            {product.colors.map((c) => (
              <li key={c} className="chip">
                {c}
              </li>
            ))}
          </ul>

          <h2 className="detail-label">Sizes &amp; Stock</h2>
          {stock && (
            <ul className="chip-list">
              {stock.map((s) => (
                <li key={s.size} className={`chip chip-size ${s.status}`}>
                  {s.size}
                  <small>{STATUS_LABEL[s.status](s.quantity)}</small>
                </li>
              ))}
            </ul>
          )}
          {!stock && !stockError && <p className="muted small">Checking stock…</p>}
          {stockError && <p className="muted small">Stock is unavailable right now.</p>}
        </div>
      </div>
    </section>
  )
}
