import { useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion, useAnimationControls } from 'motion/react'
import { Panel } from '../components/ui'
import { Step } from '../components/Step'
import { Autocorr } from '../components/Plots'
import { FRAME, SCENARIO, bitstream, columnStats, crcSearch, findSync } from '../lib/engine'
import { css, prep, useSize } from '../lib/plot'
import { useApp } from '../lib/store'

const KIND_VAR: Record<string, string> = { const: '--signal', counter: '--signal-2', random: '--bone-3', crc: '--bone-1' }

export function Frames() {
  const undecided = useApp((s) => s.job === 'undecided')
  if (undecided) return <Step n={4} title="Header & payload" lede={null} back={{ to: '/decoding', label: 'Decoding' }}>{null}</Step>
  return <FramesReady />
}

/** Assumes a recipe was found (FRAME.len > 0, a real bitstream): kept separate so Frames() can bail
 * out above before any of these hooks run (build_partial has no frame/bits to work with). */
function FramesReady() {
  const autopilot = useApp((s) => s.mode === 'autopilot')
  const doneStage = useApp((s) => s.stages[5] === 'done')
  const { stream } = useMemo(bitstream, [])
  const sync = useMemo(() => findSync(stream), [stream])
  const crc = useMemo(() => crcSearch(stream, sync), [stream, sync])
  // Autopilot arrives with the answer; Expert starts from the raw stream
  const [w, setW] = useState(autopilot ? FRAME.len : FRAME.len - 19)
  const [phase, setPhase] = useState(() => (autopilot ? findSync(bitstream().stream) : 0))
  const [snapFlash, setSnapFlash] = useState(0)
  const shake = useAnimationControls()
  const locked = w === FRAME.len
  const aligned = locked && phase === sync
  const stats = useMemo(() => columnStats(stream, w, phase), [stream, w, phase])

  const snap = () => {
    setSnapFlash(performance.now())
    shake.start({ x: [0, -2, 1.5, 0], transition: { duration: 0.16, ease: 'linear' } })
  }
  const animateTo = (to: number, set: (v: number) => void, from: number, done?: () => void) => {
    const t0 = performance.now(), dur = 700
    const tick = () => {
      const t = Math.min(1, (performance.now() - t0) / dur)
      const e = 1 - Math.pow(1 - t, 3)
      set(Math.round(from + (to - from) * e))
      if (t < 1) requestAnimationFrame(tick)
      else done?.()
    }
    requestAnimationFrame(tick)
  }

  const pay = FRAME.fields.filter((f) => f.group === 'PAYLOAD')
  const payFrom = pay.length ? pay[0].start : 0, payTo = pay.length ? pay[pay.length - 1].start + pay[pay.length - 1].len : 0
  const crcField = FRAME.fields.find((f) => f.kind === 'crc')
  const bits = (g: string) => FRAME.fields.filter((f) => f.group === g).reduce((s, f) => s + f.len, 0)
  const names = (g: string) => FRAME.fields.filter((f) => f.group === g).map((f) => (f.name === 'LEN' ? 'length' : f.name.toLowerCase())).join(', ')
  const encrypted = pay.some((f) => /encrypted/.test(f.note))
  const counterOk = useMemo(() => {
    const ctr = FRAME.fields.find((f) => f.kind === 'counter')
    let ok = 0, n = 0
    if (!ctr) return { ok, n }
    const mod = 2 ** ctr.len
    for (let k = 1; sync + (k + 1) * FRAME.len <= stream.length; k++, n++) {
      const rd = (s: number) => { let v = 0; for (let i = 0; i < ctr.len; i++) v = v * 2 + stream[s + ctr.start + i]; return v }
      if (rd(sync + k * FRAME.len) === (rd(sync + (k - 1) * FRAME.len) + 1) % mod) ok++
    }
    return { ok, n }
  }, [stream, sync])
  const payloadEnt = useMemo(() => {
    if (!aligned || payTo <= payFrom) return null
    let s = 0
    for (let c = payFrom; c < payTo; c++) s += stats.ent[c]
    return s / (payTo - payFrom)
  }, [aligned, stats, payFrom, payTo])

  const replay = () => {
    const w0 = FRAME.len - 19
    setW(w0); setPhase(0)
    setTimeout(() => animateTo(FRAME.len, setW, w0, () => { snap(); setTimeout(() => animateTo(sync, setPhase, 0), 350) }), 400)
  }

  return (
    <Step
      n={4}
      title="Header & payload"
      lede={aligned
        ? <>Frames repeat every <b>{FRAME.len} bits</b>. The <b>header</b> is {bits('HEADER')} bits ({names('HEADER')}). The <b>payload</b> is {bits('PAYLOAD')} bits of {encrypted ? 'high entropy data, likely encrypted' : 'data'}.{crcField ? ` A CRC-${crcField.len} closes each frame.` : ''}</>
        : locked ? `The frame length is ${FRAME.len} bits. Now align to the sync word so the fields can be labelled.`
        : 'Find the frame length to group the decoded bits into rows; then align the repeating header.'}
      back={{ to: '/decoding', label: 'Decoding' }}
      next={{ to: '/proof', label: 'Continue to proof', disabled: !doneStage }}
      extra={
        <>
          <button className="btn ghost sm" disabled={!aligned} onClick={() => dl('frame.ksy', ksy(), 'text/yaml')}>Export schema</button>
          <button className="btn ghost sm" onClick={() => dl('frames.txt', rasterText(stream, sync), 'text/plain')}>Export frames</button>
        </>
      }
    >
      <div className="frm">
        <Panel title="Decoded bits by frame" alt="repeating columns reveal structure" style={{ gridArea: 'raster' }}
          tools={
            <>
              <span className="mono small dim">{w} bits per row</span>
              {aligned ? (
                <button className="btn sm" onClick={replay}>Replay discovery</button>
              ) : (
                <>
                  <button className="btn sm" disabled={locked} onClick={() => animateTo(FRAME.len, setW, w, snap)}>Find frame length</button>
                  <button className="btn sm" disabled={!locked} onClick={() => animateTo(sync, setPhase, phase)}>Align header</button>
                </>
              )}
            </>
          }>
          <div className="lens">
            <div className="lens-head">
              <AnimatePresence>
                {aligned && (
                  <motion.div className="brackets" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
                    <Bracket from={0} to={payFrom} total={w} label="HEADER" big />
                    {payTo > payFrom && <Bracket from={payFrom} to={payTo} total={w} label="PAYLOAD" big />}
                    {crcField && <Bracket from={crcField.start} to={crcField.start + crcField.len} total={w} label="CRC" big />}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <p className="lens-guide">{aligned
              ? 'Each row is one frame. Orange columns repeat in the header; varied grey columns carry payload bits. The top strip shows how much each bit position changes.'
              : 'Each row groups consecutive decoded bits. Find the row length, then align the repeating header to reveal the fields.'}</p>
            <motion.div className="lens-body" animate={shake}>
              <Raster stream={stream} w={w} phase={phase} ent={stats.ent} aligned={aligned} flash={snapFlash} />
            </motion.div>
            <div className="lens-foot small dim">
              <span>{stats.rows} frames × {w} bits</span>
              <span>{aligned ? 'Header and payload boundaries shown above' : 'Use the buttons above to group and align frames'}</span>
            </div>
          </div>
        </Panel>

        <div className="frm-side" style={{ gridArea: 'side' }}>
          <Panel title="Autocorrelation" alt="peaks = frame length" style={{ height: 190, flex: 'none' }}>
            <Autocorr />
          </Panel>

          <section className="card">
            <h2>Fields</h2>
            <table className="table fields">
              <tbody>
                {FRAME.fields.map((f) => (
                  <tr key={f.name} className={aligned ? '' : 'muted'}>
                    <td style={{ width: 18 }}><span className="swatch" style={{ background: `var(${KIND_VAR[f.kind]})` }} /></td>
                    <td><span className="mono">{f.name}</span><div className="small dimmer">{f.group.toLowerCase()} · {f.len} bits</div></td>
                    <td className="small dim">
                      {f.kind === 'counter' ? `+1 per frame, ${counterOk.ok}/${counterOk.n}` :
                       f.kind === 'random' && payloadEnt !== null ? `entropy ${payloadEnt.toFixed(3)} bits/bit` :
                       f.kind === 'crc' ? `verifies on ${crc[0].ok}/${crc[0].frames} frames` : f.note}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2>Checksum</h2>
            <p className="small"><span className="mono">{crc[0].name}</span>, poly <span className="mono">0x{crc[0].poly.toString(16).toUpperCase()}</span>, init <span className="mono">0x{crc[0].init.toString(16).toUpperCase()}</span>. Found by trying {crc.length} polynomial and init pairs on this stream.</p>
            <details className="small dim">
              <summary>Show the search</summary>
              <table className="table" style={{ marginTop: 6 }}>
                <tbody>
                  {crc.slice(0, 4).map((c, i) => (
                    <tr key={c.name + c.init} className={i === 0 ? 'best' : ''}>
                      <td className="mono small">{c.name}</td>
                      <td className="mono small">init 0x{c.init.toString(16).toUpperCase().padStart(4, '0')}</td>
                      <td className="mono small">{c.ok}/{c.frames}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </section>

          <section className="card enc">
            <h2>Payload</h2>
            <p className="small">High entropy, likely encrypted or compressed. SANJAYA recovers the frame structure; decrypting the payload is out of scope by design.</p>
          </section>
        </div>
      </div>
    </Step>
  )
}

function Bracket({ from, to, total, label, big }: { from: number; to: number; total: number; label: string; big?: boolean }) {
  return (
    <div className={'bracket' + (big ? ' big' : '')} style={{ left: `${(from / total) * 100}%`, width: `${((to - from) / total) * 100}%` }}>
      <span>{label}</span>
    </div>
  )
}

function Raster({ stream, w, phase, ent, aligned, flash }: { stream: Uint8Array; w: number; phase: number; ent: Float32Array; aligned: boolean; flash: number }) {
  const wrap = useRef<HTMLDivElement>(null)
  const cv = useRef<HTMLCanvasElement>(null)
  const { w: W, h: H } = useSize(wrap)
  const theme = useApp((s) => s.theme)
  useEffect(() => {
    if (!cv.current || W < 10) return
    let raf = 0
    const draw = () => {
      const ctx = prep(cv.current!, W, H)
      const entH = 26
      const rows = Math.floor((stream.length - phase) / w)
      const cw = W / w, rh = Math.min(7, (H - entH - 6) / rows)
      const kindAt = (c: number) => FRAME.fields.find((f) => c >= f.start && c < f.start + f.len)!.kind
      const colours = Object.fromEntries(Object.entries(KIND_VAR).map(([k, v]) => [k, css(v)]))
      const on = css('--bone-1'), dim = css('--bone-3')
      // entropy strip
      for (let c = 0; c < w; c++) {
        const e = ent[c]
        ctx.fillStyle = aligned ? colours[kindAt(c)] : dim
        ctx.globalAlpha = aligned ? 0.9 : 0.7
        ctx.fillRect(c * cw, entH - e * (entH - 2), Math.max(1, cw - 0.5), e * (entH - 2) + 0.5)
      }
      ctx.globalAlpha = 1
      ctx.fillStyle = css('--line-2'); ctx.fillRect(0, entH + 2, W, 1)
      // raster
      const y0 = entH + 6
      for (let y = 0; y < rows; y++)
        for (let c = 0; c < w; c++) {
          if (!stream[phase + y * w + c]) continue
          ctx.fillStyle = aligned ? colours[kindAt(c)] : on
          ctx.globalAlpha = aligned && kindAt(c) === 'random' ? 0.55 : 0.88
          ctx.fillRect(c * cw, y0 + y * rh, Math.max(1, cw - (cw > 3 ? 1 : 0)), Math.max(1, rh - (rh > 3 ? 1 : 0)))
        }
      ctx.globalAlpha = 1
      // detent flash
      const age = (performance.now() - flash) / 400
      if (flash && age < 1) {
        ctx.fillStyle = css('--signal')
        ctx.globalAlpha = 0.18 * (1 - age)
        ctx.fillRect(0, y0, W, rows * rh)
        ctx.globalAlpha = 1
        raf = requestAnimationFrame(draw)
      }
    }
    draw()
    return () => cancelAnimationFrame(raf)
  }, [W, H, stream, w, phase, ent, aligned, flash, theme])
  return (
    <div ref={wrap} className="plot">
      <canvas ref={cv} role="img" aria-label={`${Math.floor((stream.length - phase) / w)} decoded frames, ${w} bits per row. ${aligned ? 'Header columns repeat at the start; payload columns vary.' : 'Frame alignment pending.'}`} />
    </div>
  )
}

function ksy() {
  const hexBytes = (v: number, bits: number) => {
    const out: string[] = []
    for (let i = bits - 8; i >= 0; i -= 8) out.push('0x' + (Math.floor(v / 2 ** i) % 256).toString(16).padStart(2, '0'))
    return out.join(', ')
  }
  const lines = FRAME.fields.map((f) => {
    const id = f.name.toLowerCase().replace(/[^a-z0-9]+/g, '_')
    if (f.name === 'SYNC' && f.len % 8 === 0) return `  - id: ${id}\n    contents: [${hexBytes(FRAME.sync, f.len)}]`
    if (f.kind === 'random' && f.len % 8 === 0) return `  - id: ${id}\n    size: ${f.len / 8}\n    doc: ${f.note}`
    return `  - id: ${id}\n    type: b${f.len}\n    doc: ${f.note}`
  })
  return `meta:
  id: sanjaya_frame
  title: Frame recovered from ${SCENARIO.file.name}
  endian: be
  bit-endian: be
seq:
${lines.join('\n')}
`
}

function rasterText(stream: Uint8Array, sync: number) {
  const out: string[] = []
  for (let s = sync; s + FRAME.len <= stream.length; s += FRAME.len) out.push(Array.from(stream.slice(s, s + FRAME.len)).join(''))
  return out.join('\n')
}

function dl(name: string, text: string, type: string) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([text], { type }))
  a.download = name
  a.click()
}
