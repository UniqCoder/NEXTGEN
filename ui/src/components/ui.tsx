import { useId, useRef, useState, type ReactNode } from 'react'
import { motion } from 'motion/react'
import type { Method } from '../lib/engine'
import type { StageStatus } from '../lib/store'

export function Panel(props: {
  title: ReactNode
  alt?: string
  tools?: ReactNode
  children: ReactNode
  pad?: boolean
  style?: React.CSSProperties
  className?: string
}) {
  return (
    <section className={'panel ' + (props.className ?? '')} style={props.style}>
      <header className="panel-h">
        <span className="ph">
          <span className="ph-t">{props.title}</span>
          {props.alt && <span className="ph-s">{props.alt}</span>}
        </span>
        {props.tools && <div className="tools">{props.tools}</div>}
      </header>
      <div className={'panel-b' + (props.pad ? ' pad' : '')}>{props.children}</div>
    </section>
  )
}

export function Seg<T extends string>(props: {
  value: T
  options: { v: T; label: string }[]
  onChange: (v: T) => void
  signal?: boolean
  label?: string
}) {
  const id = useId()
  return (
    <div className={'seg' + (props.signal ? ' signal' : '')} role="group" aria-label={props.label}>
      {props.options.map((o) => (
        <button key={o.v} aria-pressed={o.v === props.value} onClick={() => props.onChange(o.v)}>
          {o.v === props.value && (
            <motion.span layoutId={id} className="thumb" transition={{ duration: 0.16, ease: [0.2, 0, 0, 1] }} />
          )}
          {o.label}
        </button>
      ))}
    </div>
  )
}

/** Rotary knob with detents: drag vertically, wheel for fine steps, arrow keys when focused. */
export function Knob(props: {
  label: string
  value: number
  min: number
  max: number
  step: number
  fmt?: (v: number) => string
  onChange: (v: number) => void
}) {
  const { value, min, max, step, onChange } = props
  const drag = useRef<{ y: number; v: number } | null>(null)
  const set = (v: number) => onChange(Math.min(max, Math.max(min, Math.round(v / step) * step)))
  const t = (value - min) / (max - min)
  const a0 = -135, a1 = 135, a = a0 + t * (a1 - a0)
  const R = 13
  const pt = (deg: number, r: number) => {
    const rad = ((deg - 90) * Math.PI) / 180
    return [18 + r * Math.cos(rad), 18 + r * Math.sin(rad)]
  }
  const detents = Array.from({ length: 11 }, (_, i) => a0 + (i * (a1 - a0)) / 10)
  const arc = (from: number, to: number) => {
    const [x0, y0] = pt(from, R), [x1, y1] = pt(to, R)
    return `M${x0},${y0} A${R},${R} 0 ${to - from > 180 ? 1 : 0} 1 ${x1},${y1}`
  }
  const [px, py] = pt(a, 8)
  return (
    <div
      className="knob"
      tabIndex={0}
      role="slider"
      aria-label={props.label}
      aria-valuemin={min}
      aria-valuemax={max}
      aria-valuenow={value}
      onPointerDown={(e) => {
        ;(e.target as Element).setPointerCapture(e.pointerId)
        drag.current = { y: e.clientY, v: value }
      }}
      onPointerMove={(e) => {
        if (!drag.current) return
        const fine = e.shiftKey ? 0.2 : 1
        set(drag.current.v + ((drag.current.y - e.clientY) / 120) * (max - min) * fine)
      }}
      onPointerUp={() => (drag.current = null)}
      onWheel={(e) => set(value + (e.deltaY < 0 ? step : -step))}
      onKeyDown={(e) => {
        if (e.key === 'ArrowUp' || e.key === 'ArrowRight') set(value + step)
        if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') set(value - step)
      }}
    >
      <svg width="36" height="36" viewBox="0 0 36 36">
        {detents.map((d, i) => {
          const [x0, y0] = pt(d, 16.5), [x1, y1] = pt(d, 18)
          return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} stroke="var(--bone-4)" strokeWidth="1" />
        })}
        <path d={arc(a0, a1)} fill="none" stroke="var(--line-2)" strokeWidth="1.5" />
        <path d={arc(a0, Math.max(a0 + 0.01, a))} fill="none" stroke="var(--signal)" strokeWidth="1.5" />
        <circle cx="18" cy="18" r="9.5" fill="var(--ink-3)" stroke="var(--line-3)" />
        <line x1="18" y1="18" x2={px} y2={py} stroke="var(--bone-1)" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <span className="knob-v">{props.fmt ? props.fmt(value) : value}</span>
      <span className="kl">{props.label}</span>
    </div>
  )
}

/** Numeric field you scrub by dragging sideways. Double-click to type. */
export function Scrub(props: {
  k: string
  value: number
  min: number
  max: number
  step?: number
  fmt?: (v: number) => string
  onChange: (v: number) => void
  onRelease?: (v: number) => void
}) {
  const { value, min, max, step = 1, onChange } = props
  const [active, setActive] = useState(false)
  const [editing, setEditing] = useState(false)
  const drag = useRef<{ x: number; v: number } | null>(null)
  const set = (v: number) => {
    const nv = Math.min(max, Math.max(min, Math.round(v / step) * step))
    onChange(nv)
    return nv
  }
  return (
    <div
      className={'scrub' + (active ? ' active' : '')}
      tabIndex={0}
      role="spinbutton"
      aria-label={props.k}
      aria-valuenow={value}
      onPointerDown={(e) => {
        if (editing) return
        ;(e.currentTarget as Element).setPointerCapture(e.pointerId)
        drag.current = { x: e.clientX, v: value }
        setActive(true)
      }}
      onPointerMove={(e) => {
        if (!drag.current) return
        set(drag.current.v + ((e.clientX - drag.current.x) / 4) * step * (e.shiftKey ? 0.25 : 1))
      }}
      onPointerUp={() => {
        drag.current = null
        setActive(false)
        props.onRelease?.(value)
      }}
      onDoubleClick={() => setEditing(true)}
      onKeyDown={(e) => {
        if (e.key === 'ArrowRight' || e.key === 'ArrowUp') props.onRelease?.(set(value + step))
        if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') props.onRelease?.(set(value - step))
      }}
    >
      <span className="k">{props.k}</span>
      {editing ? (
        <input
          autoFocus
          className="v"
          style={{ background: 'transparent', border: 0, outline: 'none', width: 60 }}
          defaultValue={value}
          onBlur={(e) => {
            setEditing(false)
            props.onRelease?.(set(+e.target.value || value))
          }}
          onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
        />
      ) : (
        <span className="v">{props.fmt ? props.fmt(value) : value}</span>
      )}
    </div>
  )
}

const METHOD_LABEL: Record<Method, string> = { blind: 'Blind', library: 'Library', manual: 'Manual' }
export const MethodTag = ({ m }: { m: Method }) => (
  <span className={'meth ' + m} title={m === 'blind' ? 'Recovered from the signal alone' : m === 'library' ? 'Matched against a library of known standards' : 'Set by the analyst'}>
    {METHOD_LABEL[m]}
  </span>
)

/** The mark: a horizon and a point on it. Seeing far, precisely. */
export function Mark({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" aria-hidden>
      <circle cx="10" cy="10" r="8.5" fill="none" stroke="var(--bone-3)" strokeWidth="1" />
      <line x1="1.5" y1="10" x2="18.5" y2="10" stroke="var(--bone-1)" strokeWidth="1" />
      <circle cx="13.2" cy="10" r="2.1" fill="var(--signal)" />
    </svg>
  )
}

export function StageGlyph({ s }: { s: StageStatus }) {
  const common = { width: 12, height: 12, viewBox: '0 0 12 12', 'aria-hidden': true }
  if (s === 'done')
    return <svg {...common}><circle cx="6" cy="6" r="4" fill="var(--bone-1)" /></svg>
  if (s === 'running')
    return (
      <svg {...common} className="spin">
        <circle cx="6" cy="6" r="4.5" fill="none" stroke="var(--line-3)" strokeWidth="1.2" />
        <path d="M6 1.5 A4.5 4.5 0 0 1 10.5 6" fill="none" stroke="var(--signal)" strokeWidth="1.2" />
      </svg>
    )
  if (s === 'failed')
    return <svg {...common}><path d="M2.5 2.5 L9.5 9.5 M9.5 2.5 L2.5 9.5" stroke="var(--fault)" strokeWidth="1.4" /></svg>
  if (s === 'override')
    return <svg {...common}><rect x="3" y="3" width="6" height="6" transform="rotate(45 6 6)" fill="var(--caution)" /></svg>
  return <svg {...common}><circle cx="6" cy="6" r="4" fill="none" stroke="var(--bone-4)" strokeWidth="1" /></svg>
}

export function Conf({ p, width = 56 }: { p: number; width?: number }) {
  return (
    <span className="row" style={{ gap: 6 }} title={`Uncalibrated evidence score ${p.toFixed(2)}`}>
      <span style={{ width, height: 3, background: 'var(--line-2)', position: 'relative', display: 'inline-block' }}>
        <span style={{ position: 'absolute', inset: 0, width: `${p * 100}%`, background: 'var(--bone-2)' }} />
      </span>
      <span className="mono" style={{ fontSize: 'var(--t-10)', color: 'var(--bone-2)' }}>{p.toFixed(2)}</span>
    </span>
  )
}
