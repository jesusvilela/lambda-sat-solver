#pragma once

#include <vector>
#include <string>
#include <unordered_map>
#include <cmath>

namespace tribridge {

enum SymmetryGroup {
    GROUP_Z2_X_Z2, // Pure GF(2)
    GROUP_A4,      // Highly symmetrical saddle point
    GROUP_TRIVIAL  // Unstructured
};

class FlavorAnalyzer {
public:
    static SymmetryGroup identify_symmetry(const std::vector<std::vector<int>>& clauses, int num_vars) {
        if (clauses.empty() || num_vars <= 0) return GROUP_TRIVIAL;

        std::vector<int> var_degrees(num_vars + 1, 0);
        int total_length = 0;
        
        // Linear accumulation (O(L) contiguous memory writes)
        for (const auto& clause : clauses) {
            total_length += clause.size();
            for (int lit : clause) {
                int var = std::abs(lit);
                if (var <= num_vars) {
                    var_degrees[var]++;
                }
            }
        }

        double avg_length = static_cast<double>(total_length) / clauses.size();
        
        int active_vars = 0;
        #pragma omp simd reduction(+:active_vars)
        for (int i = 1; i <= num_vars; ++i) {
            if (var_degrees[i] > 0) {
                active_vars++;
            }
        }
        
        if (active_vars == 0) return GROUP_TRIVIAL;

        double avg_deg = static_cast<double>(total_length) / active_vars;
        double variance = 0.0;
        
        // Tensor-native SIMD variance reduction over continuous array
        #pragma omp simd reduction(+:variance)
        for (int i = 1; i <= num_vars; ++i) {
            if (var_degrees[i] > 0) {
                double diff = var_degrees[i] - avg_deg;
                variance += diff * diff;
            }
        }
        variance /= active_vars;

        // 1. Z2 x Z2 (Parity chains)
        // Typically length 3 (3-XOR) or length 4 (4-XOR) encoded into CNF.
        // The degree variance is extremely low in pure GF2 matrices (regular graphs).
        // A random graph has variance ~ avg_deg. We require variance to be strictly less than avg_deg * 0.2.
        if (variance < avg_deg * 0.2 && avg_length >= 2.9 && avg_length <= 4.1) {
            return GROUP_Z2_X_Z2;
        }

        // 2. A4 (Tetrahedral Symmetry / Cryptographic Saddles)
        // Industrial and cryptographic instances exhibit scale-free or highly modular properties.
        // The variance must be massively larger than the mean (unlike Poisson noise where var ~ mean).
        if (variance > avg_deg * 4.0 && avg_deg > 6.0) {
            return GROUP_A4;
        }

        // 3. Trivial
        return GROUP_TRIVIAL;
    }
    
    static std::string group_to_string(SymmetryGroup group) {
        switch (group) {
            case GROUP_Z2_X_Z2: return "Z2_x_Z2";
            case GROUP_A4: return "A4";
            default: return "TRIVIAL";
        }
    }
};

} // namespace tribridge
