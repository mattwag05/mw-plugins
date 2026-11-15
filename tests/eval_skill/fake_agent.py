"""Deterministic stand-in for pi: follows the codeword skill exactly."""
from pathlib import Path
Path("answer.txt").write_text(Path("CODEWORD.txt").read_text().strip()[::-1] + "\n")
