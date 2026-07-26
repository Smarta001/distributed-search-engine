import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { suggest } from '../api'
import ApertureMark from './ApertureMark'
import './SearchBar.css'

const SearchBar = forwardRef(function SearchBar(
  { initialValue = '', onSubmit, autoFocus = false, size = 'md' },
  ref
) {
  const [value, setValue] = useState(initialValue)
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const debounceRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    setValue(initialValue)
  }, [initialValue])

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleChange(e) {
    const next = e.target.value
    setValue(next)
    setActiveIndex(-1)

    clearTimeout(debounceRef.current)
    if (next.trim().length < 2) {
      setSuggestions([])
      return
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await suggest(next.trim())
        setSuggestions(res.suggestions || [])
        setShowSuggestions(true)
      } catch {
        setSuggestions([])
      }
    }, 220)
  }

  function submit(query) {
    const q = (query ?? value).trim()
    if (!q) return
    setShowSuggestions(false)
    onSubmit(q)
  }

  useImperativeHandle(ref, () => ({
    submit: () => submit(),
  }))

  function handleKeyDown(e) {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') submit()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, -1))
    } else if (e.key === 'Enter') {
      submit(activeIndex >= 0 ? suggestions[activeIndex] : undefined)
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
    }
  }

  return (
    <div className={`search-bar search-bar--${size}`} ref={containerRef}>
      <form
        className="search-bar__form"
        role="search"
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
      >
        <ApertureMark size={size === 'lg' ? 20 : 18} />
        <input
          type="text"
          className="search-bar__input"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder="Search Flick"
          aria-label="Search"
          aria-autocomplete="list"
          aria-expanded={showSuggestions}
          autoFocus={autoFocus}
          autoComplete="off"
        />
        {value && (
          <button
            type="button"
            className="search-bar__clear"
            aria-label="Clear search"
            onClick={() => {
              setValue('')
              setSuggestions([])
            }}
          >
            ×
          </button>
        )}
      </form>

      {showSuggestions && suggestions.length > 0 && (
        <ul className="search-bar__suggestions" role="listbox">
          {suggestions.map((s, i) => (
            <li
              key={s}
              role="option"
              aria-selected={i === activeIndex}
              className={`search-bar__suggestion ${i === activeIndex ? 'search-bar__suggestion--active' : ''}`}
              onMouseDown={() => submit(s)}
              onMouseEnter={() => setActiveIndex(i)}
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
})

export default SearchBar
