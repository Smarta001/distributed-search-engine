import './LoadingState.css'

export default function EmptyState({ query }) {
  return (
    <div className="empty-state">
      <span style={{ fontSize: '2rem' }} aria-hidden="true">
        ○
      </span>
      <p className="empty-state__title">No results for "{query}"</p>
      <p>Try different keywords, or check for typos.</p>
    </div>
  )
}
