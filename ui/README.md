# SANJAYA UI

Front-end for SIH 2026 PS 26147. React 19 + three.js (R3F), Vite. Runs fully offline; fonts are self-hosted.

    npm install
    npm run dev        # http://localhost:5173
    npm run build      # static bundle in dist/, to be wrapped by Tauri

For live analysis, build the UI and start the local engine:

    npm run build
    cd ../engine
    python -m sanjaya serve --open

The engine URL carries a per-launch token. Upload a recording or select a built-in sample. Without the engine, the UI clearly labels its walkthrough as demo data. The current blind decoder covers BPSK/QPSK with a rate-1/2 convolutional code and block interleaver; other known-recipe decoders are described in `../PROTOTYPE_AUDIT.md`.

Keys: Ctrl K palette · A autopilot · P prove · T 3D · E expert · \ paper theme · Alt 1-5 steps · Esc skip proof.

3D terrain: drag or use arrow keys to rotate, wheel or +/- to zoom, double-click or Home to reset. The landing model supports the same controls.
