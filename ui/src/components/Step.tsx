import { useEffect, useRef, useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { go, useRoute } from '../lib/router'
import { STEPS, setState, stepStatus, useApp } from '../lib/store'
import { Knob, Seg } from './ui'

/** One step of the flow: what is happening, the evidence, and the way forward. */
export function Step(props: {
  n: number
  title: string
  lede: ReactNode
  actions?: ReactNode
  children: ReactNode
  back?: { to: string; label: string }
  next?: { to?: string; label: string; disabled?: boolean; onClick?: () => void }
  extra?: ReactNode
}) {
  return (
    <div className="step">
      <header className="step-head">
        <div className="step-intro">
          <span className="step-k">Step {props.n} of {STEPS.length}</span>
          <h1>{props.title}</h1>
          <p className="lede">{props.lede}</p>
        </div>
        {props.actions && <div className="step-actions">{props.actions}</div>}
      </header>
      <div className="step-body">{props.children}</div>
      <footer className="step-foot">
        {props.back ? (
          <button className="btn ghost" onClick={() => go(props.back!.to)}>← {props.back.label}</button>
        ) : <span />}
        <div className="step-extra">{props.extra}</div>
        {props.next && (
          <button className="btn primary lg" disabled={props.next.disabled} onClick={props.next.onClick ?? (() => go(props.next!.to!))}>
            {props.next.label} →
          </button>
        )}
      </footer>
    </div>
  )
}

export function Stepper() {
  const route = useRoute()
  const status = useApp(stepStatus).split(',')
  const current = route === '/certificate' ? '/proof' : route
  return (
    <ol className="stepper" aria-label="Analysis steps">
      {STEPS.map((s, i) => (
        <li key={s.path} className={'st ' + status[i]}>
          {i > 0 && <span className={'st-line' + (status[i - 1] === 'done' ? ' on' : '')} aria-hidden />}
          <a href={'#' + s.path} aria-current={current === s.path ? 'step' : undefined}>
            <span className="st-dot" aria-hidden>
              {status[i] === 'done' ? (
                <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 5.2 L4.2 7.4 L8 2.8" fill="none" stroke="currentColor" strokeWidth="1.6" /></svg>
              ) : status[i] === 'fail' ? '!' : i + 1}
            </span>
            <span className="st-n">{s.n}</span>
          </a>
        </li>
      ))}
    </ol>
  )
}

export const TOOLS = [
  { path: '/scene', n: 'Scene', d: 'All emitters in the band, hidden-signal reveal' },
  { path: '/genome', n: 'Standards', d: 'Match against 31 named standards' },
  { path: '/challenge', n: 'Challenge', d: 'Full-screen blind demo for judges' },
  { path: '/compliance', n: 'Compliance', d: 'Every problem-statement clause, mapped' },
]

/** Small anchored popover that closes on outside click or Escape. */
function Popover({ label, children, wide }: { label: ReactNode; children: ReactNode; wide?: boolean }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const off = (e: Event) => {
      if (e instanceof KeyboardEvent ? e.key === 'Escape' : !ref.current?.contains(e.target as Node)) setOpen(false)
    }
    addEventListener('pointerdown', off)
    addEventListener('keydown', off)
    return () => { removeEventListener('pointerdown', off); removeEventListener('keydown', off) }
  }, [open])
  return (
    <div className="pop" ref={ref}>
      <button className={'btn ghost' + (open ? ' on' : '')} aria-expanded={open} onClick={() => setOpen(!open)}>{label}</button>
      <AnimatePresence>
        {open && (
          <motion.div className={'pop-menu' + (wide ? ' wide' : '')} initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.12 }} onClick={(e) => (e.target as HTMLElement).closest('a') && setOpen(false)}>
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export function ToolsMenu() {
  const route = useRoute()
  return (
    <Popover label={<>Tools <span className="dimmer">▾</span></>} wide>
      {TOOLS.map((t) => (
        <a key={t.path} href={'#' + t.path} className="pop-item" aria-current={route === t.path ? 'page' : undefined}>
          <span>{t.n}</span>
          <span className="small dim">{t.d}</span>
        </a>
      ))}
    </Popover>
  )
}

export function DisplayMenu() {
  const floor = useApp((s) => s.floor)
  const span = useApp((s) => s.span)
  const cmap = useApp((s) => s.cmap)
  return (
    <Popover label="Display">
      <div className="row" style={{ gap: 20, justifyContent: 'center', padding: '6px 0 10px' }}>
        <Knob label="Floor" value={floor} min={-120} max={-80} step={1} fmt={(v) => v + ' dB'} onChange={(v) => setState({ floor: v })} />
        <Knob label="Span" value={span} min={10} max={70} step={1} fmt={(v) => v + ' dB'} onChange={(v) => setState({ span: v })} />
      </div>
      <div className="row between">
        <span className="small dim">Colour map</span>
        <Seg value={cmap} onChange={(v) => setState({ cmap: v })} options={[{ v: 'valve', label: 'Valve' }, { v: 'mono', label: 'Mono' }]} label="Colour map" />
      </div>
      <p className="small dimmer" style={{ marginTop: 10 }}>FFT 1024 · Hann · 50 % overlap · RBW 46.9 Hz</p>
    </Popover>
  )
}
