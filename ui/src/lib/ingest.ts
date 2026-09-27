// Front-end file forensics: real WAV/SigMF header parsing, heuristic raw-IQ dtype sniff.
// The engine does the authoritative version; this gives the analyst an immediate first read.

import { triage, type Triage } from './triage'

export interface Finding { k: string; v: string; conf: number | null; note?: string }
export interface Ingested {
  name: string
  size: number
  route: 'wav' | 'iq'
  findings: Finding[]
  guess: { dtype: string; endian: 'LE' | 'BE'; order: 'IQ' | 'QI'; fs: number | null; fc: number | null; interp: 'real' | 'iq' }
  content: Triage | null
}

export async function ingest(files: File[]): Promise<Ingested | null> {
  const meta = files.find((f) => f.name.endsWith('.sigmf-meta'))
  const data = files.find((f) => f !== meta)
  if (!data) return null
  const sig = meta ? parseSigmf(await meta.text()) : null
  const head = new DataView(await data.slice(0, 1 << 20).arrayBuffer())
  const isWav = head.byteLength > 12 && str(head, 0, 4) === 'RIFF' && str(head, 8, 4) === 'WAVE'
  return isWav ? wav(data, head) : raw(data, head, sig)
}

const str = (v: DataView, o: number, n: number) => String.fromCharCode(...Array.from({ length: n }, (_, i) => v.getUint8(o + i)))

function wav(f: File, v: DataView): Ingested {
  let o = 12, fmt: { code: number; ch: number; fs: number; bits: number } | null = null, dataBytes = 0, dataAt = 0
  while (o + 8 <= v.byteLength) {
    const id = str(v, o, 4), sz = v.getUint32(o + 4, true)
    if (id === 'fmt ') fmt = { code: v.getUint16(o + 8, true), ch: v.getUint16(o + 10, true), fs: v.getUint32(o + 12, true), bits: v.getUint16(o + 22, true) }
    if (id === 'data') { dataBytes = sz; dataAt = o + 8; break }
    o += 8 + sz + (sz & 1)
  }
  if (!fmt) return { name: f.name, size: f.size, route: 'wav', findings: [{ k: 'Container', v: 'RIFF/WAVE, but no fmt chunk', conf: 1 }], guess: { dtype: '?', endian: 'LE', order: 'IQ', fs: null, fc: null, interp: 'real' }, content: null }
  const code = fmt.code === 0xfffe ? 'extensible' : fmt.code === 3 ? 'IEEE float' : fmt.code === 1 ? 'PCM integer' : `format ${fmt.code}`
  const iq = fmt.ch === 2
  const frames = dataBytes / (fmt.ch * (fmt.bits / 8))
  return {
    name: f.name,
    size: f.size,
    route: 'wav',
    findings: [
      { k: 'Container', v: 'RIFF / WAVE · header read', conf: 1 },
      { k: 'Sample rate', v: fmt.fs.toLocaleString('en-IN') + ' Hz', conf: 1, note: 'from header' },
      { k: 'Sample format', v: `${fmt.bits}-bit ${code}`, conf: 1, note: 'from header' },
      { k: 'Channels', v: String(fmt.ch), conf: 1 },
      { k: 'Interpretation', v: iq ? '2 channels → complex I/Q' : 'real audio (e.g. after a receiver)', conf: iq ? 0.9 : 0.95, note: iq ? 'stereo WAV from an SDR is usually I/Q' : 'single channel cannot carry I/Q' },
      { k: 'Duration', v: isFinite(frames) && fmt.fs ? (frames / fmt.fs).toFixed(2) + ' s' : '—', conf: null },
    ],
    guess: { dtype: `${fmt.bits}-bit`, endian: 'LE', order: 'IQ', fs: fmt.fs, fc: null, interp: iq ? 'iq' : 'real' },
    content: wavTriage(v, dataAt, fmt),
  }
}

function parseSigmf(text: string) {
  try {
    const j = JSON.parse(text)
    return { dtype: j.global?.['core:datatype'] as string | undefined, fs: j.global?.['core:sample_rate'] as number | undefined, fc: j.captures?.[0]?.['core:frequency'] as number | undefined }
  } catch {
    return null
  }
}

/** Score dtype hypotheses: implausible values rule a type out; among the rest, smoother = more likely. */
function raw(f: File, v: DataView, sig: ReturnType<typeof parseSigmf>): Ingested {
  const n = v.byteLength
  const hyps: { name: string; dtype: string; endian: 'LE' | 'BE'; ok: boolean; rough: number; why: string }[] = []
  const rough = (get: (i: number) => number, count: number) => {
    let d = 0, a = 0
    for (let i = 0; i + 2 < count; i++) { const x = get(i); d += Math.abs(get(i + 2) - x); a += Math.abs(x) }
    return a ? d / a : Infinity
  }
  for (const le of [true, false]) {
    const c = Math.floor(n / 2)
    let clip = 0
    for (let i = 0; i < c; i++) if (Math.abs(v.getInt16(i * 2, le)) >= 32767) clip++
    hyps.push({ name: `complex int16 ${le ? 'LE' : 'BE'}`, dtype: 'ci16', endian: le ? 'LE' : 'BE', ok: clip / c < 0.01, rough: rough((i) => v.getInt16(i * 2, le), c), why: `${((clip / c) * 100).toFixed(2)} % clipped` })
  }
  for (const le of [true, false]) {
    const c = Math.floor(n / 4)
    let bad = 0
    for (let i = 0; i < c; i++) { const x = v.getFloat32(i * 4, le); if (!isFinite(x) || Math.abs(x) > 1e4 || (x !== 0 && Math.abs(x) < 1e-30)) bad++ }
    hyps.push({ name: `complex float32 ${le ? 'LE' : 'BE'}`, dtype: 'cf32', endian: le ? 'LE' : 'BE', ok: bad / c < 0.001, rough: rough((i) => v.getFloat32(i * 4, le), c), why: `${((bad / c) * 100).toFixed(1)} % NaN / huge / denormal` })
  }
  hyps.push({ name: 'complex uint8 (offset 127)', dtype: 'cu8', endian: 'LE', ok: true, rough: rough((i) => v.getUint8(i) - 127.5, n), why: 'RTL-SDR style' })
  hyps.push({ name: 'complex int8', dtype: 'ci8', endian: 'LE', ok: true, rough: rough((i) => v.getInt8(i), n), why: 'HackRF style' })
  const ranked = hyps.filter((h) => h.ok).sort((a, b) => a.rough - b.rough)
  const w = ranked.map((h) => Math.exp(-h.rough * 3))
  const sum = w.reduce((a, b) => a + b, 0) || 1
  const best = ranked[0]
  const findings: Finding[] = [
    { k: 'Container', v: 'None (headerless raw IQ)', conf: 1, note: 'No RIFF or SigMF signature' },
    ...(sig ? [{ k: 'SigMF sidecar', v: `found · ${sig.dtype ?? 'no datatype'}`, conf: 1 } as Finding] : [{ k: 'SigMF sidecar', v: 'not provided', conf: null } as Finding]),
    ...ranked.slice(0, 3).map((h, i) => ({ k: i === 0 ? 'Sample type' : 'Alternative', v: h.name, conf: w[i] / sum, note: h.why })),
    { k: 'Ruled out', v: hyps.filter((h) => !h.ok).map((h) => h.name).join(', ') || 'none', conf: null },
    { k: 'Sample rate', v: sig?.fs ? sig.fs.toLocaleString('en-IN') + ' Hz (SigMF)' : 'unknown · will be back-solved', conf: sig?.fs ? 1 : null },
  ]
  return {
    name: f.name,
    size: f.size,
    route: 'iq',
    findings,
    // SigMF names ("cf32_le") -> the override form's names ("cf32" + endianness)
    guess: { dtype: sig?.dtype ? sig.dtype.replace(/_(le|be)$/, '') : best?.dtype ?? 'ci16',
      endian: sig?.dtype ? (sig.dtype.endsWith('_be') ? 'BE' : 'LE') : best?.endian ?? 'LE', order: 'IQ', fs: sig?.fs ?? null, fc: sig?.fc ?? null, interp: 'iq' },
    content: best ? iqTriage(v, best.dtype, best.endian === 'LE') : null,
  }
}

/** Decode the first samples of a PCM / float WAV (up to the 1 MiB already read) and triage them. */
function wavTriage(v: DataView, at: number, fmt: { code: number; ch: number; bits: number }) {
  const bytes = fmt.bits / 8, step = bytes * fmt.ch
  const n = Math.floor((v.byteLength - at) / step)
  if (at <= 0 || n <= 0 || ![8, 16, 32].includes(fmt.bits)) return null
  const float = fmt.code === 3 || (fmt.code === 0xfffe && fmt.bits === 32)
  const read = (o: number) => fmt.bits === 8 ? v.getUint8(o) - 128 : fmt.bits === 16 ? v.getInt16(o, true) : float ? v.getFloat32(o, true) : v.getInt32(o, true)
  const i = new Float32Array(n), q = fmt.ch === 2 ? new Float32Array(n) : null
  for (let k = 0; k < n; k++) { i[k] = read(at + k * step); if (q) q[k] = read(at + k * step + bytes) }
  return triage(i, q)
}

function iqTriage(v: DataView, dtype: string, le: boolean) {
  const size = dtype === 'cf32' ? 4 : dtype === 'ci16' ? 2 : 1
  const n = Math.floor(v.byteLength / (2 * size))
  const read = (o: number) => dtype === 'cf32' ? v.getFloat32(o, le) : dtype === 'ci16' ? v.getInt16(o, le) : dtype === 'cu8' ? v.getUint8(o) - 127.5 : v.getInt8(o)
  const i = new Float32Array(n), q = new Float32Array(n)
  for (let k = 0; k < n; k++) { i[k] = read(k * 2 * size); q[k] = read(k * 2 * size + size) }
  return triage(i, q)
}
