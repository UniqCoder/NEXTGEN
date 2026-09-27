import { useEffect, useMemo, useRef, type DependencyList } from 'react'
import { SCENARIO, SPEC, autocorr, bitstream, gauss, prng, rankProfile, spectrogram } from '../lib/mock'
import { axes, clamp, css, prep, useSize, type Box } from '../lib/plot'
import { LUTS } from '../lib/colormap'
import { useApp } from '../lib/store'

type Draw = (ctx: CanvasRenderingContext2D, w: number, h: number) => void

/** Static canvas that redraws on resize, theme, fonts and the given deps. */
function useDraw(draw: Draw, deps: DependencyList) {
  const wrap = useRef<HTMLDivElement>(null)
  const cv = useRef<HTMLCanvasElement>(null)
  const { w, h } = useSize(wrap)
  const fonts = useApp((s) => s.fontsReady)
  const theme = useApp((s) => s.theme)
  useEffect(() => {
    if (cv.current && w > 10 && h > 10) draw(prep(cv.current, w, h), w, h)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [w, h, fonts, theme, ...deps])
  return { wrap, cv }
}

/** Animated canvas; draw gets elapsed seconds. */
function useAnim(draw: (ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => void, deps: DependencyList) {
  const wrap = useRef<HTMLDivElement>(null)
  const cv = useRef<HTMLCanvasElement>(null)
  const { w, h } = useSize(wrap)
  const theme = useApp((s) => s.theme)
  const fonts = useApp((s) => s.fontsReady)
  useEffect(() => {
    if (!cv.current || w < 10 || h < 10) return
    let raf = 0
    const t0 = performance.now()
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
    const loop = () => {
      draw(prep(cv.current!, w, h), w, h, (performance.now() - t0) / 1000)
      if (!reduce) raf = requestAnimationFrame(loop)
    }
    loop()
    return () => cancelAnimationFrame(raf)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [w, h, theme, fonts, ...deps])
  return { wrap, cv }
}

const Frame = ({ r, children }: { r: { wrap: React.RefObject<HTMLDivElement | null>; cv: React.RefObject<HTMLCanvasElement | null> }; children?: React.ReactNode }) => (
  <div ref={r.wrap} className="plot">
    <canvas ref={r.cv} />
    {children}
  </div>
)

// ---------------- PSD: persistence spectrum ----------------

const PSD_MIN = -106, PSD_MAX = -64, PSD_LEVELS = 150

export function PSD() {
  const sel = useApp((s) => s.sel)
  const theme = useApp((s) => s.theme)
  const cmap = useApp((s) => s.cmap)
  // How often each (frequency, level) cell was hit across all rows: the "digital phosphor" density.
  const data = useMemo(() => {
    const s = spectrogram()
    const hits = new Uint16Array(PSD_LEVELS * SPEC.bins)
    const lin = new Float64Array(SPEC.bins)
    let top = 1
    for (let y = 0; y < SPEC.rows; y++)
      for (let b = 0; b < SPEC.bins; b++) {
        const db = s.full[y * SPEC.bins + b]
        if (y >= 24) lin[b] += 10 ** (db / 10) / (SPEC.rows - 24)
        const lv = Math.floor(((db - PSD_MIN) / (PSD_MAX - PSD_MIN)) * PSD_LEVELS)
        if (lv < 0 || lv >= PSD_LEVELS) continue
        const i = (PSD_LEVELS - 1 - lv) * SPEC.bins + b
        top = Math.max(top, ++hits[i])
      }
    return { hits, top, avg: Array.from(lin, (v) => 10 * Math.log10(v)) }
  }, [])
  const img = useMemo(() => {
    const c = document.createElement('canvas')
    c.width = SPEC.bins
    c.height = PSD_LEVELS
    const ctx = c.getContext('2d')!
    const im = ctx.createImageData(SPEC.bins, PSD_LEVELS)
    const lut = LUTS[theme === 'paper' ? 'paper' : cmap]
    const lt = Math.log1p(data.top)
    data.hits.forEach((h, i) => {
      if (!h) return
      const v = Math.log1p(h) / lt
      const li = Math.round((0.3 + 0.7 * v) * 255) * 3
      im.data[i * 4] = lut[li]; im.data[i * 4 + 1] = lut[li + 1]; im.data[i * 4 + 2] = lut[li + 2]
      im.data[i * 4 + 3] = Math.round(Math.min(1, 0.35 + v) * 255)
    })
    ctx.putImageData(im, 0, 0)
    return c
  }, [data, theme, cmap])

  const r = useDraw((ctx, w, h) => {
    const b: Box = { x: 40, y: 10, w: w - 52, h: h - 36 }
    axes(ctx, b, { min: -24, max: 24, fmt: (v) => (v > 0 ? '+' : '') + v, count: 8, title: 'kHz' }, { min: PSD_MIN, max: PSD_MAX, fmt: (v) => String(v), count: 4, title: 'dB' })
    const X = (bin: number) => b.x + ((bin + 0.5) / SPEC.bins) * b.w
    const Y = (db: number) => b.y + b.h - clamp((db - PSD_MIN) / (PSD_MAX - PSD_MIN)) * b.h
    const fx = (f: number) => b.x + ((f + 24000) / 48000) * b.w
    if (sel) {
      ctx.fillStyle = 'rgba(255,138,31,0.08)'
      ctx.fillRect(fx(Math.min(sel.f0, sel.f1)), b.y, Math.abs(fx(sel.f1) - fx(sel.f0)), b.h)
    }
    ctx.save()
    ctx.globalCompositeOperation = theme === 'paper' ? 'multiply' : 'lighter'
    ctx.imageSmoothingEnabled = true
    ctx.drawImage(img, b.x, b.y, b.w, b.h)
    ctx.restore()
    // long-term average on top of the phosphor
    ctx.beginPath(); data.avg.forEach((v, i) => (i ? ctx.lineTo(X(i), Y(v)) : ctx.moveTo(X(i), Y(v))))
    ctx.strokeStyle = css('--bone-1'); ctx.globalAlpha = 0.85; ctx.lineWidth = 1; ctx.stroke(); ctx.globalAlpha = 1
    // occupied-bandwidth dimension line for E1
    const e = SCENARIO.emitters[0], x0 = fx(e.f0), x1 = fx(e.f1), yy = Y(-67)
    ctx.strokeStyle = css('--bone-2'); ctx.lineWidth = 1
    ctx.beginPath(); ctx.moveTo(x0, yy - 4); ctx.lineTo(x0, yy + 4); ctx.moveTo(x1, yy - 4); ctx.lineTo(x1, yy + 4); ctx.moveTo(x0, yy); ctx.lineTo(x1, yy); ctx.stroke()
    ctx.fillStyle = css('--bone-1'); ctx.font = '8.5px "Martian Mono"'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'
    ctx.fillText('OBW 3.24 kHz · −26 dB', x1 + 6, yy)
    ctx.fillStyle = css('--bone-2'); ctx.textAlign = 'left'
    ctx.fillText('E3 CW', fx(-17500) + 6, Y(-68))
  }, [sel, img])
  return (
    <Frame r={r} />
  )
}

// ---------------- Constellation: phosphor with persistence ----------------

const QPSK = [[1, 1], [-1, 1], [-1, -1], [1, -1]].map(([i, q]) => [i / Math.SQRT2, q / Math.SQRT2])
const PSK8 = Array.from({ length: 8 }, (_, i) => [Math.cos((i * Math.PI) / 4 + Math.PI / 8), Math.sin((i * Math.PI) / 4 + Math.PI / 8)])

/** Soft round dot, pre-rendered once per colour, stamped with additive blending. */
function sprite(color: string, size = 14) {
  const c = document.createElement('canvas')
  c.width = c.height = size
  const g = c.getContext('2d')!
  const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
  grad.addColorStop(0, 'rgba(255,236,210,1)')
  grad.addColorStop(0.18, color)
  grad.addColorStop(1, 'rgba(0,0,0,0)')
  g.fillStyle = grad
  g.fillRect(0, 0, size, size)
  return c
}

export function Constellation({ locked, ref8 }: { locked: boolean; ref8: boolean }) {
  const lock = useRef(locked ? 1 : 0)
  const acc = useRef<HTMLCanvasElement | null>(null)
  const r = useAnim((ctx, w, h, t) => {
    const paper = document.documentElement.dataset.theme === 'paper'
    const dpr = Math.min(2, devicePixelRatio || 1)
    if (!acc.current) acc.current = document.createElement('canvas')
    const A = acc.current
    if (A.width !== Math.round(w * dpr) || A.height !== Math.round(h * dpr)) { A.width = Math.round(w * dpr); A.height = Math.round(h * dpr) }
    const a = A.getContext('2d')!
    a.setTransform(dpr, 0, 0, dpr, 0, 0)

    lock.current += ((locked ? 1 : 0) - lock.current) * 0.02
    const L = lock.current
    const s = Math.min(w, h - 24) - 16, cx = w / 2, cy = (h - 24) / 2 + 2, sc = s / 2 / 1.45
    const P = (i: number, q: number) => [cx + i * sc, cy - q * sc]

    // persistence: fade the previous frame instead of clearing it
    a.globalCompositeOperation = 'destination-out'
    a.fillStyle = 'rgba(0,0,0,0.14)'
    a.fillRect(0, 0, w, h)
    a.globalCompositeOperation = paper ? 'source-over' : 'lighter'
    const dot = spriteFor(paper ? css('--signal') : 'rgba(255,138,31,0.55)')
    const rnd = prng(Math.floor(t * 60))
    const n = 260
    a.globalAlpha = paper ? 0.25 : 0.34
    for (let j = 0; j < n; j++) {
      const [i0, q0] = QPSK[Math.floor(rnd() * 4)]
      const idx = t * 900 + j * 3.4
      const ph = (1 - L) * (idx * 0.011 + Math.sin(idx * 0.002) * 2 + 0.4)
      const sd = 0.065 + (1 - L) * 0.1
      const i1 = i0 * Math.cos(ph) - q0 * Math.sin(ph) + gauss(rnd) * sd
      const q1 = i0 * Math.sin(ph) + q0 * Math.cos(ph) + gauss(rnd) * sd
      const [x, y] = P(i1, q1)
      a.drawImage(dot, x - 7, y - 7)
    }
    a.globalAlpha = 1

    // reticle under the phosphor
    ctx.strokeStyle = css('--line'); ctx.lineWidth = 1
    ctx.beginPath(); ctx.moveTo(cx - s / 2, cy + 0.5); ctx.lineTo(cx + s / 2, cy + 0.5); ctx.moveTo(cx + 0.5, cy - s / 2); ctx.lineTo(cx + 0.5, cy + s / 2); ctx.stroke()
    for (const rr of [0.5, 1]) { ctx.beginPath(); ctx.arc(cx, cy, sc * rr, 0, Math.PI * 2); ctx.strokeStyle = css(rr === 1 ? '--line-2' : '--line'); ctx.stroke() }
    // lock ring: a phase-error arc that closes as the carrier loop locks
    ctx.save()
    ctx.strokeStyle = css('--signal'); ctx.lineWidth = 1.5; ctx.globalAlpha = 0.35 + 0.5 * L
    ctx.shadowColor = css('--signal'); ctx.shadowBlur = paper ? 0 : 10 * L
    ctx.beginPath(); ctx.arc(cx, cy, sc * 1.32, -Math.PI / 2 + t * (1 - L) * 3, -Math.PI / 2 + t * (1 - L) * 3 + Math.PI * 2 * (0.15 + 0.85 * L)); ctx.stroke()
    ctx.restore()
    ctx.fillStyle = css('--bone-4'); ctx.font = '8.5px "Martian Mono"'; ctx.textAlign = 'left'; ctx.textBaseline = 'top'
    ctx.fillText('I', cx + s / 2 - 8, cy + 4); ctx.fillText('Q', cx + 4, cy - s / 2 + 2)

    ctx.drawImage(A, 0, 0, w, h)

    // reference points of the current hypothesis
    ctx.strokeStyle = ref8 ? css('--fault') : css('--bone-1'); ctx.lineWidth = 1
    for (const [i, q] of ref8 ? PSK8 : QPSK) {
      const [x, y] = P(i * 1, q * 1)
      ctx.beginPath(); ctx.moveTo(x - 6, y); ctx.lineTo(x - 2, y); ctx.moveTo(x + 2, y); ctx.lineTo(x + 6, y)
      ctx.moveTo(x, y - 6); ctx.lineTo(x, y - 2); ctx.moveTo(x, y + 2); ctx.lineTo(x, y + 6); ctx.stroke()
    }
  }, [locked, ref8])
  return (
    <Frame r={r}>
      <div className="ax-title" style={{ left: 12, bottom: 8 }}>{locked ? 'EVM 6.1 % · MER 24.3 dB · CARRIER LOCKED' : 'ACQUIRING · CARRIER SPINNING'}</div>
    </Frame>
  )
}

const sprites = new Map<string, HTMLCanvasElement>()
const spriteFor = (color: string) => sprites.get(color) ?? sprites.set(color, sprite(color)).get(color)!

// ---------------- Eye diagram ----------------

export function Eye() {
  const r = useDraw((ctx, w, h) => {
    const b: Box = { x: 30, y: 10, w: w - 40, h: h - 34 }
    axes(ctx, b, { min: -1, max: 1, fmt: (v) => (v === 0 ? '0' : v + 'T'), count: 4, title: 'SYMBOL' }, { min: -1.5, max: 1.5, fmt: (v) => v.toFixed(1), count: 4 })
    const rnd = prng(5)
    const sps = 24, span = 6
    const rcP = (t: number) => {
      const a = 0.35
      if (Math.abs(t) < 1e-6) return 1
      const den = 1 - (2 * a * t) ** 2
      const sinc = Math.sin(Math.PI * t) / (Math.PI * t)
      return Math.abs(den) < 1e-6 ? (Math.PI / 4) * sinc : (sinc * Math.cos(Math.PI * a * t)) / den
    }
    const syms = Array.from({ length: 400 }, () => (rnd() < 0.5 ? -1 : 1) / Math.SQRT2 * 1.4)
    ctx.strokeStyle = css('--signal'); ctx.globalAlpha = 0.08; ctx.lineWidth = 1
    if (document.documentElement.dataset.theme !== 'paper') ctx.globalCompositeOperation = 'lighter'
    for (let k = span; k < syms.length - span - 2; k++) {
      ctx.beginPath()
      for (let s = 0; s <= 2 * sps; s++) {
        const tt = k + s / sps - 1
        let v = 0
        for (let m = Math.floor(tt) - span; m <= Math.floor(tt) + span; m++) v += syms[m] * rcP(tt - m)
        v += gauss(rnd) * 0.05
        const x = b.x + (s / (2 * sps)) * b.w, y = b.y + b.h / 2 - (v / 1.5) * (b.h / 2)
        s ? ctx.lineTo(x, y) : ctx.moveTo(x, y)
      }
      ctx.stroke()
    }
    ctx.globalAlpha = 1
    ctx.globalCompositeOperation = 'source-over'
    ctx.strokeStyle = css('--bone-2'); ctx.setLineDash([2, 3])
    ctx.beginPath(); ctx.moveTo(b.x + b.w / 2 + 0.5, b.y); ctx.lineTo(b.x + b.w / 2 + 0.5, b.y + b.h); ctx.stroke(); ctx.setLineDash([])
    ctx.fillStyle = css('--bone-2'); ctx.font = '8.5px "Martian Mono"'; ctx.textAlign = 'left'; ctx.textBaseline = 'top'
    ctx.fillText('SAMPLE · OPENING 0.82', b.x + b.w / 2 + 5, b.y + 4)
  }, [])
  return <Frame r={r} />
}

// ---------------- FSK: instantaneous frequency ----------------

export function InstFreq() {
  const r = useDraw((ctx, w, h) => {
    const b: Box = { x: 44, y: 10, w: w - 56, h: h - 34 }
    axes(ctx, b, { min: 0, max: 1, fmt: (v) => v.toFixed(1) + ' s', count: 5 }, { min: -400, max: 400, fmt: (v) => (v > 0 ? '+' : '') + v, count: 4, title: 'Hz' })
    const rnd = prng(11)
    const Y = (f: number) => b.y + b.h / 2 - (f / 400) * (b.h / 2)
    ctx.strokeStyle = css('--bone-3'); ctx.setLineDash([3, 3])
    for (const f of [-225, 225]) { ctx.beginPath(); ctx.moveTo(b.x, Y(f) + 0.5); ctx.lineTo(b.x + b.w, Y(f) + 0.5); ctx.stroke() }
    ctx.setLineDash([])
    ctx.strokeStyle = css('--signal'); ctx.lineWidth = 1; ctx.beginPath()
    let bit = 1, f = 225
    for (let i = 0; i <= 1000; i++) {
      if (i % 20 === 0) bit = rnd() < 0.5 ? 1 : -1
      f += (bit * 225 - f) * 0.35
      const x = b.x + (i / 1000) * b.w, y = Y(f + gauss(rnd) * 28)
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)
    }
    ctx.stroke()
    ctx.fillStyle = css('--bone-2'); ctx.font = '8.5px "Martian Mono"'; ctx.textAlign = 'right'; ctx.textBaseline = 'bottom'
    ctx.fillText('MARK +225', b.x + b.w - 4, Y(225) - 3)
    ctx.textBaseline = 'top'; ctx.fillText('SPACE −225', b.x + b.w - 4, Y(-225) + 3)
  }, [])
  return <Frame r={r} />
}

// ---------------- Interleaver rank profile ----------------

export function RankProfile() {
  const data = useMemo(rankProfile, [])
  const r = useAnim((ctx, w, h, t) => {
    const b: Box = { x: 44, y: 16, w: w - 60, h: h - 44 }
    axes(ctx, b, { min: 8, max: 128, fmt: (v) => String(v), count: 12, title: 'CANDIDATE PERIOD · bits' }, { min: 0.5, max: 1, fmt: (v) => v.toFixed(1), count: 5, title: 'NORM. RANK' })
    const prog = clamp(t / 1.2)
    const X = (p: number) => b.x + ((p - 8) / 120) * b.w
    const Y = (v: number) => b.y + b.h - ((v - 0.5) / 0.5) * b.h
    // baseline at full rank; each candidate period hangs down by its rank deficiency
    ctx.strokeStyle = css('--line-3'); ctx.setLineDash([2, 3])
    ctx.beginPath(); ctx.moveTo(b.x, Y(1) + 0.5); ctx.lineTo(b.x + b.w, Y(1) + 0.5); ctx.stroke(); ctx.setLineDash([])
    const shown = data.filter((_, i) => i / data.length <= prog)
    ctx.strokeStyle = css('--bone-3'); ctx.lineWidth = 1; ctx.beginPath()
    shown.forEach((d, i) => (i ? ctx.lineTo(X(d.p), Y(d.v)) : ctx.moveTo(X(d.p), Y(d.v))))
    ctx.stroke()
    for (const d of shown) {
      const dip = d.v < 0.8
      ctx.fillStyle = dip ? css('--signal') : css('--bone-2')
      if (dip) {
        ctx.strokeStyle = css('--signal'); ctx.lineWidth = 2
        ctx.beginPath(); ctx.moveTo(X(d.p), Y(1)); ctx.lineTo(X(d.p), Y(d.v)); ctx.stroke()
      }
      ctx.beginPath(); ctx.arc(X(d.p), Y(d.v), dip ? 3.5 : 1.3, 0, Math.PI * 2); ctx.fill()
    }
    if (prog > 0.35) {
      const x = X(48), y = Y(0.58)
      ctx.strokeStyle = css('--signal'); ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(x + 4, y + 2); ctx.lineTo(x + 30, y + 26); ctx.lineTo(x + 180, y + 26); ctx.stroke()
      ctx.fillStyle = css('--signal'); ctx.font = '500 9.5px "Martian Mono"'; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom'
      ctx.fillText('PERIOD = 48', x + 34, y + 23)
      ctx.fillStyle = css('--bone-2'); ctx.font = '8.5px "Martian Mono"'; ctx.textBaseline = 'top'
      ctx.fillText('rank deficiency 42 % · block', x + 34, y + 30)
    }
  }, [])
  return <Frame r={r} />
}

// ---------------- Bit-stream autocorrelation ----------------

export function Autocorr() {
  const ac = useMemo(() => autocorr(bitstream().stream, 640), [])
  const r = useDraw((ctx, w, h) => {
    const b: Box = { x: 40, y: 12, w: w - 52, h: h - 38 }
    axes(ctx, b, { min: 0, max: 640, fmt: (v) => String(v), count: 8, title: 'LAG · bits' }, { min: -0.1, max: 0.6, fmt: (v) => v.toFixed(1), count: 4, title: 'R' })
    const X = (l: number) => b.x + (l / 640) * b.w
    const Y = (v: number) => b.y + b.h - ((v + 0.1) / 0.7) * b.h
    ctx.strokeStyle = css('--bone-2'); ctx.lineWidth = 1; ctx.beginPath()
    for (let l = 1; l <= 640; l++) (l === 1 ? ctx.moveTo(X(l), Y(ac[l])) : ctx.lineTo(X(l), Y(ac[l])))
    ctx.stroke()
    ctx.fillStyle = css('--signal'); ctx.strokeStyle = css('--signal'); ctx.font = '8.5px "Martian Mono"'; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom'
    for (const l of [192, 384, 576]) {
      const x = X(l), y = Y(ac[l])
      ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.stroke()
      ctx.fillText(String(l), x, y - 5)
    }
  }, [ac])
  return <Frame r={r} />
}

/** Mini spectral fingerprint for a named standard. */
export function Fingerprint({ fam, tones = 2, bw }: { fam: string; tones?: number; bw: number }) {
  const r = useDraw((ctx, w, h) => {
    const n = 80
    ctx.strokeStyle = css('--bone-2'); ctx.lineWidth = 1; ctx.beginPath()
    const rnd = prng(fam.length * 31 + tones + Math.round(Math.log(bw) * 7))
    const width = clamp(0.25 + Math.log10(bw) / 14, 0.2, 0.8)
    for (let i = 0; i <= n; i++) {
      const x = i / n - 0.5
      let v = 0.08 * rnd()
      if (fam === 'FSK') for (let t = 0; t < tones; t++) v += 0.9 * Math.exp(-((x - (t / Math.max(1, tones - 1) - 0.5) * width) ** 2) / 0.0006)
      else if (fam === 'CW') v += Math.exp(-(x ** 2) / 0.0002)
      else if (fam === 'OFDM') v += Math.abs(x) < width / 2 ? 0.7 : 0
      else if (fam === 'AM') v += Math.exp(-(x ** 2) / 0.0002) + 0.4 * (Math.exp(-((x - 0.2) ** 2) / 0.003) + Math.exp(-((x + 0.2) ** 2) / 0.003))
      else if (fam === 'PPM') v += 0.5 * Math.exp(-(x ** 2) / 0.05)
      else v += 0.8 * (Math.abs(x) < (width / 2) * 0.7 ? 1 : Math.max(0, 1 - (Math.abs(x) - (width / 2) * 0.7) / (width * 0.15)))
      const px = (i / n) * w, py = h - 2 - clamp(v) * (h - 6)
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)
    }
    ctx.stroke()
  }, [fam, tones, bw])
  return <Frame r={r} />
}

