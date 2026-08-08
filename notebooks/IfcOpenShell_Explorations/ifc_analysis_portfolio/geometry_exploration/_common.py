"""_common.py — shared helpers for the geometry_exploration scripts.

Not a script itself; imported by 01-05.
"""

import sys
from pathlib import Path

import ifcopenshell

# The model these scripts were written and tested against. Override on the
# command line: `python 0N_whatever.py path\to\other.ifc`.
DEFAULT_IFC_PATH = (
    r"C:\Users\ReDI\Documents\GitHub\2026_GREAM\project\local_ifcopenshell"
    r"\IfcOpenShell_Explorations\ifc_analysis_portfolio\building_smart-samples\Infra-Rail.ifc"
)


def open_model() -> "ifcopenshell.file":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_IFC_PATH)
    if not path.exists():
        sys.exit(f"path does not exist: {path}")
    print(f"# opened {path.name} ({path.stat().st_size / 1024:.0f} KB)\n")
    return ifcopenshell.open(str(path))


def style_summary(style) -> str:
    """Best-effort description of an ifcopenshell.geom style/material object.

    The attribute surface documented at
    docs/ifcopenshell-python/geometry_processing.rst (`original_name()`,
    `has_diffuse`, `has_transparency` as a bool) does not match what this
    installed build (ifcopenshell 0.8.5) actually exposes on the SWIG
    `style` wrapper: there is no `original_name()`/`has_diffuse`, and
    `has_transparency` is a *method*, not a property. `diffuse` is always
    present as a `colour` object with `.r()`/`.g()`/`.b()` rather than a
    plain tuple.

    This is a good example of why it's worth introspecting the installed
    API (`dir(obj)`) rather than trusting docs blindly across versions —
    see the README for how this was diagnosed.
    """
    bits = [f"name={style.name!r}"]

    diffuse = getattr(style, "diffuse", None)
    if diffuse is not None:
        bits.append(f"diffuse=({diffuse.r():.3f}, {diffuse.g():.3f}, {diffuse.b():.3f})")

    has_transparency = getattr(style, "has_transparency", None)
    if callable(has_transparency) and has_transparency():
        bits.append(f"transparency={style.transparency:.3f}")

    return ", ".join(bits)
