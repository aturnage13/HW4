import { useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { SorryDan } from '../components/HandsomeDan'
import { CANT_FIND_SAYINGS, randomSaying } from '../data/danSayings'

export default function NotFound() {
  const { pathname } = useLocation()
  const saying = useMemo(() => randomSaying(CANT_FIND_SAYINGS), [pathname])

  return (
    <section className="section empty-state">
      <SorryDan message={saying} />
      <Link to="/products" className="btn btn-primary">
        Keep Shopping
      </Link>
    </section>
  )
}
