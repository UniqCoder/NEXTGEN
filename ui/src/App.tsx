import { useEffect } from 'react'
import { AnimatePresence } from 'motion/react'
import { Mark, Seg } from './components/ui'
import { Palette } from './components/Palette'
import { Stepper, ToolsMenu } from './components/Step'
import { SCENARIO, ping } from './lib/engine'
import { go, useRoute } from './lib/router'
import { STEPS, getState, prove, runAutopilot, setState, skipProof, useApp } from './lib/store'
import { Ingest } from './pages/Ingest'
import { Signal } from './pages/Signal'
import { Decoding } from './pages/Decoding'
import { Frames } from './pages/Frames'
import { Proof } from './pages/Proof'
import { Certificate } from './pages/Certificate'
import { Scene } from './pages/Scene'
import { Genome } from './pages/Genome'
import { Challenge } from './pages/Challenge'
import { Compliance } from './pages/Compliance'

const ROUTES: Record<string, () => React.ReactNode> = {
  '/ingest': Ingest,
  '/signal': Signal,
  '/decoding': Decoding,
  '/frames': Frames,
  '/proof': Proof,
  '/certificate': Certificate,
  '/scene': Scene,
  '/genome': Genome,
  '/challenge': Challenge,
  '/compliance': Compliance,
}

const typing = (e: KeyboardEvent) => {
  const t = e.target as HTMLElement
  return t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA' || t.isContentEditable
}

export default function App() {
  const route = useRoute()
  const mode = useApp((s) => s.mode)
  const paletteOpen = useApp((s) => s.paletteOpen)
  const engine = useApp((s) => s.engine)
  const job = useApp((s) => s.job)
  const jobNote = useApp((s) => s.jobNote)
  const dataVersion = useApp((s) => s.dataVersion)
  const Page = ROUTES[route] ?? Ingest

  useEffect(() => {
    document.fonts.ready.then(() => setState({ fontsReady: true }))
    ping().then((ok) => ok && setState({ engine: 'connected' }))
  }, [])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setState((s) => ({ paletteOpen: !s.paletteOpen }))
        return
      }
      if (e.key === 'Escape') { skipProof(); return }
      if (typing(e) || getState().paletteOpen || e.ctrlKey || e.metaKey) return
      if (e.altKey && /^[1-5]$/.test(e.key)) { e.preventDefault(); go(STEPS[+e.key - 1].path); return }
      if (e.altKey) return
      const k = e.key.toLowerCase()
      if (k === 'p') { go('/proof'); prove() }
      else if (k === 't') setState((s) => ({ view3d: !s.view3d }))
      else if (k === 'a') { go('/signal'); runAutopilot() }
      else if (k === 'e') setState((s) => ({ mode: s.mode === 'expert' ? 'autopilot' : 'expert' }))
      else if (k === '\\') setState((s) => ({ theme: s.theme === 'paper' ? 'ink' : 'paper' }))
    }
    addEventListener('keydown', onKey)
    return () => removeEventListener('keydown', onKey)
  }, [])

  if (route === '/challenge') return <Challenge />

  return (
    <div className="shell">
      <header className="titlebar">
        <a className="wordmark" href="#/ingest" aria-label="SANJAYA home">
          <Mark />
          SANJAYA
        </a>
        <Stepper />
        <div className="spacer" />
        <div className="tb-right">
          <ToolsMenu />
          <Seg label="Analysis mode" value={mode} onChange={(v) => setState({ mode: v })}
            options={[{ v: 'autopilot', label: 'Autopilot' }, { v: 'expert', label: 'Expert' }]} />
          <button className="btn ghost sm" onClick={() => setState({ paletteOpen: true })} aria-label="Open command palette">
            <span className="kbd">Ctrl K</span>
          </button>
        </div>
      </header>

      <main className="page" key={route + ':' + dataVersion}>
        <Page />
      </main>

      <footer className="statusbar">
        {engine === 'demo'
          ? <span><i className="led amber" /> Engine not connected · demo data</span>
          : <span><i className={'led ' + (job === 'error' || job === 'undecided' ? 'amber' : 'green')} /> Engine connected · {
              job === 'running' ? 'analysing…' : job === 'undecided' ? 'undecided: ' + jobNote : job === 'error' ? 'error: ' + jobNote
              : SCENARIO.view.source === 'demo' ? 'demo data' : 'results from this recording'}</span>}
        <span>Offline</span>
        <span>{SCENARIO.file.name} · {SCENARIO.text.format}</span>
        <span className="grow" />
        <span>Ctrl K for every command</span>
      </footer>

      <AnimatePresence>{paletteOpen && <Palette />}</AnimatePresence>
    </div>
  )
}
