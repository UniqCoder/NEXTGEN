import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Panel } from '../components/ui'
import { Waterfall, type Overlay } from '../components/Waterfall'
import { SCENARIO, fmtHz } from '../lib/engine'
import { go } from '../lib/router'
import { setState, useApp } from '../lib/store'

export function Scene() {
  const cancelled = useApp((s) => s.cancelled)
  const taught = useApp((s) => s.taught)
  const [k, setK] = useState(cancelled.includes('E1') ? 1 : 0)
  const [teaching, setTeaching] = useState(false)
  const revealed = cancelled.includes('E1') && k >= 1

  const cancel = () => {
    const t0 = performance.now()
    const dur = matchMedia('(prefers-reduced-motion: reduce)').matches ? 1 : 1500
    const tick = () => {
      const t = Math.min(1, (performance.now() - t0) / dur)
      setK(t)
      if (t < 1) requestAnimationFrame(tick)
      else setState((s) => ({ cancelled: [...s.cancelled, 'E1'] }))
    }
    requestAnimationFrame(tick)
  }
  const restore = () => { setK(0); setState({ cancelled: [] }) }

  const em = SCENARIO.emitters
  if (em.length < 4) return <DetectedOnly />
  const overlays: Overlay[] = [
    { ...em[0], label: 'E1 · QPSK 2400 Bd', alpha: 1 - k, tone: 'signal' },
    { ...em[1], label: taught ? 'E2 · LFM-CHIRP (taught)' : 'E2 · NOVEL', alpha: 1, tone: taught ? 'bone' : 'novel' },
    { ...em[2], label: 'E3 · CW', alpha: 1, tone: 'bone' },
    { ...em[3], label: 'E4 · RTTY 50 / 450', alpha: revealed ? 1 : 0, tone: 'signal' },
  ]
  const count = revealed ? 4 : 3

  return (
    <div className="scene">
      <Panel title="Scene" alt="wideband detection · OS-CFAR"
        tools={
          <>
            <span className="label"><b>{count}</b> emitters{revealed ? ' · 1 revealed by cancellation' : ''}</span>
            {revealed || k > 0 ? <button className="btn sm" onClick={restore}>Restore E1</button> : null}
          </>
        }>
        <Waterfall k={k} target="resid" floor={-104} span={40} overlays={overlays} />
      </Panel>

      <aside className="scene-list">
        <div className="insp-h"><span className="label">Emitters</span><span className="label">sorted by energy</span></div>

        <EmitterCard id="E1" title="QPSK · 2400 Bd" sub={band(em[0].f0, em[0].f1)} snr={em[0].snr}
          tags={<><span className="tag blind">Blind</span><span className="tag plain">No named standard</span></>}
          state={k >= 1 ? 'cancelled' : k > 0 ? 'cancelling' : 'decoded'}>
          <div className="row wrap">
            <button className="btn sm" onClick={() => { setState({ sel: { f0: em[0].f0, f1: em[0].f1 } }); go('/signal') }}>Open in Signal</button>
            <button className="btn sm primary" disabled={k > 0} onClick={cancel}>Prove &amp; cancel</button>
          </div>
          <p className="dim small">Cancellation subtracts the proven resynthesis, then reruns detection on the residual.</p>
        </EmitterCard>

        <AnimatePresence>
          {revealed && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} transition={{ duration: 0.4, ease: [0.2, 0, 0, 1] }}>
              <EmitterCard id="E4" title="2-FSK · 50 Bd · 450 Hz" sub={band(em[3].f0, em[3].f1)} snr={em[3].snr}
                tags={<><span className="tag blind">Blind</span><span className="tag library">RTTY 50 / 450 · 0.93</span></>}
                state="revealed">
                <p className="small"><span className="signal">Revealed.</span> 12.9 dB below E1 and inside its band, so it was invisible until E1 was cancelled.</p>
                <button className="btn sm" onClick={() => go('/signal')}>Demodulate</button>
              </EmitterCard>
            </motion.div>
          )}
        </AnimatePresence>

        <EmitterCard id="E2" title={taught ? 'LFM-CHIRP' : 'Unknown'} sub={band(em[1].f0, em[1].f1)} snr={em[1].snr}
          tags={taught ? <><span className="tag manual">Taught · 5 shots</span><span className="tag plain">Local class</span></> : <span className="tag novel">Novel</span>}
          state={taught ? 'classified' : 'novel'}>
          {!taught && (
            <>
              <p className="small">Outside every known class. Closest known: <span className="mono">none</span> (open set score 0.97). Bursts every 31.4 s, linear sweep 5 kHz / 3.5 s.</p>
              {!teaching ? (
                <button className="btn sm" onClick={() => setTeaching(true)}>Teach this class…</button>
              ) : (
                <Teach onDone={() => { setTeaching(false); setState({ taught: true }) }} onCancel={() => setTeaching(false)} />
              )}
            </>
          )}
          {taught && <p className="small dim">Stored in local mission memory. Future captures with this pattern will be recognised.</p>}
        </EmitterCard>

        <EmitterCard id="E3" title="CW · unmodulated carrier" sub={fmtHz(-17500, 3) + ' ± 3 Hz drift'} snr={em[2].snr}
          tags={<span className="tag blind">Blind</span>} state="measured">
          <p className="small dim">Stable carrier; likely a reference or beacon. No data to decode.</p>
        </EmitterCard>

        {!revealed && (
          <div className="ghost-card">
            <span className="label">Residual rescan</span>
            <p className="small dimmer">Weaker emitters can hide under strong ones. Cancel a proven emitter to rescan what is underneath.</p>
          </div>
        )}
      </aside>
    </div>
  )
}

const band = (f0: number, f1: number) => `${(f0 / 1e3).toFixed(2)} → ${(f1 / 1e3).toFixed(2)} kHz`

function EmitterCard(props: { id: string; title: string; sub: string; snr: number; tags: React.ReactNode; state: string; children?: React.ReactNode }) {
  return (
    <div className={'em ' + props.state}>
      <div className="row between">
        <span className="row" style={{ gap: 10 }}>
          <span className="mono em-id">{props.id}</span>
          <span className="em-title">{props.title}</span>
        </span>
        <span className="label">{props.state}</span>
      </div>
      <div className="row between" style={{ marginTop: 4 }}>
        <span className="mono small dim">{props.sub}</span>
        <span className="mono small">{props.snr.toFixed(1)}<span className="unit">dB SNR</span></span>
      </div>
      <div className="row wrap" style={{ marginTop: 8, gap: 6 }}>{props.tags}</div>
      {props.children && <div className="em-body">{props.children}</div>}
    </div>
  )
}

function Teach({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [picked, setPicked] = useState<number[]>([0, 1, 2])
  const [name, setName] = useState('LFM-CHIRP')
  return (
    <div className="teach">
      <span className="label">Select 5 example bursts</span>
      <div className="shots">
        {Array.from({ length: 8 }, (_, i) => (
          <button key={i} className={'shot' + (picked.includes(i) ? ' on' : '')} aria-pressed={picked.includes(i)}
            onClick={() => setPicked((p) => (p.includes(i) ? p.filter((x) => x !== i) : p.length < 5 ? [...p, i] : p))}>
            <svg viewBox="0 0 40 24" width="100%" height="100%" aria-hidden>
              <path d={`M4 ${20 - (i % 3)} L36 ${4 + (i % 2)}`} stroke="currentColor" strokeWidth="2" opacity="0.9" />
            </svg>
            <span className="mono">{(10 + i * 31.4).toFixed(0)}s</span>
          </button>
        ))}
      </div>
      <div className="row" style={{ marginTop: 8 }}>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} aria-label="Class name" style={{ flex: 1 }} />
        <button className="btn sm primary" disabled={picked.length < 5 || !name.trim()} onClick={onDone}>Learn · {picked.length}/5</button>
        <button className="btn sm ghost" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  )
}

/** Engine results: the emitters actually detected; multi-emitter detection (R-17) and cancellation (P2) come later. */
function DetectedOnly() {
  const em = SCENARIO.emitters
  const overlays: Overlay[] = em.map((e) => ({ ...e, label: `${e.id} · ${e.cls}`, alpha: 1, tone: 'signal' as const }))
  return (
    <div className="scene">
      <Panel title="Scene" alt="emitters in this recording" tools={<span className="label"><b>{em.length}</b> emitter{em.length === 1 ? '' : 's'}</span>}>
        <Waterfall k={0} target="resid" floor={SCENARIO.view.floor} span={SCENARIO.view.span} overlays={overlays} />
      </Panel>
      <aside className="scene-list">
        <div className="insp-h"><span className="label">Emitters</span><span className="label">from the engine</span></div>
        {em.map((e) => (
          <EmitterCard key={e.id} id={e.id} title={e.cls} sub={band(e.f0, e.f1)} snr={e.snr}
            tags={<><span className="tag blind">Blind</span><span className="tag plain">{e.std}</span></>} state="decoded">
            <p className="dim small">Wideband multiemitter detection (R-17) and successive cancellation (P2) are not in this engine build yet.</p>
          </EmitterCard>
        ))}
      </aside>
    </div>
  )
}
