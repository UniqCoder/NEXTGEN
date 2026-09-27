import { useRef, useState } from 'react'
import { ENGINE, verifyCertificate, type VerifyResult } from '../lib/engine'

/** Independent re-check: drop a certificate.json and its recording, get "reproduced" or exactly why not.
 * Re-derives every statistic from the file and the certified recipe alone — no search, no trust in the engine
 * that issued it. This is the PRD's `sanjaya verify`, reachable from the UI (Tools > Verify). */
export function Verify() {
  const [cert, setCert] = useState<File | null>(null)
  const [rec, setRec] = useState<File | null>(null)
  const [sidecar, setSidecar] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<VerifyResult | { error: string } | null>(null)
  const [over, setOver] = useState(false)
  const input = useRef<HTMLInputElement>(null)

  const take = (list: FileList | null) => {
    if (!list?.length) return
    setResult(null)
    for (const f of Array.from(list)) {
      if (f.name.endsWith('.sigmf-meta')) setSidecar(f)
      else if (f.name.endsWith('.json')) setCert(f)
      else setRec(f)
    }
  }

  const run = async () => {
    if (!cert || !rec) return
    setBusy(true)
    setResult(null)
    try {
      const sigmfMeta = sidecar ? await sidecar.text() : undefined
      setResult(await verifyCertificate(cert, rec, { sigmfMeta }))
    } catch (e) {
      setResult({ error: String(e) })
    } finally {
      setBusy(false)
    }
  }

  const reset = () => { setCert(null); setRec(null); setSidecar(null); setResult(null) }

  return (
    <div className="verify-page">
      <header className="step-intro">
        <span className="step-k">Independent re-check</span>
        <h1>Verify a certificate.</h1>
        <p className="lede">Drop a decode certificate and its recording (and its .sigmf-meta sidecar, if it has one). Every statistic is
          re-derived from the file and the certified recipe alone — no search, and no trust placed in whichever machine issued it.</p>
      </header>

      {ENGINE.available ? (
        <>
          <div
            className={'drop' + (over ? ' over' : '')}
            onDragOver={(e) => { e.preventDefault(); setOver(true) }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => { e.preventDefault(); setOver(false); take(e.dataTransfer.files) }}
          >
            <i className="c tl" /><i className="c tr" /><i className="c bl" /><i className="c br" />
            <span className="drop-t">{over ? 'Release to load' : 'Drop certificate.json + recording here'}</span>
            <span className="small dimmer">Optional: drop the .sigmf-meta sidecar too</span>
            <div className="row" style={{ marginTop: 10 }}>
              <button className="btn" onClick={() => input.current?.click()}>Choose files</button>
              {(cert || rec) && <button className="btn ghost" onClick={reset}>Clear</button>}
            </div>
            <input ref={input} type="file" multiple hidden accept=".json,.wav,.iq,.sigmf-data,.sigmf-meta,.cf32,.bin"
              onChange={(e) => take(e.target.files)} />
          </div>

          <div className="kv" style={{ marginTop: 16, maxWidth: 560 }}>
            <span>Certificate</span><span className="mono">{cert?.name ?? 'not chosen'}</span>
            <span>Recording</span><span className="mono">{rec?.name ?? 'not chosen'}</span>
            <span>Sidecar</span><span className="mono">{sidecar?.name ?? 'none'}</span>
          </div>

          <button className="btn primary lg" style={{ marginTop: 16 }} disabled={!cert || !rec || busy} onClick={() => void run()}>
            {busy ? 'Verifying…' : 'Verify'}
          </button>

          {result && 'error' in result && <p className="small caution-note" style={{ marginTop: 16 }}>{result.error}</p>}
          {result && !('error' in result) && (
            <div className={'verify-result' + (result.reproduced ? ' pass' : ' fail')} style={{ marginTop: 20 }}>
              <span className="stamp">{result.reproduced ? 'REPRODUCED' : 'NOT REPRODUCED'}</span>
              <div className="kv" style={{ marginTop: 12 }}>
                <span>Certificate</span><span className="mono">{result.certificate_id}</span>
                <span>Verdict claimed</span><span className="mono">{result.verdict ?? '—'}</span>
                <span>Signature</span><span className="mono">{result.signature}</span>
              </div>
              {result.problems.length > 0 && (
                <ul className="small" style={{ marginTop: 10 }}>
                  {result.problems.map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              )}
            </div>
          )}
        </>
      ) : (
        <p className="dim">Verify needs a connected engine (open this page from `sanjaya serve`).</p>
      )}
    </div>
  )
}
