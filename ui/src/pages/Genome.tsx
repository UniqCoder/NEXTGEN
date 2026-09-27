import { useState } from 'react'
import { Fingerprint } from '../components/Plots'
import { Seg } from '../components/ui'
import { GENOME, SCENARIO } from '../lib/engine'

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
          {SCENARIO.emitters.some((e) => e.id === 'E4') && <div className="mc hit">
            <span className="label">E4 · 2-FSK 50 Bd</span>
            <span className="mc-n">RTTY 50 / 450</span>
            <span className="mono small">match 0.93 · shift 450 Hz · ITA2 framing seen</span>
          </div>}
          <div className="mc">
            <span className="label">{SCENARIO.text.genomeE1.label}</span>
            <span className="mc-n">{SCENARIO.text.genomeE1.name}</span>
            <span className="mono small">{SCENARIO.text.genomeE1.note}</span>
          </div>
          <div className="mc">
            <span className="label">{SCENARIO.text.genomeFs.title}</span>
            <span className="mc-n mono">{SCENARIO.text.genomeFs.value}<span className="unit">Hz</span></span>
            <span className="mono small">{SCENARIO.text.genomeFs.note}</span>
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
