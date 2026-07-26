import './NavTabs.css'

const TABS = [
  { id: 'web', label: 'Web', enabled: true },
  { id: 'images', label: 'Images', enabled: false },
  { id: 'videos', label: 'Videos', enabled: false },
  { id: 'news', label: 'News', enabled: false },
  { id: 'maps', label: 'Maps', enabled: false },
  { id: 'more', label: 'More', enabled: false },
]

export default function NavTabs({ onDisabledTabClick }) {
  return (
    <nav className="nav-tabs" aria-label="Search categories">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          className={`nav-tabs__tab ${tab.enabled ? 'nav-tabs__tab--active' : ''}`}
          onClick={tab.enabled ? undefined : () => onDisabledTabClick(tab.label)}
          aria-current={tab.enabled ? 'page' : undefined}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
