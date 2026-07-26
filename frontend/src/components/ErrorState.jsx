import './LoadingState.css'

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="error-state">
      <span style={{ fontSize: '2rem' }} aria-hidden="true">
        ⚠
      </span>
      <p className="error-state__title">Search is unavailable right now</p>
      <p>{message || 'The search backend could not be reached.'}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            marginTop: '0.5rem',
            border: '1px solid var(--border-strong)',
            background: 'var(--bg-raised)',
            color: 'var(--text-primary)',
            padding: '0.5rem 1.1rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.875rem',
          }}
        >
          Try again
        </button>
      )}
    </div>
  )
}
