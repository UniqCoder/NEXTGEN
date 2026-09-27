import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Panel, Seg } from '../components/ui'
import { DisplayMenu, Step } from '../components/Step'
import { Waterfall, type Overlay } from '../components/Waterfall'
import { Terrain } from '../components/Terrain'
import { SCENARIO, gauss, prng } from '../lib/engine'
import { css, prep, useSize } from '../lib/plot'
import { go } from '../lib/router'
import { prove, setState, skipProof, useApp } from '../lib/store'

const HOW = ['Re-encode the decoded bits', 'Re-modulate with the measured parameters', 'Subtract from the recording', 'Test whether what is left is white noise']

export function Proof() {
  const proof = useApp((s) => s.proof)
  const k = useApp((s) => s.proofT)
  const override = useApp((s) => s.modOverride)
  const view3d = useApp((s) => s.view3d)
  const floor = useApp((s) => s.floor)
  const span = useApp((s) => s.span)
  const upstream = useApp((s) => s.stages.slice(0, 6).every((x) => x === 'done' || x === 'override'))
  const wrong = override !== null && override !== SCENARIO.params.modulation.value
  const fail = proof === 'fail' || (proof === 'running' && wrong)
  const P = SCENARIO.proof
  const e1 = SCENARIO.emitters[0]
  const overlays: Overlay[] = [{
    ...e1, alpha: 1,
    label: proof === 'pass' ? 'E1 · PROVEN' : `E1 · ${override ?? SCENARIO.text.mod} · ${SCENARIO.text.baud} Bd`,
    tone: proof === 'pass' ? 'proof' : fail ? 'bone' : 'signal',
  }]

  const lede =
    proof === 'pass' ? <>Proven. The decoded signal accounts for <b>{P.explained} %</b> of the recorded energy, and what is left is white noise.</> :
    proof === 'fail' ? <>Not proven. <b>{override}</b> leaves {(100 - P.failExplained).toFixed(0)} % of the energy unexplained, so that hypothesis is rejected.</> :
    proof === 'running' ? 'Rebuilding the waveform and subtracting it from the recording…' :
    'Rebuild the waveform from the decoded bits and subtract it from the recording. If only noise is left, every parameter is proven.'

  return (
    <Step
      n={5}
      title="Proof"
      lede={lede}
      actions={
        <>
          {proof === 'pass' && (
            <Seg value={k >= 1 ? 'res' : 'rec'} onChange={(v) => setState({ proofT: v === 'res' ? 1 : 0 })}
              options={[{ v: 'rec', label: 'Recording' }, { v: 'res', label: 'Residual' }]} label="Waterfall source" />
          )}
          <Seg value={view3d ? '3d' : '2d'} onChange={(v) => setState({ view3d: v === '3d' })} options={[{ v: '2d', label: '2D' }, { v: '3d', label: '3D' }]} label="Waterfall view" />
          <DisplayMenu />
        </>
      }
      back={{ to: '/frames', label: 'Header & payload' }}
      next={{ to: '/certificate', label: 'View certificate', disabled: proof !== 'pass' }}
    >
      <div className="prf">
        <Panel title="Waterfall" alt={(proof === 'pass' && k >= 1 ? 'residual after subtraction' : 'recording') + (view3d ? ' · height is power, each ridge is a transmitter' : '')} style={{ gridArea: 'wf' }}>
          {view3d
            ? <Terrain k={k} fail={fail} floor={floor} span={span} />
            : <Waterfall k={k} target={fail ? 'fail' : 'resid'} floor={floor} span={span} overlays={overlays} failBand={fail} />}
        </Panel>

        <section className={'prf-side ' + proof} style={{ gridArea: 'side' }}>
          <h2>How the proof works</h2>
          <ol className="how">
            {HOW.map((h, i) => {
              const at = (i + 1) / HOW.length - 0.05
              const state = proof === 'idle' ? '' : k >= at ? (i === 3 && proof === 'fail' ? 'bad' : 'ok') : proof === 'running' && k >= at - 0.25 ? 'now' : ''
              return (
                <li key={h} className={state}>
                  <span className="how-n mono">{i + 1}</span>
                  <span>{h}</span>
                </li>
              )
            })}
          </ol>

          <div className="hist-wrap">
            <ResidualHist k={k} fail={fail} />
            <div className="row between small dimmer"><span>Residual amplitude</span><span>line = pure noise</span></div>
          </div>

          {proof === 'idle' && (
            <p className="small dim">Watch the waterfall. If the decode is right, the orange signal band sinks into the noise and the histogram becomes a single bell curve.</p>
          )}

          <AnimatePresence mode="wait">
            {(proof === 'pass' || proof === 'fail') && (
              <motion.div key={proof} className="metrics" initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <Metric k="Energy explained" v={(proof === 'pass' ? P.explained : P.failExplained).toFixed(1) + ' %'} good={proof === 'pass'} />
                <Metric k="Whiteness (Ljung–Box p)" v={proof === 'pass' ? P.ljungP.toFixed(2) : '< 0.001'} good={proof === 'pass'} />
                <Metric k="Kurtosis (noise = 3.00)" v={proof === 'pass' ? P.kurt.toFixed(2) : '1.71'} good={proof === 'pass'} />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="prf-act">
            {proof === 'running' && (
              <>
                <div className="bar"><span style={{ width: `${k * 100}%` }} /></div>
                <button className="btn ghost sm" onClick={skipProof}>Skip animation · Esc</button>
              </>
            )}
            {proof === 'idle' && (
              <button className="btn primary lg" style={{ width: '100%' }} disabled={!upstream} onClick={prove}>
                Prove the decode <span className="kbd" style={{ color: 'inherit', borderColor: 'currentColor', opacity: 0.6 }}>P</span>
              </button>
            )}
            {proof === 'fail' && (
              <div className="verdict bad">
                <p>The loop goes back to <b>Signal</b> and tries the next-best hypothesis.</p>
                <div className="row wrap">
                  <button className="btn primary" onClick={() => { setState({ modOverride: null }); prove() }}>Retry with QPSK</button>
                  <button className="btn ghost" onClick={() => go('/signal')}>Back to Signal</button>
                </div>
              </div>
            )}
            {proof === 'pass' && (
              <div className="verdict good">
                <span className="tag proven">Proven</span>
                <p>A signed decode certificate is ready.</p>
                <button className="btn ghost sm" onClick={prove}>Run again</button>
              </div>
            )}
            {!upstream && proof === 'idle' && <p className="small dim">Finish the earlier steps first.</p>}
          </div>
        </section>
      </div>
    </Step>
  )
}

function Metric({ k, v, good }: { k: string; v: string; good: boolean }) {
  return (
    <div className="metric">
      <span className="small dim">{k}</span>
      <span className={'mono metric-v ' + (good ? 'proof' : 'fault')}>{v}</span>
    </div>
  )
}

/** Residual amplitude histogram: two humps while the signal remains, one Gaussian once it is explained. */
function ResidualHist({ k, fail }: { k: number; fail: boolean }) {
  const wrap = useRef<HTMLDivElement>(null)
  const cv = useRef<HTMLCanvasElement>(null)
  const { w, h } = useSize(wrap)
  const theme = useApp((s) => s.theme)
  useEffect(() => {
    if (!cv.current || w < 10) return
    const ctx = prep(cv.current, w, h)
    const rnd = prng(3)
    const bins = 48, hist = new Float32Array(bins)
    const left = fail ? 1 - 0.62 * k : 1 - k
    for (let i = 0; i < 6000; i++) {
      const sym = rnd() < 0.5 ? -1 : 1
      const v = sym * 1.6 * left + gauss(rnd) * 0.8
      const b = Math.floor(((v + 4) / 8) * bins)
      if (b >= 0 && b < bins) hist[b]++
    }
    const mx = Math.max(...hist)
    const bw = w / bins
    ctx.fillStyle = fail && k > 0.9 ? css('--fault') : css('--bone-3')
    hist.forEach((c, i) => ctx.fillRect(i * bw + 0.5, h - (c / mx) * (h - 4), bw - 1, (c / mx) * (h - 4)))
    ctx.strokeStyle = k > 0.98 && !fail ? css('--proof') : css('--bone-1')
    ctx.lineWidth = 1.2
    ctx.beginPath()
    for (let i = 0; i <= 100; i++) {
      const x = -4 + (i / 100) * 8
      const px = (i / 100) * w, py = h - Math.exp(-(x * x) / (2 * 0.64)) * (h - 4)
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)
    }
    ctx.stroke()
  }, [w, h, k, fail, theme])
  return (
    <div ref={wrap} style={{ position: 'relative', height: 72 }}>
      <canvas ref={cv} style={{ position: 'absolute', inset: 0 }} />
    </div>
  )
}
