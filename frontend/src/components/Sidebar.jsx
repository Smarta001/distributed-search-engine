import { useEffect, useState } from 'react'
import { popular } from '../api'
import './Sidebar.css'

function computeTopSources(results) {
  const counts = new Map()
  for (const r of results) {
    let domain
    try {
      domain = new URL(r.url).hostname.replace(/^www\./, '')
    } catch {
      continue
    }
    counts.set(domain, (counts.get(domain) || 0) + 1)
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([domain, count]) => ({ domain, count }))
}

export default function Sidebar({ results, onTrendingClick }) {
  const [trending, setTrending] = useState([])

  useEffect(() => {
    popular(5)
      .then((res) => setTrending(res.popular_queries || []))
      .catch(() => setTrending([]))
  }, [])

  const sources = computeTopSources(results || [])

  return (
    <aside className="sidebar">
      {sources.length > 0 && (
        <section className="sidebar__panel">
          <h4 className="sidebar__heading">Top sources for this search</h4>
          <ul className="sidebar__list">
            {sources.map((s) => (
              <li key={s.domain} className="sidebar__source-row">
                <span className="sidebar__favicon" aria-hidden="true">
                  {s.domain.charAt(0).toUpperCase()}
                </span>
                <span className="sidebar__domain">{s.domain}</span>
                <span className="sidebar__count">{s.count}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {trending.length > 0 && (
        <section className="sidebar__panel">
          <h4 className="sidebar__heading">
            Trending <span className="sidebar__badge">7d</span>
          </h4>
          <ul className="sidebar__list">
            {trending.map((t) => (
              <li key={t.query}>
                <button className="sidebar__trending-item" onClick={() => onTrendingClick(t.query)}>
                  {t.query}
                  <span className="sidebar__count">{t.search_count}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  )
}
