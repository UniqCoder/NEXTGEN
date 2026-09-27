"""L1 I/O. Schema-0.1 slice: SigMF (cf32_le, ci16_le) and raw interleaved IQ with an explicit dtype.
WAV families, dtype sniffing and forensics (R-01) arrive with WP01."""
import hashlib, json
from pathlib import Path
import numpy as np

RAW = {"cf32_le": ("<f4", 1.0), "ci16_le": ("<i2", 1 / 32768), "ci8": ("i1", 1 / 128), "cu8": ("u1", None)}


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
    raw = np.fromfile(path, RAW[dtype][0])
    return _to_complex(raw[: raw.size // 2 * 2], dtype)


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
    """PCM / float WAV. Two channels are read as I/Q; one channel as real samples (the spectrum is then
    mirrored; WAV-Lifting, C7, recovers complex baseband later). RF64 / auxi chunks arrive with WP01."""
    from scipy.io import wavfile
    fs, d = wavfile.read(path, mmap=True)
    d = np.asarray(d)
    scale = {np.dtype("uint8"): None, np.dtype("int16"): 1 / 32768, np.dtype("int32"): 1 / 2 ** 31}.get(d.dtype, 1.0)
    v = d.astype(np.float32)
    if scale is None:
        v = (v - 127.5) / 127.5
    else:
        v *= scale
    x = (v[:, 0] + 1j * v[:, 1]) if v.ndim == 2 and v.shape[1] >= 2 else v.reshape(-1).astype(np.complex64)
    return x.astype(np.complex64), float(fs)
