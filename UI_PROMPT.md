# UI Design Prompt: SANJAYA (SIH 2026 PS 26147, NTRO)

> Paste everything below the line into Claude / v0 / Cursor / any agent. It is self-contained.

---

## ROLE

You are a principal product designer and senior creative engineer. You have worked on instrument-grade software at companies like Linear, Teenage Engineering, Palantir, Bloomberg and Vercel. You are allergic to AI-generated UI. Every choice has to be defensible to a jury of NTRO signal-intelligence analysts **and** to a design director at a top studio.

Your job: design and build the front-end of **SANJAYA**, a desktop signal-analysis instrument. It should look and feel like it came from a company worth a billion dollars that has never shipped a template in its life.

## THE PRODUCT (read carefully, the design must come from this, not from a template)

**SANJAYA** is an offline analyst tool. You load a raw radio recording (`.wav` or `.IQ`). It automatically works out everything about the transmission: modulation (PSK/QAM/FSK), sample rate, baud, carrier. It then demodulates, finds and undoes the interleaver (block / convolutional / diagonal / PN), finds the error-correcting code (convolutional, RS, LDPC) and the scrambler, and decodes the bits into header and payload.

**The core idea, which the UI must make visible: "analysis by synthesis, with proof."** Once decoded, SANJAYA re-builds the waveform from the decoded bits, subtracts it from the recording, and checks that what is left is pure white noise. If it is, SANJAYA issues a signed **Decode Certificate**. Nobody else does this. The single most important moment in the product is when the analyst presses **PROVE**, the signal *disappears* from the spectrum, and only noise is left.

**The name.** Sanjaya is the figure in the Mahabharata who was given divine sight to see a distant battlefield and describe it truthfully. The brand idea is **"seeing what is far away, and telling the truth about it."** Express this through restraint, clarity and precision. Do **not** use literal Indian ornament, mandalas, or mythology illustrations.

**The users.** Government signal analysts working on air-gapped machines. They are experts. They want density, speed, keyboard control and evidence, not marketing. The product must feel calm and in control, like a precision instrument (a Leica, a Swiss oscilloscope, a Teenage Engineering OP-1), not like a sci-fi hacker movie.

### The 8-stage loop (this is the product's spine; show it everywhere)
`1 OBSERVE → 2 MEASURE → 3 HYPOTHESISE → 4 DEMODULATE → 5 UNWRAP → 6 STRUCTURE → 7 PROVE → 8 LEARN`
If the proof fails at stage 7, it loops back to 3 with the next-best hypothesis. If it passes, the decoded signal is subtracted and the scene is re-scanned for hidden, weaker signals.

### Features that need UI
1. **Ingest & Forensics.** Drop a file. Auto-detect dtype, endianness and metadata (SigMF). Flag DC offset and IQ imbalance. Anything ambiguous is shown as a set of hypotheses, never as a silent guess.
2. **Scene mode.** A wideband view with every detected emitter boxed and labelled. Pressing PROVE on one emitter removes it and reveals a weaker hidden signal underneath ("hidden-signal reveal").
3. **Linked signal views.** Waterfall, PSD, constellation (animated over time), eye diagram, instantaneous frequency, cyclic spectrum. Brushing time or frequency in one view updates all the others.
4. **Modulation ID with honesty.** The output is calibrated probabilities per candidate *plus* a conformal *prediction set* ("QPSK or 8PSK, 95% coverage"). Never show an uncalibrated "98.7% confident". A **NOVEL** state for unknown signals, and a "Teach" flow that learns a new class from about 5 examples.
5. **Unwrap panel.** Interleaver rank-profile plot with a visible dip at the true period, code parameters, and the scrambler polynomial. **Expert mode** lets the analyst override any stage and re-run only what comes after it.
6. **Signal Genome.** Matches the signal to about 30 named standards (e.g. STANAG 4285, NAVTEX, RTTY) and back-solves the true sample rate and clock ppm.
7. **Bit-Lens.** An aligned-frame raster whose width you can drag; the bits snap into columns when the width is right. Per-bit entropy heat map. An autocorrelation plot of the bit stream. Auto-labelled fields, grouped under the literal words **HEADER** and **PAYLOAD**: `HEADER [ SYNC | COUNTER | LEN ] | PAYLOAD | CRC-16 (poly shown)`. An encryption-likelihood flag. Schema export.
8. **Proof-of-Decode & Certificate.** Residual waterfall, a whiteness-test result, and "explained energy %". The **Decode Certificate** includes the file hash, every parameter with its evidence and its confidence set, and a signature. Exports as PDF and JSON.
9. **Autopilot vs Expert.** One click runs the whole chain in Autopilot. Expert mode exposes every stage.
10. **Mystery-Signal Challenge (demo mode).** A judge picks the modulation, interleaver, code and scrambler blind. SANJAYA recovers them all live, and the screen reveals the results against the judge's choices.

## PROBLEM-STATEMENT COMPLIANCE (non-negotiable; this overrides every design choice below)

This UI is judged against the official SIH PS 26147 text. If a design idea conflicts with this section, this section wins.

**The official text says:** *"The GUI based model will take .IQ or .wav file as input and: (i) identify signal parameters (Sampling frequency, Modulation, FEC, Interleaving); (ii) demodulate signals (FSK, QAM, PSK); (iii) de-interleave (Block, Convolution, Diagonal, Pseudo Random); (iv) FEC (short-constraint convolutional codes with Viterbi decoding, RS block codes, Concatenated codes, LDPC); (v) bit stream correlation. Expected solution: improve feature visibility of signals with the help of GUI, enable automated signal analysis to identify spectral features such as sampling frequency, constellation plot, water fall (time-frequency domain), demodulate, de-interleave, error-correct, and correlate the bit stream to identify header and payload."*

### C1. Every clause gets a visible, labelled home in the UI
Build this matrix into the app as a **Compliance view** (it doubles as a demo checklist). Every row must be reachable in 2 clicks or fewer from the Workspace.

| PS clause | Where it lives in the UI | What must be visible |
|---|---|---|
| Input: .IQ **or** .wav | Ingest | Both accepted by drag-drop and file dialog, and the detected format is shown |
| (i) Sampling frequency | Parameters panel | **File sample rate** *and* **symbol (baud) rate**, both shown and labelled. The PS wording is ambiguous, so show both |
| (i) Modulation | Parameters panel | Type + order, with a calibrated probability per candidate |
| (i) FEC | Parameters panel | Code type + parameters (rate, K, polynomials / RS n,k / LDPC n,k) |
| (i) Interleaving | Parameters panel | Type + size / period |
| (ii) Demodulate FSK, QAM, PSK | Demod view | All three families work, each with the view that suits it (below), producing a bit stream |
| (iii) Block, Convolutional, Diagonal, Pseudo-random | Unwrap view | All **four** types named explicitly, auto-detected, with manual selection |
| (iv) Conv + Viterbi, RS, Concatenated, LDPC | Unwrap view | All four named. Concatenated codes are shown as an explicit chain (outer RS → interleaver → inner conv) |
| (v) Bit stream correlation | Bit-Lens view | A real **autocorrelation plot** of the bit stream, plus sync-word search and frame alignment |
| Spectral features: sampling frequency, constellation plot, waterfall | Workspace default layout | **Waterfall, constellation and PSD are all visible on first load**, with no toggles or extra clicks |
| Header and payload identification | Bit-Lens view + Certificate | Frames split and labelled with the literal words **HEADER** and **PAYLOAD** |
| Automated | Autopilot (default mode) | One click goes from raw file to header/payload, with no mandatory user input |
| Additional features if feasible | Everything else | Scene mode, Proof, Genome, Teach, Challenge. These are **extras layered on top** and must never be required to reach the core output |

### C2. Use the official terms first, brand names second
Judges scan the screen for the words in the PS. Primary labels must use them: **Sampling Frequency, Modulation, FEC, Interleaving, De-interleaving, Demodulation, Constellation, Waterfall, Bit Stream Correlation, Header, Payload.** Brand names are allowed only as secondary labels, e.g. "Bit Stream Correlation · *Bit-Lens*" or "Standard Recognition · *Signal Genome*". Never replace an official term with a brand name.

### C3. .wav and .IQ are handled differently, and the UI shows it
- The Ingest screen shows which path the file took: **WAV (header read: Fs, bit depth, channels)** or **Raw IQ (headerless, format inferred)**.
- For .wav, it shows whether the file is real audio (e.g. AFSK after a receiver) or a 2-channel file interpreted as I/Q.
- For raw .IQ, it shows the inferred dtype (int8/int16/float32/complex64), endianness and I/Q order, each with a confidence. There must be a **manual override form** for dtype, sample rate, centre frequency and endianness, and a "re-run" button. A wrong guess must never be silent.
- It reads SigMF `.sigmf-meta` sidecars if present.

### C4. Frequencies from a few kHz to GHz, across HF, VHF and UHF
- Axis and readout units auto-scale (Hz / kHz / MHz / GHz) and are always shown next to the number.
- Show the centre frequency and the band (HF / VHF / UHF) when they are known. Allow the analyst to enter them.
- Nothing in the layout may assume a fixed sample rate, bandwidth or band.

### C5. Demodulation views that suit each family
- **PSK / QAM:** constellation (with the locking animation), eye diagram and EVM.
- **FSK:** a constellation is meaningless for FSK, so show the **instantaneous-frequency trace, tone markers on the PSD, and the tone spacing and deviation** instead. The panel layout must switch to this automatically when FSK is detected.
- All families show the recovered bit/symbol stream, which can be exported.

### C6. "Improve feature visibility": 2D analysis is always the default
- The 3D waterfall terrain is an **optional view** (`T` to tilt). The default is a standard flat 2D waterfall with frequency on the x-axis, time on the y-axis, a colour scale, a legend and a readable axis. 3D must never be the only way to see anything.
- Every plot has zoom, pan, cursors/markers, a readout on hover, and a visible colour-scale legend.
- The animation at the PROVE moment is **skippable** (click or Esc), it is disabled under reduced motion, and the residual stays fully inspectable afterwards as a normal 2D plot.

### C7. "Accuracy and confidence": show real numbers, calibrated and honest
- Every extracted parameter shows its **confidence value** (a calibrated probability, e.g. `QPSK 0.91 · 8PSK 0.07`). The PS explicitly cares about "accuracy and confidence". The conformal prediction set is shown *alongside* these probabilities.
- Each result is tagged with its method: **Blind-recovered** vs **Matched from library** vs **Manually set**. This is especially important for LDPC and pseudo-random interleavers, where fully blind recovery is only partly possible. Never overclaim.
- If the payload looks encrypted, show **"high-entropy payload, likely encrypted; decryption is out of scope"**. Never imply that it has been decrypted.

### C8. Results must feed "designated sensors"
Export results in formats another system can use: **JSON parameter report, SigMF annotations, decoded bit stream (.bin / hex), header/payload map (CSV), and the PDF Decode Certificate.** Also batch export when several files are processed.

### C9. Offline, sovereign, runs on a laptop
The app runs fully offline on Windows and Linux. The back-end stays as the plan specifies (Python / C++, with GNU Radio integration, as the PS suggests). The React UI is only the front-end.

## HARD CONSTRAINTS

- **Offline and air-gapped.** No CDN, no Google Fonts at runtime, no telemetry, no external calls. Self-host every font and asset. Ship as a **Tauri** desktop app (React front-end, local Python engine over a WebSocket/HTTP on localhost).
- **Performance.** 100 MB+ recordings. Every view must be interactive in under 2 s. Waterfalls and constellations render on the GPU (WebGL/three.js). Heavy maths runs in Web Workers. Use decimated level-of-detail tiles. Hold 60 fps while scrubbing.
- **Density over air.** This is an instrument, not a landing page. A 1440p screen should show 6+ live panels without scrolling.
- **Keyboard-first.** A command palette (⌘K), a shortcut for every action, and focus rings that are designed, not browser defaults.
- **Accessible.** WCAG AA contrast on all text. Don't use colour as the only signal (pair it with shape and label). Respect `prefers-reduced-motion`.

## THE ANTI-SLOP CONTRACT (break any of these and the design fails)

Never use:
- purple/blue/cyan gradients, gradient text, "aurora" or mesh-blob backgrounds, glowing orbs
- glassmorphism on every card, `backdrop-blur` as decoration
- neon "cyber / military-grade" styling, HUD brackets, scanlines, matrix rain, fake terminal typing
- Inter, Roboto, Poppins or the default system stack; untouched shadcn defaults; `rounded-2xl` on everything; soft grey drop shadows on every card
- Lucide icons at default stroke, used as decoration; emoji in the UI
- bento-grid feature tiles; hero sections; "✨ AI-powered" copy; fake stats; fake percentages
- particle fields, starfields or spinning globes that are not driven by real data
- every card the same size, every gap the same, every button the same weight

The rule for three.js: **3D is only allowed where the data really has a third dimension.** No decorative 3D. Ever.

## DESIGN DIRECTION: "Instrument, not dashboard"

### Identity in one line
*A quiet, exact, warm-dark precision instrument with one living colour, where the only drama is the truth being revealed.*

### Colour (define as CSS variables / tokens; don't use Tailwind's default palette)
- **Ink** (background): warm graphite, not blue-black. About `#0F0F0D`, with raised surfaces at `#161614` and `#1D1D1A`. Build layers from 1px hairlines (`#2A2A26`), not from shadows.
- **Bone** (primary text): about `#E9E5DA`. Secondary text about `#9C978A`. Tertiary about `#5E5A52`.
- **Signal** (the single brand accent): saffron/turmeric amber, about `#FF8A1F`. Use it only for "live signal energy", the active selection and the primary action. Spend it sparingly; it should feel like a lit valve.
- **Proof** (reserved): a mineral green, about `#7FD6A4`. It appears **only** when something is mathematically proven (PASS, certificate). It must be rare enough that seeing it feels earned.
- **Fault**: oxide red, about `#E5484D`, for failed proofs.
- **Data colour maps**: a custom perceptually uniform ramp from ink to bone to amber for waterfalls (not "jet", not "viridis" by default). Provide a colour-blind-safe alternative.
- Also ship a **light "paper" theme** (warm paper `#F3F0E8`, ink text) for printing certificates and daytime use.

### Typography (self-hosted)
- **UI / display:** a grotesk with character, e.g. *Neue Haas Grotesk / Söhne* if licensed; free fallback *Hanken Grotesk* or *Schibsted Grotesk*. Set tight, confident sizes; large numerals for key measurements.
- **Data / mono:** *Berkeley Mono* if licensed; free fallback *Martian Mono* or *JetBrains Mono*. All numbers use tabular figures. Units are set smaller and dimmer than the value (`2 400` <sub>baud</sub>).
- **Signature detail:** section labels in small uppercase mono with wide tracking and stage numbers (`05 — UNWRAP`), like labels on lab equipment.
- Use a real type scale (for example 11 / 12 / 13 / 15 / 20 / 28 / 44 / 72), and use the extremes on purpose.

### Shape, space and material
- Radius: 2–4 px on controls and 0 px on data panels. Sharp edges read as precise.
- A strict 4 px grid. Panels are separated by 1 px hairlines, like a machined faceplate.
- Texture: a very subtle film grain (2–3% noise) on the base surface only, so it feels like an object and not a flat screen.
- Controls should feel physical: segmented switches, detented sliders with tick marks, rotary knobs for gain and zoom (drag vertically, scroll to fine-tune), and numeric scrub-on-drag fields like in Figma or Blender.

### Motion (Motion / Framer Motion + GSAP where it fits)
- Default: fast and mechanical. 120–180 ms, custom ease `cubic-bezier(0.2, 0, 0, 1)`. No bounce and no springiness in data UI.
- Transitions carry state: a hypothesis card that becomes proven *morphs* into the certificate line item (shared-layout animation).
- The stage rail animates the loop live: the active stage pulses once, and a failed proof visibly routes back from 7 to 3.
- Save the big motion budget for the **three signature moments** below.

## SIGNATURE MOMENTS (these are what make it unforgettable; build them with care)

1. **The Waterfall Terrain (three.js / React Three Fiber).** The spectrogram as a real 3D height-field: time runs away from the viewer, frequency across, power as height and colour. It is flat 2D by default for analysis; press `T` to tilt smoothly into 3D terrain. Use a custom shader for the colour ramp and a soft falloff into fog. It is lit like a physical relief map, not glowing.
2. **PROVE.** The analyst presses PROVE (or holds `P`). The recording's terrain and the re-synthesised terrain line up, and the signal ridge *sinks* into the noise floor in a 1.2 s shader-driven dissolve that leaves flat, white, grainy noise. The residual histogram settles onto the Gaussian curve. The whiteness test ticks to PASS in Proof green, the first green on the screen. Then the Decode Certificate "prints": it slides up like a thermal receipt, lines appearing one after another, with the hash and signature last. If the proof fails, the ridge does not sink, a red residual band stays, and the stage rail routes back to 3. Failure must look honest and designed, not like an error toast.
3. **Bit-Lens snap.** A noisy field of bits (instanced meshes or a WebGL canvas). The analyst drags the frame width, and at the correct width the chaos snaps into clean vertical columns with a mechanical detent. Fields then label themselves with bracket annotations, and the CRC polynomial types in.

Secondary moments: the constellation "locking" (the cloud tightens into points as the PLL converges, with trails fading over time); a hidden signal fading into view after cancellation; the rank-profile dip drawing itself with a callout "period = 48".

## LAYOUT & SCREENS

1. **Launch / Ingest.** An almost empty ink canvas. The wordmark SANJAYA in small caps, a single drop target drawn as a thin frame with corner ticks, and recent files as a dense mono table (hash, size, date, verdict). No hero, no illustration.
2. **Workspace (main screen).**
   - Top: a slim title bar with file name, hash and format, plus an **Autopilot / Expert** segmented switch and the ⌘K hint.
   - Left: a **stage rail** (01–08) in a vertical strip, each stage showing status (pending / running / proven / failed / overridden) using glyph and colour.
   - Centre: a dockable, resizable panel grid (dockview or react-mosaic). By default: a 2D Waterfall (large), PSD under it, Constellation and Eye on the right. For FSK, Constellation and Eye are replaced by the instantaneous-frequency view.
   - Right: a **Parameters panel** at the top, always visible. It shows Sampling Frequency (file Fs + symbol rate), Modulation, FEC, Interleaving, SNR, bandwidth and centre frequency, each with a confidence value and method tag. Below it is an **Evidence inspector**. For each parameter it shows the value, the evidence behind it (a small inline plot) and the confidence set. Clicking a value opens the plot that proves it.
   - Bottom: a timeline scrubber showing the whole file's energy envelope as a minimap, with the brushed time range highlighted.
3. **Scene view.** A wideband waterfall with emitters boxed and labelled in the margin, like labels on a technical drawing. Actions on each emitter: Isolate, Decode, Prove & Cancel.
4. **Unwrap view.** The rank-profile plot, code search progress, and scrambler recovery, shown as a readable chain of transforms.
5. **Bit-Lens view.** The raster, entropy map, field table and schema export.
6. **Certificate view.** A document-quality layout (paper theme) that is print-ready, with a QR code / hash block and a signature.
7. **Genome library.** A dense catalogue of about 30 standards, each with a small spectral fingerprint thumbnail.
8. **Challenge mode.** A full-screen presentation layout for judges: their blind picks on the left, SANJAYA's live recovery on the right, and each parameter flipping to a match as it is proven.

Empty, loading, ambiguous, failed and NOVEL states must all be designed. Loading shows real progress per stage. There are no generic spinners anywhere.

## TECH STACK & COMPONENT SOURCES

- **App:** React 19 + TypeScript + Vite, inside **Tauri 2**. State: Zustand. Styling: Tailwind v4 with a **fully custom theme from the tokens above** (or vanilla-extract).
- **Primitives (behaviour only, fully restyled):** Radix UI / Base UI, `cmdk` (command palette), `sonner` (restyled into a quiet mono log line), `vaul`, `react-resizable-panels` or `dockview`.
- **3D and GPU:** `three`, `@react-three/fiber`, `@react-three/drei`, `@react-three/postprocessing` (use only subtle grain, gentle bloom on the amber and depth-of-field on tilt), and custom GLSL shaders for the waterfall and the dissolve. `regl` or `twgl` is allowed for raw 2D GPU plots.
- **2D plots:** `uPlot` for high-speed PSD and time series; `visx` / `d3-scale` for bespoke annotated plots such as the rank-profile and entropy maps. Draw axes, ticks and labels yourself, in the type system above.
- **Motion:** `motion` (Framer Motion) for UI; GSAP for the timed PROVE and certificate sequences.
- **Inspiration libraries.** React Bits, Magic UI, Aceternity, Origin UI, 21st.dev, Codrops and the three.js examples are allowed **as sources of techniques only**. Take the mechanic (a shader, a reveal, a text scramble) and rebuild it in this design language. Never paste a component in with its default look; that is exactly how every AI app ends up looking the same.
- **Reference quality bar:** Linear (craft and speed), Teenage Engineering (physical controls, restraint), Vercel / Geist (typographic discipline), Palantir Gotham (analyst density), Bloomberg Terminal (information per pixel), Stripe Press (warmth, paper theme), Rauno Freiberg's and Emil Kowalski's interaction craft, and Ableton / Blender (pro-tool ergonomics).

## PROCESS (follow in order; show output at each step)

0. **Compliance matrix first.** Before any visual work, reproduce table C1 and map each row to a screen and component. Re-check it after every step.
1. **Design brief back to me.** A 10-line restatement of the identity, and 3 rejected directions with the reason each was rejected.
2. **Tokens first.** `tokens.css` covering colour (both themes), type scale, spacing, radii, motion curves, z-layers and data colour maps. Nothing is hard-coded after this.
3. **Core instrument components.** Knob, detented slider, scrub-number field, segmented switch, stage rail item, evidence row, panel frame with header, and plot axis. Show every state of each.
4. **Workspace screen** with static mock data (a synthetic QPSK + convolutional code + block-interleaver file).
5. **Signature moments.** Waterfall terrain, then PROVE, then Bit-Lens snap. Each is isolated, tunable with Leva in dev, and has a reduced-motion fallback.
6. **Remaining screens**, then empty, error and NOVEL states.
7. **Self-critique pass.** Screenshot every screen and score it against the Anti-Slop Contract and the reference bar. Fix every violation before calling it done.

## ACCEPTANCE TEST

- **Can a judge holding the PS text tick off every clause (i)–(v), plus waterfall, constellation, sampling frequency and header/payload, on screen, using the PS's own words? This must pass. Any other failure is secondary.**
- Does one Autopilot click on a raw .IQ file *and* on a .wav file reach a labelled HEADER/PAYLOAD map with no required input?
- Are all four interleaver types and all four FEC families named and selectable?
- Does every parameter show a confidence value and a Blind / Library / Manual tag?
- Does FSK get frequency-domain views instead of a meaningless constellation?
- Can every result be exported as JSON / SigMF / bits / PDF?
- Cover the logo. Could a designer tell this is not a template, and not AI-generated? It must pass.
- Could an NTRO analyst load a file and reach a certificate without reading docs? It must pass.
- Is there exactly one accent colour in use, and does green appear only on proofs?
- Does every 3D element encode real data?
- Is the app offline-clean (zero network requests) and does it scrub a 100 MB file at 60 fps?
- Does the PROVE moment give a first-time viewer chills?
