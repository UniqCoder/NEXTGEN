import { useEffect, useRef, useState } from 'react'
import { ENGINE, SCENARIO, downloadJobCertificate, loadJobRecording, loadJobSidecar, verifyCertificate, type VerifyResult } from '../lib/engine'
import { getPending } from '../lib/store'

/** Independent re-check: drop a certificate.json and its recording, get "reproduced" or exactly why not.
 * Re-derives every statistic from the file and the certified recipe alone — no search, no trust in the engine
 * that issued it. This is the PRD's `sanjaya verify`, reachable from the UI (Tools > Verify). */
export function Verify() {
  const [cert, setCert] = useState<File | null>(null)
  const [rec, setRec] = useState<File | null>(null)
  const [sidecar, setSidecar] = useState<File | null>(null)
  const [selectedMeta, setSelectedMeta] = useState<string | null>(null)
  const [selectedFs, setSelectedFs] = useState<number | undefined>()
  const [selectedDtype, setSelectedDtype] = useState<string | undefined>()
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<VerifyResult | { error: string } | null>(null)
  const [over, setOver] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  const changedRecording = useRef(false)

  useEffect(() => {
    let active = true
    const selected = getPending()
    if (selected) {
      setRec(selected.file)
      setSelectedMeta(selected.opts.sigmf ?? null)
      setSelectedFs(selected.opts.fs ?? undefined)
      setSelectedDtype(selected.opts.dtype ?? undefined)
    } else if (ENGINE.job) {
      void loadJobRecording().then((file) => { if (active && !changedRecording.current) setRec(file) }).catch(() => {})
      void loadJobSidecar().then((meta) => { if (active && !changedRecording.current) setSelectedMeta(meta) })
    }
    return () => { active = false }
  }, [])

  const take = (list: FileList | null) => {
    if (!list?.length) return
    setResult(null)
    const files = Array.from(list)
    const nextRec = files.find((f) => !f.name.endsWith('.sigmf-meta') && !f.name.endsWith('.json'))
    if (nextRec) {
      changedRecording.current = true
      setRec(nextRec)
      setSelectedMeta(null)
      setSelectedFs(undefined)
      setSelectedDtype(undefined)
      setSidecar(null)
    }
    const nextMeta = files.find((f) => f.name.endsWith('.sigmf-meta'))
    if (nextMeta) setSidecar(nextMeta)
    const nextCert = files.find((f) => f.name.endsWith('.json'))
    if (nextCert) setCert(nextCert)
  }

  const run = async () => {
    if (!cert || !rec) return
    setBusy(true)
    setResult(null)
    try {
      const sigmfMeta = sidecar ? await sidecar.text() : selectedMeta ?? undefined
      setResult(await verifyCertificate(cert, rec, { sigmfMeta, fs: selectedFs, dtype: selectedDtype }))
    } catch (e) {
      setResult({ error: String(e) })
    } finally {
      setBusy(false)
    }
  }

  const reset = () => { changedRecording.current = true; setCert(null); setRec(null); setSidecar(null); setSelectedMeta(null); setSelectedFs(undefined); setSelectedDtype(undefined); setResult(null) }

  return (
    <div className="verify-page">
      <header className="step-intro">
        <span className="step-k">Independent recheck</span>
        <h1>Verify a certificate.</h1>
        <p className="lede">Choose a signed decode certificate. The active recording and its sidecar are selected automatically; you can replace them to check another file. Every statistic is rederived from the file and certified recipe.</p>
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
            <span className="drop-t">{over ? 'Release to load' : rec ? 'Drop the signed certificate here' : 'Drop certificate + recording here'}</span>
            <span className="small dimmer">{rec ? 'The selected recording is ready below' : 'Optional: include its .sigmf-meta sidecar'}</span>
            <div className="row" style={{ marginTop: 10 }}>
              <button className="btn" onClick={() => input.current?.click()}>{rec ? 'Choose certificate' : 'Choose files'}</button>
              {ENGINE.job && SCENARIO.view.verdict === 'pass' && <button className="btn ghost" onClick={() => void downloadJobCertificate()}>Download signed certificate</button>}
              {(cert || rec) && <button className="btn ghost" onClick={reset}>Clear</button>}
            </div>
            <input ref={input} type="file" multiple hidden accept=".json,.wav,.iq,.sigmf-data,.sigmf-meta,.cf32,.bin"
              onChange={(e) => take(e.target.files)} />
          </div>

          <div className="kv" style={{ marginTop: 16, maxWidth: 560 }}>
            <span>Certificate</span><span className="mono">{cert?.name ?? 'not chosen'}</span>
            <span>Recording</span><span className="mono">{rec?.name ?? 'not chosen'}</span>
            <span>Sidecar</span><span className="mono">{sidecar?.name ?? (selectedMeta ? 'from selected recording' : 'none')}</span>
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
