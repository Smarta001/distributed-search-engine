import ApertureMark from './ApertureMark'
import './LoadingState.css'

export default function LoadingState({ label = 'Searching…' }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <ApertureMark size={40} animated />
      <p>{label}</p>
    </div>
  )
}
