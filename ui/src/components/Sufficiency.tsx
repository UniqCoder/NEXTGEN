import { SCENARIO } from '../lib/engine'

const LIMIT: Record<string, string> = {
  data: 'too short', channel: 'not separable', scope: 'unsupported', structure: 'sync not found', signal: 'no emission',
}
const VERDICT = { sufficient: 'Sufficient', more_data: 'Record more', not_data_limited: 'No length estimate' }

/** USP 3a: the evidence ledger of the blind search, with the predicted recording length when more data would help. */
export function Sufficiency() {
  const s = SCENARIO.view.sufficiency
  if (!s) return null
  return (
    <section className="suff">
      <div className="row between">
        <span className="label">Data sufficiency · evidence ledger</span>
        <span className={'tag ' + (s.verdict === 'sufficient' ? 'proven' : s.verdict === 'more_data' ? 'manual' : 'plain')}>{VERDICT[s.verdict]}</span>
      </div>
      <p className="suff-h">{s.headline}</p>
      <table className="table">
        <tbody>
          {s.entries.map((e, i) => (
            <tr key={i}>
              <td className="label" style={{ width: 150 }}>{e.decision}</td>
              <td className="small">{e.evidence}</td>
              <td className="mono small" style={{ width: 150, textAlign: 'right' }}>
                {e.status === 'decided'
                  ? (e.min_s ? `needed ${e.min_s[0].toFixed(2)} s` : 'decided')
                  : e.need_s ? `need ${e.need_s[0].toFixed(2)} / ${e.need_s[1].toFixed(2)} s` : LIMIT[e.limit ?? ''] ?? 'open'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
