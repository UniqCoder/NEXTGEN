# NEXTGEN

Offline analysis of raw IQ and WAV signal recordings: measure the physical-layer parameters, blindly
identify the transmitter's coding recipe (modulation, forward error correction, interleaving, scrambling,
framing), and prove the recipe by resynthesising the transmission and subtracting it from the recording.
A signed certificate records what was found and how confidently.

## Why "prove", not just "guess"

Most signal-identification tools stop at a best-effort label. This one closes the loop: it rebuilds the
transmitted waveform from the bits it decoded, subtracts that reconstruction from the original recording,
and checks that what's left behaves like noise at every layer — physical, coding, and structural. If the
residual doesn't check out, the recipe is rejected rather than reported. The certificate that comes out the
other end is independently re-checkable from the recording alone.

## Layout

- `engine/` — the analysis engine (Python). Blind and known-recipe decoding, layered proof, certificate
  signing/verification, a compiler that turns a certified recipe into a standalone receiver, and a data-
  sufficiency estimator that says how much more recording would be needed when a decode is inconclusive.
- `ui/` — the front end (React + three.js). Drop a recording in, watch it move through signal → decode →
  header/payload → proof → certificate, with waterfall/constellation/eye visualisation at every step.

## Engine

```
cd engine
python -m sanjaya gen                       # synthetic test recording
python -m sanjaya analyze FILE               # blind: find the recipe and certify it
python -m sanjaya analyze FILE --recipe R.json   # known-recipe decode
python -m sanjaya verify FILE certificate.json   # independently re-check a certificate
python -m sanjaya serve --open               # local API for the UI
```

`python scripts/check.py` runs the full test suite plus an import-layering check.

## Coverage

- **Modulation:** BPSK, QPSK, 8PSK, 16-QAM, 64-QAM (known-recipe); BPSK/QPSK blind.
- **FEC:** convolutional (Viterbi), Reed–Solomon, concatenated (RS outer + convolutional inner), LDPC
  (min-sum belief propagation) — known-recipe. Convolutional is also blind-discoverable.
- **Interleaving:** block, diagonal, pseudo-random.
- **Framing:** sync-word correlation, CRC, counters, fixed/length fields — blind.

Frequency-shift-keyed signals are recognised (family, tone spacing, keying rate) but not yet decoded; that
receiver chain is architecturally different (non-coherent, no shared carrier-phase recovery) and is next.

## UI

```
cd ui
npm install
npm run dev
```

Runs standalone against bundled demo data, or against a running engine (`sanjaya serve`) for real analysis.

## Status

Working prototype. Known-recipe decoding and certification cover every modulation/FEC/interleaver family
listed above; blind (no supplied recipe) discovery currently covers BPSK/QPSK with a convolutional code and
a block interleaver. See the code for the honest, currently-reachable boundary of each capability — nothing
here overclaims what it can do on a file it hasn't seen before.
