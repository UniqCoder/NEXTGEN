import { useEffect, useMemo, useRef, useState } from 'react'
import { FRAME, SCENARIO, bitstream, findSync } from '../lib/mock'
import { motion } from 'motion/react'
import { go } from '../lib/router'
import { STEPS, getState, prove, runAutopilot, setState } from '../lib/store'
import { TOOLS } from './Step'

export interface Cmd { grp: string; label: string; kbd?: string; run: () => void }

export function commands(): Cmd[] {
  return [
    ...STEPS.map((p, i) => ({ grp: `Step ${i + 1}`, label: p.n, kbd: `Alt ${i + 1}`, run: () => go(p.path) })),
    { grp: 'Step 5', label: 'Certificate', run: () => go('/certificate') },
    ...TOOLS.map((t) => ({ grp: 'Tools', label: `${t.n} · ${t.d}`, run: () => go(t.path) })),
    { grp: 'Analyse', label: 'Run Autopilot on current file', kbd: 'A', run: () => { go('/signal'); runAutopilot() } },
    { grp: 'Analyse', label: 'Prove decode (re-synthesise and subtract)', kbd: 'P', run: () => { go('/proof'); prove() } },
    { grp: 'Mode', label: 'Switch Autopilot / Expert', kbd: 'E', run: () => setState((s) => ({ mode: s.mode === 'expert' ? 'autopilot' : 'expert' })) },
    { grp: 'View', label: 'Toggle 3D terrain', kbd: 'T', run: () => setState((s) => ({ view3d: !s.view3d })) },
    { grp: 'View', label: 'Toggle paper theme', kbd: '\\', run: () => setState((s) => ({ theme: s.theme === 'paper' ? 'ink' : 'paper' })) },
    { grp: 'View', label: 'Colour map: valve / mono (colour-blind safe)', run: () => setState((s) => ({ cmap: s.cmap === 'valve' ? 'mono' : 'valve' })) },
    { grp: 'Export', label: 'Parameter report · JSON', run: () => exportJSON() },
    { grp: 'Export', label: 'Decode certificate · PDF', run: () => { go('/certificate'); setTimeout(() => print(), 300) } },
    { grp: 'Export', label: 'SigMF annotations · .sigmf-meta', run: () => exportJSON('sigmf') },
    { grp: 'Export', label: 'Decoded bit stream · .bin', run: () => exportBits() },
    { grp: 'Export', label: 'Header / payload map · CSV', run: () => exportCSV() },
  ]
}

export function Palette() {
  const [q, setQ] = useState('')
  const [ix, setIx] = useState(0)
  const input = useRef<HTMLInputElement>(null)
  const all = useMemo(commands, [])
  const list = all.filter((c) => (c.grp + ' ' + c.label).toLowerCase().includes(q.toLowerCase()))
  useEffect(() => input.current?.focus(), [])
  useEffect(() => setIx(0), [q])
  const close = () => setState({ paletteOpen: false })
  const run = (c?: Cmd) => { if (!c) return; close(); c.run() }

  return (
    <div className="scrim" onPointerDown={(e) => e.target === e.currentTarget && close()}>
      <motion.div className="palette" role="dialog" aria-label="Command palette"
        initial={{ opacity: 0, y: -6, scale: 0.99 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.14, ease: [0.2, 0, 0, 1] }}>
        <input
          ref={input}
          value={q}
          placeholder="Type a command or a page…"
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') { e.preventDefault(); setIx((i) => Math.min(list.length - 1, i + 1)) }
            if (e.key === 'ArrowUp') { e.preventDefault(); setIx((i) => Math.max(0, i - 1)) }
            if (e.key === 'Enter') run(list[ix])
            if (e.key === 'Escape') close()
          }}
          aria-activedescendant={`cmd-${ix}`}
        />
        <ul role="listbox">
          {list.map((c, i) => (
            <li key={c.grp + c.label} id={`cmd-${i}`} role="option" aria-selected={i === ix} onPointerMove={() => setIx(i)} onClick={() => run(c)}>
              <span className="grp label">{c.grp}</span>
              <span>{c.label}</span>
              {c.kbd && <span className="kbd">{c.kbd}</span>}
            </li>
          ))}
          {!list.length && <li className="dimmer">Nothing matches “{q}”.</li>}
        </ul>
        <div className="foot label"><span>↑↓ move</span><span>↵ run</span><span>esc close</span></div>
      </motion.div>
    </div>
  )
}

// ---------- Exports (front-end versions; the engine will produce the authoritative files) ----------


function download(name: string, data: BlobPart, type: string) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([data], { type }))
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

export function exportJSON(kind: 'report' | 'sigmf' = 'report') {
  const s = getState()
  const params = Object.fromEntries(Object.values(SCENARIO.params).map((p) => [p.key, { value: p.value, unit: p.unit ?? null, method: p.method, confidence: p.conf, evidence: p.evidence }]))
  if (kind === 'sigmf') {
    const meta = {
      global: { 'core:datatype': 'ci16_le', 'core:sample_rate': 48000, 'core:version': '1.0.0', 'core:description': 'SANJAYA analysis', 'core:sha512': null },
      captures: [{ 'core:sample_start': 0, ...(s.fcHz ? { 'core:frequency': s.fcHz } : {}) }],
      annotations: SCENARIO.emitters.map((e) => ({
        'core:sample_start': Math.round(e.t0 * SCENARIO.file.duration * 48000),
        'core:sample_count': Math.round((e.t1 - e.t0) * SCENARIO.file.duration * 48000),
        'core:freq_lower_edge': e.f0 + (s.fcHz ?? 0), 'core:freq_upper_edge': e.f1 + (s.fcHz ?? 0),
        'core:label': e.id, 'core:comment': `${e.cls} · ${e.std}`,
      })),
    }
    return download(SCENARIO.file.name.replace(/\.\w+$/, '.sigmf-meta'), JSON.stringify(meta, null, 2), 'application/json')
  }
  const report = { file: SCENARIO.file, certificate: SCENARIO.cert.id, proof: s.proof, parameters: params, frame: FRAME.fields, generated: new Date().toISOString() }
  download('sanjaya-report.json', JSON.stringify(report, null, 2), 'application/json')
}

function exportBits() {
  const { stream } = bitstream()
  const bytes = new Uint8Array(Math.ceil(stream.length / 8))
  stream.forEach((b, i) => (bytes[i >> 3] |= b << (7 - (i & 7))))
  download('sanjaya-bits.bin', bytes, 'application/octet-stream')
}

function exportCSV() {
  const { stream } = bitstream()
  const s0 = findSync(stream)
  const rows = ['frame,start_bit,group,field,bit_offset,length,hex']
  for (let f = 0; s0 + (f + 1) * FRAME.len <= stream.length; f++)
    for (const fl of FRAME.fields) {
      let v = 0n
      for (let i = 0; i < fl.len; i++) v = (v << 1n) | BigInt(stream[s0 + f * FRAME.len + fl.start + i])
      rows.push([f, s0 + f * FRAME.len, fl.group, fl.name, fl.start, fl.len, '0x' + v.toString(16).toUpperCase()].join(','))
    }
  download('sanjaya-header-payload.csv', rows.join('\n'), 'text/csv')
}
