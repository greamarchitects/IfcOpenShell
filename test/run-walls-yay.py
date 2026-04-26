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
# The IfcOpenShell test suite downloads IFC files that are publicely          #
# available on the internet and uses Blender and IfcOpenShell to generate a   #
# render of the parsed file. For the script to run, Blender needs to be       #
# installed and added to PATH.                                                #
#                                                                             #
###############################################################################

import inspect
import os
import subprocess
import sys
from urllib.request import urlretrieve
from zipfile import ZipFile

BLENDER = r"C:\Blender43\blender-4.3.2-windows-x64\blender.exe"

cwd = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
os.chdir(cwd)

os.makedirs("output", exist_ok=True)
os.makedirs("input", exist_ok=True)


def run_blender(*args):
    return subprocess.call([BLENDER, "-b", "-P", "bpy.py", *args])


# Test Blender + bpy.py
if run_blender("TEST") != 0:
    print("[Error] Failed to launch Blender or bpy.py")
    sys.exit(1)

print("[Notice] Found Blender and IfcOpenShell on system")


def extension(fn):
    return os.path.splitext(fn)[-1].lower()


class TestFile:
    def __init__(self, fn, store_as=None):
        self.fn = fn
        self.store_as = store_as
        self.failed = []

    def __call__(self):
        if self.fn.startswith(("http://", "https://", "ftp://")):
            fn = self.store_as if self.store_as else self.fn.split("/")[-1]
            target = os.path.join("input", fn)

            if os.path.exists(target):
                print("[Notice] Already downloaded:", fn)
            else:
                print("[Notice] Downloading:", fn)
                urlretrieve(self.fn, target)

            self.fn = fn

        if extension(self.fn) == ".zip":
            print("[Warning] ZIP extraction skipped:", self.fn)
            return False
            zip_path = os.path.join("input", self.fn)

            with ZipFile(zip_path) as zf:
                files = [
                    n for n in zf.namelist()
                    if extension(n) == ".ifc"
                    and not n.startswith("__")
                    and not n.startswith(".")
                ]

                for fn in files:
                    out_path = os.path.join("input", fn)
                    if not os.path.exists(out_path):
                        zf.extract(fn, "input")

                self.fn = files
        else:
            self.fn = [self.fn]

        for fn in self.fn:
            print("[Notice] Rendering:", fn)

            ok = run_blender("render", os.path.join("input", fn)) == 0

            if not ok:
                self.failed.append(fn)

        return len(self.failed) == 0

    def __str__(self):
        return "\n".join(self.failed)


# ---------------------------------------------------------------------
# START SMALL: test only one local IFC first
# Put the file here:
# repo/test/input/acad2010_walls.ifc
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
# START SMALL: test only one local IFC first
# Put the file here:
# repo/test/input/acad2010_walls.ifc
# ---------------------------------------------------------------------

test_cases = [
    TestFile("revit2014_multiple_bounded_halfspaces.ifc"),
]

failed = []

for test in test_cases:
    ok = test()
    if not ok:
        failed.append(test)

if failed:
    print("[Notice] Conversion failed for:")
    for test in failed:
        print(test)
else:
    print("[Notice] All cases succeeded")

