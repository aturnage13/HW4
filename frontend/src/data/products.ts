import catalogue from './catalogue.json'
import type { CardData } from '../components/ProductCard'

export interface Product {
  productId: string
  name: string
  garmentType: string
  description: string
  colors: string[]
  searchTags: string[]
  imageFilePath: string
  price: number
}

export const products: Product[] = catalogue

export function getProduct(productId: string): Product | undefined {
  return products.find((p) => p.productId === productId)
}

// image_file_path in the database is relative (e.g. "products/x.jpg");
// the images live in public/products, so serve them from the site root.
export function imageUrl(product: Product): string {
  return `/${product.imageFilePath}`
}

export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`
}

export function toCard(product: Product): CardData {
  return {
    productId: product.productId,
    name: product.name,
    price: product.price,
    imageUrl: imageUrl(product),
    blurb: product.description,
  }
}
