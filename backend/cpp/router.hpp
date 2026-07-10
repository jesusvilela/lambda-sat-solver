#pragma once

#include <vector>
#include <string>
#include <memory>
#include "gf2_oracle.hpp"
#include "flavor_analyzer.hpp"

namespace tribridge {

enum StructuralClass {
    PURE_GF2,
    PARTIAL_XOR_SADDLE,
    UNSTRUCTURED
};

struct RouterResult {
    StructuralClass type;
    std::string route_name;
    double expected_overhead_ms;
    std::string flavor_group;
};

class GatedRouter {
public:
    static RouterResult classify(const std::vector<std::vector<int>>& clauses, int num_vars) {
        // Group-theoretic flavor extraction replacing heuristic parsing
        SymmetryGroup group = FlavorAnalyzer::identify_symmetry(clauses, num_vars);
        
        if (group == GROUP_Z2_X_Z2) {
            return {StructuralClass::PURE_GF2, "Parity Oracle", 0.1, FlavorAnalyzer::group_to_string(group)};
        } else if (group == GROUP_A4) {
            return {StructuralClass::PARTIAL_XOR_SADDLE, "CMS (Gauss-Jordan Fold)", 1.5, FlavorAnalyzer::group_to_string(group)};
        } else {
            return {StructuralClass::UNSTRUCTURED, "Bare Kissat", 0.0, FlavorAnalyzer::group_to_string(group)};
        }
    }
    
    // Evaluate based on known metrics (legacy fallback if needed)
    static RouterResult evaluate(float xor_fraction) {
        if (xor_fraction >= 0.999f) {
            return {StructuralClass::PURE_GF2, "Parity Oracle", 0.1, "Z2_x_Z2"};
        } else if (xor_fraction > 0.05f) {
            return {StructuralClass::PARTIAL_XOR_SADDLE, "CMS (Gauss-Jordan Fold)", 1.5, "A4"};
        } else {
            return {StructuralClass::UNSTRUCTURED, "Bare Kissat", 0.0, "TRIVIAL"};
        }
    }
};

} // namespace tribridge
