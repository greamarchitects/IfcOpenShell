#!/usr/bin/env python3
"""list_element_types.py — print the distinct IfcElement types in an .ifc model.

Metadata-only: this reads the model's entity table and doesn't touch
geometry, so it stays fast even on large files (contrast with the
ifcopenshell.geom serializer pattern, which triangulates everything and is
worth reaching for only when you actually need shapes/output geometry).

Usage:
    python list_element_types.py <file.ifc>            # one file
    python list_element_types.py <folder-of-.ifc-files>  # every .ifc inside

Examples (paths on this machine):
    python list_element_types.py ../model.ifc
    python list_element_types.py ../../AC20-FZK-Haus.ifc
    python list_element_types.py "C:\\Users\\ReDI\\Documents\\GitHub\\2026_GREAM\\project\\local_ifcopenshell\\IfcOpenShell_Explorations\\ifc_analysis_portfolio\\building_smart-samples"
"""

import sys
from collections import Counter
from pathlib import Path

import ifcopenshell


def element_type_counts(path: Path) -> Counter:
    """Open one .ifc file and count instances per IfcElement subtype."""
    model = ifcopenshell.open(str(path))
    return Counter(e.is_a() for e in model.by_type("IfcElement"))


def report(path: Path) -> None:
    counts = element_type_counts(path)
    total = sum(counts.values())

    print(f"==== {path.name} ====")
    print(f"{total} elements across {len(counts)} types\n")

    width = max((len(t) for t in counts), default=0)
    for element_type, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {element_type:<{width}}  {n}")
    print()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: list_element_types.py <file.ifc | folder-of-.ifc-files>")
        return 1

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"path does not exist: {target}", file=sys.stderr)
        return 1

    if target.is_dir():
        ifc_files = sorted(p for p in target.iterdir() if p.suffix.lower() == ".ifc")
        if not ifc_files:
            print(f"no .ifc files found in {target}", file=sys.stderr)
            return 1
        for p in ifc_files:
            report(p)
    else:
        report(target)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
