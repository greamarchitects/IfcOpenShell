"""02_geometry_iterator.py — bulk geometry processing with ifcopenshell.geom.iterator.

Docs: docs/ifcopenshell-python/geometry_processing.rst, "Geometry iterator"
      docs/ifcopenshell/geometry_iterator.rst

"For any bulk geometry processing, it is always recommended to use the
iterator" over calling create_shape() in a loop — it's multi-threaded and
caches/reuses identical geometry (e.g. Infra-Rail.ifc's 66 IfcTrackElements
are likely repeats of a handful of distinct rail-fastener shapes).

Usage:
    python 02_geometry_iterator.py [file.ifc]
"""

import multiprocessing
import time
from collections import Counter

import ifcopenshell.geom

from _common import open_model

model = open_model()

settings = ifcopenshell.geom.settings()

# --- Pass 1: every element with geometry, tallied by IFC class ---------
t0 = time.time()
iterator = ifcopenshell.geom.iterator(
    settings, model, multiprocessing.cpu_count(), geometry_library="hybrid-cgal-simple-opencascade"
)

counts = Counter()
verts_total = 0
faces_total = 0

if iterator.initialize():
    while True:
        shape = iterator.get()
        element = model.by_id(shape.id)
        counts[element.is_a()] += 1
        verts_total += len(shape.geometry.verts) // 3
        faces_total += len(shape.geometry.faces) // 3
        # matrix / edges / materials / material_ids are all available here
        # too, same shape as 01_individual_processing.py — this is exactly
        # what create_shape() gives you per element, just driven for you
        # across the whole model, multi-threaded.
        if not iterator.next():
            break

elapsed = time.time() - t0
n_elements = len(model.by_type("IfcElement"))
n_shaped = sum(counts.values())

print(f"{n_shaped}/{n_elements} elements produced geometry in {elapsed:.2f}s "
      f"({n_elements - n_shaped} have no representation)\n")
print(f"{verts_total} total vertices, {faces_total} total triangles\n")

print("by type:")
for ifc_class, n in counts.most_common():
    print(f"  {ifc_class:<24} {n}")

# --- Pass 2: the `include` filter — only process a subset of elements --
# "One of the more common settings used is the include setting, which
# specifies only to process certain geometry." — docs
rails = model.by_type("IfcRail")
if rails:
    print(f"\nfiltered pass: only {len(rails)} IfcRail element(s)")
    filtered_iterator = ifcopenshell.geom.iterator(
        settings, model, multiprocessing.cpu_count(),
        include=rails, geometry_library="hybrid-cgal-simple-opencascade",
    )
    n = 0
    if filtered_iterator.initialize():
        while True:
            filtered_iterator.get()
            n += 1
            if not filtered_iterator.next():
                break
    print(f"  iterator yielded {n} shape(s) — matches len(rails)={len(rails)}: {n == len(rails)}")
