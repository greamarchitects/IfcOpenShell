###############################################################################
#                                                                             #
# This file is part of IfcOpenShell.                                          #
#                                                                             #
# IfcOpenShell is free software: you can redistribute it and/or modify        #
# it under the terms of the Lesser GNU General Public License as published by #
# the Free Software Foundation, either version 3.0 of the License, or         #
# (at your option) any later version.                                         #
#                                                                             #
# IfcOpenShell is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
# Lesser GNU General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the Lesser GNU General Public License    #
# along with this program. If not, see <http://www.gnu.org/licenses/>.        #
#                                                                             #
###############################################################################

###############################################################################
#                                                                             #
# Do not run this script directly, it is called by run.py                     #
#                                                                             #
###############################################################################

import os
import sys
import time
from math import radians

import bpy
from mathutils import Vector as V

try:
    import ifcopenshell
    import ifcopenshell.geom
    print("IfcOpenShell OK:", ifcopenshell.version)
except Exception:
    import traceback
    traceback.print_exc()
    print("[Error] Unable to import IfcOpenShell")
    raise


# ---------------------------------------------------------------------
# Scene cleanup
# ---------------------------------------------------------------------

scn = bpy.context.scene

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


# This script is called by run.py like:
# blender -b -P bpy.py render input/file.ifc
if len(sys.argv) < 2 or sys.argv[-2] != "render":
    sys.exit(0)


# ---------------------------------------------------------------------
# Import IFC with Bonsai / BlenderBIM
# ---------------------------------------------------------------------

fn = sys.argv[-1]
t1 = time.time()

try:
    import addon_utils

    addon_utils.enable("bonsai", default_set=True, persistent=True)
    print("Bonsai enabled")

    print("Available BIM ops:")
    print([x for x in dir(bpy.ops.bim) if "project" in x.lower() or "load" in x.lower() or "import" in x.lower()])

    bpy.ops.bim.load_project(
        filepath=fn,
        should_start_fresh_session=True,
        use_relative_path=False,
    )

    scn = bpy.context.scene

    succes = True

except Exception:
    import traceback
    traceback.print_exc()
    print("[Error] Could not import IFC into Blender.")
    sys.exit(1)

# Labels
for ob in bpy.context.scene.objects:
    if ob.type == "MESH":
        text = bpy.data.curves.new(ob.name + "_label", "FONT")
        text.body = ob.name
        text.size = 0.3

        label = bpy.data.objects.new(ob.name + "_label", text)
        label.location = ob.location
        label.location.z += 1.0

        bpy.context.scene.collection.objects.link(label)


# Color elements by type
colors = {
    "IfcWall": (1, 1, 1, 1),
    "IfcSlab": (0.2, 0.2, 0.2, 1),
    "IfcDoor": (0.4, 0.2, 0.05, 1),
    "IfcWindow": (0.4, 0.7, 1, 0.35),
    "IfcBeam": (0.8, 0.4, 0.1, 1),
    "IfcColumn": (0.7, 0.7, 0.7, 1),
}

materials = {}

for ifc_type, color in colors.items():
    mat = bpy.data.materials.new(ifc_type)
    mat.diffuse_color = color
    materials[ifc_type] = mat

for ob in bpy.context.scene.objects:
    if ob.type != "MESH":
        continue

    if ob.data is None:
        continue

    for ifc_type, mat in materials.items():
        if ifc_type in ob.name:
            ob.data.materials.clear()
            ob.data.materials.append(mat)
            break


mat = bpy.data.materials.new("TEST_COLOR")
mat.diffuse_color = (1, 0, 0, 1)

for ob in bpy.context.scene.objects:
    if ob.type == "MESH" and ob.data:
        ob.data.materials.clear()
        ob.data.materials.append(mat)

# ---------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------

cam = bpy.data.cameras.new("cam")
cam.angle = radians(45)

cam_ob = bpy.data.objects.new("cam", cam)
scn.collection.objects.link(cam_ob)
cam_ob.location = (8, -8, 6)

cam_ob.rotation_euler = (radians(67), 0, radians(45))
scn.camera = cam_ob

scn.render.resolution_percentage = 100
scn.render.resolution_x = 2048
scn.render.resolution_y = 2048

try:
    scn.render.image_settings.color_mode = "RGBA"
except Exception:
    pass

# Ambient

light = bpy.data.lights.new("Sun", "SUN")
light.energy = 2.0
light_ob = bpy.data.objects.new("Sun", light)
bpy.context.scene.collection.objects.link(light_ob)
light_ob.rotation_euler = (radians(45), 0, radians(30))


# ---------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------

for m in bpy.data.materials:
    if hasattr(m, "specular_intensity"):
        m.specular_intensity = 0


def material(name, settings):
    m = bpy.data.materials.get(name)
    if not m:
        return

    for k, v in settings.items():
        if hasattr(m, k):
            setattr(m, k, v)


material("IfcWall", {"diffuse_color": (1, 1, 1, 1)})
material("IfcWallStandardCase", {"diffuse_color": (1, 1, 1, 1)})
material("IfcSite", {"diffuse_color": (0.4, 0.5, 0.25, 1)})
material("IfcSlab", {"diffuse_color": (0.2, 0.2, 0.2, 1)})
material("IfcDoor", {"diffuse_color": (0.25, 0.1, 0.05, 1)})
material("IfcWindow", {"diffuse_color": (0.5, 0.7, 0.5, 0.3)})
material("IfcRoof", {"diffuse_color": (0.35, 0.2, 0.2, 1)})
material("IfcFurnishingElement", {"diffuse_color": (0.8, 0.7, 0.5, 1)})


# ---------------------------------------------------------------------
# Lights
# ---------------------------------------------------------------------

def create_lamp(eul):
    light = bpy.data.lights.new("sun", "SUN")
    light.energy = 1.3

    light_ob = bpy.data.objects.new("sun", light)
    scn.collection.objects.link(light_ob)

    light_ob.rotation_euler = [radians(e) for e in eul]


create_lamp((20, 0, 60))
create_lamp((0, -120, -50))


# ---------------------------------------------------------------------
# Bounding box
# ---------------------------------------------------------------------

A = V([1e9] * 3)
B = V([-1e9] * 3)

for ob in scn.objects:
    if ob.type != "MESH":
        continue
    if ob.hide_get():
        continue

    bb = [ob.matrix_world @ V(x) for x in ob.bound_box]

    for b in bb:
        for i in range(3):
            if b[i] < A[i]:
                A[i] = b[i]
            if b[i] > B[i]:
                B[i] = b[i]


C = V((1.2, -1.2, 0.6))
D = B - A
E = max(D) * C + (A + B) / 2

cam_ob.location = E
cam.clip_end = max(D) * 10


# ---------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------

os.makedirs("output", exist_ok=True)

scn.render.filepath = os.path.join("output", os.path.basename(fn) + ".png")

bpy.ops.wm.save_as_mainfile(
    filepath=os.path.join("output", os.path.basename(fn) + ".blend"),
    compress=True,
)

bpy.ops.render.render(write_still=True)

# gITF for web viewing
bpy.ops.export_scene.gltf(
    filepath=os.path.join("output", os.path.basename(fn) + ".glb"),
    export_format="GLB"
)

sys.exit(0)