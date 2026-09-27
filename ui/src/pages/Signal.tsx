import { useState } from 'react'
import { Panel, Seg } from '../components/ui'
import { DisplayMenu, Step } from '../components/Step'
import { Waterfall, type Overlay } from '../components/Waterfall'
import { Terrain } from '../components/Terrain'
import { Constellation, Eye, InstFreq, PSD } from '../components/Plots'
import { Params } from '../components/Params'
import { SCENARIO } from '../lib/engine'
import { runAutopilot, setState, useApp } from '../lib/store'

type View = 'const' | 'eye' | 'fsk'

export function Signal() {
  const view3d = useApp((s) => s.view3d)
  const floor = useApp((s) => s.floor)
  const span = useApp((s) => s.span)
  const override = useApp((s) => s.modOverride)
  const demodDone = useApp((s) => s.stages[3] === 'done')
  const undecided = useApp((s) => s.job === 'undecided')
  const measured = useApp((s) => s.stages.slice(0, 4).every((x) => x === 'done' || x === 'override')) || undecided
  const running = useApp((s) => s.stages.some((x) => x === 'running'))
  const [view, setView] = useState<View>('const')

  const e1 = SCENARIO.emitters[0]
  const T = SCENARIO.text
  const m = SCENARIO.view.measured
  const overlays: Overlay[] = e1 ? [{ ...e1, alpha: 1,
    label: undecided ? 'E1 · undecided' : `E1 · ${override ?? T.mod} · ${T.baud} Bd`, tone: undecided ? 'bone' : 'signal' }] : []

  return (
    <Step
      n={2}
      title="Signal"
      lede={undecided ? (
        m ? <><b>{m.modulation}</b> at <b>{m.rate_hz.toFixed(2)} Bd</b>{m.family === 'FSK' ? <>, {m.tones_hz.length} tones {Math.round(m.spacing_hz ?? 0)} Hz apart</> : null}, carrier {Math.round(m.carrier_hz)} Hz, {m.snr_db.toFixed(0)} dB SNR{m.standards.length ? <> — consistent with <b>{m.standards.map((x) => x.name).join(' / ')}</b></> : null}. Identified from the recording alone; not decoded — see why on <a href="#/decoding">Decoding</a>.</>
          : 'No emission stood out from the noise floor.'
      ) : measured ? (
        <>One strong signal at <b>{T.at}</b>: <b>{override ?? T.mod}</b> at <b>{T.baudSpaced}</b> symbols per second, SNR {T.snr} dB.{T.others ? <> {T.others}, <a href="#/scene">see them in Scene</a>.</> : null}</>
      ) : running ? 'Measuring the recording: sample rate, bandwidth, symbol rate, then the modulation…' : 'Run Autopilot to measure the recording.'}
      actions={
        <>
          <Seg value={view3d ? '3d' : '2d'} onChange={(v) => setState({ view3d: v === '3d' })} options={[{ v: '2d', label: '2D' }, { v: '3d', label: '3D' }]} label="Waterfall view" />
          <DisplayMenu />
          <button className="btn" onClick={runAutopilot} disabled={running}>{running ? 'Running…' : 'Re-run Autopilot'}</button>
        </>
      }
      back={{ to: '/ingest', label: 'Recording' }}
      next={{ to: '/decoding', label: 'Continue to decoding', disabled: !measured }}
    >
      <div className="sig">
        <Panel title="Waterfall" alt={view3d ? 'left–right: frequency · front–back: time · height: power · each ridge is a transmitter' : 'time vs frequency · drag to select · wheel to zoom'} style={{ gridArea: 'wf' }}>
          {view3d ? <Terrain k={0} fail={false} floor={floor} span={span} /> : <Waterfall k={0} target="resid" floor={floor} span={span} overlays={overlays} />}
        </Panel>

        <Panel title="Power spectrum" alt="brighter = more often · line = average" style={{ gridArea: 'psd' }}>
          <PSD />
        </Panel>

        <Panel
          title={view === 'const' ? 'Constellation' : view === 'eye' ? 'Eye diagram' : 'FSK frequency'}
          style={{ gridArea: 'con' }}
          tools={<Seg value={view} onChange={setView} label="Demodulation view"
            options={[{ v: 'const', label: 'Constellation' }, { v: 'eye', label: 'Eye' }, { v: 'fsk', label: 'FSK · E4' }]} />}
        >
          {view === 'const' ? <Constellation locked={demodDone || undecided} ref8={override === '8PSK'} /> : view === 'eye' ? <Eye /> : <InstFreq />}
        </Panel>

        <section className="found" style={{ gridArea: 'found' }}>
          <h2>What we found</h2>
          <p className="small dim">Click a value to see the evidence.</p>
          <Params keys={['content', 'fs', 'baud', 'modulation', 'std', 'snr', 'bw', 'cfo', 'fc', 'tones']} />
        </section>
      </div>
    </Step>
  )
}
