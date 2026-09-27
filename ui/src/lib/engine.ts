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
function apply(r: Any, s: M.Spectrogram) {
  const S = M.SCENARIO as Any
  Object.assign(S.file, r.scenario.file)
  replace(S.forensics, r.scenario.forensics)
  for (const k of Object.keys(S.params)) delete S.params[k]
  Object.assign(S.params, r.scenario.params)
  replace(S.emitters, r.scenario.emitters)
  Object.assign(S.proof, r.scenario.proof)
  Object.assign(S.cert, r.scenario.cert)
  Object.assign(S.view, r.scenario.view)
  Object.assign(S.text, r.scenario.text)
  cons = Float32Array.from((r.scenario.constellation ?? []) as number[])
  Object.assign(M.SPEC, r.spec)
  const F = M.FRAME as Any
  F.len = r.frame.len
  F.sync = r.frame.sync
  replace(F.fields, r.frame.fields)
  const stream = Uint8Array.from(r.bits as string, (c) => (c === '1' ? 1 : 0))
  bits = { stream, offset: 0, frames: Math.floor(stream.length / r.frame.len) }
  crc = r.crc
  prof = r.rankProfile
  replace(M.CONV_CANDIDATES as Any[], r.conv)
  replace(M.FEC_FAMILIES as Any[], r.fecFamilies)
  replace(M.INTERLEAVER_TYPES as Any[], r.interleaverTypes)
  spec = s
}

async function load(id: string) {
  const r = await (await api(`/v1/jobs/${id}/scenario`)).json()
  const get = async (k: string) => new Float32Array(await (await api(`/v1/jobs/${id}/spectrogram/${k}`)).arrayBuffer())
  const [full, resid, fail, rowPower] = await Promise.all(['full', 'resid', 'fail', 'rowPower'].map(get))
  apply(r, { full, resid, fail, rowPower })
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
  for (;;) {
    const st: JobStatus = await (await api(`/v1/jobs/${id}`)).json()
    onStatus(st)
    if (st.state !== 'queued' && st.state !== 'running') {
      if (st.state === 'done') await load(id)
      return st
    }
    await new Promise((res) => setTimeout(res, 250))
  }
}

/** UI dtype names + endianness -> engine SigMF datatype names. */
export function engineDtype(dtype: string, endian: 'LE' | 'BE') {
  const le = endian === 'LE' ? '_le' : '_be'
  return { cf32: 'cf32' + le, ci16: 'ci16' + le, ci8: 'ci8', cu8: 'cu8' }[dtype] ?? dtype
}
