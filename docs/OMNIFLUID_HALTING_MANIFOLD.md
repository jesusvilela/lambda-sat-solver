# Omnifluid Halting Manifold — MΩ

## Claim Discipline

  This document does NOT claim to solve classical Turing Halting.
  It characterizes the range of halting sectionability over a
  lifted computational manifold MΩ.

  Core slogans:
  *Halting is not simply absent.*
  *Halting lives as a field over computational submanifolds.*
  *We are not denying the classical theorem.*
  *We are refusing to collapse the entire halting field into one Boolean wall.*
  *Z/n is a local residue chart; MΩ is the lifted computational manifold.*
  *Projection is not ontology.*
  *Human recognition is not external verification.*

## What This Document Contains

1. Sectionability classifier
2. MΩ as lifted computational manifold
3. Local vs global halting sections
4. Holonomy obstruction
5. Observer Absorption boundary
6. Classical boundary
7. Field range summary

## 1. Sectionability Classifier

We do not start from "undecidable = absolute wall."
We open the halting problem as a field-range characterization.

For every submanifold M' ⊆ MΩ, classify what kind of
halting section exists over M'.

### The Halt Field

The field F_halting is not {0,1} but a range of statuses:

  halts, does not halt,
  locally recognized, semi-decided,
  externally verified, obstructed,
  unknown in chart, non-globally-sectionable

### HaltSectionability regimes

| Regime | Meaning |
|--------|---------|
| `total_decidable` | A global section exists |
| `semi_decidable` | Halting recognized when it happens |
| `co_semi_decidable` | Non-halting certified in restricted cases |
| `locally_decidable` | Each chart has recognizer, but may not glue |
| `externally_verifiable` | Candidate claim independently checkable |
| `holonomy_obstructed` | Local recognizers fail to form global section |
| `observer_absorbed` | Human/model recognition mistaken for verification |
| `unknown` | Status unknown in this submanifold |

### Classical undecidability is a boundary theorem

Classical undecidability says: the full self-referential MΩ
admits no total computable global section. But this is one
boundary in a field, not the only ontology.

## 2. MΩ as Lifted Computational Manifold

MΩ is the omnifluid computational manifold:
discrete in local charts, numeric in representation,
variable-dimensional in lift, continuous/geometric in transport.
Not reducible to any single projection.

### Submanifolds M'

A submanifold M' of MΩ is a restricted computational ecology:

  M' = { machines satisfying some constraint }

Examples:

| Submanifold | Constraint | Known status |
|-------------|-----------|-------------|
| M_finite | Bounded-time / bounded-space | locally_decidable |
| M_primitive | Primitive recursive | total_decidable |
| M_GF2 | Parity/XOR-decidable traces | locally_decidable |
| M_self | Self-referential / quine-like | holonomy_obstructed |
| M_verified | Externally checked traces | externally_verifiable |
| M_chart_i | One local representation | locally_decidable |
| M_observer | Human/model-recognized traces | observer_absorbed |

### Halt field

A halt field assigns a sectionability status to each state:

```lean
structure HaltField (M : MΩ) where
  status : M.State → HaltSectionability
  status_dec : ∀ s, Decidable (status s)
```

## 3. Local vs Global Halting Sections

### Local halting recognizer

A local halting recognizer operates on a single chart:

```
R_i : π_i(X) → {halts, does_not_halt}
```

### Global halting section

A global halting section is a Bool-valued predicate compatible
with all local recognizers:

```lean
structure GlobalHaltSection (M : MΩ) where
  decides : M.State → Bool
  compatible : ∀ (L : LocalHaltSection M) (s : M.State),
    L.recognizes s → decides s = true
```

### The classical boundary

Classical undecidability denies the existence of a total
computable global section over the full self-referential MΩ.
But local sections may exist on many submanifolds.

## 4. Holonomy Obstruction

### Holonomy system

```lean
structure HolonomySystem (M : MΩ) where
  Hol : M.State → Nat
  zeroHol : Nat := 0
  Flat : M.State → Prop := fun s => Hol s = zeroHol
```

### Valid global section requires flatness

```lean
structure ValidGlobalHaltSection
    (M : MΩ) (H : HolonomySystem M) (G : GlobalHaltSection M) : Prop where
  flat_required : ∀ s, G.decides s = true → H.Flat s
  externally_verified : ∀ s, G.decides s = true → ExtVer.verifies s
```

### Theorem A: Nonzero holonomy blocks valid global halt section

If a state has nonzero holonomy, it cannot be decided by a
valid global halting section (which requires flatness).

```lean
theorem nonzero_holonomy_blocks_valid_global_halt
    (M : MΩ) (H : HolonomySystem M) (G : GlobalHaltSection M)
    (V : ValidGlobalHaltSection M H G)
    (s : M.State) (hdec : G.decides s = true)
    (hnonzero : H.Hol s ≠ H.zeroHol) :
    False
```

This does NOT assume the whole problem is undecidable.
It classifies where gluing fails: at states with nonzero holonomy.

### Theorem B: Local recognition cannot be promoted without flatness

If a local recognizer recognizes s, and compatibility would
imply G.decides s = true, but s has nonzero holonomy,
then G cannot be a valid global section.

```lean
theorem local_recognition_not_global_without_flatness
    (M : MΩ) (H : HolonomySystem M) (G : GlobalHaltSection M)
    (L : LocalHaltSection M) (s : M.State)
    (h_recog : L.recognizes s) (hdec : G.decides s = true)
    (hnonzero : H.Hol s ≠ H.zeroHol) :
    ¬ ValidGlobalHaltSection M H G
```

## 5. Observer Absorption Boundary

### Theorem C: Human recognition not global section

Human recognition alone cannot establish a valid global section.
Reuses `human_recognition_alone_insufficient` from OAR.lean.

```lean
theorem human_recognition_not_global_section
    (x : Fin 8 → ℝ) (h_human : HumanRecognized x) (h_no_ext : ¬ ExternallyVerified x) :
    ¬ ValidGlobalSection x
```

### Safety invariant

```
HumanRecognized(x) ∧ ¬ ExternallyVerified(x) ⇒ ¬ ValidGlobalSection(x)
```

## 6. Classical Boundary

Classical undecidability is not assumed as the starting ontology.
It is represented as a non-semantic interface marker:

```lean
def classicalHaltingInterfaceMarker : Unit := ()
```

This is a type-level placeholder, not a theorem. It can later be
replaced with a formal statement when the full self-referential MΩ
is instantiated for Turing machines.

## 7. Field Range Summary

### Classical framing (not ours)

```
HALT(P,x) ∈ {0,1} for all programs P, inputs x.
```

### Our framing

```
F_halting : MΩ → Sec
where Sec = {total_decidable, semi_decidable, locally_decidable,
             externally_verifiable, holonomy_obstructed,
             observer_absorbed, unknown}
```

### For every submanifold M' ⊆ MΩ

```
Sec_halting(M') = classify what halting section exists over M'
```

### Regimes

| # | Regime | Description |
|---|--------|-------------|
| 1 | Total decidable | Global section exists |
| 2 | Semi-decidable | Halting recognized when it happens |
| 3 | Co-semi-decidable | Non-halting certified in restricted cases |
| 4 | Locally decidable | Each chart has recognizer, but may not glue |
| 5 | Externally verifiable | Candidate claim independently checkable |
| 6 | Holonomy-obstructed | Local recognizers fail to form global section |
| 7 | Observer-absorbed | Recognition mistaken for verification |

### The final slogan

The wall is not a wall everywhere.
It is a curvature field. Some regions close, some locally shimmer,
some require external verification, and the omni-fluid whole
refuses one final Boolean flattening.

---

## Cross-references

- `LambdaSatSolver/VDIS/OmnifluidManifold.lean` — main Lean file
- `LambdaSatSolver/VDIS/OAR.lean` — Observer Absorption Risk layer
- `LambdaSatSolver/VDIS/TuringHalting_Master.lean` — classical boundary
- `connection_laplacian_lean/ConnectionLaplacian/Ontology.lean` — formal verification spine
- `nnn-hyperbolic-ramdisk_v2/src/ledger.py` — runtime memory manifold
