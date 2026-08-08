"""01_individual_processing.py — create_shape() on a single element.

Docs: docs/ifcopenshell-python/geometry_processing.rst, "Individual processing"

This is the simplest way to turn one IFC element into a mesh: vertices,
edges, faces, its placement matrix, and the materials/styles applied to it.
The docs explicitly warn this is for *learning*, not bulk work — for
processing every element in a model, use the iterator instead (see
02_geometry_iterator.py), which is faster and multi-threaded.

Usage:
    python 01_individual_processing.py [file.ifc]
"""

from typing import cast

import ifcopenshell.geom
import ifcopenshell.util.shape
from ifcopenshell import ifcopenshell_wrapper

from _common import open_model, style_summary

model = open_model()

# Infra-Rail.ifc's headline element type. Fall back to whatever the file
# actually has if you point this at a different model.
element = (model.by_type("IfcRail") or model.by_type("IfcElement"))[0]
print(f"Processing {element.is_a()} {element.GlobalId!r} {element.Name!r}\n")

settings = ifcopenshell.geom.settings()

# "Choosing a geometry kernel has a big impact on speed and capability. It
# is recommended to use the hybrid-cgal-simple-opencascade kernel" — docs.
#
# create_shape()'s declared return type is a broad Union covering every
# possible call shape (whole element vs. bare representation/profile,
# triangulated vs. BRep vs. serialized, ...) since the function has no
# @overload variants to narrow it per-argument. Passing a whole IfcProduct
# with no `repr` argument and default (triangulating) settings always
# returns a TriangulationElement at runtime — this cast just tells the
# type checker what we already know, it's a no-op at runtime.
shape = cast(
    ifcopenshell_wrapper.TriangulationElement,
    ifcopenshell.geom.create_shape(settings, element, geometry_library="hybrid-cgal-simple-opencascade"),
)

print("guid           ", shape.guid)
print("id             ", shape.id)
print("resolved elem  ", model.by_guid(shape.guid))

# A unique geometry ID: IfcShapeRepresentation.id{-layerset-N}{-material-N}
# {-openings-[...]}{-world-coords} — useful for caching/reuse, since two
# elements sharing a type often share this ID and can reuse one mesh.
print("geometry id    ", shape.geometry.id)

# 4x4 placement matrix: first 3 columns are the local X/Y/Z axes
# (right-handed, unscaled), last column is the XYZ position.
matrix = ifcopenshell.util.shape.get_shape_matrix(shape)
location = matrix[:, 3][0:3]
print("location (xyz) ", location)

verts = shape.geometry.verts   # flat [x,y,z, x,y,z, ...]
edges = shape.geometry.edges   # flat vertex-index pairs; not necessarily triangulated
faces = shape.geometry.faces   # flat vertex-index triples; always triangulated
print(f"\n{len(verts) // 3} vertices, {len(edges) // 2} edges, {len(faces) // 3} triangles")

# Same data, grouped into nested arrays instead of flat lists — usually
# nicer to work with (e.g. numpy math, exporting to another format).
grouped_verts = ifcopenshell.util.shape.get_vertices(shape.geometry)
grouped_faces = ifcopenshell.util.shape.get_faces(shape.geometry)
print("first 3 grouped verts:", grouped_verts[:3].tolist())
print("first 3 grouped faces:", grouped_faces[:3].tolist())

print("\nstyles (materials) applied to this shape:")
for style in shape.geometry.materials:
    print(" ", style_summary(style))

# Per-triangle bookkeeping: which style and which source IFC representation
# item produced each face. Same length as the triangle count.
material_ids = shape.geometry.material_ids
item_ids = shape.geometry.item_ids
print(f"\nmaterial_ids sample: {list(material_ids[:10])}")
print(f"item_ids sample:     {list(item_ids[:10])}")
