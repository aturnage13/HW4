import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useLocation } from 'react-router-dom'

// Dev-only site-testing tool: asks Claude to screenshot the page for
// output/app_check.html (see backend/app_check.py). Hidden in production builds.
const CHECKS = ['Inventory level', 'Search-result cards', 'Problem 9 usability feature', 'Other'] as const

type Status = { id: number; state: 'waiting' | 'captured' | 'error'; text: string }

export default function SnapButton() {
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [check, setCheck] = useState<(typeof CHECKS)[number]>(CHECKS[0])
  const [note, setNote] = useState('')
  const [status, setStatus] = useState<Status | null>(null)

  // Poll until Claude has saved the screenshot, so you know when to move on.
  useEffect(() => {
    if (!status || status.state !== 'waiting') return
    const started = Date.now()
    const timer = window.setInterval(async () => {
      try {
        const res = await fetch(`/api/dev/snap/${status.id}`)
        const data = await res.json()
        if (data.captured) {
          setStatus({ id: status.id, state: 'captured', text: `✓ Snap #${status.id} saved` })
        } else if (Date.now() - started > 120_000) {
          setStatus({ id: status.id, state: 'error', text: `Snap #${status.id} is taking a while, so check the Claude chat.` })
        }
      } catch {
        // Keep polling; the API may be reloading.
      }
    }, 2000)
    return () => window.clearInterval(timer)
  }, [status])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setOpen(false)
    try {
      const res = await fetch('/api/dev/snap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ check, note, path: location.pathname + location.search }),
      })
      if (!res.ok) throw new Error()
      const { id } = await res.json()
      setStatus({ id, state: 'waiting', text: `📸 Snap #${id} requested. Hold still while Claude captures it…` })
      setNote('')
    } catch {
      setStatus({ id: 0, state: 'error', text: 'Could not request a snap. Is the API running?' })
    }
  }

  return (
    <div className="snap-tool">
      {status && (
        <div className={`snap-toast ${status.state}`} onClick={() => status.state !== 'waiting' && setStatus(null)}>
          {status.text}
        </div>
      )}
      {open && (
        <form className="snap-form" onSubmit={submit}>
          <strong>Request a screenshot</strong>
          <label>
            Check
            <select value={check} onChange={(e) => setCheck(e.target.value as (typeof CHECKS)[number])}>
              {CHECKS.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Note for Claude (optional)
            <input value={note} maxLength={300} onChange={(e) => setNote(e.target.value)} placeholder="What should this show?" />
          </label>
          <div className="snap-actions">
            <button type="button" onClick={() => setOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="primary">
              Snap it
            </button>
          </div>
        </form>
      )}
      <button className="snap-button" onClick={() => setOpen((o) => !o)} aria-label="Request a screenshot for the app check">
        📸 Snap
      </button>
    </div>
  )
}
