"""04_serialization.py — export geometry to glTF/glb and OBJ.

Docs: docs/ifcopenshell-python/geometry_processing.rst, "Geometry serialisation"
      docs/ifcopenshell/serialiser_settings.rst

Same shape as the sample this was built from: settings -> serializer ->
iterator -> write per shape -> finalize. Both formats are produced here
(the docs show them as alternatives / one commented out) so you can diff
them against each other.

Usage:
    python 04_serialization.py [file.ifc]
"""

import multiprocessing
from pathlib import Path

import ifcopenshell.geom

from _common import open_model

model = open_model()

out_dir = Path(__file__).parent / "output"
out_dir.mkdir(exist_ok=True)

settings = ifcopenshell.geom.settings()
settings.set("dimensionality", ifcopenshell.ifcopenshell_wrapper.CURVES_SURFACES_AND_SOLIDS)
# "Applying default materials is required in glTF serialisation." — docs
settings.set("apply-default-materials", True)

serialiser_settings = ifcopenshell.geom.serializer_settings()
# Optional, but useful to uniquely identify objects in non-semantic formats.
serialiser_settings.set("use-element-guids", True)

# --- glTF / glb ----------------------------------------------------------
glb_path = out_dir / "Infra-Rail.glb"
serialiser = ifcopenshell.geom.serializers.gltf(str(glb_path), settings, serialiser_settings)
serialiser.setFile(model)
serialiser.setUnitNameAndMagnitude("METER", 1.0)
serialiser.writeHeader()

iterator = ifcopenshell.geom.iterator(settings, model, multiprocessing.cpu_count())
n = 0
if iterator.initialize():
    while True:
        serialiser.write(iterator.get())
        n += 1
        if not iterator.next():
            break
serialiser.finalize()
print(f"wrote {glb_path}  ({glb_path.stat().st_size / 1024:.0f} KB, {n} shapes)")

# --- OBJ -------------------------------------------------------------------
# OBJ has no material/GUID metadata channel like glTF, so world coordinates
# are usually what you want (otherwise every element sits at its own local
# origin, which looks like a pile of overlapping geometry in a viewer).
settings.set("use-world-coords", True)

obj_path = out_dir / "Infra-Rail.obj"
mtl_path = out_dir / "Infra-Rail.mtl"
serialiser = ifcopenshell.geom.serializers.obj(str(obj_path), str(mtl_path), settings, serialiser_settings)
serialiser.setFile(model)
serialiser.setUnitNameAndMagnitude("METER", 1.0)
serialiser.writeHeader()

iterator = ifcopenshell.geom.iterator(settings, model, multiprocessing.cpu_count())
n = 0
if iterator.initialize():
    while True:
        serialiser.write(iterator.get())
        n += 1
        if not iterator.next():
            break
serialiser.finalize()
print(f"wrote {obj_path}  ({obj_path.stat().st_size / 1024:.0f} KB, {n} shapes)")
