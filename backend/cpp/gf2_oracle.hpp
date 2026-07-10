#pragma once

#include <vector>
#include <unordered_map>
#include <cstdint>
#include <algorithm>
#include <iostream>

namespace tribridge {

// A simple dynamic bitset for GF(2) operations
class BitSet {
public:
    std::vector<uint64_t> words;
    size_t num_bits;

    BitSet(size_t bits = 0) : num_bits(bits) {
        words.resize((bits + 63) / 64, 0);
    }

    void set(size_t pos) {
        if (pos >= num_bits) {
            num_bits = pos + 1;
            words.resize((num_bits + 63) / 64, 0);
        }
        words[pos / 64] |= (1ULL << (pos % 64));
    }

    bool get(size_t pos) const {
        if (pos >= num_bits) return false;
        return (words[pos / 64] >> (pos % 64)) & 1ULL;
    }

    void xor_with(const BitSet& other) {
        if (other.words.size() > words.size()) {
            words.resize(other.words.size(), 0);
            num_bits = other.num_bits;
        }
        for (size_t i = 0; i < other.words.size(); ++i) {
            words[i] ^= other.words[i];
        }
    }

    // Returns the index of the lowest set bit, or -1 if empty
    int lowest_set_bit() const {
        for (size_t i = 0; i < words.size(); ++i) {
            if (words[i] != 0) {
                uint64_t w = words[i];
                // Find lowest set bit in this 64-bit word using builtin (or intrinsic)
                // Equivalently, count trailing zeros.
                int bit = 0;
                while ((w & (1ULL << bit)) == 0) {
                    bit++;
                }
                return (int)(i * 64 + bit);
            }
        }
        return -1;
    }

    bool is_zero() const {
        for (uint64_t w : words) {
            if (w != 0) return false;
        }
        return true;
    }
};

struct XORConstraint {
    std::vector<int> variables; // 1-indexed
    int rhs; // 0 or 1
};

struct XORRefutation {
    bool refuted;
    int num_xors;
    bool decides_fully;
};

class GF2Oracle {
public:
    // Returns true if the system is inconsistent (refuted)
    static XORRefutation gf2_xor_refutation(const std::vector<XORConstraint>& xors, int num_vars, float xor_clause_fraction) {
        std::unordered_map<int, BitSet> pivots;
        bool refuted = false;

        for (const auto& x : xors) {
            BitSet row(num_vars + 1);
            for (int v : x.variables) {
                row.set(v - 1);
            }
            if (x.rhs) {
                row.set(num_vars); // The RHS bit
            }

            while (!row.is_zero()) {
                int lead = row.lowest_set_bit();
                if (lead == num_vars) {
                    // Reduced to 0 = 1 (LHS empty, RHS 1)
                    refuted = true;
                    break;
                }
                if (pivots.find(lead) != pivots.end()) {
                    row.xor_with(pivots[lead]);
                } else {
                    pivots[lead] = row;
                    break;
                }
            }
            if (refuted) break;
        }

        XORRefutation result;
        result.refuted = refuted;
        result.num_xors = xors.size();
        result.decides_fully = (xor_clause_fraction >= 0.999f);
        return result;
    }
};

} // namespace tribridge
