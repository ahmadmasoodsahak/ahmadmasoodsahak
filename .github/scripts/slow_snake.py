from __future__ import annotations

import argparse
import re
from pathlib import Path


def slow_svg(path: Path, factor: float) -> None:
    source = path.read_text(encoding="utf-8")
    updated = re.sub(
        r"(?<![\w.])(\d+)ms",
        lambda match: f"{round(int(match.group(1)) * factor)}ms",
        source,
    )
    path.write_text(updated, encoding="utf-8")


parser = argparse.ArgumentParser(description="Slow generated snake SVG animations.")
parser.add_argument("paths", nargs="+", type=Path)
parser.add_argument("--factor", type=float, default=2.0)
args = parser.parse_args()

for svg_path in args.paths:
    slow_svg(svg_path, args.factor)

