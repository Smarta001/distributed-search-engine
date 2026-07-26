import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { search, ApiError } from '../api'
import Logo from '../components/Logo'
import SearchBar from '../components/SearchBar'
import NavTabs from '../components/NavTabs'
import ThemeToggle from '../components/ThemeToggle'
import Toast from '../components/Toast'
import ResultCard from '../components/ResultCard'
import Pagination from '../components/Pagination'
import Sidebar from '../components/Sidebar'
import LoadingState from '../components/LoadingState'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import './ResultsPage.css'

const PAGE_SIZE = 10

export default function ResultsPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const query = searchParams.get('q') || ''
  const page = parseInt(searchParams.get('page') || '1', 10)

  const [data, setData] = useState(null)
  const [status, setStatus] = useState('loading') // loading | success | empty | error
  const [errorMessage, setErrorMessage] = useState('')
  const [toastMessage, setToastMessage] = useState('')

  const runSearch = useCallback(() => {
    if (!query) return
    setStatus('loading')
    search(query, { page, size: PAGE_SIZE })
      .then((res) => {
        setData(res)
        setStatus(res.results.length === 0 ? 'empty' : 'success')
      })
      .catch((err) => {
        setErrorMessage(err instanceof ApiError ? err.message : 'Something went wrong.')
        setStatus('error')
      })
  }, [query, page])

  useEffect(() => {
    runSearch()
  }, [runSearch])

  function goToQuery(newQuery) {
    navigate(`/search?q=${encodeURIComponent(newQuery)}`)
  }

  function goToPage(newPage) {
    navigate(`/search?q=${encodeURIComponent(query)}&page=${newPage}`)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total_hits / PAGE_SIZE)) : 1

  return (
    <div className="results-page">
      <header className="results-page__header">
        <div className="results-page__header-row">
          <Logo />
          <div className="results-page__header-search">
            <SearchBar initialValue={query} onSubmit={goToQuery} />
          </div>
          <ThemeToggle />
        </div>
        <NavTabs onDisabledTabClick={(label) => setToastMessage(`${label} search is coming soon`)} />
      </header>

      <div className="results-page__body">
        <main className="results-page__main container-main">
          {status === 'loading' && <LoadingState />}
          {status === 'error' && <ErrorState message={errorMessage} onRetry={runSearch} />}
          {status === 'empty' && <EmptyState query={query} />}
          {status === 'success' && data && (
            <>
              <p className="results-page__meta">
                About {data.total_hits.toLocaleString()} results ({data.took_ms}ms
                {data.from_cache ? ', cached' : ''})
              </p>
              {data.results.map((result) => (
                <ResultCard key={result.url} result={result} />
              ))}
              <Pagination page={page} totalPages={totalPages} onPageChange={goToPage} />
            </>
          )}
        </main>

        <div className="container-sidebar">
          <Sidebar results={data?.results || []} onTrendingClick={goToQuery} />
        </div>
      </div>

      <Toast message={toastMessage} onDismiss={() => setToastMessage('')} />
    </div>
  )
}
