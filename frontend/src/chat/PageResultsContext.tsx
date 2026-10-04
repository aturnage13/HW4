import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { PageResults } from '../api/chat'

// Holds the latest chat search so the Products page can show it. Kept in
// sessionStorage too, so Back/refresh from a product page still shows it.
const STORAGE_KEY = 'cc-chat-page-results'

interface PageResultsState {
  results: PageResults | null
  setResults: (results: PageResults | null) => void
}

const PageResultsContext = createContext<PageResultsState | null>(null)

function load(): PageResults | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as PageResults) : null
  } catch {
    return null
  }
}

export function PageResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResultsState] = useState<PageResults | null>(load)

  function setResults(next: PageResults | null) {
    setResultsState(next)
    try {
      if (next) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      else sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      // Storage can be unavailable (private mode); in-memory state still works.
    }
  }

  return (
    <PageResultsContext.Provider value={{ results, setResults }}>
      {children}
    </PageResultsContext.Provider>
  )
}

export function usePageResults(): PageResultsState {
  const ctx = useContext(PageResultsContext)
  if (!ctx) throw new Error('usePageResults must be used inside PageResultsProvider')
  return ctx
}
