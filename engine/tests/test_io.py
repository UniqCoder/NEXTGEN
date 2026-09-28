"""Raw IQ ingestion must honour the override offered by the UI and reject truncated pairs."""
import numpy as np
import pytest

from sanjaya.io import read_raw


@pytest.mark.parametrize("dtype,scalar,scale", [
    ("cf32_le", "<f4", 1.0), ("cf32_be", ">f4", 1.0),
    ("ci16_le", "<i2", 1 / 32768), ("ci16_be", ">i2", 1 / 32768),
])
def test_raw_iq_endianness(tmp_path, dtype, scalar, scale):
    path = tmp_path / "capture.iq"
    np.array([100, -200, 300, -400], dtype=scalar).tofile(path)
    np.testing.assert_allclose(read_raw(path, dtype), np.array([100-200j, 300-400j]) * scale)


def test_raw_iq_truncated_pair_is_rejected(tmp_path):
    path = tmp_path / "capture.iq"
    path.write_bytes(b"\x00\x00\x00\x00\x01")
    with pytest.raises(ValueError, match="whole number"):
        read_raw(path, "ci16_le")
