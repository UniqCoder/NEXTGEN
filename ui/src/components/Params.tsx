import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { SCENARIO, bandOf, fmtHz } from '../lib/engine'
import { setState, useApp } from '../lib/store'
import { Conf, MethodTag, Seg } from './ui'

/** Extracted parameters as a readable list; click a row to see the evidence behind it. */
export function Params({ keys }: { keys: string[] }) {
  const stages = useApp((s) => s.stages)
  const mode = useApp((s) => s.mode)
  const override = useApp((s) => s.modOverride)
  const fcHz = useApp((s) => s.fcHz)
  const [open, setOpen] = useState<string | null>(null)

  return (
    <div className="params">
      {keys.map((key) => {
        const p = SCENARIO.params[key]
        if (!p) return null                             // not measured on this job (e.g. undecided: only a few params exist)
        // an undecided job never marks its stages "done" (the search stopped partway); its params are still final
        const ready = stages[p.stage] === 'done' || stages[p.stage] === 'override' || key === 'fc' || SCENARIO.view.verdict === 'undecided'
        const isOpen = open === key
        let value = p.value, unit = p.unit, method = p.method
        if (key === 'modulation' && override) { value = override; method = 'manual' }
        if (key === 'fc' && fcHz) { value = fmtHz(fcHz, 4); unit = undefined }
        return (
          <div key={key} className={'prm' + (isOpen ? ' open' : '') + (ready ? '' : ' wait')}>
            <button className="prm-top" onClick={() => setOpen(isOpen ? null : key)} aria-expanded={isOpen} disabled={!ready}>
              <span className="prm-l">{p.label}</span>
              {ready ? (
                <motion.span className="prm-v" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.18 }}>
                  <span className="mono prm-num">{value}</span>
                  {unit && <span className="unit">{unit}</span>}
                  {key === 'fc' && fcHz && <span className="tag plain" style={{ marginLeft: 8 }}>{bandOf(fcHz)}</span>}
                </motion.span>
              ) : (
                <span className="prm-v small dimmer">measuring…</span>
              )}
              <span className="prm-meta">
                {ready && p.conf !== null && !(key === 'modulation' && override) && <Conf p={p.conf} width={32} />}
                {ready && <MethodTag m={method} />}
              </span>
            </button>
            <AnimatePresence initial={false}>
              {isOpen && ready && (
                <motion.div className="prm-ev" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.18, ease: [0.2, 0, 0, 1] }}>
                  {p.cands && (
                    <div className="cands">
                      {p.cands.map((c) => (
                        <div key={c.v} className="cand">
                          <span className="mono">{c.v}</span>
                          <span className="bar"><span style={{ width: `${c.p * 100}%` }} /></span>
                          <span className="mono dim">{c.p.toFixed(2)}</span>
                        </div>
                      ))}
                      {p.set && <div className="small dim" style={{ marginTop: 4 }}>Candidate set (uncalibrated): <span className="mono">{p.set}</span></div>}
                    </div>
                  )}
                  <p>{p.evidence}</p>
                  {key === 'modulation' && mode === 'expert' && SCENARIO.view.source === 'demo' && (
                    <div className="row" style={{ marginTop: 10 }}>
                      <span className="small dim">Override</span>
                      <Seg value={override ?? 'auto'} onChange={(v) => setState({ modOverride: v === 'auto' ? null : v })}
                        options={[{ v: 'auto', label: 'Auto' }, { v: 'QPSK', label: 'QPSK' }, { v: '8PSK', label: '8PSK' }, { v: 'OQPSK', label: 'OQPSK' }]} />
                    </div>
                  )}
                  {key === 'fc' && (
                    <form className="row" style={{ marginTop: 10 }} onSubmit={(e) => {
                      e.preventDefault()
                      const v = parseFloat((new FormData(e.currentTarget).get('mhz') as string) || '')
                      setState({ fcHz: isFinite(v) && v > 0 ? v * 1e6 : null })
                    }}>
                      <input name="mhz" className="input" placeholder="e.g. 6.2450" defaultValue={fcHz ? fcHz / 1e6 : ''} style={{ width: 120 }} aria-label="Centre frequency in MHz" />
                      <span className="unit">MHz</span>
                      <button className="btn sm" type="submit">Set</button>
                    </form>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}
