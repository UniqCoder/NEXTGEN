"""L0 kernels. NumPy reference implementations; the C++ (pybind11) kernels of WP05 will sit behind
these same functions and must produce identical bits (PRD §15, kill-matrix row "− C++ kernels")."""
from .viterbi import trellis, conv_encode, viterbi_soft

BACKEND = "numpy"
__all__ = ["trellis", "conv_encode", "viterbi_soft", "BACKEND"]
