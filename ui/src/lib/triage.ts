// Content triage: what kind of transmission is in the file, before the decode chain runs.
// Front-end preview using spectral features; the engine runs the calibrated version.

export type Content = 'digital' | 'voice' | 'cw' | 'noise'
export interface Triage { label: Content; conf: number; why: string }

export const CONTENT_TEXT: Record<Content, string> = {
  digital: 'Digital data - continuing to the decode chain',
  voice: 'Analog voice - no digital data to decode',
  cw: 'Carrier / Morse (CW)',
  noise: 'No signal above the noise floor',
}

function fft(re: Float64Array, im: Float64Array) {
  const n = re.length
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1
    for (; j & bit; bit >>= 1) j ^= bit
    j ^= bit
    if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]] }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const a = (-2 * Math.PI) / len
    for (let i = 0; i < n; i += len)
      for (let k = 0; k < len / 2; k++) {
        const wr = Math.cos(a * k), wi = Math.sin(a * k)
        const ur = re[i + k], ui = im[i + k]
        const vr = re[i + k + len / 2] * wr - im[i + k + len / 2] * wi
        const vi = re[i + k + len / 2] * wi + im[i + k + len / 2] * wr
        re[i + k] = ur + vr; im[i + k] = ui + vi
        re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi
      }
  }
}

const median = (a: number[]) => [...a].sort((x, y) => x - y)[a.length >> 1]

/** i/q are the sample streams; q is null for real (audio) data. */
export function triage(i: Float32Array, q: Float32Array | null): Triage | null {
  const N = 1024, frames = Math.min(64, Math.floor(i.length / N))
  if (frames < 8) return null
  const bins = q ? N : N / 2
  const psd = new Float64Array(bins), energy: number[] = [], spectra: Float64Array[] = []
  for (let f = 0; f < frames; f++) {
    const re = new Float64Array(N), im = new Float64Array(N)
    for (let k = 0; k < N; k++) {
      const w = 0.5 - 0.5 * Math.cos((2 * Math.PI * k) / N)
      re[k] = i[f * N + k] * w
      im[k] = q ? q[f * N + k] * w : 0
    }
    fft(re, im)
    const s = new Float64Array(bins)
    let e = 0
    for (let b = 0; b < bins; b++) { s[b] = re[b] * re[b] + im[b] * im[b]; psd[b] += s[b]; e += s[b] }
    spectra.push(s); energy.push(e)
  }
  const arr = Array.from(psd)
  const floor = median(arr) || 1e-30
  const peak = Math.max(...arr)
  const peakDb = 10 * Math.log10(peak / floor)
  const occupied = arr.filter((v) => v > floor * 4).length / bins            // bins > floor + 6 dB
  const top = arr.indexOf(peak)
  let near = 0
  for (let b = Math.max(0, top - 2); b <= Math.min(bins - 1, top + 2); b++) near += arr[b]
  const excess = arr.reduce((s, v) => s + Math.max(0, v - floor), 0) || 1e-30
  const tonal = near / excess                                                 // share of signal energy in one narrow line
  const mE = energy.reduce((a, b) => a + b, 0) / frames
  const cv = Math.sqrt(energy.reduce((a, b) => a + (b - mE) ** 2, 0) / frames) / (mE || 1e-30)

  if (peakDb < 8 || occupied < 0.003) return { label: 'noise', conf: Math.min(0.99, 0.7 + (8 - Math.min(8, peakDb)) / 20), why: `peak only ${peakDb.toFixed(1)} dB above the floor` }
  if (tonal > 0.6) return { label: 'cw', conf: Math.min(0.99, 0.6 + tonal / 2.5), why: `${(tonal * 100).toFixed(0)} % of signal energy in one narrow line${cv > 0.5 ? '; on-off keying seen' : ''}` }
  // speech: energy and spectral shape change syllable by syllable; data stays steady
  let flux = 0
  for (let f = 1; f < frames; f++) {
    let d = 0, t = 0
    for (let b = 0; b < bins; b++) { d += Math.abs(spectra[f][b] - spectra[f - 1][b]); t += spectra[f][b] + spectra[f - 1][b] }
    flux += d / (t || 1e-30)
  }
  flux /= frames - 1
  const voiceScore = Math.min(1, cv / 0.6) * 0.5 + Math.min(1, flux / 0.5) * 0.5
  return voiceScore > 0.55
    ? { label: 'voice', conf: Math.min(0.97, 0.5 + voiceScore / 2), why: `level varies ${(cv * 100).toFixed(0)} % frame to frame; spectrum keeps changing` }
    : { label: 'digital', conf: Math.min(0.97, 0.5 + (1 - voiceScore) / 2), why: `steady occupied band (${(occupied * 100).toFixed(1)} % of span); stable level` }
}
