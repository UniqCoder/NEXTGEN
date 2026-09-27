# SANJAYA UI

Front-end for an offline signal-analysis brief. React 19 + three.js (R3F), Vite. Runs fully offline; fonts are self-hosted.

    npm install
    npm run dev        # http://localhost:5173
    npm run build      # static bundle in dist/, to be wrapped by Tauri

The engine is not wired yet. `src/lib/mock.ts` is the demo scenario (synthetic spectrogram and bit frames);
autocorrelation, entropy, CRC search, WAV/SigMF header parsing and raw-IQ dtype sniffing are computed for real.
Replace `mock.ts` calls with the localhost engine API when it exists.

Keys: Ctrl K palette · A autopilot · P prove · T 3D · E expert · \ paper theme · Alt 1-5 steps · Esc skip proof.
