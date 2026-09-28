"""L1 I/O: SigMF, raw interleaved IQ with an explicit dtype, and PCM/float WAV.
The full R-01 container and dtype matrix remains future work."""
import hashlib, json
from pathlib import Path
import numpy as np

RAW = {"cf32_le": ("<f4", 1.0), "cf32_be": (">f4", 1.0),
       "ci16_le": ("<i2", 1 / 32768), "ci16_be": (">i2", 1 / 32768),
       "ci8": ("i1", 1 / 128), "cu8": ("u1", None)}


def _to_complex(raw: np.ndarray, dtype: str) -> np.ndarray:
    v = raw.astype(np.float32)
    if dtype == "cu8":
        v = (v - 127.5) / 127.5
    else:
        v *= RAW[dtype][1]
    return (v[0::2] + 1j * v[1::2]).astype(np.complex64)


def read_raw(path: str | Path, dtype: str) -> np.ndarray:
    if dtype not in RAW:
        raise ValueError(f"unsupported dtype {dtype}; supported: {sorted(RAW)}")
    scalar = np.dtype(RAW[dtype][0])
    size = Path(path).stat().st_size
    if size % (2 * scalar.itemsize):
        raise ValueError(f"raw IQ byte length {size} is not a whole number of {dtype} I/Q pairs")
    raw = np.fromfile(path, scalar)
    return _to_complex(raw, dtype)


def sigmf_paths(path: str | Path) -> tuple[Path, Path]:
    p = Path(path)
    base = p.with_suffix("") if p.suffix in (".sigmf-data", ".sigmf-meta") else p
    return base.with_suffix(".sigmf-data"), base.with_suffix(".sigmf-meta")


def load(path: str | Path, fs: float | None = None, dtype: str | None = None) -> tuple[np.ndarray, float, Path]:
    """Returns (complex64 samples, sample rate, data file path)."""
    p = Path(path)
    if p.suffix in (".sigmf-data", ".sigmf-meta"):
        data, meta = sigmf_paths(p)
        if meta.exists():
            g = json.loads(meta.read_text())["global"]
            return read_raw(data, g["core:datatype"]), float(g["core:sample_rate"]), data
        if fs is None or dtype is None:                          # data uploaded without its sidecar
            raise ValueError("SigMF data without its .sigmf-meta: pass the sample rate and datatype")
        return read_raw(data, dtype), float(fs), data
    if p.suffix.lower() == ".wav":
        return read_wav(p) + (p,)
    if fs is None or dtype is None:
        raise ValueError("raw IQ needs --fs and --dtype until dtype sniffing lands (WP01)")
    return read_raw(p, dtype), float(fs), p


def write_sigmf(base: str | Path, x: np.ndarray, fs: float, extra: dict | None = None) -> Path:
    data, meta = sigmf_paths(Path(str(base) + ".sigmf-data"))
    data.parent.mkdir(parents=True, exist_ok=True)
    np.asarray(x, np.complex64).tofile(data)
    g = {"core:datatype": "cf32_le", "core:sample_rate": fs, "core:version": "1.0.0",
         "core:description": "SANJAYA-Gen", **(extra or {})}
    meta.write_text(json.dumps({"global": g, "captures": [{"core:sample_start": 0}], "annotations": []}, indent=1))
    return data


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_wav(path: str | Path) -> tuple[np.ndarray, float]:
    """PCM / float WAV. Two channels are read as I/Q; one channel (receiver audio) is lifted to its analytic
    signal, so an SSB audio tone at +1.8 kHz stays at +1.8 kHz with no mirror image. RF64 / auxi: WP01."""
    from scipy.io import wavfile
    fs, d = wavfile.read(path, mmap=True)
    d = np.asarray(d)
    scale = {np.dtype("uint8"): None, np.dtype("int16"): 1 / 32768, np.dtype("int32"): 1 / 2 ** 31}.get(d.dtype, 1.0)
    v = d.astype(np.float32)
    if scale is None:
        v = (v - 127.5) / 127.5
    else:
        v *= scale
    if v.ndim == 2 and v.shape[1] >= 2:
        x = v[:, 0] + 1j * v[:, 1]
    else:                                                          # WAV-lifting v0: real audio -> analytic signal
        from scipy.signal import hilbert
        x = hilbert(v.reshape(-1).astype(np.float64))
    return x.astype(np.complex64), float(fs)
