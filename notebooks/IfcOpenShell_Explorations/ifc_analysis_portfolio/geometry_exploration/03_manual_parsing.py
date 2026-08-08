"""03_manual_parsing.py — read geometry straight off the IFC entity graph.

Docs: docs/ifcopenshell-python/geometry_processing.rst, "Manual parsing"

"IfcOpenShell lets you traverse any IFC entity graph [...] This approach
requires an in-depth understanding of IFC geometry representations [...]
but can be very simple and extremely fast to extract specific types of
geometry [...] generally not recommended except in specific tasks."

The docs' own example reads an IfcCircle's Radius directly. Infra-Rail.ifc
doesn't use swept circular profiles for its rails — every element's Body
representation is an IfcTriangulatedFaceSet (a raw mesh), so this script
adapts the same idea to that: pull Coordinates/CoordIndex straight off the
entity instead of going through create_shape() at all.

Two gotchas this handles that create_shape() normally hides from you:
  - IFC's CoordIndex is 1-based, not 0-based.
  - Coordinates are in the file's length unit (millimeters here), not
    meters — use ifcopenshell.util.unit to find the scale factor.

Usage:
    python 03_manual_parsing.py [file.ifc]
"""

import ifcopenshell.util.unit

from _common import open_model

model = open_model()

unit_scale = ifcopenshell.util.unit.calculate_unit_scale(model)
print(f"unit_scale = {unit_scale} (1 file unit = {unit_scale} m)\n")

tessellations = model.by_type("IfcTriangulatedFaceSet")
print(f"{len(tessellations)} IfcTriangulatedFaceSet representation items in this file\n")

for tessellation in tessellations[:3]:
    coords = tessellation.Coordinates.CoordList  # tuple of (x, y, z) tuples, in file units
    face_indices = tessellation.CoordIndex        # tuple of (i, j, k) tuples, 1-based

    # Which element owns this representation item? Walk back up the graph:
    # Item -> IfcShapeRepresentation -> IfcProductDefinitionShape -> element.
    # inverse attributes make this a two-line lookup instead of scanning.
    owners = [
        el for el in model.by_type("IfcElement")
        if el.Representation
        and any(tessellation in rep.Items for rep in el.Representation.Representations)
    ]
    owner = owners[0] if owners else None

    print(f"item #{tessellation.id()}  owner={owner.is_a() if owner else '?'} "
          f"{owner.GlobalId if owner else ''}")
    print(f"  {len(coords)} raw coords, {len(face_indices)} triangles")

    # First triangle, converted from 1-based file indices to 0-based Python,
    # and scaled from file units (mm) to meters.
    i, j, k = face_indices[0]
    triangle_m = [tuple(c * unit_scale for c in coords[idx - 1]) for idx in (i, j, k)]
    print(f"  first triangle (meters): {triangle_m}\n")
