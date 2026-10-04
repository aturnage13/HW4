// Mirrors ChatRequest / ChatResponse / ProductCard in backend/models.py.
export interface ChatProductCard {
  productId: string
  name: string
  category: string
  price: number
  colors: string[]
  shortDescription: string
  imageUrl: string
  url: string
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

// Chat search results for the main page (PageResults in backend/models.py).
export interface PageResults {
  heading: string
  totalMatches: number
  products: ChatProductCard[]
  note: string
}

export interface ChatResponse {
  reply: string
  products: ChatProductCard[]
  page: PageResults | null
  suggestions: string[] // tappable follow-up questions
  sorry: boolean // show the "sorry" Handsome Dan
}

export interface SizeStock {
  size: string
  quantity: number
  status: 'in_stock' | 'low_stock' | 'out_of_stock'
}

// What the customer is looking at, so "do you have this in red?" means the shown product.
export interface PageContext {
  path: string
  productId: string | null
  resultsHeading: string | null
  shownProductIds: string[]
}

export interface HistoryMessage extends ChatTurn {
  products: ChatProductCard[]
  createdAt: string
}

export async function fetchHistory(): Promise<HistoryMessage[]> {
  const res = await fetch('/api/chat/history', { credentials: 'same-origin' })
  if (!res.ok) throw new Error('History unavailable')
  const data = (await res.json()) as { messages: HistoryMessage[] }
  return data.messages
}

export async function sendChat(
  message: string,
  history: ChatTurn[],
  page: PageContext,
): Promise<ChatResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, page }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(
      typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.',
    )
  }
  return data as ChatResponse
}

export async function fetchStock(productId: string): Promise<SizeStock[]> {
  const res = await fetch(`/api/products/${encodeURIComponent(productId)}/stock`)
  if (!res.ok) throw new Error('Stock unavailable')
  return res.json()
}
