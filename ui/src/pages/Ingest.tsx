import { useRef, useState } from 'react'
import { motion } from 'motion/react'
import { Conf, MethodTag } from '../components/ui'
import { Terrain } from '../components/Terrain'
import { ingest, type Ingested } from '../lib/ingest'
import { CONTENT_TEXT } from '../lib/triage'
import { RECENT, SCENARIO, fmtBytes } from '../lib/mock'
import { go } from '../lib/router'
import { runAutopilot, setState } from '../lib/store'

const ACCEPT = '.wav,.iq,.cfile,.bin,.raw,.dat,.cu8,.cs8,.cs16,.cf32,.sigmf-data,.sigmf-meta'

export function Ingest() {
  const [over, setOver] = useState(false)
  const [file, setFile] = useState<Ingested | null>(null)
  const [busy, setBusy] = useState(false)
  const input = useRef<HTMLInputElement>(null)

  const take = async (list: FileList | null) => {
    if (!list?.length) return
    setBusy(true)
    setFile(await ingest(Array.from(list)))
    setBusy(false)
  }
  const autopilot = () => { go('/signal'); runAutopilot() }

  return (
    <div className="ingest">
      <div className="hero-bg" aria-hidden>
        <Terrain hero k={0} fail={false} floor={-104} span={44} />
        <div className="hero-fade" />
        <div className="hero-cap mono">LIVE REPLAY · {SCENARIO.file.name} · 48 kHz · 251 s</div>
      </div>
      <div className="ingest-inner">
        <section className={'hero-left' + (file ? ' wide' : '')}>
        <span className="step-k">Step 1 of 5 · Recording</span>
        <h1 className="ingest-h">Drop a recording.</h1>
        <p className="dim ingest-sub">.wav or raw .IQ, from any sensor. SANJAYA works out the rest, and nothing leaves this machine.</p>

        {!file ? (
          <div
            className={'drop' + (over ? ' over' : '')}
            onDragOver={(e) => { e.preventDefault(); setOver(true) }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => { e.preventDefault(); setOver(false); take(e.dataTransfer.files) }}
          >
            <i className="c tl" /><i className="c tr" /><i className="c bl" /><i className="c br" />
            <span className="drop-t">{busy ? 'Reading header…' : over ? 'Release to analyse' : 'Drop .wav or .IQ here'}</span>
            <span className="small dimmer">Optional: drop a .sigmf-meta sidecar with it</span>
            <div className="row" style={{ marginTop: 18 }}>
              <button className="btn" onClick={() => input.current?.click()}>Choose file</button>
              <button className="btn ghost" onClick={autopilot}>Try the demo capture</button>
            </div>
            <input ref={input} type="file" multiple accept={ACCEPT} hidden onChange={(e) => take(e.target.files)} />
          </div>
        ) : (
          <Forensics f={file} onReset={() => setFile(null)} onRun={autopilot} />
        )}
        </section>

        <div className="recent">
          <h2 className="sub-h">Recent recordings</h2>
          <table className="table">
            <tbody>
              {RECENT.map((r) => (
                <tr key={r.name} className={r.name === SCENARIO.file.name ? 'hover' : ''} tabIndex={r.name === SCENARIO.file.name ? 0 : undefined} onClick={() => r.name === SCENARIO.file.name && go('/signal')}>
                  <td className="mono">{r.name}</td>
                  <td className="mono small dim">{fmtBytes(r.size)}</td>
                  <td className="mono small dim">{r.fmt}</td>
                  <td className="small dim">{r.note}</td>
                  <td className="mono small dimmer">{r.when}</td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={'tag ' + (r.verdict === 'proven' ? 'proven' : r.verdict === 'novel' ? 'novel' : 'plain')}>{r.verdict}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function Forensics({ f, onReset, onRun }: { f: Ingested; onReset: () => void; onRun: () => void }) {
  const [dtype, setDtype] = useState(f.guess.dtype)
  const [endian, setEndian] = useState(f.guess.endian)
  const [order, setOrder] = useState(f.guess.order)
  const [interp, setInterp] = useState(f.guess.interp)
  const [fs, setFs] = useState(f.guess.fs ? String(f.guess.fs) : '')
  const [fc, setFc] = useState(f.guess.fc ? String(f.guess.fc / 1e6) : '')
  return (
    <motion.div className="forensics" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
      <div className="fx-head">
        <div>
          <div className="mono" style={{ fontSize: 15 }}>{f.name}</div>
          <div className="mono small dim">{fmtBytes(f.size)}</div>
        </div>
        <span className={'route ' + f.route}>{f.route === 'wav' ? 'WAV · header read' : 'Raw IQ · format inferred'}</span>
      </div>
      {f.content && (
        <div className={'content-banner ' + f.content.label}>
          <span className="small dim">What is in this file</span>
          <b>{CONTENT_TEXT[f.content.label]}</b>
          <Conf p={f.content.conf} width={48} />
          <span className="small dim">{f.content.why}</span>
        </div>
      )}
      <div className="fx-grid">
        <table className="table">
          <tbody>
            {f.findings.map((x, i) => (
              <tr key={i}>
                <td className="label" style={{ width: 130 }}>{x.k}</td>
                <td className="mono small">{x.v}{x.note && <div className="dimmer" style={{ marginTop: 2 }}>{x.note}</div>}</td>
                <td style={{ width: 110 }}>{x.conf !== null && <Conf p={x.conf} width={40} />}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <form className="fx-override" onSubmit={(e) => { e.preventDefault(); if (fc) setState({ fcHz: parseFloat(fc) * 1e6 || null }); onRun() }}>
          <div className="row between"><span className="label">Override</span><MethodTag m="manual" /></div>
          <p className="small dim">A wrong guess is never silent. Correct anything here and the chain re-runs from ingest.</p>
          {f.route === 'iq' && (
            <>
              <label className="field"><span className="label">Sample type</span>
                <select className="select" value={dtype} onChange={(e) => setDtype(e.target.value)}>
                  {['ci16', 'cf32', 'cu8', 'ci8', 'ci32'].map((d) => <option key={d}>{d}</option>)}
                </select>
              </label>
              <div className="row">
                <label className="field" style={{ flex: 1 }}><span className="label">Endianness</span>
                  <select className="select" value={endian} onChange={(e) => setEndian(e.target.value as 'LE' | 'BE')}><option>LE</option><option>BE</option></select>
                </label>
                <label className="field" style={{ flex: 1 }}><span className="label">Order</span>
                  <select className="select" value={order} onChange={(e) => setOrder(e.target.value as 'IQ' | 'QI')}><option>IQ</option><option>QI</option></select>
                </label>
              </div>
            </>
          )}
          {f.route === 'wav' && (
            <label className="field"><span className="label">Interpretation</span>
              <select className="select" value={interp} onChange={(e) => setInterp(e.target.value as 'real' | 'iq')}>
                <option value="iq">2 channels as complex I/Q</option>
                <option value="real">Real audio</option>
              </select>
            </label>
          )}
          <label className="field"><span className="label">Sample rate · Hz</span>
            <input className="input" value={fs} placeholder="blank = back-solve" onChange={(e) => setFs(e.target.value)} inputMode="numeric" />
          </label>
          <label className="field"><span className="label">Centre frequency · MHz</span>
            <input className="input" value={fc} placeholder="unknown" onChange={(e) => setFc(e.target.value)} inputMode="decimal" />
          </label>
          <button className="btn primary lg" type="submit">{f.content && f.content.label !== 'digital' ? 'Run Autopilot anyway' : 'Run Autopilot'}</button>
          <button className="btn ghost sm" type="button" onClick={onReset}>Choose another file</button>
          <p className="small caution-note">Engine not connected: Autopilot runs on the demo capture, so you can walk the full flow.</p>
        </form>
      </div>
    </motion.div>
  )
}
