"""05_geometry_tree.py — spatial queries and clash detection.

Docs: docs/ifcopenshell-python/geometry_tree.rst

Not in the pasted samples, but it's the other major "geometry exploration"
capability the docs cover: building a tree from the model, then using it to
(a) select elements by point/box/ray and (b) clash-detect one group of
elements against another.

API note found while writing this (installed build: ifcopenshell 0.8.5):
the docs' tree examples build the tree by adding shapes one at a time from
the iterator (`tree.add_element(iterator.get())`). That works fine for
clash_intersection_many/clash_collision_many/clash_clearance_many and for
select()/select_ray(), but select_box() (by element or by raw point)
returned an empty list for *every* query on this build when the tree was
built that way — including an element querying its own bounding box, which
the docs promise always returns at least itself. Building the tree with
tree.add_file(model, settings) instead (which registers a bounding box per
instance up front, not just triangulated shapes) fixed it — used below.
select_box(point, extend=...) still has no matching C++ overload at all
(the point form only accepts a bare point, no tolerance) — use
select(point, extend=...) for a point + radius query instead. That wrapper
is also picky: it only recognises a point tuple when every element's type
is exactly `float`, so a numpy-derived value needs float(...) first.

Usage:
    python 05_geometry_tree.py [file.ifc]
"""

import ifcopenshell.geom
import ifcopenshell.util.shape

from _common import open_model

model = open_model()

settings = ifcopenshell.geom.settings()

# "The most efficient way to build a tree is by using the iterator [...]
# if triangulation is added, a BVH Tree is built" — supports clash
# detection and box/point/ray selection. In this installed build,
# add_file() is what actually makes select_box() (by element or point)
# work correctly — see module docstring above.
tree = ifcopenshell.geom.tree()
tree.add_file(model, settings)
print(f"tree built from {len(model.by_type('IfcElement'))} elements\n")

# --- Clash detection: do any rails intersect the track-element ballast? --
rails = model.by_type("IfcRail")
track_elements = model.by_type("IfcTrackElement")
print(f"clashing {len(rails)} IfcRail against {len(track_elements)} IfcTrackElement...")
clashes = tree.clash_intersection_many(
    rails,
    track_elements,
    tolerance=0.002,  # ignore protrusions under 2mm
    check_all=True,
)
print(f"  {len(clashes)} intersection clash(es)")
for clash in clashes[:5]:
    a, b = clash.a, clash.b
    clash_type = ["protrusion", "pierce", "collision", "clearance"][clash.clash_type]
    print(f"  {a.is_a()} {a.Name!r}  x  {b.is_a()} {b.Name!r}  ({clash_type}, {clash.distance:.4f}m)")

# Collision check (surfaces merely touching or intersecting) is cheaper and
# a common first pass before the more expensive intersection check above.
collisions = tree.clash_collision_many(rails, track_elements, allow_touching=True)
print(f"\n  {len(collisions)} collision clash(es) (rails resting on/touching track elements is expected)")

# --- Spatial selection -----------------------------------------------------
# Build a quick centroid from the raw vertices of everything in the tree,
# rather than assuming (0,0,0) is meaningful for this model. get_shape_matrix
# returns numpy values, so cast to plain float — see module docstring.
xs, ys, zs = [], [], []
iterator = ifcopenshell.geom.iterator(settings, model)
if iterator.initialize():
    while True:
        shape = iterator.get()
        matrix = ifcopenshell.util.shape.get_shape_matrix(shape)
        loc = matrix[:, 3][0:3]
        xs.append(loc[0])
        ys.append(loc[1])
        zs.append(loc[2])
        if not iterator.next():
            break
centre = (float(sum(xs) / len(xs)), float(sum(ys) / len(ys)), float(sum(zs) / len(zs)))
print(f"\napproximate model centre: {tuple(round(c, 2) for c in centre)}")

# select_box(element) -- bounding-box containment/intersection query.
course = model.by_type("IfcCourse")[0]
box_hits = tree.select_box(course)
print(f"\nselect_box(course) -> {len(box_hits)} element(s) sharing/containing its bounding box:")
for el in box_hits[:10]:
    print(f"  {el.is_a()} {el.Name!r}")

# select(point, extend=radius) -- precise geometry query within a sphere.
nearby = tree.select(centre, extend=10.0)
print(f"\nselect(centre, extend=10m) -> {len(nearby)} element(s) within 10m of the model centre")

# --- Ray casting: fire straight up from the model centre ------------------
results = tree.select_ray(centre, (0.0, 0.0, 1.0), length=50.0)
print(f"\nvertical ray from centre -> {len(results)} intersection(s):")
for result in results[:5]:
    hit = model.by_id(result.instance.id())
    print(f"  {hit.is_a()} at distance {result.distance:.2f}m")
