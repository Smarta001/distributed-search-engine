import ApertureMark from './ApertureMark'
import './Logo.css'

export default function Logo({ size = 'md', linkTo = '/' }) {
  return (
    <a href={linkTo} className={`logo logo--${size}`} aria-label="Flick home">
      <ApertureMark size={size === 'lg' ? 44 : 26} />
      <span className="logo__word">Flick</span>
    </a>
  )
}
