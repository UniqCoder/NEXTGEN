import { useEffect, useMemo, useRef } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Bloom, EffectComposer, Vignette } from '@react-three/postprocessing'
import * as THREE from 'three'
import { LUTS } from '../lib/colormap'
import { SCENARIO, SPEC, freqBin, spectrogram } from '../lib/engine'
import { css } from '../lib/plot'
import { useApp } from '../lib/store'

// dB is packed into bytes over the scenario's window (SCENARIO.view); the shader unpacks and applies floor/span.
// World size of the data plane: frequency across, time into the screen.
const W = 4.6, D = 3.0, H = 1.4

const vert = /* glsl */ `
uniform sampler2D uData;
uniform float uK, uFloor, uSpan, uFail, uH, uRise, uScroll, uLo, uRange;
varying float vT; varying float vRed; varying float vDepth; varying float vRow; varying float vDb; varying vec2 vUv;
void main() {
  vUv = uv;
  float row = fract(uv.y + uScroll);
  vRow = row;
  vec4 d = texture2D(uData, vec2(uv.x, row));
  float full = uLo + d.r * uRange;
  float res = uLo + mix(d.g, d.b, uFail) * uRange;
  float w = 0.28;
  float kk = clamp((uK * (1.0 + w) - row) / w, 0.0, 1.0);
  kk = kk * kk * (3.0 - 2.0 * kk);
  float db = mix(full, res, kk);
  vDb = db;
  float t = clamp((db - uFloor) / uSpan, 0.0, 1.0);
  vT = t;
  vRed = uFail * kk * smoothstep(1.5, 6.0, (d.b - d.g) * uRange);
  // intro: the landscape rises out of the noise, far edge first
  float rise = clamp(uRise * 1.7 - (1.0 - uv.y) * 0.7, 0.0, 1.0);
  rise = rise * rise * (3.0 - 2.0 * rise);
  vec3 p = position;
  p.z += pow(t, 1.45) * uH * rise;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vDepth = -mv.z;
  gl_Position = projectionMatrix * mv;
}`

const frag = /* glsl */ `
uniform sampler2D uRamp;
uniform vec3 uFog, uFault, uGrid, uScanCol;
uniform float uFogNear, uFogFar, uTime, uScan, uGlow, uTGrid;
varying float vT; varying float vRed; varying float vDepth; varying float vRow; varying float vDb; varying vec2 vUv;

float gridLine(float x) {
  float d = abs(fract(x - 0.5) - 0.5);
  return 1.0 - smoothstep(0.0, fwidth(x) * 1.2, d);
}

void main() {
  vec3 c = texture2D(uRamp, vec2(vT, 0.5)).rgb;

  // relief light from screen-space slope
  float dx = dFdx(vT), dy = dFdy(vT);
  vec3 n = normalize(vec3(-dx * 26.0, -dy * 26.0, 1.0));
  c *= 0.6 + 0.6 * max(0.0, dot(n, normalize(vec3(-0.5, 0.6, 0.62))));

  // strong peaks run hot so the bloom pass picks them up
  c *= 1.0 + uGlow * pow(vT, 2.2) * 4.2;

  // topographic contours every 3 dB, only where there is signal
  float contour = gridLine(vDb / 3.0) * smoothstep(0.16, 0.34, vT);
  c = mix(c, c * 1.7 + uGrid * 0.25, contour * 0.45);

  // instrument grid on the surface: 2 kHz minor, 10 kHz major, 50 s rows
  float fMinor = gridLine(vUv.x * 24.0), fMajor = gridLine(vUv.x * 4.8);
  float tLine = gridLine(vRow * uTGrid);
  c += uGrid * (fMinor * 0.035 + fMajor * 0.09 + tLine * 0.05) * (1.0 - vT);

  // scan line sweeping through time
  float sd = (vUv.y - uScan) * 140.0;
  float s = exp(-sd * sd);
  c += uScanCol * s * (0.25 + vT * 3.0);

  c = mix(c, uFault * 1.4, vRed * 0.75);

  float g = fract(sin(dot(gl_FragCoord.xy + fract(uTime) * 91.0, vec2(12.9898, 78.233))) * 43758.5453);
  c += (g - 0.5) * 0.02;

  // float the plane in space: soft edges, fog with depth
  float edge = smoothstep(0.0, 0.035, vUv.x) * smoothstep(1.0, 0.965, vUv.x) * smoothstep(0.0, 0.05, vUv.y) * smoothstep(1.0, 0.95, vUv.y);
  c = mix(uFog, c, edge);
  c = mix(c, uFog, smoothstep(uFogNear, uFogFar, vDepth));
  gl_FragColor = vec4(max(c, vec3(0.0)), 1.0);
  #include <colorspace_fragment>
}`

const groundFrag = /* glsl */ `
uniform vec3 uGrid, uFog;
varying vec2 vUv;
float gridLine(float x) {
  float d = abs(fract(x - 0.5) - 0.5);
  return 1.0 - smoothstep(0.0, fwidth(x) * 1.1, d);
}
void main() {
  vec2 p = (vUv - 0.5) * vec2(${(W * 3).toFixed(1)}, ${(D * 3).toFixed(1)});
  float l = max(gridLine(p.x / 0.23), gridLine(p.y / 0.23)) * 0.5 + max(gridLine(p.x / 1.15), gridLine(p.y / 1.15)) * 0.7;
  float fade = 1.0 - smoothstep(1.0, 5.0, length(p * vec2(0.8, 1.0)));
  gl_FragColor = vec4(mix(uFog, uGrid, l * 0.075 * fade), 1.0);
  #include <colorspace_fragment>
}`

export interface TerrainProps {
  k: number
  fail: boolean
  floor: number
  span: number
  hero?: boolean // full-bleed landing: live replay, no axes, slower camera
}

interface Label { text: string; sub?: string; pos: THREE.Vector3; kind: 'emitter' | 'axis' | 'title' }

function Surface(props: TerrainProps) {
  const cmap = useApp((s) => s.cmap)
  const theme = useApp((s) => s.theme)
  const spec = useMemo(spectrogram, [])
  const data = useMemo(() => {
    const n = SPEC.bins * SPEC.rows
    const buf = new Uint8Array(n * 4)
    const { lo, range } = SCENARIO.view
    const pack = (v: number) => Math.max(0, Math.min(255, Math.round(((v - lo) / range) * 255)))
    for (let i = 0; i < n; i++) {
      buf[i * 4] = pack(spec.full[i])
      buf[i * 4 + 1] = pack(spec.resid[i])
      buf[i * 4 + 2] = pack(spec.fail[i])
      buf[i * 4 + 3] = 255
    }
    const t = new THREE.DataTexture(buf, SPEC.bins, SPEC.rows, THREE.RGBAFormat)
    t.minFilter = t.magFilter = THREE.LinearFilter
    t.needsUpdate = true
    return t
  }, [spec])

  const ramp = useMemo(() => {
    const lut = LUTS[theme === 'paper' ? 'paper' : cmap]
    const buf = new Uint8Array(256 * 4)
    for (let i = 0; i < 256; i++) { buf[i * 4] = lut[i * 3]; buf[i * 4 + 1] = lut[i * 3 + 1]; buf[i * 4 + 2] = lut[i * 3 + 2]; buf[i * 4 + 3] = 255 }
    const t = new THREE.DataTexture(buf, 256, 1, THREE.RGBAFormat)
    t.colorSpace = THREE.SRGBColorSpace
    t.minFilter = t.magFilter = THREE.LinearFilter
    t.needsUpdate = true
    return t
  }, [cmap, theme])

  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: vert,
        fragmentShader: frag,
        uniforms: {
          uData: { value: data }, uRamp: { value: ramp }, uK: { value: 0 }, uFail: { value: 0 },
          uFloor: { value: -104 }, uSpan: { value: 44 }, uH: { value: H }, uTime: { value: 0 },
          uRise: { value: 0 }, uScroll: { value: 0 }, uScan: { value: 0 }, uGlow: { value: 1 },
          uFog: { value: new THREE.Color() }, uFault: { value: new THREE.Color() }, uGrid: { value: new THREE.Color() },
          uScanCol: { value: new THREE.Color() }, uFogNear: { value: 4.5 }, uFogFar: { value: 9.5 },
          uLo: { value: SCENARIO.view.lo }, uRange: { value: SCENARIO.view.range },
          uTGrid: { value: SCENARIO.file.duration / SCENARIO.view.gridSeconds },
        },
      }),
    [data],
  )
  const ground = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
        fragmentShader: groundFrag,
        uniforms: { uGrid: { value: new THREE.Color() }, uFog: { value: new THREE.Color() } },
      }),
    [],
  )
  useEffect(() => { mat.uniforms.uRamp.value = ramp }, [ramp, mat])
  useEffect(() => {
    const u = mat.uniforms
    ;(u.uFog.value as THREE.Color).set(css(props.hero ? '--ink-0' : '--ink-1'))
    ;(u.uFault.value as THREE.Color).set(css('--fault'))
    ;(u.uGrid.value as THREE.Color).set(css('--bone-1'))
    ;(u.uScanCol.value as THREE.Color).set(css('--signal'))
    u.uGlow.value = theme === 'paper' ? 0 : 1
    ;(ground.uniforms.uGrid.value as THREE.Color).set(css('--bone-2'))
    ;(ground.uniforms.uFog.value as THREE.Color).set(css(props.hero ? '--ink-0' : '--ink-1'))
  }, [theme, mat, ground, props.hero])

  const reduce = useMemo(() => matchMedia('(prefers-reduced-motion: reduce)').matches, [])
  const t0 = useRef<number | null>(null)
  useFrame(({ clock }) => {
    const u = mat.uniforms
    const t = clock.elapsedTime
    if (t0.current === null) t0.current = t
    const since = t - t0.current
    u.uK.value = props.k
    u.uFail.value = props.fail ? 1 : 0
    u.uFloor.value = props.floor
    u.uSpan.value = props.span
    u.uTime.value = t
    u.uRise.value = reduce ? 1 : Math.min(1, since / 2.2)
    u.uScroll.value = props.hero && !reduce ? (t * 0.012) % 1 : 0
    u.uScan.value = reduce ? -1 : ((since * 0.09) % 1.3) - 0.15
  })

  return (
    <>
      <mesh rotation-x={-Math.PI / 2} material={mat}>
        <planeGeometry args={[W, D, 511, 255]} />
      </mesh>
      <mesh rotation-x={-Math.PI / 2} position-y={-0.004} material={ground}>
        <planeGeometry args={[W * 3, D * 3]} />
      </mesh>
    </>
  )
}

/** Frequency ticks in kHz inside +-fs/2 (demo: -20..20 every 10). */
function fTicks() {
  const half = SPEC.fs / 2000, step = [1, 2, 5, 10, 20, 50, 100, 200, 500].find((s) => half / s <= 3) ?? 1000
  const out: number[] = []
  for (let f = -Math.floor(half / step) * step; f <= half; f += step) if (Math.abs(f) < half) out.push(f)
  return out
}
/** Time ticks every `every` grid steps (demo: 0..250 every 50 s). */
function tTicks(every: number) {
  const out: number[] = []
  for (let t = 0; t <= SCENARIO.file.duration + 1e-9; t += SCENARIO.view.gridSeconds * every) out.push(+t.toFixed(3))
  return out
}

/** Height of a dB value on the surface, matching the vertex shader. */
const yOf = (db: number, floor: number, span: number) => Math.pow(Math.max(0, Math.min(1, (db - floor) / span)), 1.45) * H

/** Scientific-plot frame: frequency along the front edge, time along the right edge, power up the back-left corner. */
function AxisFrame({ floor, span }: { floor: number; span: number }) {
  const theme = useApp((s) => s.theme)
  const geo = useMemo(() => {
    const pts: number[] = []
    const seg = (a: number[], b: number[]) => pts.push(...a, ...b)
    const x0 = -W / 2, x1 = W / 2, zf = D / 2, zb = -D / 2
    seg([x0, 0, zf], [x1, 0, zf]); seg([x1, 0, zf], [x1, 0, zb]); seg([x0, 0, zb], [x1, 0, zb]); seg([x0, 0, zf], [x0, 0, zb])
    for (const f of fTicks()) { const x = ((f * 1000) / SPEC.fs) * W; seg([x, 0, zf], [x, 0, zf + 0.09]) }
    for (const sec of tTicks(1)) { const z = -(sec / SCENARIO.file.duration - 0.5) * D; seg([x1, 0, z], [x1 + 0.09, 0, z]) }
    seg([x0, 0, zb], [x0, H, zb])
    for (let db = Math.ceil(floor / 10) * 10; db <= floor + span; db += 10) { const y = yOf(db, floor, span); seg([x0, y, zb], [x0 - 0.09, y, zb]) }
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3))
    return g
  }, [floor, span])
  const mat = useMemo(() => new THREE.LineBasicMaterial({ color: new THREE.Color(css('--bone-2')), transparent: true, opacity: 0.8 }), [theme])
  return <lineSegments geometry={geo} material={mat} />
}

type View = { az: number; el: number; zoom: number }

/** Camera: fits the data plane to whatever shape the panel is, then drifts gently. Drag orbits, wheel zooms. */
function Rig({ view, hero }: { view: React.MutableRefObject<View | null>; hero?: boolean }) {
  const { camera, size } = useThree()
  const cur = useRef({ az: 0, el: 0, r: 6 })
  const fitR = useRef(6)
  const v = useMemo(() => new THREE.Vector3(), [])
  const corners = useMemo(() => {
    const out: THREE.Vector3[] = []
    for (const x of [-W / 2, W / 2]) for (const z of [-D / 2, D / 2]) for (const y of [0, H * 0.5]) out.push(new THREE.Vector3(x, y, z))
    return out
  }, [])
  useFrame(({ clock }) => {
    const aspect = size.width / size.height
    if (!view.current) {
      // wide, short panels read best from the front; squarer ones from a three-quarter angle
      view.current = hero ? { az: -0.42, el: 0.4, zoom: 1 } : aspect > 3 ? { az: -0.22, el: 0.42, zoom: 1 } : { az: -0.36, el: 0.5, zoom: 1 }
      Object.assign(cur.current, { az: view.current.az, el: view.current.el })
    }
    const t = view.current, c = cur.current
    const drift = hero ? Math.sin(clock.elapsedTime * 0.07) * 0.2 : Math.sin(clock.elapsedTime * 0.1) * 0.04
    c.az += (t.az + drift - c.az) * 0.06
    c.el += (t.el - c.el) * 0.06
    c.r = hero ? 4.9 : fitR.current * t.zoom
    camera.position.set(c.r * Math.sin(c.az) * Math.cos(c.el), c.r * Math.sin(c.el), c.r * Math.cos(c.az) * Math.cos(c.el))
    camera.lookAt(hero ? -1.15 : 0, hero ? 0.35 : H * 0.18, 0)
    if (hero) return
    // measure how much of the screen the plane fills and converge on ~92 % wide / ~80 % tall
    camera.updateMatrixWorld()
    let ex = 0, ey = 0
    for (const p of corners) { v.copy(p).project(camera); ex = Math.max(ex, Math.abs(v.x)); ey = Math.max(ey, Math.abs(v.y)) }
    const want = Math.max(ex / 0.92, ey / 0.8)
    if (isFinite(want) && want > 0) fitR.current *= 1 + (want - 1) * 0.25
  })
  return null
}

/** Projects 3D anchor points to screen space and moves DOM labels there; stacks emitter callouts so they never overlap. */
function Projector({ labels, els }: { labels: Label[]; els: React.MutableRefObject<(HTMLDivElement | null)[]> }) {
  const { camera, size } = useThree()
  const v = useMemo(() => new THREE.Vector3(), [])
  useFrame(() => {
    const callouts: { i: number; x: number; y: number }[] = []
    labels.forEach((l, i) => {
      const el = els.current[i]
      if (!el) return
      v.copy(l.pos).project(camera)
      const x = (v.x * 0.5 + 0.5) * size.width, y = (-v.y * 0.5 + 0.5) * size.height
      el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`
      el.style.opacity = v.z < 1 ? '1' : '0'
      if (l.kind === 'emitter') callouts.push({ i, x, y })
    })
    // callout boxes sit in rows near the top, joined to their peak by a leader line;
    // a box goes to the next row down only if it would collide with one already placed (~190 px wide)
    const lanes: number[] = []
    callouts.sort((a, b) => a.x - b.x).forEach((c) => {
      let lane = lanes.findIndex((right) => c.x > right + 12)
      if (lane < 0) lane = lanes.length
      lanes[lane] = c.x + 190
      const boxBottom = 104 + lane * 46
      els.current[c.i]!.style.setProperty('--stem', `${Math.max(14, c.y - boxBottom)}px`)
    })
  })
  return null
}

export function Terrain(props: TerrainProps) {
  const view = useRef<View | null>(null)
  const drag = useRef<{ x: number; y: number } | null>(null)
  const theme = useApp((s) => s.theme)
  const els = useRef<(HTMLDivElement | null)[]>([])
  const gone = props.k > 0.95 && !props.fail

  const labels = useMemo<Label[]>(() => {
    const s = spectrogram()
    const peak = (f: number) => {
      const b = Math.round(freqBin(f))
      let m = -200
      for (let y = SCENARIO.view.rowStart; y < SPEC.rows; y++) m = Math.max(m, s.full[y * SPEC.bins + b])
      return m
    }
    const at = (f: number, row: number, db: number) => new THREE.Vector3(((f + SPEC.fs / 2) / SPEC.fs - 0.5) * W, yOf(db, props.floor, props.span) + 0.03, -(row - 0.5) * D)
    const em = SCENARIO.emitters
    const e1 = em[0], e2 = em.find((e) => e.id === 'E2'), e3 = em.find((e) => e.id === 'E3')
    const out: Label[] = [
      { kind: 'emitter', text: gone ? 'E1 · subtracted' : e1.label, sub: gone ? 'only noise is left' : e1.sub, pos: at(e1.fc, props.hero ? 0.62 : 0.55, gone ? props.floor + 4 : peak(e1.fc)) },
    ]
    if (props.hero) return out
    if (e3) out.push({ kind: 'emitter', text: e3.label, sub: e3.sub, pos: at(e3.fc, 0.55, peak(e3.fc)) })
    if (e2) out.push({ kind: 'emitter', text: e2.label, sub: e2.sub, pos: at((e2.f0 + e2.f1) / 2, 0.61, props.floor + 12) })
    for (const f of fTicks())
      out.push({ kind: 'axis', text: (f > 0 ? '+' : '') + f, pos: new THREE.Vector3(((f * 1000) / SPEC.fs) * W, 0, D / 2 + 0.22) })
    for (const sec of tTicks(2))
      out.push({ kind: 'axis', text: sec + ' s', pos: new THREE.Vector3(W / 2 + 0.3, 0, -(sec / SCENARIO.file.duration - 0.5) * D) })
    for (let db = Math.ceil(props.floor / 10) * 10; db <= props.floor + props.span; db += 20)
      out.push({ kind: 'axis', text: db + ' dB', pos: new THREE.Vector3(-W / 2 - 0.3, yOf(db, props.floor, props.span), -D / 2) })
    out.push(
      { kind: 'title', text: 'Frequency, kHz →', pos: new THREE.Vector3(0, 0, D / 2 + 0.5) },
      { kind: 'title', text: 'Time →', pos: new THREE.Vector3(W / 2 + 0.75, 0, 0) },
      { kind: 'title', text: 'Power ↑', pos: new THREE.Vector3(-W / 2, H + 0.18, -D / 2) },
    )
    return out
  }, [props.floor, props.span, props.hero, gone])

  return (
    <div
      className={'plot terrain' + (props.hero ? ' hero' : '')}
      style={{ cursor: props.hero ? 'default' : 'grab' }}
      onPointerDown={(e) => { if (props.hero) return; drag.current = { x: e.clientX, y: e.clientY }; (e.currentTarget as Element).setPointerCapture(e.pointerId) }}
      onPointerMove={(e) => {
        const t = view.current
        if (!drag.current || !t) return
        t.az = Math.max(-1.2, Math.min(1.2, t.az - (e.clientX - drag.current.x) * 0.005))
        t.el = Math.max(0.15, Math.min(1.4, t.el + (e.clientY - drag.current.y) * 0.004))
        drag.current = { x: e.clientX, y: e.clientY }
      }}
      onPointerUp={() => (drag.current = null)}
      onWheel={(e) => { const t = view.current; if (!props.hero && t) t.zoom = Math.max(0.5, Math.min(2, t.zoom * (e.deltaY > 0 ? 1.08 : 0.93))) }}
      onDoubleClick={() => (view.current = null)}
    >
      <Canvas key={theme} dpr={[1, 2]} camera={{ fov: 30, near: 0.1, far: 60 }} gl={{ antialias: true, powerPreference: 'high-performance' }}
        fallback={<div className="t-fallback">3D needs WebGL, which is not available here. Switch to 2D.</div>}
        onCreated={({ scene }) => { scene.background = new THREE.Color(css(props.hero ? '--ink-0' : '--ink-1')) }}>
        <Rig view={view} hero={props.hero} />
        <Surface {...props} />
        {!props.hero && <AxisFrame floor={props.floor} span={props.span} />}
        <Projector labels={labels} els={els} />
        {theme !== 'paper' && (
          <EffectComposer multisampling={4}>
            <Bloom mipmapBlur intensity={props.hero ? 1.5 : 1.0} luminanceThreshold={0.62} luminanceSmoothing={0.25} radius={0.7} />
            <Vignette offset={0.3} darkness={props.hero ? 0.75 : 0.45} />
          </EffectComposer>
        )}
      </Canvas>
      {labels.map((l, i) => (
        <div key={i} ref={(el) => { els.current[i] = el }} className={'t-label ' + l.kind}>
          {l.kind === 'emitter' ? (
            <>
              <span className="t-stem" />
              <span className="t-box"><b>{l.text}</b>{l.sub && <em>{l.sub}</em>}</span>
            </>
          ) : l.text}
        </div>
      ))}
      {!props.hero && (
        <>
          <div className="ax-title" style={{ right: 12, bottom: 10 }}>DRAG TO TURN · WHEEL TO ZOOM · DOUBLE-CLICK TO RESET</div>
        </>
      )}
    </div>
  )
}
