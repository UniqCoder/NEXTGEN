import { useEffect, useMemo, useRef, useState } from 'react'
import { LUTS } from '../lib/colormap'
import { SPEC, SCENARIO, binFreq, freqBin, spectrogram } from '../lib/mock'
import { axes, clamp, css, prep, sweep, useSize, type Box } from '../lib/plot'
import { setState, useApp } from '../lib/store'

export interface Overlay { id: string; f0: number; f1: number; t0: number; t1: number; label: string; alpha: number; tone: 'signal' | 'bone' | 'proof' | 'novel' }

const M = { l: 46, r: 58, t: 10, b: 30 }

export function Waterfall(props: {
  k: number
  target: 'resid' | 'fail'
  floor: number
  span: number
  overlays?: Overlay[]
  failBand?: boolean
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const cv = useRef<HTMLCanvasElement>(null)
  const { w, h } = useSize(wrap)
  const cmap = useApp((s) => s.cmap)
  const theme = useApp((s) => s.theme)
  const sel = useApp((s) => s.sel)
  const fonts = useApp((s) => s.fontsReady)
  const [hover, setHover] = useState<{ x: number; y: number } | null>(null)
  const drag = useRef<number | null>(null)
  const [view, setView] = useState({ a: -SPEC.fs / 2, b: SPEC.fs / 2 })
  const spec = useMemo(spectrogram, [])
  const off = useMemo(() => {
    const c = document.createElement('canvas')
    c.width = SPEC.bins
    c.height = SPEC.rows
    return c
  }, [])

  const box: Box = { x: M.l, y: M.t, w: Math.max(10, w - M.l - M.r), h: Math.max(10, h - M.t - M.b) }
  const fmin = view.a, fmax = view.b, dur = SCENARIO.file.duration

  // Rebuild the image: mix recording and residual row by row behind the sweep front.
  useEffect(() => {
    const ctx = off.getContext('2d')!
    const img = ctx.createImageData(SPEC.bins, SPEC.rows)
    const lut = LUTS[theme === 'paper' ? 'paper' : cmap]
    const tgt = props.target === 'fail' ? spec.fail : spec.resid
    for (let y = 0; y < SPEC.rows; y++) {
      const kk = sweep(props.k, y / SPEC.rows)
      for (let b = 0; b < SPEC.bins; b++) {
        const i = y * SPEC.bins + b
        const db = spec.full[i] + (tgt[i] - spec.full[i]) * kk
        const t = clamp((db - props.floor) / props.span)
        const li = Math.round(t * 255) * 3, o = i * 4
        img.data[o] = lut[li]; img.data[o + 1] = lut[li + 1]; img.data[o + 2] = lut[li + 2]; img.data[o + 3] = 255
      }
    }
    ctx.putImageData(img, 0, 0)
  }, [props.k, props.target, props.floor, props.span, cmap, theme, spec, off])

  useEffect(() => {
    if (!cv.current || w < 20) return
    const ctx = prep(cv.current, w, h)
    ctx.imageSmoothingEnabled = true
    ctx.imageSmoothingQuality = 'high'
    const sx = ((fmin + SPEC.fs / 2) / SPEC.fs) * SPEC.bins, sw = ((fmax - fmin) / SPEC.fs) * SPEC.bins
    ctx.drawImage(off, sx, 0, sw, SPEC.rows, box.x, box.y, box.w, box.h)
    axes(ctx, box,
      { min: fmin / 1e3, max: fmax / 1e3, fmt: (v) => (v > 0 ? '+' : '') + v, count: 10, title: fmax - fmin < SPEC.fs ? 'FREQUENCY · kHz · ZOOMED · DOUBLE-CLICK RESETS' : 'FREQUENCY · kHz · WHEEL ZOOMS' },
      { min: 0, max: dur, fmt: (v) => v + ' s', count: 6, flip: true, title: 'TIME' }, false)

    const fx = (f: number) => box.x + ((f - fmin) / (fmax - fmin)) * box.w
    const ty = (t: number) => box.y + t * box.h

    // Proof failure: the part of the ridge that did not go away
    if (props.failBand && props.k > 0) {
      const e1 = SCENARIO.emitters[0]
      const x0 = fx(e1.f0), x1 = fx(e1.f1)
      const yEnd = box.y + clamp(props.k * 1.28) * box.h
      ctx.save()
      ctx.beginPath(); ctx.rect(x0, ty(e1.t0), x1 - x0, Math.max(0, yEnd - ty(e1.t0))); ctx.clip()
      ctx.strokeStyle = css('--fault'); ctx.globalAlpha = 0.55; ctx.lineWidth = 1
      for (let d = -box.h; d < x1 - x0 + box.h; d += 6) { ctx.beginPath(); ctx.moveTo(x0 + d, ty(e1.t0)); ctx.lineTo(x0 + d + box.h, ty(e1.t0) + box.h); ctx.stroke() }
      ctx.restore()
      ctx.strokeStyle = css('--fault'); ctx.strokeRect(x0 + 0.5, ty(e1.t0) + 0.5, x1 - x0, Math.max(0, yEnd - ty(e1.t0)))
      ctx.fillStyle = css('--fault'); ctx.font = '500 9px "Martian Mono"'; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom'
      ctx.fillText(`UNEXPLAINED ENERGY ${(100 - SCENARIO.proof.failExplained).toFixed(1)} %`, x1 + 6, ty(e1.t0) + 12)
    }

    // Emitter annotations, drawn like callouts on a technical drawing
    for (const o of props.overlays ?? []) {
      if (o.alpha <= 0.01) continue
      const x0 = fx(o.f0), x1 = fx(o.f1), y0 = ty(o.t0), y1 = ty(o.t1)
      const col = o.tone === 'signal' ? css('--signal') : o.tone === 'proof' ? css('--proof') : css('--bone-1')
      ctx.save()
      ctx.globalAlpha = o.alpha
      ctx.strokeStyle = col
      ctx.lineWidth = 1
      if (o.tone === 'novel') ctx.setLineDash([3, 3])
      ctx.strokeRect(Math.round(x0) + 0.5, Math.round(y0) + 0.5, Math.round(x1 - x0), Math.round(y1 - y0))
      ctx.setLineDash([])
      const tick = 5
      for (const [cx, cy, sx, sy] of [[x0, y0, 1, 1], [x1, y0, -1, 1], [x0, y1, 1, -1], [x1, y1, -1, -1]] as const) {
        ctx.beginPath(); ctx.moveTo(cx, cy + sy * tick); ctx.lineTo(cx, cy); ctx.lineTo(cx + sx * tick, cy); ctx.lineWidth = 2; ctx.stroke()
      }
      ctx.font = '9px "Martian Mono"'
      const tw = ctx.measureText(o.label).width + 10
      const lx = Math.min(x0, box.x + box.w - tw), ly = Math.max(box.y, y0 - 16)
      ctx.fillStyle = css('--ink-0'); ctx.fillRect(lx, ly, tw, 14)
      ctx.strokeStyle = col; ctx.lineWidth = 1; ctx.strokeRect(lx + 0.5, ly + 0.5, tw - 1, 13)
      ctx.fillStyle = col; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'
      ctx.fillText(o.label, lx + 5, ly + 7.5)
      ctx.restore()
    }

    // Linked selection
    if (sel) {
      const x0 = fx(Math.min(sel.f0, sel.f1)), x1 = fx(Math.max(sel.f0, sel.f1))
      ctx.fillStyle = 'rgba(255,138,31,0.08)'
      ctx.fillRect(x0, box.y, x1 - x0, box.h)
      ctx.strokeStyle = css('--signal')
      ctx.beginPath(); ctx.moveTo(x0 + 0.5, box.y); ctx.lineTo(x0 + 0.5, box.y + box.h); ctx.moveTo(x1 - 0.5, box.y); ctx.lineTo(x1 - 0.5, box.y + box.h); ctx.stroke()
    }

    // Colour-scale legend
    const lx = box.x + box.w + 14, lw = 8
    const lut = LUTS[theme === 'paper' ? 'paper' : cmap]
    for (let i = 0; i < box.h; i++) {
      const li = Math.round((1 - i / box.h) * 255) * 3
      ctx.fillStyle = `rgb(${lut[li]},${lut[li + 1]},${lut[li + 2]})`
      ctx.fillRect(lx, box.y + i, lw, 1)
    }
    ctx.strokeStyle = css('--line-2'); ctx.strokeRect(lx + 0.5, box.y + 0.5, lw - 1, box.h - 1)
    ctx.fillStyle = css('--bone-3'); ctx.font = '8.5px "Martian Mono"'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'
    for (let i = 0; i <= 4; i++) {
      const v = props.floor + props.span * (1 - i / 4)
      ctx.fillText(v.toFixed(0), lx + lw + 4, box.y + (i / 4) * box.h)
    }
    ctx.textBaseline = 'bottom'; ctx.fillStyle = css('--bone-4')
    ctx.fillText('dB', lx, box.y + box.h + 22)
  }, [w, h, props.k, props.floor, props.span, props.overlays, props.failBand, sel, cmap, theme, fonts, off, view])

  const toF = (x: number) => fmin + ((x - box.x) / box.w) * (fmax - fmin)
  const inside = (x: number, y: number) => x >= box.x && x <= box.x + box.w && y >= box.y && y <= box.y + box.h

  let readout = null
  if (hover && inside(hover.x, hover.y)) {
    const f = toF(hover.x)
    const row = Math.floor(((hover.y - box.y) / box.h) * SPEC.rows)
    const b = Math.round(freqBin(f))
    const i = clamp(row, 0, SPEC.rows - 1) * SPEC.bins + clamp(b, 0, SPEC.bins - 1)
    const kk = sweep(props.k, row / SPEC.rows)
    const tgt = props.target === 'fail' ? spec.fail : spec.resid
    const db = spec.full[i] + (tgt[i] - spec.full[i]) * kk
    const right = hover.x > box.x + box.w - 150
    readout = (
      <>
        <div className="xhair-v" style={{ left: hover.x, top: box.y, height: box.h }} />
        <div className="xhair-h" style={{ top: hover.y, left: box.x, width: box.w }} />
        <div className="readout" style={{ left: right ? hover.x - 142 : hover.x + 10, top: hover.y + 10 }}>
          <span className="dim">f </span>{(binFreq(b) >= 0 ? '+' : '') + (binFreq(b) / 1e3).toFixed(3)} kHz
          <span className="dim"> · t </span>{((row / SPEC.rows) * dur).toFixed(1)} s
          <span className="dim"> · </span>{db.toFixed(1)} dB
        </div>
      </>
    )
  }

  return (
    <div
      ref={wrap}
      className="plot"
      style={{ cursor: 'crosshair' }}
      onPointerMove={(e) => {
        const r = wrap.current!.getBoundingClientRect()
        const x = e.clientX - r.left, y = e.clientY - r.top
        setHover({ x, y })
        if (drag.current !== null && Math.abs(x - drag.current) > 3)
          setState({ sel: { f0: toF(drag.current), f1: toF(clamp(x, box.x, box.x + box.w)) } })
      }}
      onPointerLeave={() => setHover(null)}
      onWheel={(e) => {
        const r = wrap.current!.getBoundingClientRect()
        const x = e.clientX - r.left
        if (!inside(x, e.clientY - r.top)) return
        const f = toF(x), z = e.deltaY < 0 ? 0.8 : 1.25
        let a = f - (f - fmin) * z, b = f + (fmax - f) * z
        if (b - a < 1500) return
        if (b - a >= SPEC.fs) { a = -SPEC.fs / 2; b = SPEC.fs / 2 }
        const sh = a < -SPEC.fs / 2 ? -SPEC.fs / 2 - a : b > SPEC.fs / 2 ? SPEC.fs / 2 - b : 0
        setView({ a: a + sh, b: b + sh })
      }}
      onDoubleClick={() => setView({ a: -SPEC.fs / 2, b: SPEC.fs / 2 })}
      onPointerDown={(e) => {
        const r = wrap.current!.getBoundingClientRect()
        const x = e.clientX - r.left, y = e.clientY - r.top
        if (!inside(x, y)) return
        ;(e.currentTarget as Element).setPointerCapture(e.pointerId)
        drag.current = x
      }}
      onPointerUp={(e) => {
        const r = wrap.current!.getBoundingClientRect()
        if (drag.current !== null && Math.abs(e.clientX - r.left - drag.current) <= 3) setState({ sel: null })
        drag.current = null
      }}
    >
      <canvas ref={cv} style={{ left: 0, top: 0 }} />
      {readout}
    </div>
  )
}
