# walk_ifc — a small C++ practice project on real IFC models

A dependency-free C++17 program that parses the IFC (`.ifc`) STEP text
format by hand — no IfcOpenShell library, no Boost, no OpenCASCADE. Just
`<filesystem>`, `<fstream>`, and a hand-rolled tokenizer.

It takes any `.ifc` file or folder of them as a command-line argument, so it
doesn't need to sit next to its data. Two ready-made things to point it at:
- `..\model.ifc` and `..\..\AC20-FZK-Haus.ifc` — already in this repo, right
  next door.
- The 14 buildingSMART sample models used by `bsi_samples_analysis.ipynb`,
  which (as of writing) live outside the repo at
  `C:\Users\ReDI\Downloads\IfcOpenShell_Explorations\ifc_analysis_portfolio\building_smart-samples\`.

Building the real IfcOpenShell C++ library (`src/ifcparse`) from source is a
heavy, multi-hour setup on Windows (Boost + OpenCASCADE + CMake), so this
takes the other route: IFC's STEP format is just text —

```
#123=IFCWALL('1xS3BCk291UvhgP2dvNsgp',#41,$,'Wall-01',$,#456,#789,$,$);
 ^id  ^type   ^--------------------- args ---------------------------^
```

— so a small parser gets you real practice (file I/O, manual tokenizing,
`std::map`/`std::vector`, `std::optional`, structured bindings, lambdas)
directly on your own data, with nothing to install.

## Build

**MSVC** (from a "Developer Command Prompt", or after running `vcvars64.bat`):
```
cl /EHsc /std:c++17 /O2 walk_ifc.cpp /Fe:walk_ifc.exe
```

**MinGW / g++:**
```
g++ -std=c++17 -O2 walk_ifc.cpp -o walk_ifc.exe
```

## Run

```
walk_ifc.exe ..\model.ifc                                              # one file, from this repo
walk_ifc.exe ..\..\AC20-FZK-Haus.ifc                                   # another one, one level further up

walk_ifc.exe "C:\Users\ReDI\Downloads\IfcOpenShell_Explorations\ifc_analysis_portfolio\building_smart-samples\Building-Architecture.ifc"  # one bSI sample
walk_ifc.exe "C:\Users\ReDI\Downloads\IfcOpenShell_Explorations\ifc_analysis_portfolio\building_smart-samples"                            # all 14 at once
```

For each file it prints the entity count, the 10 busiest entity types, and a
small inventory of walls/windows/doors/slabs/columns/beams with their
GlobalId + Name.

## How it works

1. `extract_data_section` — cuts the text down to what's between `DATA;`
   and `ENDSEC;`, skipping the STEP header.
2. `split_statements` — splits that text on `;`, but not while inside a
   quoted string (so a `;` could never appear there today, but it's the
   right habit — same logic `split_args` needs for commas).
3. `parse_entity` — turns one `#123=IFCWALL(...)` statement into an
   `Entity{id, type, args_raw}`.
4. `split_args` — splits `args_raw` on top-level commas, respecting both
   quotes and nested parentheses (list attributes like `(#100,#101)`).
   This is the same core problem as parsing a CSV line or a function-call
   argument list.
5. `as_root_info` — every IFC entity that models "a real thing" inherits
   from `IfcRoot`, whose first three attributes are always
   `(GlobalId, OwnerHistory, Name)` in that order — so `args[0]` and
   `args[2]` give a GlobalId + Name on *any* such entity, without needing a
   full schema-specific attribute table.

## Known limitations (= good next exercises)

- **Multi-line entities.** This assumes one statement doesn't get
  interrupted by something that looks like a new `#id=` mid-string across a
  line break in a way that confuses `split_statements`. The buildingSMART
  samples don't do this, but a hardened parser should join continuation
  lines before splitting.
- **No cross-referencing.** `#41` in an entity's args is just left as the
  string `"#41"` — it's never resolved to the actual `IFCOWNERHISTORY`
  entity. Try building a `std::unordered_map<int, Entity>` keyed by `id`
  and writing a `resolve(const std::string& ref)` helper.
- **No geometry.** `IFCCARTESIANPOINT(0.,0.,0.)` args are just a raw string.
  Try parsing those into `struct Point3 { double x,y,z; }` and computing a
  bounding box per file — a nice follow-on to what `02_geometry.ipynb` does
  in Python next door.
- **No spatial tree.** `IFCRELAGGREGATES` / `IFCRELCONTAINEDINSPATIALSTRUCTURE`
  relate elements to their spatial parent (Site → Building → Storey →
  Element). Try building that as an actual tree structure in C++ — it's the
  same relationship graph `bsi_samples_analysis.ipynb` builds with
  `networkx`, just in C++ with your own struct instead.
- **Not validating.** Malformed input just gets silently skipped
  (`std::nullopt`). Fine for practice; a real tool would report where and
  why parsing failed.
