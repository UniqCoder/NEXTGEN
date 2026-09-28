import { motion } from 'motion/react'
import { Mark } from '../components/ui'
import { Undecided } from '../components/Step'
import { exportJSON } from '../components/Palette'
import { FRAME, SCENARIO, downloadJobCertificate, downloadReceiver, fmtBytes } from '../lib/engine'
import { go } from '../lib/router'
import { useApp } from '../lib/store'

const line = {
  hidden: { opacity: 0, y: 4 },
  show: (i: number) => ({ opacity: 1, y: 0, transition: { delay: 0.05 + i * 0.045, duration: 0.2, ease: [0.2, 0, 0, 1] as const } }),
}

export function Certificate() {
  const proof = useApp((s) => s.proof)
  const fcHz = useApp((s) => s.fcHz)
  const job = useApp((s) => s.job)
  const jobNote = useApp((s) => s.jobNote)
  if (job === 'undecided') return <Undecided reason={jobNote} />
  if (proof !== 'pass')
    return (
      <div className="empty">
        <span className="label">08 — Learn · Decode certificate</span>
        <h2>No certificate yet.</h2>
        <p className="dim">A certificate is issued only after the proof passes: the decoded bits are resynthesised, subtracted, and the residual tests as white noise.</p>
        <button className="btn primary" onClick={() => go('/proof')}>Go to the proof step</button>
      </div>
    )

  const P = SCENARIO.params
  const rows = ['fs', 'baud', 'modulation', 'fec', 'interleaver', 'scrambler', 'snr', 'bw', 'cfo'].map((k) => P[k])
  let i = 0
  const L = (props: { children: React.ReactNode; className?: string }) => (
    <motion.div variants={line} custom={i++} initial="hidden" animate="show" className={props.className}>{props.children}</motion.div>
  )

  return (
    <div className="cert-page">
      <div className="cert-tools no-print">
        <button className="btn ghost sm" onClick={() => go('/proof')}>← Proof</button>
        <span className="small dim" style={{ marginRight: 'auto' }}>Exports for designated sensors</span>
        <button className="btn sm" onClick={() => print()}>PDF</button>
        <button className="btn sm" onClick={() => exportJSON()}>Analysis report (.json)</button>
        {SCENARIO.view.source !== 'demo' && <button className="btn sm" onClick={() => void downloadJobCertificate()}>Signed certificate (.json)</button>}
        <button className="btn sm" onClick={() => exportJSON('sigmf')}>SigMF</button>
        {SCENARIO.view.source !== 'demo' && <button className="btn sm" onClick={() => go('/verify')}>Verify certificate</button>}
        {SCENARIO.view.compiler?.passed && <button className="btn sm primary" onClick={() => void downloadReceiver()}>Receiver (.zip)</button>}
        <button className="btn sm" onClick={() => go('/frames')}>Frames · schema</button>
      </div>

      <article className="cert paper">
        <L className="cert-top">
          <div className="row" style={{ gap: 10 }}><Mark size={22} /><span className="cert-brand">SANJAYA</span></div>
          <div className="cert-id mono">{SCENARIO.cert.id}</div>
        </L>
        <L><h1>Decode certificate</h1></L>
        <L className="cert-verdict">
          <span className="stamp">PROVEN</span>
          <span>The recording is explained to the noise floor by the parameters below. Residual is white Gaussian noise.</span>
        </L>

        <L className="cert-sec"><span className="label">Recording</span></L>
        <L className="kv">
          <span>File</span><span className="mono">{SCENARIO.file.name}</span>
          <span>Size</span><span className="mono">{fmtBytes(SCENARIO.file.size)} · {SCENARIO.file.size.toLocaleString('en-IN')} bytes</span>
          <span>Format</span><span className="mono">{SCENARIO.text.certFormat}</span>
          <span>SHA-256</span><span className="mono hash">{SCENARIO.file.sha256}</span>
          <span>Centre freq.</span><span className="mono">{fcHz ? (fcHz / 1e6).toFixed(4) + ' MHz (analyst entered)' : 'not provided'}</span>
        </L>

        <L className="cert-sec"><span className="label">Proof</span></L>
        <L className="cert-proof">
          <div><span className="label">Explained energy</span><span className="mono big">{SCENARIO.proof.explained}<small>%</small></span></div>
          <div><span className="label">Ljung–Box p</span><span className="mono big">{SCENARIO.proof.ljungP}</span></div>
          <div><span className="label">Residual kurtosis</span><span className="mono big">{SCENARIO.proof.kurt}</span></div>
          <div><span className="label">Residual floor</span><span className="mono big">{SCENARIO.proof.residFloor}<small>dB</small></span></div>
        </L>

        <L className="cert-sec"><span className="label">Signal parameters</span></L>
        <L>
          <table className="cert-table">
            <thead><tr><th>Parameter</th><th>Value</th><th>Method</th><th>Evidence score</th><th>Evidence</th></tr></thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.key}>
                  <td>{p.label}</td>
                  <td className="mono">{p.value}{p.unit ? ' ' + p.unit : ''}</td>
                  <td className="mono">{p.method}</td>
                  <td className="mono">{p.conf !== null ? p.conf.toFixed(2) : '—'}{p.set ? ` · candidates ${p.set}` : ''}</td>
                  <td className="ev">{p.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </L>
        <L className="small dim">Evidence scores and candidate sets are uncalibrated; no 95 % coverage claim has been validated.</L>

        <L className="cert-sec"><span className="label">Frame structure · header and payload</span></L>
        <L className="framebar">
          {FRAME.fields.map((f) => (
            <div key={f.name} style={{ flex: f.len }} className={'fb ' + f.group.toLowerCase()}>
              <span className="mono">{f.name}</span><span className="mono dimmer">{f.len}</span>
            </div>
          ))}
        </L>
        <L className="small dim">{SCENARIO.text.frameLine}</L>

        {SCENARIO.view.compiler && (
          <>
            <L className="cert-sec"><span className="label">Compiled receiver · for the designated sensors</span></L>
            <L className="kv">
              <span>Release gate</span>
              <span className="mono">{SCENARIO.view.compiler.passed
                ? `PASSED · the standalone receiver reproduced SANJAYA's bits exactly: ${SCENARIO.view.compiler.frames_equal}/${SCENARIO.view.compiler.frames} frames, ${SCENARIO.view.compiler.bits_compared?.toLocaleString('en-IN')} bits`
                : `FAILED · not released (${SCENARIO.view.compiler.error ?? 'bits differ'})`}</span>
              <span>Package</span><span className="mono">receiver.py (NumPy only) · recipe.sigmf-meta · sanjaya_receiver.grc (GNU Radio, not executed here)</span>
              {SCENARIO.view.compiler.other_sensors?.map((o) => (
                <span key={o.name} style={{ display: 'contents' }}><span>{o.name}</span><span className="mono">{o.error ? 'receiver error' : `same receiver on this sensor's file: ${o.crc_ok}/${o.frames} CRC-valid frames`}</span></span>
              ))}
            </L>
          </>
        )}

        <L className="cert-sec"><span className="label">Signature</span></L>
        <L className="cert-sig">
          <HashGlyph hex={SCENARIO.file.sha256} />
          <div className="kv" style={{ flex: 1 }}>
            <span>Issued</span><span className="mono">{SCENARIO.cert.issued}</span>
            <span>Signing key</span><span className="mono">{SCENARIO.cert.key}</span>
            <span>Signature</span><span className="mono">{SCENARIO.cert.sig}</span>
            <span>Verify</span><span className="mono">sanjaya verify {SCENARIO.file.path || SCENARIO.file.name} {SCENARIO.cert.id}.json</span>
          </div>
        </L>
        <L className="small dim no-print">Or verify without a terminal: <a href="#/verify">drop this certificate and the recording</a> for an independent, from scratch recheck.</L>
        {SCENARIO.view.source === 'demo' && <L className="cert-foot mono">Preview: signature fields are placeholders until the engine signs certificates.</L>}
      </article>
    </div>
  )
}

/** Visual fingerprint of the file hash: 16 × 16 cells, mirrored. Not a QR code. */
function HashGlyph({ hex }: { hex: string }) {
  const bits = hex.split('').flatMap((c) => parseInt(c, 16).toString(2).padStart(4, '0').split('').map(Number))
  const cells: React.ReactNode[] = []
  for (let y = 0; y < 16; y++)
    for (let x = 0; x < 8; x++)
      if (bits[(y * 8 + x) % bits.length])
        for (const xx of [x, 15 - x]) cells.push(<rect key={`${y}-${xx}`} x={xx * 5} y={y * 5} width={5} height={5} />)
  return (
    <figure className="hashglyph">
      <svg viewBox="0 0 80 80" width="88" height="88" fill="var(--bone-1)" aria-label="Visual fingerprint of the file hash">{cells}</svg>
      <figcaption className="label">SHA-256 glyph</figcaption>
    </figure>
  )
}
