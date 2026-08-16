# Manifold Research Bootstrap

Bootstrap and govern conversations about Jesus Vilela Jato's Manifold Research Atlas and its hypercomplex/hyperdimensional research programme.

## When to trigger

Use when the user mentions:
- The Atlas, numbered R-rounds (R30–R185+)
- IGBundle, UTAI/Bunny, SGS, Ω*, [R], MHRR
- Cayley-Dickson regimes, Berry/Jacobi/holonomy
- The connection Laplacian, SAT/Clay obstruction work
- SAT solver, ACAF, fuzzer, hypercomplex learning towers
- Asks to: continue, audit, consolidate, formalize, visualize, or extend

## Boot protocol for naive conversations

1. **Orient**: Read this skill file + `atlas.md` + `index.json`
2. **Classify**: Every claim the user makes about the programme gets assigned to one of the four fibers:
   - Algebraic computation (hypercomplex algebra, operators, Lean proofs)
   - Lean formalization (HardnessHolonomy, TuringHalting, HaltingSetSearch)
   - Conceptual architecture (observability coordinates, MHRR, semantic objects)
   - Honest assessment (demoted claims, null results, ρ* = 0.135±0.003)
3. **Pre-register**: Before extending the programme, state what round this conversation enters and what the next round will test
4. **Recover objects**: Only load the specific mathematical objects needed for the current claim — not the entire archive
5. **Preserve corrections**: If a claim was previously demoted, do not revive it without explicit acknowledgment
6. **Honest frontier**: The current scientific center is NOT a Clay solution. It is the visibility-coupling programme (g_r field, r_c scaling, ρ_backbone). The algebra reveals the wall; it does not remove it.

## Evidence lattice (P/A/M/H/S/R)

Every object in the programme is classified by its evidence state:

| State | Meaning | Examples |
|-------|---------|----------|
| **P** | Proved (Lean-checked) | Holonomy lemmas, embedding theorems, native_decide results |
| **A** | Axiomatized (defined, not proved) | Observability coordinates, MHRR tensors, g_r field definition |
| **M** | Measured (empirical, reproducible) | ρ* = 0.135±0.003, g_r(α) field values, finite-size collapse |
| **H** | Hypothesized (consistent with data, not falsified) | Critical exponent ν≈1.7, r_c scaling law |
| **S** | Semantic (conceptual status, not mathematical) | "Hypercomplex solves SAT", Clay mappings |
| **R** | Retired (demoted, contradicted, or superseded) | Hidden volumetric coupling, special residual geometry, G₂ certification |

**Rule**: Never treat S or R objects as if they were M or P. Never revive a retired claim without explicit acknowledgment of its demotion.

## Current honest frontier

The programme's scientific center is the **visibility-coupling programme**:

### Core empirical objects
- **g_r(α)** = #{certified backbone literals invisible at depth r} / #{certified backbone literals}
- **r_c(α, n)** ~ n^(1/ν) F((α-α_c) n^(1/ν)) — finite-size scaling
- **ρ_backbone(α, n)** — obstruction density

### Key empirical facts
- g_r(α) rises toward the random 3-SAT threshold
- Characteristic depth r ≈ 5
- Tentative ν ≈ 1.7
- Hidden hypercomplex volume FAILED (response looked scalar and single-scale)
- ρ* = 0.135 ± 0.003 (substrate-stable across algebraic variants)

### Retired claims
- Ruggedness as separator (XOR counterexample)
- Special residual geometry
- Monotone Cayley-Dickson solver benefit
- Zeta alignment
- Cone-consistency signal
- Hidden volumetric coupling

### Open questions
- Does a genuine finite-size collapse exist?
- Is r_c logarithmic, polynomial, or bounded in n?
- How does visibility depth relate to frozen variables, whitening cores, reconstruction thresholds?
- Is g_r predicting algorithmic difficulty or merely measuring a known backbone transition?

## Research queues

### Active (next round pre-registration)
| Queue | Status | Next action |
|-------|--------|-------------|
| Visibility field | M (measured) → H (hypothesized) | n=128,192,256 finite-size collapse |
| Kernel theorem | P (partial proof) | Close spanning-tree witness, character sectors, kernel multiplicity |
| Observability axioms | A (defined) | Formalize observational advantage vs solver advantage |
| Anti-Löb harness | Infrastructure | Preregistration manifests, matched-null generation |

### Frozen (superseded by structural insight)
- Cayley-Dickson levels beyond R183
- Living-animal/civilization metaphors without ablations
- Clay mappings
- Constants from [R] without typing
- One-instance SAT victories
- Further attempts at hidden-volume/residual-holonomy separators

## Canonical mathematical spine

### Definitions
```
Sign := ZMod 3
signToReal : Sign → ℝ    -- 0→-1, 1→0, 2→1
toZMod3 : ℝ → Sign       -- -1→0, 0→1, 1→2 (other values → 2)

-- HaltingSetSearch (finite checks)
isSubalgebra (T : Fin 8 → Sign) : Bool
isSubalgebra_n (n : ℕ) (T : Fin (2^n) → ZMod 3) : Bool
isSubalgebra_n_ℝ (n : ℕ) (T : Fin (2^n) → ℝ) : Bool  -- ℝ-based, uses mulByLevel

-- Visibility field
g_r(α) = #{invisible backbone literals at depth r} / #{certified backbone literals}
r_c(α, n) = finite-size scaling function
ρ_backbone(α, n) = obstruction density

-- Holonomy (HardnessHolonomy)
AlgebraicHolonomy (T s : Fin 8 → ℝ) : Prop
computationalHolonomy (T s : Fin 8 → ℝ) : Fin 8 → ℝ

-- Turing Halting (TuringHalting)
halting_undecidable_for_acaf_quine (T : Fin 8 → ℝ) : Prop
halting_undecidable_n (n : ℕ) (hn : 3 ≤ n) : Prop

-- Witness
witness (n : ℕ) : Fin (2^n) → ℝ  -- e₀ + e_{2^{n-1}} + e_{2^n-1}
structuralWitness (n : ℕ) (hn : 3 ≤ n) : Fin (2^n) → ℝ
embedOctInto (n : ℕ) (hn : 3 ≤ n) : (Fin 8 → ℝ) → Fin (2^n) → ℝ
```

### Key formulas
```
-- Node activation (Origami Ascendancy)
a_{i,t+Δt} = clamp(0.86·a_i + η + 0.12·S_int, 0, 1)
S_int = clamp(0.92·S_int + 0.08·(0.25·threat + 0.08·food + 40·vibration + 0.1·ambientLight), 0, 1)

-- Memory update
lr = (0.012 + 0.09·plasticity) · neuralCapacity
M(cue)_{t+1} = clamp(M(cue)_t + lr·(reward - M(cue)_t), -1, 1)

-- Cayley-Dickson recurrence (level n ≥ 4)
mulByLevel n x y = 
  embedFirst(mulByLevel (n-1) (firstHalf x) (firstHalf y) - 
    mulByLevel (n-1) (conjByLevel (n-1) (secondHalf y)) (secondHalf x)) +
  embedSecond(mulByLevel (n-1) (conjByLevel (n-1) (firstHalf x)) (secondHalf y) +
    mulByLevel (n-1) (firstHalf y) (secondHalf x))
```

## Semantic-to-mathematical translation rules

| Semantic term | Mathematical object | Evidence state |
|---------------|---------------------|----------------|
| "Hypercomplex algebra" | Cayley-Dickson tower, mulByLevel | P (defined) |
| "Obstruction" | ρ_backbone, g_r field | M (measured) |
| "Visibility" | Invisibility ratio of certified backbone | H (hypothesized) |
| "Holonomy" | AlgebraicHolonomy, computationalHolonomy | P (partial proof) |
| "Structural witness" | structuralWitness n hn = embedOctInto n hn (witness 3) | P (proved) |
| "Anti-Löb" | Null-generation, matched-null, claim demotion | Infrastructure |
| "MHRR" | Carrier/role/relation tensor dynamics | A (defined) |
| "SGS" | Substrate-stable scaling | M (measured) |
| "[R]" | Unspecified relation/operator | S (semantic placeholder) |
| "Ω*" | Obstruction density / critical threshold | M (measured) |
| "Clay mapping" | Proposed P/NP reduction | R (retired) |

## Safeguards

1. **No P/NP claims**: The programme explicitly retires the claim that changing hypercomplex algebra changes the scaling law. Do not revive this.
2. **No ruggedness claims**: XOR counterexample (R142) retired this.
3. **No hidden volume**: The programme tested it and it failed (scalar, single-scale response).
4. **No special residual geometry**: Five matched-null investigations eliminated this.
5. **ρ* = 0.135±0.003 is substrate-stable**: This is the most robust empirical fact. Do not claim it depends on a specific algebra.
6. **Lean proofs are the gold standard for P claims**: Semantic claims (S) without Lean formalization are hypotheses, not results.
7. **Every R-round must be referenced by number**: R30–R185 are the canonical round reports. Do not invent new round numbers without clear lineage.

## Composition guidance

### For `thinking-with-jesus-vilela`
- Prioritize the visibility-coupling programme
- Use the P/A/M/H/S/R lattice to classify every claim
- Pre-register the next round before extending

### For `hypercomplex-learning-towers`
- Focus on the Cayley-Dickson algebraic structures
- Connect to the HardnessHolonomy and TuringHalting formalizations
- The tower metaphor is useful for visualization; the algebra is the formal content

### For `acaf-fuzzer`
- The fuzzer generates hypercomplex vectors in {-1,0,1}^(2^n)
- Use isSubalgebra_n_ℝ to check the subalgebra condition
- Target n=3 (native_decide), n=4,6,8 (structural embedding)

### For new conversations starting from naive state
Use this exact first prompt:

> "Continue the Manifold research from its current honest frontier. Recover only the relevant mathematical objects, classify every claim by evidence level, and pre-register the next round before extending the programme."

## Files

- `atlas.md` — Complete 21-page research atlas in Markdown
- `index.json` — Machine-readable index of 115 round reports with claim ledger
