import { useSyncExternalStore } from 'react'
import { ENGINE, SCENARIO, listSamples, runJob, runSample, type SampleMeta } from './engine'

export type StageStatus = 'pending' | 'running' | 'done' | 'failed' | 'override'
export type ProofState = 'idle' | 'running' | 'pass' | 'fail'

export interface AppState {
  mode: 'autopilot' | 'expert'
  theme: 'ink' | 'paper'
  cmap: 'valve' | 'mono'
  view3d: boolean
  paletteOpen: boolean
  fontsReady: boolean
  stages: StageStatus[] // 8 stages, index 0 = OBSERVE
  loopBack: boolean // a failed proof routed 7 -> 3
  proof: ProofState
  proofT: number // 0..1 progress of the PROVE dissolve
  modOverride: string | null // expert-mode override of modulation
  cancelled: string[] // scene: emitters removed by successive cancellation
  taught: boolean // NOVEL emitter taught as a class
  sel: { f0: number; f1: number } | null // linked frequency selection, Hz
  fcHz: number | null // analyst-entered centre frequency
  floor: number // waterfall display range, dB
  span: number
  engine: 'demo' | 'connected' // demo = no engine reachable; the flow runs on the demo capture
  job: 'idle' | 'running' | 'done' | 'undecided' | 'error'
  jobNote: string | null // the engine's reason when it is undecided or failed
  dataVersion: number // bumps when engine results replace the demo data; pages remount on it
  samples: SampleMeta[] // the built-in demo library (engine/samples), fetched once an engine is reachable
}

const READY: StageStatus[] = ['done', 'done', 'done', 'done', 'done', 'done', 'pending', 'pending']

let state: AppState = {
  mode: 'autopilot',
  theme: 'ink',
  cmap: 'valve',
  view3d: false,
  paletteOpen: false,
  fontsReady: false,
  stages: READY,
  loopBack: false,
  proof: 'idle',
  proofT: 0,
  modOverride: null,
  cancelled: [],
  taught: false,
  sel: null,
  fcHz: null,
  floor: -104,
  span: 44,
  engine: 'demo',
  job: 'idle',
  jobNote: null,
  dataVersion: 0,
  samples: [],
}

const listeners = new Set<() => void>()

export const getState = () => state
export function setState(p: Partial<AppState> | ((s: AppState) => Partial<AppState>)) {
  state = { ...state, ...(typeof p === 'function' ? p(state) : p) }
  // set before listeners fire, so canvases redrawing on this change read the new theme's tokens
  document.documentElement.dataset.theme = state.theme
  listeners.forEach((l) => l())
}
const subscribe = (l: () => void) => {
  listeners.add(l)
  return () => listeners.delete(l)
}

/** Select a primitive or a stable reference; never build new objects in the selector. */
export function useApp<T>(sel: (s: AppState) => T): T {
  return useSyncExternalStore(subscribe, () => sel(state))
}

// ---------- Pipeline actions (front-end simulation until the engine is wired) ----------

let timers: number[] = []
const later = (ms: number, fn: () => void) => timers.push(window.setTimeout(fn, ms))
const clear = () => { timers.forEach(clearTimeout); timers = [] }

const setStage = (i: number, s: StageStatus) =>
  setState((st) => ({ stages: st.stages.map((v, j) => (j === i ? s : v)) }))

// the recording the analyst dropped, run by the engine when one is connected
type JobOpts = { fs?: number | null; dtype?: string | null; fc?: number | null; sigmf?: string | null }
let pending: { file: File; opts: JobOpts } | null = null
export function setPending(file: File | null, opts: JobOpts = {}) {
  pending = file ? { file, opts } : null
  ENGINE.job = null
}
export const getPending = () => pending

async function settle(run: () => Promise<Awaited<ReturnType<typeof runJob>>>) {
  clear()
  setState({ stages: Array(8).fill('pending'), proof: 'idle', proofT: 0, loopBack: false, cancelled: [], job: 'running', jobNote: null })
  try {
    const st = await run()
    if (st.state === 'done' || st.state === 'undecided')
      setState((s) => ({ job: st.state as 'done' | 'undecided', jobNote: st.error, dataVersion: s.dataVersion + 1,
        floor: SCENARIO.view.floor ?? s.floor, span: SCENARIO.view.span ?? s.span, modOverride: null }))
    else setState({ job: 'error', jobNote: st.error })
  } catch (e) {
    setState({ job: 'error', jobNote: String(e) })
  }
}

async function runEngine(p: NonNullable<typeof pending>) {
  await settle(() => runJob(p.file, p.opts, (s) => setState({ stages: s.stages.map((x) => x) as StageStatus[] })))
}

export function runAutopilot() {
  if (ENGINE.connected && pending) return void runEngine(pending)
  clear()
  setState({ stages: Array(8).fill('pending'), proof: 'idle', proofT: 0, loopBack: false, cancelled: [] })
  const step = 520
  for (let i = 0; i < 6; i++) {
    later(i * step, () => setStage(i, 'running'))
    later((i + 1) * step - 60, () => setStage(i, 'done'))
  }
}

/** Run one of the built-in demo recordings (from Ingest's "Recent recordings" list). */
export function runSampleJob(sample: SampleMeta) {
  setPending(null)
  void settle(() => runSample(sample, (s) => setState({ stages: s.stages.map((x) => x) as StageStatus[] })))
}

export async function loadSampleLibrary() {
  const samples = await listSamples()
  if (samples.length) setState({ samples })
}

/** PROVE: re-synthesise, subtract, test residual whiteness. */
export function prove() {
  if (state.job === 'running' || state.job === 'undecided' || state.job === 'error' ||
      (SCENARIO.view.source !== 'demo' && (state.job !== 'done' || SCENARIO.view.verdict !== 'pass'))) return
  clear()
  const wrong = (state.modOverride !== null && state.modOverride !== SCENARIO.params.modulation.value) || SCENARIO.view.verdict === 'fail'
  setStage(6, 'running')
  setState({ proof: 'running', proofT: 0, loopBack: false })
  const dur = matchMedia('(prefers-reduced-motion: reduce)').matches ? 1 : 1400
  const t0 = performance.now()
  skipFlag = false
  const tick = () => {
    const t = skipFlag ? 1 : Math.min(1, (performance.now() - t0) / dur)
    setState({ proofT: t })
    if (t < 1) return void requestAnimationFrame(tick)
    if (wrong) {
      setStage(6, 'failed')
      setState({ proof: 'fail', loopBack: true })
      setStage(2, 'running')
      later(900, () => setStage(2, 'override'))
    } else {
      setStage(6, 'done')
      setState({ proof: 'pass' })
      later(260, () => setStage(7, 'done'))
    }
  }
  requestAnimationFrame(tick)
}

let skipFlag = false
export function skipProof() {
  skipFlag = true
}

// ---------- The five user-facing steps, derived from the eight engine stages ----------

export type StepStatus = 'pending' | 'running' | 'done' | 'fail'
export const STEPS = [
  { path: '/ingest', n: 'Recording' },
  { path: '/signal', n: 'Signal' },
  { path: '/decoding', n: 'Decoding' },
  { path: '/frames', n: 'Header & payload' },
  { path: '/proof', n: 'Proof' },
]
const group = (st: StageStatus[]): StepStatus =>
  st.some((x) => x === 'running') ? 'running' : st.every((x) => x === 'done' || x === 'override') ? 'done' : 'pending'

/** Returns a comma-joined string so it can be selected without creating objects. */
export function stepStatus(s: AppState) {
  const out: StepStatus[] = [
    'done',
    s.loopBack ? 'fail' : group(s.stages.slice(0, 4)),
    group(s.stages.slice(4, 5)),
    group(s.stages.slice(5, 6)),
    s.proof === 'pass' ? 'done' : s.proof === 'fail' ? 'fail' : s.proof === 'running' ? 'running' : 'pending',
  ]
  return out.join(',')
}
