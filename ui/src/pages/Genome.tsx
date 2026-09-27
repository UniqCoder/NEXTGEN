import { useState } from 'react'
import { Fingerprint } from '../components/Plots'
import { Seg } from '../components/ui'
import { GENOME } from '../lib/mock'

export function Genome() {
  const [band, setBand] = useState<'all' | 'HF' | 'VHF' | 'UHF'>('all')
  const [fam, setFam] = useState<'all' | 'PSK' | 'FSK' | 'QAM' | 'other'>('all')
  const list = GENOME.filter((s) => (band === 'all' || s.band.includes(band)) && (fam === 'all' || (fam === 'other' ? !['PSK', 'FSK', 'QAM'].includes(s.fam) : s.fam === fam)))
    .sort((a, b) => (b.match ?? 0) - (a.match ?? 0))

  return (
    <div className="genome">
      <header className="genome-top">
        <div>
          <span className="label">Standard recognition · Signal Genome</span>
          <h2>Named standards in this recording</h2>
        </div>
        <div className="match-cards">
          <div className="mc hit">
            <span className="label">E4 · 2-FSK 50 Bd</span>
            <span className="mc-n">RTTY 50 / 450</span>
            <span className="mono small">match 0.93 · shift 450 Hz · ITA2 framing seen</span>
          </div>
          <div className="mc">
            <span className="label">E1 · QPSK 2400 Bd</span>
            <span className="mc-n">No named standard</span>
            <span className="mono small">closest MIL-STD-188-110A · 0.22 (it uses 8PSK)</span>
          </div>
          <div className="mc">
            <span className="label">Sampling frequency · back-solved</span>
            <span className="mc-n mono">48 000<span className="unit">Hz</span></span>
            <span className="mono small">RTTY clock 49.99984 Bd ⇒ clock error −3.2 ppm</span>
          </div>
        </div>
      </header>

      <div className="genome-filter">
        <Seg value={band} onChange={setBand} label="Band" options={[{ v: 'all', label: 'All bands' }, { v: 'HF', label: 'HF' }, { v: 'VHF', label: 'VHF' }, { v: 'UHF', label: 'UHF' }]} />
        <Seg value={fam} onChange={setFam} label="Family" options={[{ v: 'all', label: 'All' }, { v: 'PSK', label: 'PSK' }, { v: 'FSK', label: 'FSK' }, { v: 'QAM', label: 'QAM' }, { v: 'other', label: 'Other' }]} />
        <span className="label" style={{ marginLeft: 'auto' }}><b>{list.length}</b> of {GENOME.length} standards in library</span>
      </div>

      <div className="genome-grid">
        {list.map((s) => (
          <div key={s.name} className={'std' + (s.match && s.match > 0.5 ? ' hit' : '')}>
            <div className="std-fp"><Fingerprint fam={s.fam} tones={s.tones} bw={s.bw} /></div>
            <div className="std-n">{s.name}</div>
            <div className="row between">
              <span className="mono small dim">{s.fam} · {s.baud} Bd</span>
              <span className="tag plain">{s.band}</span>
            </div>
            <div className="small dimmer">{s.shape}</div>
            {s.match !== undefined && (
              <div className="std-match">
                <span className="bar"><span style={{ width: `${s.match * 100}%` }} /></span>
                <span className="mono small">{s.match.toFixed(2)}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
