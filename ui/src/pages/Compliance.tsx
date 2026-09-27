import { go } from '../lib/router'

// The design brief, clause by clause, with where each one lives in the UI.
const ROWS = [
  { c: 'Input: .IQ or .wav', where: 'Ingest', to: '/ingest', what: 'Both accepted; route shown (WAV header read vs raw IQ inferred); manual override form; SigMF sidecar read' },
  { c: '(i) Sampling frequency', where: 'Step 2 · Signal', to: '/signal', what: 'File sample rate and symbol rate, both labelled, with confidence and method' },
  { c: '(i) Modulation', where: 'Step 2 · Signal', to: '/signal', what: 'Type and order, calibrated probability per candidate, 95 % conformal set' },
  { c: '(i) FEC', where: 'Step 3 · Decoding', to: '/decoding', what: 'Code type and parameters' },
  { c: '(i) Interleaving', where: 'Step 3 · Decoding', to: '/decoding', what: 'Type and size' },
  { c: '(ii) Demodulate FSK, QAM, PSK', where: 'Step 2 · Signal', to: '/signal', what: 'Constellation, eye and EVM for PSK/QAM; discriminator trace and tone spacing for FSK' },
  { c: '(iii) Block, Convolutional, Diagonal, Pseudo-random', where: 'Step 3 · Decoding', to: '/decoding', what: 'All four named, scored, and manually selectable in Expert mode' },
  { c: '(iv) Conv + Viterbi, RS, Concatenated, LDPC', where: 'Step 3 · Decoding', to: '/decoding', what: 'All four named; concatenated chain drawn explicitly; LDPC reported honestly' },
  { c: '(v) Bit stream correlation', where: 'Step 4 · Header & payload', to: '/frames', what: 'Autocorrelation plot, sync-word search, frame alignment raster' },
  { c: 'Spectral features: sampling frequency, constellation, waterfall', where: 'Step 2 · Signal (default view)', to: '/signal', what: 'Waterfall, PSD and constellation visible on first load, no toggles' },
  { c: 'Header and payload identification', where: 'Step 4 · Header & payload', to: '/frames', what: 'Fields grouped under the literal labels HEADER and PAYLOAD' },
  { c: 'Automated', where: 'Autopilot (default mode)', to: '/ingest', what: 'One click from raw file to header / payload, no required input' },
  { c: 'Improve feature visibility', where: 'All plots', to: '/signal', what: 'Wheel zoom, crosshair readout, colour legend, linked frequency selection, colour-blind map, 2D default' },
  { c: 'Accuracy and confidence', where: 'Signal, Decoding, Proof, Certificate', to: '/proof', what: 'Confidence per value, Blind / Library / Manual tags, proof of decode' },
  { c: 'Output for designated sensors', where: 'Certificate · exports', to: '/certificate', what: 'JSON report, SigMF, bits, header / payload CSV, PDF certificate' },
  { c: 'Additional features', where: 'Scene, Standards, Challenge', to: '/scene', what: 'Multi-signal scene, hidden-signal reveal, standard recognition, few-shot teach' },
]

export function Compliance() {
  return (
    <div className="compliance">
      <header>
        <span className="label">Offline Signal Analysis</span>
        <h2>Problem-statement compliance</h2>
        <p className="dim">Every clause of the problem statement, where it lives on screen, and whether the engine behind it is wired yet.</p>
        <div className="comp-stats">
          <div><span className="mono big">{ROWS.length} / {ROWS.length}</span><span className="label">clauses with a UI home</span></div>
          <div><span className="mono big">0 / {ROWS.length}</span><span className="label">wired to the engine</span></div>
          <div><span className="mono big">5</span><span className="label">steps, one after another</span></div>
        </div>
      </header>
      <table className="table">
        <thead><tr><th>Clause</th><th>Where</th><th>What is visible</th><th>UI</th><th>Engine</th></tr></thead>
        <tbody>
          {ROWS.map((r) => (
            <tr key={r.c} className="hover" onClick={() => go(r.to)} tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && go(r.to)}>
              <td>{r.c}</td>
              <td className="mono small">{r.where} →</td>
              <td className="small dim">{r.what}</td>
              <td><span className="tag plain" style={{ color: 'var(--bone-1)' }}>Built</span></td>
              <td><span className="tag manual">Demo data</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
