// walk_ifc.cpp
//
// A small, dependency-free C++ program for practicing on real IFC files
// without building the full IfcOpenShell C++ library (that needs Boost,
// OpenCASCADE, and a multi-hour CMake build). IFC's STEP (.ifc) format is
// plain text, so we can hand-roll a light parser instead:
//
//   #123=IFCWALL('1xS3BCk291UvhgP2dvNsgp',#41,$,'Wall-01',$,#456,#789,$,$);
//    ^id  ^type   ^--------------------- args ---------------------------^
//
// What this teaches, in order:
//   1. std::filesystem  - walking a directory of .ifc files
//   2. std::ifstream    - reading a text file
//   3. Manual tokenizing - splitting text on a delimiter *except* inside
//      quotes/parens (a real parser has to do this; naive std::regex or
//      strtok can't)
//   4. std::map / std::vector / structured bindings / lambdas
//   5. std::optional for "this attribute might be null ($)"
//
// Build (from this folder):
//   MSVC:   cl /EHsc /std:c++17 walk_ifc.cpp /Fe:walk_ifc.exe
//   MinGW:  g++ -std=c++17 -O2 walk_ifc.cpp -o walk_ifc.exe
//
// Run:
//   walk_ifc.exe <path-to-one-.ifc-file>
//   walk_ifc.exe <path-to-a-folder-of-.ifc-files>
//
// See README.md in this folder for what to try extending next.

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

// ---------------------------------------------------------------------------
// One parsed STEP entity instance, e.g. line "#123=IFCWALL(...);"
// ---------------------------------------------------------------------------
struct Entity {
    int id = 0;              // 123
    std::string type;        // "IFCWALL" (always upper-case in the file)
    std::string args_raw;    // everything between the outer parens, unsplit
};

// ---------------------------------------------------------------------------
// Strip the ISO-10303-21 header/footer and return only the text between
// DATA; and ENDSEC; (the actual entity instances we care about).
// ---------------------------------------------------------------------------
std::string extract_data_section(const std::string& text) {
    auto data_pos = text.find("DATA;");
    auto end_pos = text.rfind("ENDSEC;");
    if (data_pos == std::string::npos || end_pos == std::string::npos || end_pos <= data_pos) {
        // Not a well-formed STEP file - fall back to the whole thing so the
        // rest of the pipeline still has something to work with.
        return text;
    }
    return text.substr(data_pos + 5, end_pos - (data_pos + 5));
}

// ---------------------------------------------------------------------------
// Split `text` into top-level statements on ';', but NOT while inside a
// single-quoted string. IFC escapes a literal quote as '' (doubled), so a
// quote toggles the "in string" state one character at a time - two quotes
// in a row just toggle twice and net out to "still in string, one literal
// quote emitted", which is exactly what we want without any special-casing.
// ---------------------------------------------------------------------------
std::vector<std::string> split_statements(const std::string& text) {
    std::vector<std::string> out;
    std::string current;
    bool in_string = false;

    for (char c : text) {
        if (c == '\'') {
            in_string = !in_string;
        }
        if (c == ';' && !in_string) {
            // Trim leading whitespace/newlines left over from the file layout.
            auto start = current.find_first_not_of(" \t\r\n");
            if (start != std::string::npos) {
                out.push_back(current.substr(start));
            }
            current.clear();
            continue;
        }
        current += c;
    }
    return out;
}

// ---------------------------------------------------------------------------
// Split the comma-separated argument list of one entity, respecting nested
// parentheses (for list-valued attributes like (#100,#101,#102)) and quoted
// strings (so a comma inside a Name like 'Wall, Type A' isn't split on).
// This is the same shape of problem as splitting a CSV line or parsing a
// function-call argument list - a good one to be able to write from memory.
// ---------------------------------------------------------------------------
std::vector<std::string> split_args(const std::string& args) {
    std::vector<std::string> out;
    std::string current;
    int depth = 0;
    bool in_string = false;

    for (char c : args) {
        if (c == '\'') {
            in_string = !in_string;
        } else if (!in_string && c == '(') {
            ++depth;
        } else if (!in_string && c == ')') {
            --depth;
        }

        if (c == ',' && depth == 0 && !in_string) {
            out.push_back(current);
            current.clear();
            continue;
        }
        current += c;
    }
    if (!current.empty()) {
        out.push_back(current);
    }
    return out;
}

// ---------------------------------------------------------------------------
// Parse one statement of the form  #ID=TYPE(ARGS)  into an Entity.
// Returns std::nullopt for anything that doesn't match (e.g. blank lines,
// or header-section statements that slipped through).
// ---------------------------------------------------------------------------
std::optional<Entity> parse_entity(const std::string& statement) {
    if (statement.empty() || statement[0] != '#') {
        return std::nullopt;
    }

    auto eq_pos = statement.find('=');
    auto open_paren = statement.find('(');
    auto close_paren = statement.rfind(')');
    if (eq_pos == std::string::npos || open_paren == std::string::npos ||
        close_paren == std::string::npos || open_paren < eq_pos || close_paren < open_paren) {
        return std::nullopt;
    }

    Entity e;
    try {
        e.id = std::stoi(statement.substr(1, eq_pos - 1));
    } catch (const std::exception&) {
        return std::nullopt;
    }
    e.type = statement.substr(eq_pos + 1, open_paren - (eq_pos + 1));
    e.args_raw = statement.substr(open_paren + 1, close_paren - (open_paren + 1));
    return e;
}

// ---------------------------------------------------------------------------
// Read a whole .ifc file and return every parsed entity instance.
// ---------------------------------------------------------------------------
std::vector<Entity> parse_ifc_file(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    std::stringstream buffer;
    buffer << in.rdbuf();

    std::string data = extract_data_section(buffer.str());

    std::vector<Entity> entities;
    for (auto& statement : split_statements(data)) {
        if (auto e = parse_entity(statement)) {
            entities.push_back(std::move(*e));
        }
    }
    return entities;
}

// ---------------------------------------------------------------------------
// Most IFC entities that model "real things" (walls, windows, spaces, ...)
// inherit from IfcRoot, whose first attributes are always, in order:
//   (1) GlobalId : IfcGloballyUniqueId   -- a quoted 22-char string
//   (2) OwnerHistory : IfcOwnerHistory   -- a #ref, or $ if unset
//   (3) Name : OPTIONAL IfcLabel         -- a quoted string, or $ if unset
// So arg[0] and arg[2] give us a GlobalId + Name for free on any IfcRoot
// subtype, without needing a schema-specific attribute table.
// ---------------------------------------------------------------------------
struct RootInfo {
    std::string global_id;
    std::string name; // "(unnamed)" if the file left it null ($)
};

std::string strip_quotes(std::string s) {
    if (s.size() >= 2 && s.front() == '\'' && s.back() == '\'') {
        return s.substr(1, s.size() - 2);
    }
    return s;
}

std::optional<RootInfo> as_root_info(const Entity& e) {
    auto args = split_args(e.args_raw);
    if (args.size() < 3) {
        return std::nullopt;
    }
    RootInfo info;
    info.global_id = strip_quotes(args[0]);
    info.name = (args[2] == "$") ? "(unnamed)" : strip_quotes(args[2]);
    return info;
}

// ---------------------------------------------------------------------------
// Print a per-file report: entity count, top element types, and a small
// inventory of building elements with their GlobalId + Name.
// ---------------------------------------------------------------------------
void report_file(const fs::path& path) {
    auto entities = parse_ifc_file(path);

    std::cout << "==== " << path.filename().string() << " ====\n";
    std::cout << entities.size() << " entities\n\n";

    // --- Count instances per entity type, then show the busiest 10. ---
    std::map<std::string, int> type_counts;
    for (auto& e : entities) {
        ++type_counts[e.type];
    }

    std::vector<std::pair<std::string, int>> sorted_counts(type_counts.begin(), type_counts.end());
    std::sort(sorted_counts.begin(), sorted_counts.end(),
              [](auto& a, auto& b) { return a.second > b.second; });

    std::cout << "Top entity types:\n";
    for (size_t i = 0; i < sorted_counts.size() && i < 10; ++i) {
        std::cout << "  " << sorted_counts[i].second << "\t" << sorted_counts[i].first << "\n";
    }
    std::cout << "\n";

    // --- List a handful of building elements with GlobalId + Name. ---
    static const std::vector<std::string> element_types = {
        "IFCWALL", "IFCWINDOW", "IFCDOOR", "IFCSLAB", "IFCCOLUMN", "IFCBEAM",
    };

    std::cout << "Sample elements:\n";
    int shown = 0;
    for (auto& e : entities) {
        bool is_element_type = std::find(element_types.begin(), element_types.end(), e.type) != element_types.end();
        if (!is_element_type) {
            continue;
        }
        if (auto info = as_root_info(e)) {
            std::cout << "  #" << e.id << "  " << e.type << "  " << info->global_id << "  \"" << info->name << "\"\n";
            if (++shown >= 15) {
                std::cout << "  ...\n";
                break;
            }
        }
    }
    if (shown == 0) {
        std::cout << "  (none of " << element_types.size() << " tracked types found in this file)\n";
    }
    std::cout << "\n";
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cout << "usage: walk_ifc <file.ifc | folder-of-.ifc-files>\n";
        return 1;
    }

    fs::path target(argv[1]);
    if (!fs::exists(target)) {
        std::cerr << "path does not exist: " << target << "\n";
        return 1;
    }

    if (fs::is_directory(target)) {
        for (auto& entry : fs::directory_iterator(target)) {
            if (entry.path().extension() == ".ifc") {
                report_file(entry.path());
            }
        }
    } else {
        report_file(target);
    }

    return 0;
}
