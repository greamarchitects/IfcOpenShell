# IfcOpenShell - IFC toolkit and geometry engine
# Copyright (C) 2021 Dion Moult <dion@thinkmoult.com>
#
# This file is part of IfcOpenShell.
#
# IfcOpenShell is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IfcOpenShell is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with IfcOpenShell.  If not, see <http://www.gnu.org/licenses/>.

"""Run this test from src/ifcopenshell-python folder: pytest --durations=0 ifcopenshell/util/test_pset.py"""

from ifcopenshell.util import pset
from ifcopenshell.util.pset import ApplicableEntity, PsetQto


class TestPsetQto:
    @classmethod
    def setup_class(cls):
        cls.pset_qto = pset.PsetQto("IFC4")

    def test_get_applicables(self):
        for i in range(1000):
            assert len(self.pset_qto.get_applicable("IfcMaterial")) == 9

    def test_get_applicables_names(self):
        for i in range(1000):
            assert len(self.pset_qto.get_applicable_names("IfcMaterial")) == 9

    def test_getting_applicables_for_a_specific_predefined_type(self):
        names = self.pset_qto.get_applicable_names("IfcAudioVisualAppliance")
        assert len(names) == 12
        assert "Pset_AudioVisualApplianceTypeAmplifier" not in names
        names = self.pset_qto.get_applicable_names("IfcAudioVisualAppliance", predefined_type="AMPLIFIER")
        assert "Pset_AudioVisualApplianceTypeAmplifier" in names
        assert len(names) == 13

    def test_getting_a_pset_of_a_type_where_the_type_class_is_not_explicitly_applicable(self):
        names = self.pset_qto.get_applicable_names("IfcWall")
        assert "Pset_WallCommon" in names
        names = self.pset_qto.get_applicable_names("IfcWallType")
        assert len(names) == 12
        assert "Pset_WallCommon" in names
        assert "Qto_WallBaseQuantities" in names  # Backported fix for IFC4

    def test_getting_applicable_names_by_predefined_type(self):
        names = self.pset_qto.get_applicable_names("IfcFurniture")
        assert "Pset_FurnitureTypeTable" not in names
        names = self.pset_qto.get_applicable_names("IfcFurniture", "TABLE")
        assert "Pset_FurnitureTypeTable" in names
        names = self.pset_qto.get_applicable_names("IfcFurnitureType", "TABLE")
        assert "Pset_FurnitureTypeTable" in names
        names = self.pset_qto.get_applicable_names("IfcFurnitureType")
        names2 = self.pset_qto.get_applicable_names("IfcFurnitureType", "CUSTOM")
        assert names == names2

    def test_getting_applicables_for_a_material_category(self):
        names = self.pset_qto.get_applicable_names("IfcMaterial")
        assert "Pset_MaterialConcrete" not in names
        names = self.pset_qto.get_applicable_names("IfcMaterial", "concrete")
        assert "Pset_MaterialConcrete" in names


class TestParseApplicableEntity:
    def test_run(self):
        assert pset.parse_applicable_entity("IfcBoilerType") == [
            ApplicableEntity("IfcBoilerType", "IfcBoilerType", None, False)
        ]

    def test_two_entities(self):
        assert pset.parse_applicable_entity("IfcBoilerType,IfcWallType") == [
            ApplicableEntity("IfcBoilerType", "IfcBoilerType", None, False),
            ApplicableEntity("IfcWallType", "IfcWallType", None, False),
        ]

    def test_two_entities_with_performance_history(self):
        assert pset.parse_applicable_entity("IfcBoilerType[PerformanceHistory],IfcWallType") == [
            ApplicableEntity("IfcBoilerType[PerformanceHistory]", "IfcBoilerType", None, True),
            ApplicableEntity("IfcWallType", "IfcWallType", None, False),
        ]

    def test_two_entities_with_predefined_type(self):
        assert pset.parse_applicable_entity("IfcBoilerType/STEAM,IfcWallType") == [
            ApplicableEntity("IfcBoilerType/STEAM", "IfcBoilerType", "STEAM", False),
            ApplicableEntity("IfcWallType", "IfcWallType", None, False),
        ]

    def test_two_entities_with_predefined_type_and_performance_history(self):
        assert pset.parse_applicable_entity("IfcBoilerType[PerformanceHistory]/STEAM,IfcWallType") == [
            ApplicableEntity("IfcBoilerType[PerformanceHistory]/STEAM", "IfcBoilerType", "STEAM", True),
            ApplicableEntity("IfcWallType", "IfcWallType", None, False),
        ]


class TestConvertApplicableEntitiesToQuery:
    def test_run(self):
        entities = [ApplicableEntity("IfcBoilerType", "IfcBoilerType", None, False)]
        assert pset.convert_applicable_entities_to_query(entities) == "IfcBoilerType"

    def test_two_entities(self):
        entities = [
            ApplicableEntity("IfcBoilerType", "IfcBoilerType", None, False),
            ApplicableEntity("IfcWallType", "IfcWallType", None, False),
        ]
        assert pset.convert_applicable_entities_to_query(entities) == "IfcBoilerType + IfcWallType"

    def test_two_entities_with_performance_history(self):
        entities = [
            ApplicableEntity("IfcBoilerType[PerformanceHistory]", "IfcBoilerType", None, True),
            ApplicableEntity("IfcWallType", "IfcWallType", None, False),
        ]
        assert pset.convert_applicable_entities_to_query(entities) == "IfcBoilerType + IfcWallType"

    def test_two_entities_with_predefined_type(self):
        entities = [
            ApplicableEntity("IfcBoilerType/STEAM", "IfcBoilerType", "STEAM", False),
            ApplicableEntity("IfcWallType", "IfcWallType", None, False),
        ]
        assert (
            pset.convert_applicable_entities_to_query(entities) == 'IfcBoilerType, PredefinedType="STEAM" + IfcWallType'
        )

    def test_two_entities_with_predefined_type_and_performance_history(self):
        entities = [
            ApplicableEntity("IfcBoilerType[PerformanceHistory]/STEAM", "IfcBoilerType", "STEAM", True),
            ApplicableEntity("IfcWallType", "IfcWallType", None, False),
        ]
        assert (
            pset.convert_applicable_entities_to_query(entities) == 'IfcBoilerType, PredefinedType="STEAM" + IfcWallType'
        )


class TestPsetTemplateFiles:
    """Guards against malformed IfcSimplePropertyTemplate entities in the bundled
    Pset/Qto template files (see #9289).

    A missing OwnerHistory attribute (the second attribute, which should always be
    ``$``) shifts every subsequent attribute over by one. The practical symptom is
    that ``Name`` ends up holding the property's ``Description`` text instead of its
    real name (e.g. "Indicates whether the object is intended to carry loads..."
    instead of "LoadBearing"), which silently hides the property from anything that
    looks it up by name.
    """

    def test_property_templates_are_well_formed(self):
        for schema in PsetQto.templates_path:
            template_file = PsetQto(schema).templates[0]
            for template in template_file.by_type("IfcSimplePropertyTemplate"):
                name = template.Name
                assert name, f"{schema} {template} has no Name (OwnerHistory attribute may be missing)"
                assert " " not in name, (
                    f"{schema} {template} has a Name that looks like a Description "
                    "(OwnerHistory attribute is probably missing, shifting all following attributes)"
                )

    def test_load_bearing_is_defined_in_ifc4(self):
        pset_qto = PsetQto("IFC4")
        for pset_name in ("Pset_RoofCommon", "Pset_RampCommon", "Pset_StairCommon"):
            pset_template = pset_qto.get_by_name(pset_name)
            assert pset_template, f"{pset_name} not found"
            properties = {prop.Name: prop for prop in pset_template.HasPropertyTemplates}
            assert "LoadBearing" in properties, f"LoadBearing missing from {pset_name}"
            assert properties["LoadBearing"].PrimaryMeasureType == "IfcBoolean"
