import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Logo from '../components/Logo'
import SearchBar from '../components/SearchBar'
import ThemeToggle from '../components/ThemeToggle'
import './HomePage.css'

const CURIOUS_QUERIES = ['aurora borealis', 'bm25 ranking', 'distributed systems', 'elasticsearch']

export default function HomePage() {
  const navigate = useNavigate()
  const searchBarRef = useRef(null)

  function goToSearch(query) {
    navigate(`/search?q=${encodeURIComponent(query)}`)
  }

  function feelingCurious() {
    const pick = CURIOUS_QUERIES[Math.floor(Math.random() * CURIOUS_QUERIES.length)]
    goToSearch(pick)
  }

  return (
    <div className="home-page">
      <div className="home-page__topbar">
        <ThemeToggle />
      </div>

      <main className="home-page__center">
        <Logo size="lg" />
        <div className="home-page__search">
          <SearchBar ref={searchBarRef} onSubmit={goToSearch} autoFocus size="lg" />
        </div>
        <div className="home-page__actions">
          <button className="home-page__button" onClick={() => searchBarRef.current?.submit()}>
            Flick Search
          </button>
          <button className="home-page__button home-page__button--ghost" onClick={feelingCurious}>
            I'm Feeling Curious
          </button>
        </div>
      </main>
    </div>
  )
}
