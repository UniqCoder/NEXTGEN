"""L7 structure: CRC over bit arrays and frame field helpers."""
import numpy as np


def crc_bits(bits: np.ndarray, width: int, poly: int, init: int, refin=False, refout=False, xorout=0) -> int:
    """Bitwise CRC over a uint8 0/1 array (MSB-first bytes when refin=False)."""
    b = np.asarray(bits, np.uint8)
    if refin:                                                   # reflect each input byte
        b = b.reshape(-1, 8)[:, ::-1].ravel()
    top, mask, reg = 1 << (width - 1), (1 << width) - 1, init
    for bit in b.tolist():
        fb = ((reg & top) != 0) ^ bit
        reg = ((reg << 1) & mask) ^ (poly if fb else 0)
    if refout:
        reg = int(f"{reg:0{width}b}"[::-1], 2)
    return reg ^ xorout


def to_bits(value: int, width: int) -> np.ndarray:
    return np.array([(value >> (width - 1 - i)) & 1 for i in range(width)], np.uint8)


def from_bits(b: np.ndarray) -> int:
    v = 0
    for x in np.asarray(b).tolist():
        v = (v << 1) | int(x)
    return v
