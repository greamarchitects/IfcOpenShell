import ifcopenshell

print("IfcOpenShell imported")
print(ifcopenshell.version)

model = ifcopenshell.file()
print(model)