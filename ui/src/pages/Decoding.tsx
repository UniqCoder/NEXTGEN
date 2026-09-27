import { useState } from 'react'
import { motion } from 'motion/react'
import { Conf, MethodTag, Panel, Scrub } from '../components/ui'
import { Step } from '../components/Step'
import { Sufficiency } from '../components/Sufficiency'
import { RankProfile } from '../components/Plots'
import { CONV_CANDIDATES, FEC_FAMILIES, INTERLEAVER_TYPES, SCENARIO } from '../lib/engine'
import { useApp } from '../lib/store'


export function Decoding() {
  const undecided = useApp((s) => s.job === 'undecided')
  if (undecided) return <Step n={3} title="Decoding" lede={null} back={{ to: '/signal', label: 'Signal' }} next={{ to: '/frames', label: 'Continue to header & payload', disabled: true }}>{null}</Step>
  return <DecodingReady />
}

/** Everything below assumes a recipe was found: SCENARIO.text.chain, ilRows/ilCols etc. are only ever
 * populated once a job decodes (build_partial has none of it) — kept in its own component so Decoding()
 * can bail out above before any of these hooks run. */
function DecodingReady() {
  const expert = useApp((s) => s.mode === 'expert')
  const done = useApp((s) => s.stages[4] === 'done')
  const [ilType, setIlType] = useState('Block')
  const T = SCENARIO.text
  const CHAIN = T.chain
  const [rows, setRows] = useState(T.ilRows)
  const [cols, setCols] = useState(T.ilCols)

  return (
    <Step
      n={3}
      title="Decoding"
      lede={done
        ? <>The bits were protected by a <b>{T.codeKind}</b> and shuffled by a <b>{T.ilKind}</b>. Both were identified from the signal alone and undone: {T.decodeLine}.</>
        : 'Waiting for the signal to be demodulated…'}
      back={{ to: '/signal', label: 'Signal' }}
      next={{ to: '/frames', label: 'Continue to header & payload', disabled: !done }}
    >
      <div className="dec">
        <section className="chain" style={{ gridArea: 'chain' }}>
          <div className="chain-row">
            {CHAIN.map((c, i) => (
              <motion.div key={c.n} className="node" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06, duration: 0.2 }}>
                <span className="small dimmer">{c.role}</span>
                <span className="node-n">{c.n}</span>
                <span className="row between"><span className="mono node-v">{c.v}</span><MethodTag m={c.m} /></span>
                {i < CHAIN.length - 1 && <span className="flow" aria-hidden />}
              </motion.div>
            ))}
          </div>
          <div className="concat">
            <span className="concat-br" />
            <span className="small dim">{T.fecLine}</span>
          </div>
        </section>

        <Panel title="De-interleaving" alt="which interleaver, and its size" style={{ gridArea: 'il' }}
          tools={expert ? (
            <span className="row" style={{ gap: 6 }}>
              <Scrub k="ROWS" value={rows} min={2} max={256} onChange={setRows} />
              <Scrub k="COLS" value={cols} min={2} max={256} onChange={setCols} />
              {(rows !== T.ilRows || cols !== T.ilCols) && <span className="tag manual">Override</span>}
            </span>
          ) : <span className="mono small dim">{T.ilLabel}</span>}>
          <div className="il">
            <div className="il-types">
              {INTERLEAVER_TYPES.map((t) => (
                <button key={t.name} className={'il-type' + (t.name === ilType ? ' on' : '') + (t.score > 0.5 ? ' found' : '')}
                  disabled={!expert && t.name !== ilType} onClick={() => setIlType(t.name)} aria-pressed={t.name === ilType}
                  title={expert ? 'Select to force this interleaver type' : t.note}>
                  <span className="row between"><span className="il-n">{t.name}</span><MethodTag m={t.method} /></span>
                  <Conf p={t.score} width={70} />
                </button>
              ))}
            </div>
            <div className="il-plot">
              <span className="small dim" style={{ padding: '10px 14px 0' }}>Rank of the bit stream at each candidate period. The dip marks the interleaver.</span>
              <div style={{ position: 'relative', flex: 1 }}><RankProfile /></div>
            </div>
          </div>
        </Panel>

        <Panel title="Error correction" alt="FEC" style={{ gridArea: 'fec' }} pad>
          <div className="fams">
            {FEC_FAMILIES.map((f) => (
              <div key={f.name} className={'fam' + (f.score > 0.5 ? ' found' : '')}>
                <span className="row between"><span className="fam-n">{f.name}</span><MethodTag m={f.method} /></span>
                <span className="mono small">{f.found}</span>
              </div>
            ))}
          </div>
          <h3 className="sub-h">Convolutional code search <span className="dim">· lower syndrome weight is better</span></h3>
          <table className="table">
            <thead><tr><th>K</th><th>Rate</th><th>Generators</th><th>Syndrome weight</th></tr></thead>
            <tbody>
              {CONV_CANDIDATES.slice(0, 3).map((c, i) => (
                <tr key={i} className={i === 0 ? 'best' : ''}>
                  <td className="mono">{c.k}</td>
                  <td className="mono">{c.r}</td>
                  <td className="mono">{c.g}</td>
                  <td>
                    <span className="row" style={{ gap: 8 }}>
                      <span className="synbar"><span style={{ width: `${c.syn * 190}%` }} /></span>
                      <span className="mono small">{c.syn.toFixed(3)}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small dim" style={{ marginTop: 12 }}>LDPC was searched for (n ≤ 1024 and library matrices) and is not present. It is reported as absent, not guessed.</p>
        </Panel>

        <section className="strip" style={{ gridArea: 'strip' }}>
          <div className="strip-item">
            <span className="small dim">Scrambler</span>
            <span className="mono">{T.scrText}</span>
            <span className="small dimmer">{T.scrNote}</span>
          </div>
          <div className="strip-lfsr"><Lfsr /></div>
          <div className="strip-item">
            <span className="small dim">Phase ambiguity</span>
            <span className="mono">{T.phaseText}</span>
            <span className="small dimmer">{T.phaseNote}</span>
          </div>
        </section>
      </div>
      {done && <Sufficiency />}
    </Step>
  )
}

/** 15-cell LFSR with feedback taps at 14 and 15. */
function Lfsr() {
  const { seed, taps } = SCENARIO.text.lfsr
  if (!seed) return null
  const cw = 22, x0 = 10, y0 = 34
  const cx = (cell: number) => x0 + (cell - 1) * cw + 9                // centre of 1-indexed cell
  const lo = Math.min(...taps), hi = Math.max(...taps), xm = (cx(lo) + cx(hi)) / 2
  return (
    <svg viewBox={`0 0 ${x0 * 2 + cw * seed.length} 74`} width="100%" style={{ maxHeight: 90, display: 'block' }} aria-label={`LFSR diagram, taps ${taps.join(' and ')}`}>
      {seed.split('').map((b, i) => (
        <g key={i}>
          <rect x={x0 + i * cw + 0.5} y={y0} width={cw - 3} height={20} fill={b === '1' ? 'var(--bone-1)' : 'var(--ink-0)'} stroke={taps.includes(i + 1) ? 'var(--signal)' : 'var(--line-3)'} />
          <text x={x0 + i * cw + (cw - 3) / 2} y={y0 + 34} textAnchor="middle" fontFamily="Martian Mono" fontSize="7.5" fill="var(--bone-3)">{i + 1}</text>
        </g>
      ))}
      {/* taps to XOR, feedback into cell 1 */}
      <path d={taps.map((c) => `M${cx(c)} ${y0} V16`).join(' ') + ` M${cx(lo)} 16 H${cx(hi)}`} stroke="var(--signal)" fill="none" />
      <circle cx={xm} cy={10} r={6} fill="var(--ink-1)" stroke="var(--signal)" />
      <path d={`M${xm - 4} 10 h8 M${xm} 6 v8`} stroke="var(--signal)" />
      <path d={`M${xm - 6} 10 H${x0 + 9} V${y0 - 2}`} stroke="var(--signal)" fill="none" markerEnd="url(#ah)" />
      <defs><marker id="ah" markerWidth="6" markerHeight="6" refX="3" refY="5" orient="auto"><path d="M0 0 L3 5 L6 0" fill="none" stroke="var(--signal)" /></marker></defs>
    </svg>
  )
}
