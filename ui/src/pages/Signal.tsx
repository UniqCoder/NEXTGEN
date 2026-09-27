import { useState } from 'react'
import { Panel, Seg } from '../components/ui'
import { DisplayMenu, Step } from '../components/Step'
import { Waterfall, type Overlay } from '../components/Waterfall'
import { Terrain } from '../components/Terrain'
import { Constellation, Eye, InstFreq, PSD } from '../components/Plots'
import { Params } from '../components/Params'
import { SCENARIO } from '../lib/mock'
import { runAutopilot, setState, useApp } from '../lib/store'

type View = 'const' | 'eye' | 'fsk'

export function Signal() {
  const view3d = useApp((s) => s.view3d)
  const floor = useApp((s) => s.floor)
  const span = useApp((s) => s.span)
  const override = useApp((s) => s.modOverride)
  const demodDone = useApp((s) => s.stages[3] === 'done')
  const measured = useApp((s) => s.stages.slice(0, 4).every((x) => x === 'done' || x === 'override'))
  const running = useApp((s) => s.stages.some((x) => x === 'running'))
  const [view, setView] = useState<View>('const')

  const e1 = SCENARIO.emitters[0]
  const overlays: Overlay[] = [{ ...e1, alpha: 1, label: `E1 · ${override ?? 'QPSK'} · 2400 Bd`, tone: 'signal' }]

  return (
    <Step
      n={2}
      title="Signal"
      lede={measured ? (
        <>One strong signal at <b>+3.5 kHz</b>: <b>{override ?? 'QPSK'}</b> at <b>2 400</b> symbols per second, SNR 14 dB. Three weaker emitters share the band, <a href="#/scene">see them in Scene</a>.</>
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
          {view === 'const' ? <Constellation locked={demodDone} ref8={override === '8PSK'} /> : view === 'eye' ? <Eye /> : <InstFreq />}
        </Panel>

        <section className="found" style={{ gridArea: 'found' }}>
          <h2>What we found</h2>
          <p className="small dim">Click a value to see the evidence.</p>
          <Params keys={['content', 'fs', 'baud', 'modulation', 'snr', 'bw', 'cfo', 'fc']} />
        </section>
      </div>
    </Step>
  )
}
