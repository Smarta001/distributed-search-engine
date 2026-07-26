import './ResultCard.css'

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function faviconLetter(domain) {
  return domain.charAt(0).toUpperCase()
}

export default function ResultCard({ result }) {
  const domain = extractDomain(result.url)

  return (
    <article className="result-card">
      <div className="result-card__breadcrumb">
        <span className="result-card__favicon" aria-hidden="true">
          {faviconLetter(domain)}
        </span>
        <span className="result-card__domain">{domain}</span>
      </div>
      <h3 className="result-card__title">
        <a href={result.url} target="_blank" rel="noopener noreferrer">
          {result.title}
        </a>
      </h3>
      <p className="result-card__snippet">{result.snippet}</p>
    </article>
  )
}
