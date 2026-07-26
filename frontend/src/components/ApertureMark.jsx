/**
 * The aperture/iris mark — six overlapping blades forming a hexagonal
 * opening. Used static as the logo, and animated (blades rotating closed
 * then open) as the loading state — a literal "flick" of the shutter.
 */
export default function ApertureMark({ size = 32, animated = false, color = 'var(--color-accent)' }) {
  const blades = Array.from({ length: 6 })

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={animated ? 'aperture-mark aperture-mark--animated' : 'aperture-mark'}
      role="img"
      aria-label={animated ? 'Loading' : 'Flick'}
    >
      <circle cx="24" cy="24" r="22" stroke={color} strokeOpacity="0.18" strokeWidth="2" />
      <g style={{ transformOrigin: '24px 24px' }}>
        {blades.map((_, i) => (
          <path
            key={i}
            d="M24 24 L24 8 A16 16 0 0 1 37.86 16 Z"
            fill={color}
            fillOpacity={animated ? 0.85 : 0.9}
            style={{
              transformOrigin: '24px 24px',
              transform: `rotate(${i * 60}deg)`,
              '--r': `${i * 60}deg`,
            }}
            className="aperture-blade"
          />
        ))}
      </g>
      <circle cx="24" cy="24" r="7" fill="var(--bg-page)" />
    </svg>
  )
}
