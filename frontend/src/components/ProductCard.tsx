import { Link } from 'react-router-dom'
import { formatPrice } from '../data/products'

export interface CardData {
  productId: string
  name: string
  price: number
  imageUrl: string
  blurb: string
}

// Used for the full catalogue and for chat search results; clicking opens the
// single-item page at /products/:productId.
export default function ProductCard({ product }: { product: CardData }) {
  return (
    <Link to={`/products/${product.productId}`} className="product-card">
      <div className="product-card-image">
        <img src={product.imageUrl} alt={product.name} loading="lazy" />
      </div>
      <div className="product-card-body">
        <h3>{product.name}</h3>
        <p className="price">{formatPrice(product.price)}</p>
        <p className="short-desc">{product.blurb}</p>
      </div>
    </Link>
  )
}
