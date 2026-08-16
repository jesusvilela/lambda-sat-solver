# Manifold Research Atlas v0.1

## 0. Evidence Lattice

| State | Meaning | Examples |
|-------|---------|----------|
| **P** | Proved (Lean-checked) | Holonomy lemmas, embedding theorems, native_decide results |
| **A** | Axiomatized (defined, not proved) | Observability coordinates, MHRR tensors, g_r field definition |
| **M** | Measured (empirical, reproducible) | ρ* = 0.135±0.003, g_r(α) field values, finite-size collapse |
| **H** | Hypothesized (consistent with data, not falsified) | Critical exponent ν≈1.7, r_c scaling law |
| **S** | Semantic (conceptual status, not mathematical) | "Hypercomplex solves SAT", Clay mappings |
| **R** | Retired (demoted, contradicted, or superseded) | Hidden volumetric coupling, special residual geometry, G₂ certification |

---

## 1. Programme Overview

The Manifold Research programme investigates the relationship between hypercomplex algebraic structure and computational complexity. It asks: does changing the algebraic substrate change the scaling law for SAT solvers?

**Answer (R183–R185):** The algebra reveals the wall; it does not remove it. The obstruction density ρ* = 0.135±0.003 is substrate-stable across Cayley-Dickson variants.

The programme has four interacting fibers:
1. **Algebraic computation** — Cayley-Dickson towers, mulByLevel, HolnessHolonomy
2. **Lean formalization** — HardnessHolonomy, TuringHalting, HaltingSetSearch
3. **Conceptual architecture** — Observability coordinates, MHRR, semantic objects
4. **Honest assessment** — Matched-null generation, claim demotion, ρ* measurement

---

## 2. Chronological Phases

### Phase 1: R30–R39 — Solver Foundation
- R30–R39: Foundation of the R30–R39 solver
- ACAF (Adaptive Constraint Acquisition Framework) fuzzer
- First hypercomplex SAT instances
- HardnessHolonomy formalization started

### Phase 2: R40–R90 — Structural Analysis
- Embedding lemmas (embedOctInto)
- Structural witness construction
- Holonomy–annihilator bridge proposed
- Connection Laplacian investigations

### Phase 3: R91–R140 — Hypercomplex Regimes
- Cayley-Dickson failure ladder (octonions work, sedenions lose norm multiplicativity)
- Berry/Jacobi/holonomy hierarchy
- MHRR (Multi-Hypercomplex Relational Representation) ontology
- IGBundle, UTAI/Bunny, SGS (Substrate-Stable Scaling) concepts

### Phase 4: R141–R160 — Corrections and Demotions
- XOR ruggedness counterexample (R142) — retired ruggedness as separator
- Five matched-null investigations eliminate special residual geometry
- Anti-Löb governance method developed
- P versus NP explicitly untouched

### Phase 5: R161–R180 — Field Characterisation
- g_r(α) visibility field defined and measured
- r_c(α,n) finite-size scaling proposed
- ρ_backbone(α,n) obstruction density measured
- ρ* = 0.135±0.003 reported (substrate-stable)

### Phase 6: R181–R185 — Current Frontier
- Hidden hypercomplex volume FAILED (scalar, single-scale response)
- Algebra reveals wall but does not remove it
- Strong null-generation and Anti-Löb methodology
- P versus NP remains untouched

---

## 3. Canonical Taxonomy

### 3.1 Ground States

| State | Description |
|-------|-------------|
| **Frozen** | Backbone variables determined by unit propagator |
| **Critical** | At the phase transition, backbone and non-backbone merge |
| **Fluid** | Non-backbone variables with freedom to vary |

### 3.2 Boundaries

| Boundary | Description |
|----------|-------------|
| **Visibility boundary** | Depth at which global structure becomes locally invisible |
| **Certification boundary** | Frontier of certifiable backbone literals |
| **Complexity boundary** | Where local algorithms fail and global search is required |

### 3.3 Hypercomplex Regimes

| Level | Algebra | Dimension | Associativity | Norm |
|-------|---------|-----------|---------------|------|
| n=0 | ℝ | 1 | Yes | Yes |
| n=1 | ℂ | 2 | Yes | Yes |
| n=2 | ℍ | 4 | Yes | Yes |
| n=3 | 𝕆 (octonions) | 8 | No (Fano) | Yes |
| n=4 | 𝕊 (sedenions) | 16 | No | No |
| n≥5 | Aₙ | 2ⁿ | No | No |

### 3.4 Operator Families

| Operator | Description |
|----------|-------------|
| **mulByLevel** | Full Cayley-Dickson multiplication (ℝ, recursive) |
| **mulByLevelSign** | Sign-table multiplication (ZMod 3, component-wise for n≥4) |
| **conjByLevel** | Cayley-Dickson conjugation |
| **embedOctInto** | Embed Fin 8 → ℝ into Fin 2ⁿ → ℝ |
| **embedFirst/embedSecond** | Octonion embedding components |
| **firstHalf/secondHalf** | Split vector into two halves |

### 3.5 Semantic Objects

| Object | Evidence | Description |
|--------|----------|-------------|
| **g_r(α)** | H | Visibility field: invisible/certified backbone ratio at depth r |
| **r_c(α,n)** | H | Finite-size scaling function |
| **ρ_backbone(α,n)** | M | Obstruction density |
| **ρ*** | M | Substrate-stable obstruction density = 0.135±0.003 |
| **ν** | H | Tentative critical exponent ≈ 1.7 |
| **Holonomy** | P (partial) | AlgebraicHolonomy, computationalHolonomy |
| **MHRR** | A | Carrier/role/relation tensor dynamics |
| **SGS** | M | Substrate-stable scaling |

### 3.6 Complexity Instruments

| Instrument | Description |
|------------|-------------|
| **ACAF fuzzer** | Generates hypercomplex SAT instances in {-1,0,1}^(2ⁿ) |
| **HaltingSetSearch** | Finite checks on ZMod 3 (isSubalgebra, countFixedPoints) |
| **HardnessHolonomy** | Algebraic holonomy as hardness invariant |
| **TuringHalting** | Undecidability of halting in non-scalar geometry |
| **isSubalgebra_n_ℝ** | ℝ-based subalgebra check (ℝ vectors, mulByLevel) |

---

## 4. Mathematical Artifact Compendium

### 4.1 Core Definitions

```lean
-- HaltingSetSearch (HaltingSetSearch.lean)
Sign := ZMod 3
signToReal : Sign → ℝ    -- 0→-1, 1→0, 2→1
toZMod3 : ℝ → Sign       -- -1→0, 0→1, 1→2

isSubalgebra (T : Fin 8 → Sign) : Bool
isSubalgebra_n (n : ℕ) (T : Fin (2^n) → ZMod 3) : Bool
isSubalgebra_n_ℝ (n : ℕ) (T : Fin (2^n) → ℝ) : Bool

-- Witness construction (TuringHalting_Hyperdim.lean)
witness (n : ℕ) : Fin (2^n) → ℝ  -- e₀ + e_{2^{n-1}} + e_{2^n-1}
structuralWitness (n : ℕ) (hn : 3 ≤ n) : Fin (2^n) → ℝ
embedOctInto (n : ℕ) (hn : 3 ≤ n) : (Fin 8 → ℝ) → Fin (2^n) → ℝ

-- Holonomy (HardnessHolonomy.lean)
AlgebraicHolonomy (T s : Fin 8 → ℝ) : Prop
computationalHolonomy (T s : Fin 8 → ℝ) : Fin 8 → ℝ
```

### 4.2 Visibility Field

```
g_r(α) = #{certified backbone literals invisible at depth r} / #{certified backbone literals}
```

Key empirical facts:
- g_r(α) rises toward the random 3-SAT threshold
- Characteristic depth r ≈ 5
- Tentative ν ≈ 1.7
- Hidden hypercomplex volume FAILED — response looked scalar and single-scale

### 4.3 Obstruction Density

```
ρ_backbone(α, n) — obstruction density
ρ* = 0.135 ± 0.003 — substrate-stable across algebraic variants
```

### 4.4 Cayley-Dickson Failure Ladder

| n | Algebra | Hurwitz | Norm multiplicativity | Associativity |
|---|---------|---------|----------------------|---------------|
| 0 | ℝ | Yes | Yes | Yes |
| 1 | ℂ | Yes | Yes | Yes |
| 2 | ℍ | Yes | Yes | Yes |
| 3 | 𝕆 | Yes | Yes | No (Fano) |
| 4 | 𝕊 | No | No | No |
| ≥5 | Aₙ | No | No | No |

### 4.5 Holonomy–Annihilator Bridge

Proposed theorem (partially proved):

```
k ∈ Ann(H_C) ⟹ L_k f = 0, f ≠ 0
```

Using spanning-tree potential:
```
f(v) = ω_k^hol(v₀ → v)
```

Proof architecture:
1. Additive holonomy under walk concatenation
2. Tree-edge cancellation
3. Nonzero spanning section
4. Annihilation of path differences
5. Translation between ZMod_n arithmetic and complex exponential transport
6. Full covering-Laplacian equation

### 4.6 MHRR (Multi-Hypercomplex Relational Representation)

```
X_t = (carrier states, role potentials, relation tensor)
X_{t+1} = Φ(X_t)
```

Proposed state space, tensor symmetries, gauge equivalences, update law, conserved quantities, stability, identifiability — not yet fully specified.

### 4.7 Observability Coordinates

Encoding family E_λ : X → V_λ is an observability coordinate when:
1. Dynamical equivalence: encodings produce conjugate or information-equivalent evolution
2. Observational inequivalence: some invariants become lower-degree, more separable, or more statistically visible in one encoding
3. Algorithmic neutrality: equal-compute solution scaling remains unchanged
4. Discovery advantage: candidate structures are detected earlier or with greater signal-to-noise

---

## 5. Corrections and Demotion Ledger

| Claim | Status | Round | Reason |
|-------|--------|-------|--------|
| Ruggedness separates SAT from XOR | **R** | R142 | XOR counterexample (Gaussian elimination supplies affine gate) |
| Special residual geometry exists | **R** | R160+ | Five matched-null investigations |
| Hidden volumetric coupling | **R** | R170+ | Programme tested and eliminated |
| Monotone Cayley-Dickson solver benefit | **R** | R150+ | Not observed in experiments |
| Zeta alignment | **R** | R140+ | Not replicated |
| Cone-consistency signal | **R** | R145+ | Not replicated |
| G₂ certification | **R** | R130+ | Not replicated |
| Clay mappings | **R** | R175+ | Programme moved away from P/NP claims |
| Changing hypercomplex algebra changes scaling law | **R** | R183 | ρ* substrate-stable across ℝ, ℂ, ℍ, 𝕆 |
| Hidden volumetric coupling | **R** | R170+ | Programme tested and eliminated |
| Special residual geometry | **R** | R143-160 | Five matched-null investigations |
| XOR ruggedness as separator | **R** | R142 | Gaussian elimination supplies affine gate |
| Hypercomplex solves SAT | **S** | R30-R185 | Never formalized, superseded by structural insight |
| Ruggedness separates SAT from XOR | **R** | R142 | XOR counterexample |
| Solver advantage claim | **R** | R183 | No solver advantage demonstrated |
| Changing algebra removes obstruction | **R** | R185 | Algebra reveals but does not remove wall |

---

## 6. Current Scientific Landing (R185)

The programme's current position:

1. **No P/NP claim.** The algebra reveals the wall; it does not remove it. ρ* = 0.135±0.003 is substrate-stable across Cayley-Dickson variants.
2. **ρ* = 0.135±0.003 is substrate-stable.** Tested across ℝ, ℂ, ℍ, 𝕆. The obstruction density is independent of algebraic encoding.
3. **g_r(α) is the surviving empirical direction.** The visibility field measures local invisibility of certified global structure. g_r(α) rises toward the random 3-SAT threshold. A characteristic depth r_c ≈ 5 emerges. Tentative critical exponent ν ≈ 1.7.
4. **Five matched-null investigations** eliminated the proposed special residual geometry. The durable output is a strong null-generation and Anti-Löb governance method.
5. **P versus NP remains untouched.** The programme explicitly does not address this.
6. **Observability coordinates** formalized: encoding can raise information accessibility without changing complexity class. Cayley-Dickson provides O(1) backbone visibility vs O(2^n) in Boolean encoding.
7. **Anti-Löb methodology** operationalized: 8 null families, evidence lattice (P/A/M/H/S/R), claim registry with 30+ claims, automatic demotion infrastructure.

---

## 7. Research Queues

### Active
| Queue | Status | Next action |
|-------|--------|-------------|
| Visibility field | M→H | n=128,192,256 finite-size collapse; SAT solver integration for backbone computation |
| Kernel theorem | P (partial) | 2 sorrys remain; companion proofs file written |
| Observability axioms | A | Formalize separation from solver advantage |
| Anti-Löb harness | A | Populate claim registry (30+ claims registered); implement null testing loop |

### Frozen
- Cayley-Dickson levels beyond R183 (algebraic computation continues)
- Living-animal/civilization metaphors without ablations
- Clay mappings
- Constants from [R] without typing
- One-instance SAT victories
- Further attempts at hidden-volume/residual-holonomy separators

---

## 8. Lean and Repository Status

| Component | Status | Location |
|-----------|--------|----------|
| HardnessHolonomy | Builds | `LambdaSatSolver/VDIS/HardnessHolonomy.lean` |
| TuringHalting_Hyperdim | Builds | `LambdaSatSolver/VDIS/TuringHalting_Hyperdim.lean` |
| HaltingSetSearch | Builds | `LambdaSatSolver/HaltingSetSearch.lean` |
| ACAF fuzzer + visibility | Builds | `LambdaSatSolver/VDIS/AcafQuine.lean` |
| CD algebra | Builds | `LambdaSatSolver/VDIS/Algebra/CD.lean` |
| ConnectionLaplacian | Builds (2 sorrys) | `LambdaSatSolver/VDIS/ConnectionLaplacian.lean` |
| ConnectionLaplacian/Proofs | Builds (4 sorrys) | `LambdaSatSolver/VDIS/ConnectionLaplacian/Proofs.lean` |
| Observability | Builds | `LambdaSatSolver/VDIS/Observability.lean` |
| Anti-Löb harness | Builds | `LambdaSatSolver/VDIS/AntiLob/Basic.lean` |
| GRD | Builds | `LambdaSatSolver/VDIS/GRD.lean` |
| External: connection_laplacian_lean | Builds | `~/connection_laplacian_lean` |

**Note:** All Lean and repository statuses are reported by the conversation, not independently reverified. Next defensible layer: commit-level reconciliation (bind every promoted object to its exact Lean proof surface, source commit, raw data, environment, seeds, and reproduction command).

---

## 9. Index of Rounds

115 documented round reports (R30–R185+). Each round contains:
- Claim changes
- Evidence state transitions
- Key mathematical objects introduced or modified
- Decisions and rationale

See `index.json` for the machine-readable round manifest.
