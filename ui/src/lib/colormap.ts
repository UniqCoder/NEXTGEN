// Perceptual ramps as 256-entry RGB LUTs. "valve": ink -> ember -> amber -> bone. "mono": ink -> bone.
type Stop = [number, string]

const VALVE: Stop[] = [
  [0, '#0f0f0d'], [0.22, '#1f1c18'], [0.42, '#4a3a28'], [0.6, '#8d5a26'],
  [0.76, '#e0761c'], [0.9, '#ffab55'], [1, '#fff1dc'],
]
const MONO: Stop[] = [[0, '#0f0f0d'], [0.5, '#6b675e'], [1, '#f3efe4']]
const PAPER: Stop[] = [[0, '#f3f0e8'], [0.35, '#d8c6a8'], [0.65, '#c07a3a'], [0.85, '#7a3a0a'], [1, '#1c1208']]

const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))

function build(stops: Stop[]) {
  const lut = new Uint8Array(256 * 3)
  for (let i = 0; i < 256; i++) {
    const t = i / 255
    let k = 0
    while (k < stops.length - 2 && t > stops[k + 1][0]) k++
    const [t0, c0] = stops[k], [t1, c1] = stops[k + 1]
    const u = Math.min(1, Math.max(0, (t - t0) / (t1 - t0)))
    const a = hex(c0), b = hex(c1)
    for (let c = 0; c < 3; c++) lut[i * 3 + c] = Math.round(a[c] + (b[c] - a[c]) * u)
  }
  return lut
}

export const LUTS = { valve: build(VALVE), mono: build(MONO), paper: build(PAPER) }
export type LutName = keyof typeof LUTS
