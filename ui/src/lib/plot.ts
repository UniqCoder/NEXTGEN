import { useEffect, useState, type RefObject } from 'react'

export function useSize(ref: RefObject<HTMLElement | null>) {
  const [size, setSize] = useState({ w: 0, h: 0 })
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => {
      const { width, height } = e.contentRect
      setSize({ w: Math.floor(width), h: Math.floor(height) })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [ref])
  return size
}

/** Size a canvas for the device pixel ratio and return a context in CSS pixels. */
export function prep(c: HTMLCanvasElement, w: number, h: number) {
  const dpr = Math.min(2, devicePixelRatio || 1)
  if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) {
    c.width = Math.round(w * dpr)
    c.height = Math.round(h * dpr)
    c.style.width = w + 'px'
    c.style.height = h + 'px'
  }
  const ctx = c.getContext('2d')!
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)
  return ctx
}

export const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

export function ticks(min: number, max: number, count = 6) {
  const span = max - min
  const raw = span / count
  const mag = Math.pow(10, Math.floor(Math.log10(raw)))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= count) ?? 10 * mag
  const out: number[] = []
  for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) out.push(+v.toFixed(10))
  return out
}

export interface Box { x: number; y: number; w: number; h: number }

export const MONO_FONT = '8.5px "Martian Mono", ui-monospace, monospace'

/** Axis frame: hairline box, ticks outside, labels in the mono face. */
export function axes(
  ctx: CanvasRenderingContext2D,
  b: Box,
  x: { min: number; max: number; fmt: (v: number) => string; count?: number; title?: string } | null,
  y: { min: number; max: number; fmt: (v: number) => string; count?: number; title?: string; flip?: boolean } | null,
  grid = true,
) {
  const line = css('--line'), lbl = css('--bone-3'), line2 = css('--line-2')
  ctx.font = MONO_FONT
  ctx.lineWidth = 1
  if (x) {
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    for (const v of ticks(x.min, x.max, x.count ?? 6)) {
      const px = Math.round(b.x + ((v - x.min) / (x.max - x.min)) * b.w) + 0.5
      if (grid) { ctx.strokeStyle = line; ctx.beginPath(); ctx.moveTo(px, b.y); ctx.lineTo(px, b.y + b.h); ctx.stroke() }
      ctx.strokeStyle = line2
      ctx.beginPath(); ctx.moveTo(px, b.y + b.h); ctx.lineTo(px, b.y + b.h + 4); ctx.stroke()
      ctx.fillStyle = lbl
      ctx.fillText(x.fmt(v), px, b.y + b.h + 6)
    }
    if (x.title) { ctx.textAlign = 'right'; ctx.fillStyle = css('--bone-4'); ctx.fillText(x.title, b.x + b.w, b.y + b.h + 18) }
  }
  if (y) {
    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    for (const v of ticks(y.min, y.max, y.count ?? 4)) {
      const t = (v - y.min) / (y.max - y.min)
      const py = Math.round(y.flip ? b.y + t * b.h : b.y + b.h - t * b.h) + 0.5
      if (grid) { ctx.strokeStyle = line; ctx.beginPath(); ctx.moveTo(b.x, py); ctx.lineTo(b.x + b.w, py); ctx.stroke() }
      ctx.strokeStyle = line2
      ctx.beginPath(); ctx.moveTo(b.x - 4, py); ctx.lineTo(b.x, py); ctx.stroke()
      ctx.fillStyle = lbl
      ctx.fillText(y.fmt(v), b.x - 6, py)
    }
    if (y.title) {
      ctx.textAlign = 'left'; ctx.textBaseline = 'top'
      ctx.fillStyle = css('--bone-4'); ctx.fillText(y.title, b.x + 4, b.y + 3)
    }
  }
  ctx.strokeStyle = line2
  ctx.strokeRect(b.x + 0.5, b.y + 0.5, b.w - 1, b.h - 1)
}

export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v))
export const smooth = (t: number) => t * t * (3 - 2 * t)

/** Per-row dissolve weight: a front sweeping down the waterfall as proof progresses. */
export const sweep = (k: number, row01: number, w = 0.28) => smooth(clamp((k * (1 + w) - row01) / w))
