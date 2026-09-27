/*
 * Engine adapter (PRD §10): the same exports as mock.ts. Until a job finishes, everything is the demo scenario;
 * when it does, the engine's results are written into the same objects in place, so no component changes
 * how it reads data. Browser mode: `sanjaya serve` hosts this UI and passes the per-launch token as ?token=.
 */
import * as M from './mock'
export * from './mock'

const TOKEN = new URLSearchParams(location.search).get('token')
const BASE: string = (import.meta as unknown as { env: Record<string, string | undefined> }).env.VITE_ENGINE ?? ''

export const ENGINE = { available: TOKEN !== null, connected: false, version: '', job: null as string | null }

export interface JobStatus {
  id: string; state: 'queued' | 'running' | 'done' | 'undecided' | 'error'
  stages: ('pending' | 'running' | 'done' | 'failed')[]; error: string | null; verdict: 'pass' | 'fail' | null
  log: { stage: string; finding: string; method: M.Method }[]
}

export interface SampleMeta {
  id: string; name: string; kind: 'synthetic' | 'real'; what: string; source: string; duration_s?: number
}

/** The built-in demo library (engine/samples), fetched once a job-capable engine is reachable. */
export async function listSamples(): Promise<SampleMeta[]> {
  if (!ENGINE.available) return []
  try {
    return await (await api('/v1/samples')).json()
  } catch {
    return []
  }
}

async function api(path: string, init?: RequestInit) {
  const r = await fetch(BASE + path, { ...init, headers: { ...(init?.headers ?? {}), 'X-Sanjaya-Token': TOKEN ?? '' } })
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r
}

export async function ping() {
  if (!ENGINE.available) return false
  try {
    const h = await (await api('/v1/health')).json()
    ENGINE.connected = true
    ENGINE.version = h.engine_version
  } catch {
    ENGINE.connected = false
  }
  return ENGINE.connected
}

// ---- engine-backed data (null = demo) ----
let spec: M.Spectrogram | null = null
let bits: { stream: Uint8Array; offset: number; frames: number } | null = null
let crc: ReturnType<typeof M.crcSearch> | null = null
let prof: { p: number; v: number }[] | null = null
let cons: Float32Array | null = null

export function spectrogram(): M.Spectrogram { return spec ?? M.spectrogram() }
export function bitstream() { return bits ?? M.bitstream() }
export function findSync(b: Uint8Array) { return bits ? 0 : M.findSync(b) }
export function crcSearch(b: Uint8Array, phase: number) { return crc ?? M.crcSearch(b, phase) }
export function rankProfile() { return prof ?? M.rankProfile() }
/** Measured symbols (I, Q interleaved, unit average energy) for the constellation; null = demo phosphor. */
export function constellation() { return cons }

function replace<T>(arr: T[], items: T[]) { arr.splice(0, arr.length, ...items) }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Any = any
/** No recipe survived the search: undecided jobs carry only a reduced scenario (spectrogram + whatever
 * measured on its own — see sanjaya/api/scenario.py build_partial). Clear the decode-only state to empty,
 * not the demo mock, so pages show "nothing decoded" rather than fabricated demo frames as if real. */
function apply(r: Any, s: M.Spectrogram) {
  const S = M.SCENARIO as Any
  Object.assign(S.file, r.scenario.file)
  replace(S.forensics, r.scenario.forensics)
  for (const k of Object.keys(S.params)) delete S.params[k]
  Object.assign(S.params, r.scenario.params)
  replace(S.emitters, r.scenario.emitters)
  for (const k of Object.keys(S.proof)) delete S.proof[k]
  Object.assign(S.proof, r.scenario.proof)
  for (const k of Object.keys(S.cert)) delete S.cert[k]
  Object.assign(S.cert, r.scenario.cert)
  Object.assign(S.view, r.scenario.view)
  for (const k of Object.keys(S.text)) delete S.text[k]
  Object.assign(S.text, r.scenario.text)
  cons = r.scenario.constellation ? Float32Array.from(r.scenario.constellation as number[]) : new Float32Array(0)
  Object.assign(M.SPEC, r.spec)
  const F = M.FRAME as Any
  F.len = r.frame?.len ?? 0
  F.sync = r.frame?.sync ?? 0
  replace(F.fields, r.frame?.fields ?? [])
  const stream = r.bits ? Uint8Array.from(r.bits as string, (c: string) => (c === '1' ? 1 : 0)) : new Uint8Array(0)
  bits = { stream, offset: 0, frames: F.len ? Math.floor(stream.length / F.len) : 0 }
  crc = r.crc ?? []
  prof = r.rankProfile ?? []
  replace(M.CONV_CANDIDATES as Any[], r.conv ?? [])
  replace(M.FEC_FAMILIES as Any[], r.fecFamilies ?? [])
  replace(M.INTERLEAVER_TYPES as Any[], r.interleaverTypes ?? [])
  spec = s
}

function rowPowerFrom(full: Float32Array, rows: number, bins: number): Float32Array {
  const out = new Float32Array(rows)
  for (let row = 0; row < rows; row++) {
    let p = 0
    for (let b = 0; b < bins; b++) p += 10 ** (full[row * bins + b] / 10)
    out[row] = 10 * Math.log10(p + 1e-20)
  }
  return out
}

async function load(id: string) {
  const r = await (await api(`/v1/jobs/${id}/scenario`)).json()
  const get = async (k: string) => new Float32Array(await (await api(`/v1/jobs/${id}/spectrogram/${k}`)).arrayBuffer())
  const full = await get('full')
  // an undecided job's partial result carries only "full" (no recipe to resynthesise a residual or a
  // rejected near-miss from); fall back to it so the waterfall still shows the real recording, not nothing.
  const [resid, fail] = await Promise.all(['resid', 'fail'].map((k) => get(k).catch(() => full)))
  const rowPower = await get('rowPower').catch(() => rowPowerFrom(full, r.spec.rows, r.spec.bins))
  apply(r, { full, resid, fail, rowPower })
}

async function poll(id: string, onStatus: (s: JobStatus) => void): Promise<JobStatus> {
  for (;;) {
    const st: JobStatus = await (await api(`/v1/jobs/${id}`)).json()
    onStatus(st)
    if (st.state !== 'queued' && st.state !== 'running') {
      if (st.state === 'done' || st.state === 'undecided') await load(id)
      return st
    }
    await new Promise((res) => setTimeout(res, 250))
  }
}

/** Upload (browser mode) and run the blind search; onStatus fires on every poll. Resolves with the final status. */
export async function runJob(file: File, opts: { fs?: number | null; dtype?: string | null; fc?: number | null; sigmf?: string | null },
                             onStatus: (s: JobStatus) => void): Promise<JobStatus> {
  const q = new URLSearchParams({ name: file.name })
  if (opts.fs) q.set('fs', String(opts.fs))
  if (opts.dtype) q.set('dtype', opts.dtype)
  if (opts.fc) q.set('fc_hz', String(opts.fc))
  if (opts.sigmf) q.set('sigmf', opts.sigmf)                       // the engine reads the sidecar itself
  const { id } = await (await api('/v1/jobs?' + q, { method: 'POST', body: file })).json()
  ENGINE.job = id
  return poll(id, onStatus)
}

/** Run one of the built-in demo recordings (engine/samples), no upload needed. */
export async function runSample(sample: SampleMeta, onStatus: (s: JobStatus) => void): Promise<JobStatus> {
  const q = new URLSearchParams({ name: sample.name, sample: sample.id })
  const { id } = await (await api('/v1/jobs?' + q, { method: 'POST' })).json()
  ENGINE.job = id
  return poll(id, onStatus)
}

/** UI dtype names + endianness -> engine SigMF datatype names. */
export function engineDtype(dtype: string, endian: 'LE' | 'BE') {
  const le = endian === 'LE' ? '_le' : '_be'
  return { cf32: 'cf32' + le, ci16: 'ci16' + le, ci8: 'ci8', cu8: 'cu8' }[dtype] ?? dtype
}
