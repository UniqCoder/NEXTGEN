/*
 * Demo scenario for the front-end, until the Python engine is wired over localhost.
 * It mirrors the P0 plan file: synthetic QPSK + concatenated RS/conv code + block interleaver,
 * with a weak RTTY signal hidden under it, an LFM chirp nobody has a class for, and a CW carrier.
 * The spectrogram is synthesised; the bit-level analysis (autocorrelation, entropy, CRC check) is really computed.
 */

export function prng(seed: number) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
export function gauss(r: () => number) {
  return Math.sqrt(-2 * Math.log(r() + 1e-12)) * Math.cos(2 * Math.PI * r())
}

export type Method = 'blind' | 'library' | 'manual'

export interface Param {
  key: string
  label: string
  value: string
  unit?: string
  method: Method
  conf: number | null
  stage: number // stage index that produces it
  cands?: { v: string; p: number }[]
  set?: string
  evidence: string
}

const FS = 48000

export const SCENARIO = {
  file: {
    name: 'sanjaya-gen_0042.iq',
    path: 'D:/captures/bench/sanjaya-gen_0042.iq',
    size: 48_234_496,
    sha256: 'b41e9a0c7d53f2e18a6c04f9d1e7b2a35c9f08e6d4a1b7c2e90f3d58a6b1c4e7',
    format: 'Raw IQ',
    route: 'iq' as const,
    duration: 251.2,
  },
  forensics: [
    { k: 'Container', v: 'None (headerless)', conf: 1, method: 'blind' as Method, note: 'No RIFF / SigMF signature in first 4 KiB' },
    { k: 'Sample type', v: 'complex int16', conf: 0.97, method: 'blind' as Method, note: 'int16: kurtosis 3.01, 0 clipped · float32: 71 % NaN/denormal' },
    { k: 'Endianness', v: 'little', conf: 0.99, method: 'blind' as Method, note: 'Byte swapped reading gives flat spectrum' },
    { k: 'I/Q order', v: 'I first', conf: 0.93, method: 'blind' as Method, note: 'Q-first mirrors CW carrier to +17.5 kHz' },
    { k: 'DC offset', v: '−41.2 dBFS · removed', conf: null, method: 'blind' as Method, note: '' },
    { k: 'IQ imbalance', v: '0.21 dB / 0.8° · corrected', conf: null, method: 'blind' as Method, note: 'Image rejection 38 dB → 61 dB' },
    { k: 'SigMF sidecar', v: 'Not found', conf: null, method: 'blind' as Method, note: '' },
  ],
  params: {} as Record<string, Param>,
  emitters: [
    { id: 'E1', f0: 1880, f1: 5140, t0: 0.07, t1: 1, snr: 16.1, cls: 'QPSK · 2400 Bd', std: 'No named standard', state: 'decoded', label: 'E1 · QPSK signal', sub: '2400 Bd · 16 dB SNR · decoded', fc: 3512 },
    { id: 'E2', f0: -14200, f1: -8800, t0: 0, t1: 1, snr: 12.0, cls: 'NOVEL', std: 'closest: none', state: 'novel', label: 'E2 · short bursts', sub: 'unknown type', fc: -11500 },
    { id: 'E3', f0: -17620, f1: -17380, t0: 0, t1: 1, snr: 30.2, cls: 'CW · unmodulated', std: 'Carrier', state: 'measured', label: 'E3 · steady carrier', sub: 'CW · 30 dB', fc: -17500 },
    { id: 'E4', f0: 2640, f1: 3360, t0: 0.17, t1: 0.92, snr: 3.1, cls: '2-FSK · 50 Bd · 450 Hz', std: 'RTTY 50 Bd / 450 Hz', state: 'hidden', label: 'E4 · RTTY 50 / 450', sub: '', fc: 3000 },
  ] as { id: string; f0: number; f1: number; t0: number; t1: number; snr: number; cls: string; std: string; state: string; label: string; sub: string; fc: number }[],
  proof: { explained: 99.1, ljungP: 0.41, kurt: 3.02, residFloor: -100.1, failExplained: 38.7 },
  cert: { id: 'SNJ-2026-0926-0042', key: 'ed25519:7Q4f…m2Xk', sig: '9f2c1e…a07b3d', issued: '2026-09-26 14:12:07 IST' },
  // Scenario-bound display values (PRD §10.2): the demo's values here; the engine writes the job's values.
  view: {
    lo: -110, range: 60, floor: -104, span: 44, rowStart: 24, gridSeconds: 50, psdMin: -106, psdMax: -64, obwDb: -67,
    verdict: null as 'pass' | 'fail' | 'undecided' | null, source: 'demo',
    reason: null as string | null,
    measured: null as {
      band_lo_hz: number; band_hi_hz: number; centre_hz: number; snr_db: number; floor_db: number; rate_hz: number
      carrier_hz: number; family: 'PSK' | 'FSK'; modulation: string; order: number | null; tones_hz: number[]; spacing_hz: number | null
      standards: { name: string; ppm: number | null }[]
    } | null,
    layers: [] as { layer: string; verdict: string; reason: string | null }[], equivalences: [] as string[],
    compiler: null as {
      passed: boolean; frames: number; frames_equal?: number; bits_compared?: number; receiver_crc_ok?: number
      receiver_seconds?: number; error?: string; other_sensors?: { name: string; frames: number; crc_ok: number; error: string | null }[]
    } | null,
    stitch: null as {
      reference: string; pooled_frames: number; pooled_seconds: number
      sensors: { name: string; seconds: number; fs_hz: number; alone: { verdict: string; headline: string }; associated: boolean
        frames: number; proof?: string[]; crc_ok?: number; crc_frames?: number; clock_ppm?: number; cfo_hz?: number
        esn0_db?: number; gain_db?: number; inverted?: boolean; consistent?: boolean; excluded?: boolean }[]
    } | null,
    sufficiency: null as {
      verdict: 'sufficient' | 'more_data' | 'not_data_limited'; headline: string; have_s: number
      entries: { decision: string; status: string; evidence: string; limit: string | null; need_s: number[] | null; min_s?: number[]; blocking?: boolean }[]
    } | null,
  },
  text: {
    evm: 'EVM 6.1 % · MER 24.3 dB',
    certFormat: 'Raw IQ · complex int16 · little endian · I first (inferred)',
    fecLine: 'Concatenated code: RS outer, block interleaver, convolutional inner · 41 symbol errors corrected · 0 failures',
    scrText: '1 + x¹⁴ + x¹⁵ · seed 100101010000000', scrNote: 'Recovered blind with Berlekamp–Massey',
    phaseText: '90° rotation · Gray mapping', phaseNote: 'All 4 rotations decoded; only 90° satisfies the code',
    lfsr: { seed: '100101010000000', taps: [14, 15] },
    rankAxis: 'NORM. RANK', rankNote: 'rank deficiency 42 % · block',
    mod: 'QPSK', baud: '2400', baudSpaced: '2 400', at: '+3.5 kHz', snr: '14', others: 'Three weaker emitters share the band',
    obw: 'OBW 3.24 kHz · −26 dB', format: 'complex int16 · 48 kHz', heroCap: '48 kHz · 251 s', sigmfDtype: 'ci16_le',
    frameLine: '192 bit frames · sync 0xFAF320 · CRC-16/CCITT verified on 95 / 95 complete frames · payload high entropy (not decrypted).',
    codeKind: 'concatenated code', ilKind: 'block interleaver', decodeLine: '96 of 96 codewords decode', ilRows: 48, ilCols: 32,
    ilLabel: 'Block 48 × 32',
    chain: [
      { role: 'Input', n: 'Demodulated bits', v: 'soft bits · 4 phase rotations tried', m: 'blind' },
      { role: 'Error correction · inner', n: 'Viterbi', v: 'Conv. K=7 r½ (171,133)₈', m: 'blind' },
      { role: 'Deinterleaving', n: 'Block deinterleave', v: '48 × 32', m: 'blind' },
      { role: 'Error correction · outer', n: 'Reed–Solomon', v: 'RS(255,223) GF(2⁸)', m: 'library' },
      { role: 'Descrambling', n: 'Descramble', v: '1 + x¹⁴ + x¹⁵', m: 'blind' },
      { role: 'Output', n: 'Clean bit stream', v: '192 bit frames', m: 'blind' },
    ] as { n: string; v: string; m: Method; role: string }[],
    genomeE1: { label: 'E1 · QPSK 2400 Bd', name: 'No named standard', note: 'closest MIL-STD-188-110A · 0.22 (it uses 8PSK)' },
    genomeFs: { title: 'Sampling frequency · backsolved', value: '48 000', note: 'RTTY clock 49.99984 Bd ⇒ clock error −3.2 ppm' },
  },
}

const P = (p: Param) => (SCENARIO.params[p.key] = p)
P({ key: 'content', label: 'Signal type', value: 'Digital data', method: 'blind', conf: 0.96, stage: 0,
  evidence: 'Steady 3.2 kHz occupied band with a symbol rate line at 2 400 Hz; level varies about 4 % frame to frame (speech varies by more than 30 %). Not voice, not a lone carrier, not noise - so the decode chain runs.' })
P({ key: 'fs', label: 'Sampling frequency', value: '48 000', unit: 'Hz', method: 'blind', conf: 0.99, stage: 1,
  evidence: 'No header. Backsolved from the RTTY symbol clock (49.99984 Bd vs nominal 50) and the anti-alias roll-off at ±22.5 kHz. Clock error −3.2 ppm.' })
P({ key: 'baud', label: 'Symbol rate', value: '2 400.0', unit: 'Bd', method: 'blind', conf: 0.99, stage: 1,
  evidence: 'Cyclostationary line at 2 400.02 Hz in |x|² spectrum, 23 dB above floor. Oerder–Meyr timing converges in 380 symbols.' })
P({ key: 'modulation', label: 'Modulation', value: 'QPSK', method: 'blind', conf: 0.91, stage: 2,
  cands: [{ v: 'QPSK', p: 0.91 }, { v: '8PSK', p: 0.07 }, { v: 'OQPSK', p: 0.02 }], set: '{QPSK}',
  evidence: 'Fourth power line at 4·Δf, none at 8·Δf. Cumulants C40 = −0.98, C42 = −1.01 (QPSK theory −1, −1). Decode fit EVM 6.1 %.' })
P({ key: 'fec', label: 'FEC', value: 'RS(255,223) ∘ CC K=7 r½', method: 'blind', conf: 0.96, stage: 4,
  evidence: 'Inner: dual-code syndrome weight minimum at (171,133)₈, 0.02 vs 0.50 random. Outer: RS(255,223) GF(2⁸) matched from library, 96/96 codewords decode, 41 symbols corrected.' })
P({ key: 'interleaver', label: 'Interleaving', value: 'Block 48 × 32', method: 'blind', conf: 0.94, stage: 4,
  evidence: 'Rank profile of the Viterbi output dips at period 48 (normalised rank 0.58) and its multiple 96. Depth 32 from the second order rank profile.' })
P({ key: 'scrambler', label: 'Scrambler', value: '1 + x¹⁴ + x¹⁵', method: 'blind', conf: 0.9, stage: 4,
  evidence: 'Berlekamp–Massey on known zero padding: linear complexity 15. Seed 100101010000000. Additive (synchronous).' })
P({ key: 'snr', label: 'SNR', value: '14.2', unit: 'dB', method: 'blind', conf: null, stage: 1,
  evidence: 'M2M4 estimator on matched filter output; cross-checked with in band vs out of band PSD (14.6 dB).' })
P({ key: 'bw', label: 'Occupied bandwidth', value: '3.24', unit: 'kHz', method: 'blind', conf: null, stage: 1,
  evidence: '−26 dB points of the averaged PSD. Consistent with RRC roll-off α = 0.35 at 2 400 Bd.' })
P({ key: 'cfo', label: 'Carrier offset', value: '+3 512.4', unit: 'Hz', method: 'blind', conf: null, stage: 1,
  evidence: 'Fourth power spectral line at 14 049.6 Hz ÷ 4. Costas loop residual < 0.4 Hz.' })
P({ key: 'fc', label: 'Centre frequency', value: 'Unknown', method: 'manual', conf: null, stage: 0,
  evidence: 'Raw IQ without SigMF metadata carries no RF frequency. Enter it to see absolute frequencies and the band (HF / VHF / UHF).' })

// ---------------- Spectrogram ----------------

export const SPEC = { bins: 1024, rows: 360, fs: FS }
export const binFreq = (b: number) => -SPEC.fs / 2 + ((b + 0.5) * SPEC.fs) / SPEC.bins
export const freqBin = (f: number) => ((f + SPEC.fs / 2) / SPEC.fs) * SPEC.bins - 0.5

export interface Spectrogram {
  full: Float32Array // dB, as recorded
  resid: Float32Array // dB, E1 (QPSK) subtracted: what a PASS leaves
  fail: Float32Array // dB, residual of a wrong hypothesis
  rowPower: Float32Array // dB, per-row in-band power, for the timeline minimap
}

function rc(df: number, rs: number, a: number) {
  const x = Math.abs(df), f1 = ((1 - a) * rs) / 2, f2 = ((1 + a) * rs) / 2
  if (x <= f1) return 1
  if (x <= f2) return 0.5 * (1 + Math.cos((Math.PI * (x - f1)) / (f2 - f1)))
  return 0
}

let cached: Spectrogram | null = null
export function spectrogram(): Spectrogram {
  if (cached) return cached
  const { bins, rows } = SPEC
  const r = prng(42)
  const n = bins * rows
  const full = new Float32Array(n), resid = new Float32Array(n), fail = new Float32Array(n), rowPower = new Float32Array(rows)
  const fsk = prng(7)
  for (let y = 0; y < rows; y++) {
    const fade = 1 + 0.28 * Math.sin(y * 0.047) + 0.12 * Math.sin(y * 0.21 + 1.3)
    const crash = r() < 0.012 ? 2.2 : 1 // HF static crash
    const markFrac = 0.5 + 0.35 * (fsk() - 0.5)
    const fskOn = y > 60 && y < 330 && Math.sin(y * 0.09) > -0.7
    const burstPhase = (y - 10) % 45
    const burst = y >= 10 && burstPhase >= 0 && burstPhase < 5
    const cw = -17500 + 3 * Math.sin(y * 0.02)
    let rp = 0
    for (let b = 0; b < bins; b++) {
      const f = binFreq(b)
      const g = 1 / (1 + Math.pow(Math.abs(f) / 22500, 16))
      // Welch-averaged noise: mean of 4 exponentials
      const noise = (-Math.log(r()) - Math.log(r()) - Math.log(r()) - Math.log(r())) / 4
      let base = noise * g * crash
      base += 1000 * Math.exp(-((f - cw) ** 2) / (2 * 22 ** 2))
      if (burst) {
        const lo = -14000 + burstPhase * 1000
        if (f > lo && f < lo + 1000) base += 16 * (0.8 + 0.4 * r())
      }
      if (fskOn) {
        base += 2.4 * markFrac * Math.exp(-((f - 2775) ** 2) / (2 * 45 ** 2))
        base += 2.4 * (1 - markFrac) * Math.exp(-((f - 3225) ** 2) / (2 * 45 ** 2))
      }
      let e1 = 0
      if (y >= 24) e1 = 40 * fade * (rc(f - 3512.4, 2400, 0.35) + 1e-4) * (0.85 + 0.3 * r())
      const i = y * bins + b
      full[i] = 10 * Math.log10(base + e1) - 100
      resid[i] = 10 * Math.log10(base) - 100
      fail[i] = 10 * Math.log10(base + e1 * 0.38) - 100
      if (f > 1880 && f < 5140) rp += base + e1
    }
    rowPower[y] = 10 * Math.log10(rp) - 100
  }
  return (cached = { full, resid, fail, rowPower })
}

// ---------------- Bit stream: frames, autocorrelation, entropy, CRC ----------------

export const FRAME = {
  len: 192,
  sync: 0xfaf320,
  fields: [
    { name: 'SYNC', group: 'HEADER', start: 0, len: 24, kind: 'const', note: '0xFAF320 · constant 96/96' },
    { name: 'COUNTER', group: 'HEADER', start: 24, len: 16, kind: 'counter', note: '+1 per frame · from 0x0A31' },
    { name: 'LEN', group: 'HEADER', start: 40, len: 8, kind: 'const', note: '0x0F = 15 B = payload length ✓' },
    { name: 'TYPE', group: 'HEADER', start: 48, len: 8, kind: 'const', note: '0x5A · constant' },
    { name: 'PAYLOAD', group: 'PAYLOAD', start: 56, len: 120, kind: 'random', note: 'entropy 0.99 b/bit · likely encrypted' },
    { name: 'CRC-16', group: 'TRAILER', start: 176, len: 16, kind: 'crc', note: 'poly 0x1021 · init 0xFFFF' },
  ],
}

export function crc16(bits: ArrayLike<number>, start: number, len: number, poly: number, init: number) {
  let c = init
  for (let i = 0; i < len; i++) {
    const top = ((c >> 15) & 1) ^ bits[start + i]
    c = (c << 1) & 0xffff
    if (top) c ^= poly
  }
  return c
}

function putBits(out: number[], v: number, n: number) {
  for (let i = n - 1; i >= 0; i--) out.push((v >> i) & 1)
}

let bitsCache: { stream: Uint8Array; offset: number; frames: number } | null = null
export function bitstream() {
  if (bitsCache) return bitsCache
  const r = prng(1337)
  const frames = 96
  const all: number[] = []
  for (let k = 0; k < frames; k++) {
    const fr: number[] = []
    putBits(fr, FRAME.sync, 24)
    putBits(fr, 0x0a31 + k, 16)
    putBits(fr, 0x0f, 8)
    putBits(fr, 0x5a, 8)
    for (let i = 0; i < 120; i++) fr.push(r() < 0.5 ? 1 : 0)
    putBits(fr, crc16(fr, 0, 176, 0x1021, 0xffff), 16)
    all.push(...fr)
  }
  const offset = 57 // the recording starts mid-frame
  return (bitsCache = { stream: Uint8Array.from(all.slice(offset)), offset, frames })
}

/** Normalised autocorrelation of the ±1 bit stream. */
export function autocorr(bits: Uint8Array, maxLag: number) {
  const n = Math.min(bits.length, 8192)
  const out = new Float32Array(maxLag + 1)
  for (let lag = 1; lag <= maxLag; lag++) {
    let s = 0
    for (let i = 0; i + lag < n; i++) s += (bits[i] * 2 - 1) * (bits[i + lag] * 2 - 1)
    out[lag] = s / (n - lag)
  }
  return out
}

/** Per-column binary entropy of the raster at width w, phase offset `phase`. */
export function columnStats(bits: Uint8Array, w: number, phase: number) {
  const rows = Math.floor((bits.length - phase) / w)
  const ent = new Float32Array(w), ones = new Float32Array(w)
  for (let c = 0; c < w; c++) {
    let s = 0
    for (let y = 0; y < rows; y++) s += bits[phase + y * w + c]
    const p = s / rows
    ones[c] = p
    ent[c] = p <= 0 || p >= 1 ? 0 : -(p * Math.log2(p) + (1 - p) * Math.log2(1 - p))
  }
  return { ent, ones, rows }
}

/** Search a small library of CRC-16 polynomials and inits; count frames that verify. */
export function crcSearch(bits: Uint8Array, phase: number) {
  const polys = [
    { poly: 0x1021, name: 'CRC-16/CCITT' },
    { poly: 0x8005, name: 'CRC-16/IBM' },
    { poly: 0x3d65, name: 'CRC-16/DNP' },
    { poly: 0x0589, name: 'CRC-16/DECT' },
  ]
  const frames = Math.floor((bits.length - phase) / FRAME.len)
  const out: { name: string; poly: number; init: number; ok: number; frames: number }[] = []
  for (const p of polys)
    for (const init of [0x0000, 0xffff]) {
      let ok = 0
      for (let k = 0; k < frames; k++) {
        const s = phase + k * FRAME.len
        let got = 0
        for (let i = 0; i < 16; i++) got = (got << 1) | bits[s + 176 + i]
        if (crc16(bits, s, 176, p.poly, init) === got) ok++
      }
      out.push({ name: p.name, poly: p.poly, init, ok, frames })
    }
  return out.sort((a, b) => b.ok - a.ok)
}

/** Sync-word search: position of first frame start in the stream. */
export function findSync(bits: Uint8Array) {
  for (let i = 0; i + 24 <= bits.length; i++) {
    let v = 0
    for (let j = 0; j < 24; j++) v = (v << 1) | bits[i + j]
    if (v === FRAME.sync) return i
  }
  return -1
}

// ---------------- Interleaver rank profile ----------------

export function rankProfile() {
  const r = prng(99)
  const out: { p: number; v: number }[] = []
  for (let p = 8; p <= 128; p++) {
    let v = 0.985 + 0.012 * r()
    if (p === 48) v = 0.58
    else if (p === 96) v = 0.66
    else if (p === 24 || p === 72) v = 0.955 + 0.01 * r()
    out.push({ p, v })
  }
  return out
}

export const INTERLEAVER_TYPES = [
  { name: 'Block', score: 0.94, method: 'blind' as Method, note: 'rank dip at 48, 96' },
  { name: 'Convolutional', score: 0.03, method: 'blind' as Method, note: 'no staircase in rank vs delay' },
  { name: 'Diagonal', score: 0.02, method: 'blind' as Method, note: 'no diagonal dependence' },
  { name: 'Pseudo random', score: 0.01, method: 'library' as Method, note: '14 known PN permutations tried' },
]

export const FEC_FAMILIES = [
  { name: 'Convolutional · Viterbi', found: 'K=7 r½ (171,133)₈', method: 'blind' as Method, score: 0.97 },
  { name: 'Reed–Solomon', found: 'RS(255,223) GF(2⁸)', method: 'library' as Method, score: 0.96 },
  { name: 'Concatenated', found: 'RS outer → interleaver → CC inner', method: 'blind' as Method, score: 0.96 },
  { name: 'LDPC', found: 'Not present · dual search n ≤ 1024 null', method: 'blind' as Method, score: 0.02 },
]

export const CONV_CANDIDATES = [
  { k: 7, r: '1/2', g: '171, 133', syn: 0.021, note: 'CCSDS / NASA standard' },
  { k: 7, r: '1/2', g: '133, 171', syn: 0.024, note: 'same code, swapped outputs' },
  { k: 9, r: '1/2', g: '561, 753', syn: 0.481, note: '' },
  { k: 5, r: '1/2', g: '23, 35', syn: 0.494, note: '' },
  { k: 3, r: '1/2', g: '5, 7', syn: 0.502, note: '' },
  { k: 7, r: '1/3', g: '133, 171, 165', syn: 0.497, note: '' },
]

// ---------------- Signal Genome: named standards ----------------

export type Family = 'PSK' | 'FSK' | 'QAM' | 'OFDM' | 'CW' | 'AM' | 'PPM' | 'MSK'
export interface Standard { name: string; band: 'HF' | 'VHF' | 'UHF' | 'HF/VHF'; fam: Family; baud: string; shape: string; tones?: number; bw: number; match?: number }

export const GENOME: Standard[] = [
  { name: 'STANAG 4285', band: 'HF', fam: 'PSK', baud: '2400', shape: '8PSK, 1800 Hz carrier', bw: 3000 },
  { name: 'STANAG 4539', band: 'HF', fam: 'QAM', baud: '2400', shape: 'up to 64QAM', bw: 3000 },
  { name: 'MIL-STD-188-110A', band: 'HF', fam: 'PSK', baud: '2400', shape: '8PSK serial tone', bw: 3000, match: 0.22 },
  { name: 'MIL-STD-188-110C', band: 'HF', fam: 'QAM', baud: '2400', shape: 'WBHF up to 256QAM', bw: 3000 },
  { name: 'MIL-STD-188-141 ALE', band: 'HF', fam: 'FSK', baud: '125', shape: '8-FSK', tones: 8, bw: 2000 },
  { name: 'NAVTEX', band: 'HF', fam: 'FSK', baud: '100', shape: '170 Hz shift', tones: 2, bw: 300 },
  { name: 'SITOR-B', band: 'HF', fam: 'FSK', baud: '100', shape: '170 Hz shift', tones: 2, bw: 300 },
  { name: 'RTTY 45.45 / 170', band: 'HF', fam: 'FSK', baud: '45.45', shape: '170 Hz shift', tones: 2, bw: 250 },
  { name: 'RTTY 50 / 450', band: 'HF', fam: 'FSK', baud: '50', shape: '450 Hz shift', tones: 2, bw: 560, match: 0.93 },
  { name: 'RTTY 75 / 850', band: 'HF', fam: 'FSK', baud: '75', shape: '850 Hz shift', tones: 2, bw: 1000 },
  { name: 'PACTOR-I', band: 'HF', fam: 'FSK', baud: '100/200', shape: '200 Hz shift', tones: 2, bw: 500 },
  { name: 'CLOVER-2000', band: 'HF', fam: 'PSK', baud: '62.5', shape: '8 tones, BPSK→8PSK', bw: 2000 },
  { name: 'HFDL', band: 'HF', fam: 'PSK', baud: '1800', shape: 'PSK, 1440 Hz carrier', bw: 2400 },
  { name: 'DSC', band: 'HF/VHF', fam: 'FSK', baud: '100', shape: '170 Hz shift', tones: 2, bw: 300 },
  { name: 'DRM30', band: 'HF', fam: 'OFDM', baud: '—', shape: 'OFDM, 4.5–20 kHz', bw: 10000 },
  { name: 'PSK31', band: 'HF', fam: 'PSK', baud: '31.25', shape: 'BPSK', bw: 60 },
  { name: 'FT8', band: 'HF', fam: 'FSK', baud: '6.25', shape: '8-GFSK', tones: 8, bw: 50 },
  { name: 'WEFAX', band: 'HF', fam: 'FSK', baud: '—', shape: 'FM ±400 Hz', tones: 2, bw: 900 },
  { name: 'CW (Morse)', band: 'HF/VHF', fam: 'CW', baud: '—', shape: 'on off keyed carrier', bw: 100 },
  { name: 'AIS', band: 'VHF', fam: 'MSK', baud: '9600', shape: 'GMSK BT 0.4', bw: 14000 },
  { name: 'ACARS', band: 'VHF', fam: 'MSK', baud: '2400', shape: 'AM-MSK', bw: 5000 },
  { name: 'APRS / AX.25', band: 'VHF', fam: 'FSK', baud: '1200', shape: 'AFSK 1200/2200', tones: 2, bw: 3000 },
  { name: 'POCSAG', band: 'VHF', fam: 'FSK', baud: '512–2400', shape: '±4.5 kHz FSK', tones: 2, bw: 12000 },
  { name: 'NOAA APT', band: 'VHF', fam: 'AM', baud: '—', shape: '2400 Hz AM subcarrier', bw: 34000 },
  { name: 'Meteor-M LRPT', band: 'VHF', fam: 'PSK', baud: '72k', shape: 'QPSK, CC + RS', bw: 120000 },
  { name: 'DMR', band: 'UHF', fam: 'FSK', baud: '4800', shape: '4-FSK', tones: 4, bw: 12500 },
  { name: 'P25 Phase 1', band: 'UHF', fam: 'FSK', baud: '4800', shape: 'C4FM', tones: 4, bw: 12500 },
  { name: 'dPMR', band: 'UHF', fam: 'FSK', baud: '2400', shape: '4-FSK', tones: 4, bw: 6250 },
  { name: 'NXDN', band: 'UHF', fam: 'FSK', baud: '2400/4800', shape: '4-FSK', tones: 4, bw: 6250 },
  { name: 'TETRA', band: 'UHF', fam: 'PSK', baud: '18k', shape: 'π/4-DQPSK', bw: 25000 },
  { name: 'ADS-B', band: 'UHF', fam: 'PPM', baud: '1M', shape: 'PPM 1090 MHz', bw: 2000000 },
]

export function fmtBytes(n: number) {
  return n > 1e9 ? (n / 1e9).toFixed(2) + ' GB' : n > 1e6 ? (n / 1e6).toFixed(1) + ' MB' : (n / 1e3).toFixed(0) + ' kB'
}

export function fmtHz(f: number, digits = 2) {
  const a = Math.abs(f)
  if (a >= 1e9) return (f / 1e9).toFixed(digits) + ' GHz'
  if (a >= 1e6) return (f / 1e6).toFixed(digits) + ' MHz'
  if (a >= 1e3) return (f / 1e3).toFixed(digits) + ' kHz'
  return f.toFixed(0) + ' Hz'
}

export function bandOf(hz: number) {
  if (hz >= 3e6 && hz < 30e6) return 'HF'
  if (hz >= 30e6 && hz < 300e6) return 'VHF'
  if (hz >= 300e6 && hz < 3e9) return 'UHF'
  if (hz < 3e6) return 'MF/LF'
  return 'SHF'
}

export const RECENT = [
  { name: 'sanjaya-gen_0042.iq', size: 48_234_496, fmt: 'Raw IQ · c16 LE', when: '26 Sep 14:12', verdict: 'proven', note: 'QPSK · RS∘CC · Block 48×32' },
  { name: 'kiwi_navtex_518k_0914.wav', size: 11_520_044, fmt: 'WAV · 12 kHz · real', when: '24 Sep 09:41', verdict: 'proven', note: 'NAVTEX · SITOR-B' },
  { name: 'kiwi_s4285_8416k_0915.wav', size: 92_160_044, fmt: 'WAV · 2ch → IQ', when: '23 Sep 21:07', verdict: 'proven', note: 'STANAG 4285 · 8PSK' },
  { name: 'uhf_433_burst_0916.iq', size: 201_326_592, fmt: 'Raw IQ · cf32', when: '22 Sep 18:30', verdict: 'partial', note: 'payload high entropy' },
  { name: 'unknown_0911_2203.iq', size: 16_777_216, fmt: 'Raw IQ · c8', when: '19 Sep 22:03', verdict: 'novel', note: 'LFM chirp · no class' },
]
