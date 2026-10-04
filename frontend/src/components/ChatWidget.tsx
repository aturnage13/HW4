import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { fetchHistory, sendChat } from '../api/chat'
import type { ChatProductCard, ChatTurn, PageContext } from '../api/chat'
import { useAuth } from '../auth/AuthContext'
import { usePageResults } from '../chat/PageResultsContext'
import { formatPrice, getProduct } from '../data/products'
import { DanAvatar, SorryDan } from './HandsomeDan'

interface Message extends ChatTurn {
  products?: ChatProductCard[]
  suggestions?: string[]
  sorry?: boolean
  error?: boolean
}

// Conversation starters before the first message.
const STARTERS = ['What hoodies do you have?', 'Show me red t-shirts', 'What do you sell?']
const PRODUCT_STARTERS = ['How much is this?', 'Is this in stock in medium?', 'What colors does it come in?']

const HISTORY_TURNS = 12

// Older saved replies (seed data) contain markdown bold; the bubbles are plain text.
const plain = (text: string) => text.replace(/\*\*(.+?)\*\*/g, '$1')

export default function ChatWidget() {
  const { user, loading } = useAuth()
  const { results, setResults } = usePageResults()
  const navigate = useNavigate()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [sending, setSending] = useState(false)
  const [hasSavedHistory, setHasSavedHistory] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Logged in: show the customer's saved chat. Logged out/guest: start fresh.
  const userId = user?.id
  useEffect(() => {
    if (loading) return
    setHasSavedHistory(false)
    if (userId === undefined) {
      setMessages([])
      return
    }
    let cancelled = false
    fetchHistory()
      .then((saved) => {
        if (cancelled) return
        setMessages(saved.map(({ role, content, products }) => ({ role, content, products })))
        setHasSavedHistory(saved.length > 0)
      })
      .catch(() => !cancelled && setMessages([]))
    return () => {
      cancelled = true
    }
  }, [userId, loading])

  // What's on screen right now, so "this" means the product being viewed.
  const productMatch = location.pathname.match(/^\/products\/([^/]+)$/)
  const viewedProduct = productMatch ? getProduct(decodeURIComponent(productMatch[1])) : undefined
  const showingChatResults =
    location.pathname === '/products' && new URLSearchParams(location.search).get('view') === 'chat' && results
  const pageContext: PageContext = {
    path: location.pathname + location.search,
    productId: viewedProduct?.productId ?? null,
    resultsHeading: showingChatResults ? results.heading : null,
    shownProductIds: showingChatResults ? results.products.map((p) => p.productId) : [],
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending, open])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    send(draft)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || sending) return

    // Guests: recent turns give the agent context for follow-ups. Logged-in
    // customers' history is loaded from the database by the server instead.
    const history: ChatTurn[] = user
      ? []
      : messages
          .filter((m) => !m.error)
          .slice(-HISTORY_TURNS)
          .map(({ role, content }) => ({ role, content }))

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setDraft('')
    setSending(true)
    try {
      const { reply, products, page, suggestions, sorry } = await sendChat(text, history, pageContext)
      setMessages((prev) => [...prev, { role: 'assistant', content: reply, products, suggestions, sorry }])
      // A browsing search ("what hoodies do you have?") fills the Products page.
      if (page) {
        setResults(page)
        navigate('/products?view=chat')
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: err instanceof Error ? err.message : 'Something went wrong.',
          error: true,
        },
      ])
    } finally {
      setSending(false)
    }
  }

  const greeting = user
    ? hasSavedHistory
      ? `Welcome back, ${user.firstName}! Here's where we left off. What can I help you find today?`
      : `Ruff, hi ${user.firstName}! I'm Handsome Dan, your Campus Customs sidekick. Hunting for a hoodie, a tee, or something for game day?`
    : "Ruff, hi there! I'm Handsome Dan, your Campus Customs sidekick. Ask me about hoodies, crewnecks, tees, sizes, or what's in stock!"

  return (
    <div className="chat-widget">
      {open && (
        <section className="chat-panel" aria-label="Campus Customs chat">
          <header className="chat-header">
            <DanAvatar size={42} />
            <div>
              <strong>Handsome Dan · Campus Customs</strong>
              <span>
                {viewedProduct
                  ? `Viewing: ${viewedProduct.name}`
                  : user
                    ? 'Your chats are saved to your account'
                    : 'Guest chat · log in to save your history'}
              </span>
            </div>
            <button aria-label="Close chat" onClick={() => setOpen(false)}>
              ×
            </button>
          </header>
          <div className="chat-messages" aria-live="polite">
            <div className="chat-bubble bot">{greeting}</div>
            {messages.length === 0 && (
              <Suggestions items={viewedProduct ? PRODUCT_STARTERS : STARTERS} onPick={send} disabled={sending} />
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-row ${m.role}`}>
                {m.sorry ? (
                  <SorryDan message={plain(m.content)} compact />
                ) : (
                  <div className={`chat-bubble ${m.role === 'user' ? 'user' : 'bot'}${m.error ? ' error' : ''}`}>
                    {plain(m.content)}
                  </div>
                )}
                {m.products && m.products.length > 0 && (
                  <div className="chat-cards">
                    {m.products.map((p) => (
                      <Link key={p.productId} to={p.url} className="chat-card">
                        <img src={p.imageUrl} alt="" />
                        <div>
                          <strong>{p.name}</strong>
                          <span>{formatPrice(p.price)}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
                {/* Only the latest reply offers next steps. */}
                {i === messages.length - 1 && m.suggestions && m.suggestions.length > 0 && (
                  <Suggestions items={m.suggestions} onPick={send} disabled={sending} />
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-bubble bot typing" aria-label="Assistant is typing">
                <span />
                <span />
                <span />
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Type a message…"
              value={draft}
              maxLength={1000}
              onChange={(e) => setDraft(e.target.value)}
              aria-label="Chat message"
            />
            <button type="submit" disabled={sending || !draft.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        className="chat-launcher"
        aria-label={open ? 'Close chat' : 'Open chat'}
        onClick={() => setOpen((o) => !o)}
      >
        {open ? '×' : <DanAvatar size={60} />}
      </button>
    </div>
  )
}

function Suggestions({ items, onPick, disabled }: { items: string[]; onPick: (text: string) => void; disabled: boolean }) {
  return (
    <div className="chat-suggestions">
      {items.map((s) => (
        <button key={s} type="button" className="chat-suggestion" onClick={() => onPick(s)} disabled={disabled}>
          {s}
        </button>
      ))}
    </div>
  )
}
