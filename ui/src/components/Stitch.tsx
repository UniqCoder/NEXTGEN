import { SCENARIO } from '../lib/engine'

const sign = (v: number | undefined, d = 1) => (v === undefined ? '—' : (v > 0 ? '+' : '') + v.toFixed(d))

/** USP 3b: several captures of one emitter pooled; each proven alone; each sensor measured against the emitter. */
export function Stitch() {
  const st = SCENARIO.view.stitch
  if (!st) return null
  const used = st.sensors.filter((s) => s.consistent).length
  return (
    <section className="suff">
      <div className="row between">
        <span className="label">Evidence stitching · sensor twin</span>
        <span className="tag novel">{used} of {st.sensors.length} captures</span>
      </div>
      <p className="suff-h">
        {used} captures of one emitter, {st.pooled_seconds.toFixed(2)} s and {st.pooled_frames} frames pooled on the sync marker of {st.reference}.
        The recipe found from the pool is then proven on each capture alone; clocks are relative to the other sensors.
      </p>
      <table className="table">
        <thead><tr><th>Capture</th><th>Alone</th><th>Pooled proof</th><th>Clock</th><th>Tuning</th><th>SNR</th><th>Gain</th><th>Spectrum</th></tr></thead>
        <tbody>
          {st.sensors.map((s) => (
            <tr key={s.name} className={s.excluded ? 'dimmer' : ''}>
              <td className="mono small">{s.name}<div className="dimmer">{s.seconds.toFixed(2)} s · {s.frames} frames</div></td>
              <td className="small" style={{ maxWidth: 260 }}>{s.alone.verdict === 'decoded' ? 'decoded alone' : s.alone.headline}</td>
              <td className="mono small">{s.excluded ? 'rejected: not this emitter' : s.proof ? `${s.proof.join(' · ')} · CRC ${s.crc_ok}/${s.crc_frames}` : 'not associated'}</td>
              <td className="mono small">{sign(s.clock_ppm)} ppm</td>
              <td className="mono small">{sign(s.cfo_hz)} Hz</td>
              <td className="mono small">{s.esn0_db?.toFixed(1) ?? '—'} dB</td>
              <td className="mono small">{sign(s.gain_db)} dB</td>
              <td className="mono small">{s.inverted ? 'inverted' : 'normal'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
