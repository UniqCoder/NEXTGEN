"""L0 kernels. NumPy reference implementations; the C++ (pybind11) kernels of WP05 will sit behind
these same functions and must produce identical bits (PRD §15, kill-matrix row "− C++ kernels")."""
from .viterbi import trellis, conv_encode, viterbi_soft
from .rs import rs_encode, rs_decode, bits_to_symbols, symbols_to_bits

BACKEND = "numpy"
__all__ = ["trellis", "conv_encode", "viterbi_soft", "rs_encode", "rs_decode", "bits_to_symbols", "symbols_to_bits", "BACKEND"]
