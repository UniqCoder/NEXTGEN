import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Mark } from '../components/ui'
import { go } from '../lib/router'

const OPTIONS: Record<string, string[]> = {
  Modulation: ['BPSK', 'QPSK', '8PSK', '16QAM', '2-FSK', '4-FSK'],
  'Symbol rate': ['1 200 Bd', '2 400 Bd', '4 800 Bd'],
  Interleaver: ['Block 24 × 16', 'Block 48 × 32', 'Convolutional 12 × 17', 'Diagonal 32', 'Pseudo-random (lib #7)'],
  FEC: ['CC K=7 r½', 'RS(255,223)', 'RS ∘ CC concatenated', 'LDPC (648,324)'],
  Scrambler: ['None', '1 + x¹⁴ + x¹⁵', '1 + x⁴ + x⁷'],
  'Frame sync': ['0xFAF320', '0x1ACFFC1D', '0x7E'],
}
const KEYS = Object.keys(OPTIONS)
const STAGE_OF = [2, 1, 4, 4, 4, 5] // pipeline stage that recovers each row

type Phase = 'setup' | 'locked' | 'running' | 'done' | 'revealed'

export function Challenge() {
  const [phase, setPhase] = useState<Phase>('setup')
  const [picks, setPicks] = useState<Record<string, string>>(() => Object.fromEntries(KEYS.map((k) => [k, OPTIONS[k][Math.floor(Math.random() * OPTIONS[k].length)]])))
  const [stage, setStage] = useState(-1)
  const [t, setT] = useState(0)
  const t0 = useRef(0)

  useEffect(() => {
    if (phase !== 'running') return
    t0.current = performance.now()
    const ids: number[] = []
    for (let s = 0; s <= 7; s++) ids.push(window.setTimeout(() => setStage(s), 700 + s * 900))
    ids.push(window.setTimeout(() => setPhase('done'), 700 + 8 * 900))
    const iv = window.setInterval(() => setT((performance.now() - t0.current) / 1000), 100)
    return () => { ids.forEach(clearTimeout); clearInterval(iv) }
  }, [phase])

  const recovered = (i: number) => phase === 'done' || phase === 'revealed' || (phase === 'running' && stage >= STAGE_OF[i])
  const matches = KEYS.length

  return (
    <div className="challenge">
      <header className="ch-top">
        <div className="row" style={{ gap: 12 }}>
          <Mark size={22} />
          <span className="label" style={{ fontSize: 11 }}><b>SANJAYA</b> · Mystery-signal challenge</span>
        </div>
        <div className="mono ch-timer">{t.toFixed(1).padStart(5, '0')}<span className="unit">s</span></div>
        <div className="row">
          {phase === 'setup' && <button className="btn primary" onClick={() => setPhase('locked')}>Hide &amp; lock picks</button>}
          {phase === 'locked' && <button className="btn primary" onClick={() => { setStage(-1); setT(0); setPhase('running') }}>Generate &amp; analyse</button>}
          {phase === 'done' && <button className="btn primary" onClick={() => setPhase('revealed')}>Reveal</button>}
          {phase === 'revealed' && <button className="btn" onClick={() => { setPhase('setup'); setStage(-1); setT(0) }}>New challenge</button>}
          <button className="btn ghost" onClick={() => go('/signal')}>Exit</button>
        </div>
      </header>

      <div className="ch-body">
        <section className="ch-col">
          <div className="ch-h"><span className="label">Judge's blind picks</span><span className="label">{phase === 'setup' ? 'choose, then lock' : phase === 'revealed' ? 'revealed' : 'hidden'}</span></div>
          {KEYS.map((k) => (
            <div key={k} className="ch-row">
              <span className="label">{k}</span>
              {phase === 'setup' ? (
                <select className="select" value={picks[k]} onChange={(e) => setPicks({ ...picks, [k]: e.target.value })} aria-label={k}>
                  {OPTIONS[k].map((o) => <option key={o}>{o}</option>)}
                </select>
              ) : (
                <AnimatePresence mode="wait">
                  {phase === 'revealed' ? (
                    <motion.span key="v" className="mono ch-v" initial={{ rotateX: 90, opacity: 0 }} animate={{ rotateX: 0, opacity: 1 }} transition={{ delay: KEYS.indexOf(k) * 0.12, duration: 0.25 }}>{picks[k]}</motion.span>
                  ) : (
                    <motion.span key="h" className="mono ch-v masked" exit={{ rotateX: -90, opacity: 0 }} transition={{ duration: 0.15 }}>● ● ● ● ● ●</motion.span>
                  )}
                </AnimatePresence>
              )}
            </div>
          ))}
        </section>

        <section className="ch-mid">
          <div className="ch-stages">
            {['Observe', 'Measure', 'Hypothesise', 'Demodulate', 'Unwrap', 'Structure', 'Prove', 'Learn'].map((s, i) => (
              <div key={s} className={'ch-st' + (stage >= i ? ' on' : '') + (stage === i && phase === 'running' ? ' now' : '')}>
                <span className="mono">{String(i + 1).padStart(2, '0')}</span>
                <span>{s}</span>
              </div>
            ))}
          </div>
          <div className="ch-verdict">
            {phase === 'revealed' ? (
              <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.8 }}>
                <span className="mono ch-score proof">{matches} / {KEYS.length}</span>
                <span className="label">recovered blind in {t.toFixed(1)} s · proof passed</span>
              </motion.div>
            ) : phase === 'running' ? (
              <span className="label">Analysing a file SANJAYA has never seen</span>
            ) : phase === 'done' ? (
              <span className="label"><b className="proof">Proof passed.</b> Ready to reveal.</span>
            ) : (
              <span className="label">{phase === 'setup' ? 'The judge chooses every parameter of the transmission' : 'Picks locked. The generator will build the file.'}</span>
            )}
          </div>
        </section>

        <section className="ch-col">
          <div className="ch-h"><span className="label">SANJAYA recovered</span><span className="label">blind</span></div>
          {KEYS.map((k, i) => (
            <div key={k} className="ch-row">
              <span className="label">{k}</span>
              <span className="row" style={{ gap: 10 }}>
                {recovered(i) ? (
                  <motion.span className="mono ch-v" initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}>{picks[k]}</motion.span>
                ) : (
                  <span className="mono ch-v dimmer">{phase === 'running' ? 'searching…' : '—'}</span>
                )}
                {phase === 'revealed' && (
                  <motion.span className="tag proven" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 + i * 0.12 }}>Match</motion.span>
                )}
              </span>
            </div>
          ))}
        </section>
      </div>
      <footer className="ch-foot label">Preview · recovery is simulated in the front-end until the engine and generator are connected.</footer>
    </div>
  )
}
