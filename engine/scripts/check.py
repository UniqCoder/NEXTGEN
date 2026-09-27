"""Run every CI check locally and offline: engine layering rule (PRD §6.4) + the test suite.
Usage: python scripts/check.py"""
import ast, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "sanjaya"
# a module may import only from packages of equal or lower rank (recipe is the shared schema)
RANK = {"recipe": 0, "kernels": 0, "dsp": 1, "io": 1, "measure": 2, "classify": 4, "demod": 5, "coding": 6, "bits": 7, "chain": 7,
        "pipeline": 8, "proof": 9, "search": 9, "sufficiency": 9, "stitch": 9, "api": 10, "gen": 10, "compiler": 10, "cli": 11, "__main__": 11}


def layering() -> list[str]:
    errs = []
    for f in PKG.rglob("*.py"):
        parts = f.relative_to(PKG).with_suffix("").parts
        if parts == ("__init__",):
            continue
        own, package = parts[0], parts[:-1]
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.level:
                resolved = package[: len(package) - (node.level - 1)] + tuple((node.module or "").split(".") if node.module else ())
                target = resolved[0] if resolved else None
                if target in RANK and RANK[target] > RANK[own]:
                    errs.append(f"{f.relative_to(ROOT)} imports higher layer '{target}'")
    return errs


def main():
    errs = layering()
    for e in errs:
        print("LAYERING:", e)
    print(f"layering: {'FAIL' if errs else 'ok'}")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    sys.exit(1 if errs or r.returncode else 0)


if __name__ == "__main__":
    main()
