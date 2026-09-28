import { useEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import { Conf, MethodTag } from '../components/ui'
import { Terrain } from '../components/TerrainLazy'
import { ingest, type Ingested } from '../lib/ingest'
import { CONTENT_TEXT } from '../lib/triage'
import { ENGINE, HERO_SCENARIO, RECENT, SCENARIO, fmtBytes, ping } from '../lib/engine'
import { go } from '../lib/router'
import { getState, loadSampleLibrary, runAutopilot, runSampleJob, setPending, setState, useApp } from '../lib/store'
import { engineDtype } from '../lib/engine'

const ACCEPT = '.wav,.iq,.cfile,.bin,.raw,.dat,.cu8,.cs8,.cs16,.cf32,.sigmf-data,.sigmf-meta'

export function Ingest() {
  const [over, setOver] = useState(false)
  const [file, setFile] = useState<Ingested | null>(null)
  const [busy, setBusy] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  const dropped = useRef<File | null>(null)
  const sidecar = useRef<string | null>(null)
  const samples = useApp((s) => s.samples)
  useEffect(() => { if (ENGINE.available) void loadSampleLibrary() }, [])
  const runSample = (id: string) => {
    const s = samples.find((s) => s.id === id)
    if (!s) return
    go('/signal')
    runSampleJob(s)
  }

  const take = async (list: FileList | null) => {
    if (!list?.length) return
    setBusy(true)
    const files = Array.from(list)
    dropped.current = files.find((f) => !f.name.endsWith('.sigmf-meta')) ?? null
    const meta = files.find((f) => f.name.endsWith('.sigmf-meta'))
    sidecar.current = meta ? await meta.text() : null
    setPending(dropped.current, { sigmf: sidecar.current })
    setFile(await ingest(files))
    setBusy(false)
  }
  const autopilot = () => { go('/signal'); runAutopilot() }

  return (
    <div className="ingest">
      <div className="hero-bg">
        <Terrain hero k={0} fail={false} floor={-104} span={44} />
        <div className="hero-fade" />
        <div className="hero-cap mono">DRAG TO TURN · SCROLL TO ZOOM · {HERO_SCENARIO.text.heroCap}</div>
      </div>
      <div className="ingest-inner">
        <section className={'hero-left' + (file ? ' wide' : '')}>
        <span className="step-k">Step 1 of 5 · Recording</span>
        <h1 className="ingest-h">Drop a recording.</h1>
        <p className="dim ingest-sub">Drop a .wav or .IQ recording. On supported signals, SANJAYA recovers and proves the receiver recipe; otherwise it shows what was measured and why the decode is undecided.</p>

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
              <button className="btn ghost" onClick={async () => {
                // With a live engine, run the real sample behind the scripted walkthrough instead of the
                // scripted mock timeline - what this button shows should always be a real decode when one
                // is available, never numbers that only look like one. ENGINE.connected/samples are set by
                // a background ping()/loadSampleLibrary() that may not have resolved yet on a fast click, so
                // check for real here rather than trusting whatever they happened to reach by now (that race
                // is what silently fell back to the mock walkthrough even with the engine reachable).
                if (ENGINE.available && !ENGINE.connected) await ping()
                if (ENGINE.connected && getState().samples.length === 0) await loadSampleLibrary()
                const demo = getState().samples.find((s) => s.id === 'syn-qpsk-k7-48x32-12db')
                if (ENGINE.connected && demo) { go('/signal'); runSampleJob(demo); return }
                setPending(null); autopilot()
              }}>Try the demo capture</button>
            </div>
            <input ref={input} type="file" multiple accept={ACCEPT} hidden onChange={(e) => take(e.target.files)} />
          </div>
        ) : (
          <Forensics f={file} file={dropped.current} sidecar={sidecar.current} onReset={() => { setPending(null); setFile(null) }} onRun={autopilot} />
        )}
        </section>

        <section className="usp-grid" aria-label="What SANJAYA demonstrates">
          <div><b>01 · Proof of decode</b><p>Rebuild the waveform, test the residual, and issue a signed certificate that can be checked again.</p></div>
          <div><b>02 · Blind coding search</b><p>Recover the convolutional code, block interleaver and frame fields on supported BPSK/QPSK captures.</p></div>
          <div><b>03 · Enough data?</b><p>Explain undecided results and show when synthetic multisensor captures can be pooled.</p></div>
          <div><b>04 · Receiver export</b><p>Package a receiver only after it reproduces the decoded bits on the source recording.</p></div>
        </section>

        <div className="recent">
          <h2 className="sub-h">{samples.length ? 'Proof ready sample library' : 'Recent recordings'}</h2>
          {samples.length ? (
            <table className="table">
              <tbody>
                {samples.map((s) => (
                  <tr key={s.id} className="hover" tabIndex={0} onClick={() => runSample(s.id)}>
                    <td className="mono">{s.name}</td>
                    <td className="small dim">{s.what}</td>
                    <td className="mono small dimmer">{s.duration_s ? `${s.duration_s.toFixed(1)} s` : ''}</td>
                    <td style={{ textAlign: 'right' }}>
                      <span className={'tag ' + (s.kind === 'stitch' ? 'novel' : 'proven')}>{s.kind === 'stitch' ? 'multisensor' : 'proof demo'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
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
          )}
        </div>
      </div>
    </div>
  )
}

function Forensics({ f, file, sidecar, onReset, onRun }: { f: Ingested; file: File | null; sidecar: string | null; onReset: () => void; onRun: () => void }) {
  const engine = useApp((s) => s.engine)
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
        <form className="fx-override" onSubmit={(e) => {
          e.preventDefault()
          if (fc) setState({ fcHz: parseFloat(fc) * 1e6 || null })
          // the engine reads headers and sidecars itself; the form's values go along only for headerless raw IQ
          const raw = f.route === 'iq' && !sidecar
          setPending(file, { fs: raw && fs ? parseFloat(fs) : null, dtype: raw ? engineDtype(dtype, endian) : null,
            fc: fc ? parseFloat(fc) * 1e6 : null, sigmf: sidecar })
          onRun()
        }}>
          <div className="row between"><span className="label">Override</span><MethodTag m="manual" /></div>
          <p className="small dim">A wrong guess is never silent. Correct anything here and the chain reruns from ingest.</p>
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
            <input className="input" value={fs} placeholder="blank = backsolve" onChange={(e) => setFs(e.target.value)} inputMode="numeric" />
          </label>
          <label className="field"><span className="label">Centre frequency · MHz</span>
            <input className="input" value={fc} placeholder="unknown" onChange={(e) => setFc(e.target.value)} inputMode="decimal" />
          </label>
          <button className="btn primary lg" type="submit">{f.content && f.content.label !== 'digital' ? 'Run Autopilot anyway' : 'Run Autopilot'}</button>
          <button className="btn ghost sm" type="button" onClick={onReset}>Choose another file</button>
          {engine === 'demo' && <p className="small caution-note">Engine not connected: Autopilot runs on the demo capture, so you can walk the full flow.</p>}
        </form>
      </div>
    </motion.div>
  )
}
