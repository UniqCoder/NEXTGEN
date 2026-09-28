import { go } from '../lib/router'

// Coverage is about demonstrated engine behaviour, not the presence of a screen.
const ROWS = [
  { c: '.IQ and .wav input', to: '/ingest', status: 'Working', what: 'SigMF, common raw IQ and PCM/float WAV; large-file streaming and RF64 remain open.' },
  { c: 'Sampling and signal parameters', to: '/signal', status: 'Partial', what: 'Header sample rate and measured rate, band, offset and SNR; intervals are not calibrated.' },
  { c: 'Modulation identification', to: '/signal', status: 'Partial', what: 'Blind BPSK/QPSK on the supported frame family; six public HF files identified at family/rate level.' },
  { c: 'FEC identification', to: '/decoding', status: 'Partial', what: 'Blind rate 1/2 convolutional K=3–9; RS, concatenated and LDPC need a supplied recipe.' },
  { c: 'Interleaving identification', to: '/decoding', status: 'Partial', what: 'Blind block geometry; diagonal, pseudo random and convolutional identification remain open.' },
  { c: 'FSK, PSK and QAM demodulation', to: '/signal', status: 'Partial', what: 'PSK/QAM work with a supplied recipe. A tested FSK tone bank is not yet wired into jobs.' },
  { c: 'Four deinterleaver types', to: '/decoding', status: 'Partial', what: 'Block, diagonal and pseudo random work with supplied recipes; convolutional has a tested standalone inverse.' },
  { c: 'Viterbi, RS, concatenated, LDPC', to: '/decoding', status: 'Recipe only', what: 'All four decode generated recordings with a supplied recipe; broad blind selection is open.' },
  { c: 'Bit stream, header and payload', to: '/frames', status: 'Partial', what: 'Blind sync, CRC and fields on generated BPSK/QPSK captures; real payload decode is open.' },
  { c: 'Proof and certificate', to: '/proof', status: 'Working', what: 'Layered proof and signed recheckable certificate. Wrong certificate rate is unmeasured.' },
  { c: 'Sufficiency and sensor stitching', to: '/scene', status: 'Synthetic', what: 'Evidence ledger, length estimate and multisensor pooling tested on generated captures.' },
  { c: 'Receiver compiler', to: '/certificate', status: 'Synthetic', what: 'Standalone receiver gated bit for bit on generated captures; GNU Radio graph is unexecuted.' },
]

export function Compliance() {
  return (
    <div className="compliance">
      <header>
        <span className="label">SIH 2026 · PS 26147 · NTRO</span>
        <h2>Capability scorecard</h2>
        <p className="dim">What the current engine demonstrates. “Partial” and “Recipe only” are not claims of blind recovery on an unknown recording.</p>
      </header>
      <table className="table">
        <thead><tr><th>Requirement or feature</th><th>Engine status</th><th>Evidence and limit</th></tr></thead>
        <tbody>
          {ROWS.map((r) => (
            <tr key={r.c} className="hover" onClick={() => go(r.to)} tabIndex={0} onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && go(r.to)}>
              <td>{r.c}</td>
              <td><span className={'tag ' + (r.status === 'Working' ? 'proven' : 'manual')}>{r.status}</span></td>
              <td className="small dim">{r.what}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
