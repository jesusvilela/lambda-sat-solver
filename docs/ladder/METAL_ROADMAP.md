# Geometry → metal: optimizing computation in our spaces, honestly

*How the hyperbolic / hypercomplex / hyperdimensional program we built maps to
CPU and GPU — with the one measurement that reframes the whole question.*

## The core insight: understanding wants curvature, computation wants flatness

The whole ladder was a search for **where hardness hides** — and it hides in rich,
curved structure (the shallow-Emperor frame, the G₂ symmetry, the sheaf
obstruction). But optimization runs the *opposite* direction. The place a problem
is **fast to compute** is the flattest algebra it fits in: **characteristic 2 —
GF(2)** — where addition is XOR (its own inverse, no carries), multiplication is
AND, and there is no rounding, no curvature to carry.

The frame router is the bridge between the two:

> The curved, hypercomplex space is where you **find** the frame.
> The flat GF(2) shadow is where you **compute** it.
> Metal accelerates the flat part.

And the deep fact that makes this more than a metaphor: **silicon has spent 15
years building characteristic-2 hardware** — `PCLMULQDQ` (carry-less multiply,
2010), `GFNI` (Galois-Field New Instructions, AVX-512, 2018) — because
cryptography (AES, CRC, Reed–Solomon) needed exactly this algebra. **The flat
frames our geometry lands in are the ones the metal already accelerates
natively.** We are not asking the hardware for a favor; we are landing where it is
fastest.

## The measurement that reframes it (do not skip this)

Before proposing any rewrite, the honest question: *where does the time actually
go?* Measured, GF(2) row-reduction of a 700×700 system:

| approach | time |
|---|---|
| Python-loop over **bigint** rows (what `xor_extraction` does now) | **13 ms** |
| naive numpy `uint64`-packed, elimination vectorized | 27 ms (**0.5×, slower**) |

**Python bigints are already bit-packed and XOR at C speed.** The naive numpy
rewrite is *slower*, because it trades one fast C-level XOR-of-a-word-array for a
per-column Python loop (argmax, masking) that the interpreter pays for. This is
the Charter applied to performance: *measure before you "optimize."* At our
current research scale (hundreds of variables, frames already ~1 ms) the metal win
is **negligible** — the geometry is already so metal-friendly that a builtin
suffices.

### The frame-router scaling probe (what "prototype and benchmark" surfaced)

Crystallizing the three frames into one call (`backend/frame_solver.py`) and then
scaling it on Tseitin exposed the *real* cost split — and a free win that has
nothing to do with metal (reproduce: `python -m
docs.ladder.scripts.frame_router_scaling`):

| stage (Tseitin, 4500 vars / 12000 clauses) | time |
|---|---|
| 2-SAT scan | 5.5 ms |
| XOR parsing (`extract_xors`) | 28 ms |
| **sound GF(2) refutation** (`gf2_xor_refutation`) | **30 ms** |
| full GF(2) **solve** (RREF + model rebuild, `gf2_xor_solve`) | **1149 ms** |
| **router, refute-first** (`frame_solve`) | **41 ms** |

The refutation triangularizes until a row hits `0 = 1` — **near-linear**, and
parsing dominates it. The full *solve* keeps every basis row mutually reduced
(reduced row-echelon) to reconstruct a model — **superlinear** (~O(pivots²)). The
router therefore **refutes before it reconstructs**: UNSAT (the common case for
the hard families) stays linear, and the RREF cost is paid *only* when a
satisfying model is actually needed. That ordering — not any kernel change — took
the UNSAT path from 1149 ms to 41 ms at 4500 vars (**~28×**), in pure Python.

The lesson the benchmark taught, and the honest survivor of the whole
metal-optimization thread: **the win was algorithmic (do the cheap sound test
first), not silicon.** The Gaussian core is already near-free at research scale;
M4RI and a compiled rewrite remain premature until a measured crossover
(below), because nothing here is Gaussian-bound yet — it is *parse*-bound, and
the refutation is faster than the parsing that feeds it.

### Then optimize the serial code — before parallelizing (two measured passes)

Since the router is parse-bound, `extract_xors` is where the next in-code win
lives, and it splits into an honest negative and an honest positive — both
differential-tested to produce **byte-identical output** (92 cases incl.
adversarial duplicate-variable/tautology/over-arity clauses, 0 mismatches):

1. **Negative — the "obvious" rewrite bought nothing.** Sorting each clause once
   into `(var, sign)` pairs (dropping the per-clause `set`/`frozenset`/`sign`-dict
   scaffolding) measured **1.00×**: the tuple allocation in the sort exactly
   offset the scaffolding removed. *Cleaner ≠ faster; measure it.*
2. **Positive — attack the allocation, not the structure.** Encoding each sorted
   sign-pattern as a **k-bit `int`** (bit *i* = "*i*-th variable negated")
   instead of a tuple, deduped in two parity-pre-split sets, measured **~1.4×**.
   Small ints are interned and hash cheaper than tuples, and the parity pre-split
   turns the group test into a bare `len()` with no inner pass. This is the
   in-code floor for pure Python: the remaining cost is irreducible per-clause
   interpreter overhead, spread evenly (no dominant line) — so the *next* lever is
   genuinely across-instance batching or a C-level parser, not another micro-pass.

3. **Positive — let the clauses live in a tensor.** The deeper move (and the
   one that most directly answers "can they live in hyperbolic/nnn tensors, can
   you compact identicals into single points"): bucket clauses **by arity** so
   each bucket is a dense `(m, k)` integer tensor, then run abs / per-row sort /
   sign-encode / negation-parity as **array ops with no Python loop**, and let
   **`np.unique` be the "compact identical patterns into one point" step** — the
   distinct sign-patterns per variable-set collapse to unique rows, and a
   complete parity group is just a `unique`-count equal to `2^(k-1)`. Measured
   **~1.7× on Tseitin and ~2.3–2.8× on ragged/random CNF** over the bitmask form
   (ragged wins *more*, because "no complete group" is decided in bulk instead of
   per clause). Honest boundaries, all handled: the packed varset key is a signed
   `int64`, so a bucket with `bits·k > 62` **falls back to the pure-Python
   reference** (correctness universal); tiny buckets skip numpy (its overhead
   isn't worth it); and because extraction is **soundness-critical** (a spurious
   XOR would be an *unsound* refutation), the pure-Python path stays the trusted
   spec and a **differential test pins the two to byte-identical output** over a
   randomized battery. This is exactly the "loop-free / array-native" shape
   METAL_ROADMAP predicted would be the real GPU-friendly win — and it already
   pays off on CPU because arity-bucketing turns ragged combinatorial data dense.

   The honest limit on the *geometry* words: this is **tensorization**, not
   *hyperbolization*. Parsing is flat combinatorial bookkeeping — there is no
   curvature to exploit, so "hyperbolic" buys nothing here; and hypercomplex
   (GF(2ᵏ), CLMUL/GFNI) accelerates the *arithmetic* core, which is already
   near-free. The lever that fit was the dense tensor + the quotient-by-identicals
   (`unique`), which is precisely what was asked for, named correctly.

The ordering the three passes teach: **cheap-frame-first (algorithm) → attack
allocation, not structure (in-code) → let the data live in dense tensors
(vectorize) → batch across instances (parallelism)** — in that order, each gated
on a measurement, before any thought of metal.

So the metal roadmap is **not** "port to Rust for its own sake." It matters in
exactly three regimes, each with the *right* primitive:

## Where metal actually wins, per frame

### 1. Parity / GF(2) — the flat core

- **Scale (algorithmic):** at thousands+ of variables the win is the **Method of
  Four Russians (M4RI)** — precompute a Gray-code table of all 2ᵏ combinations of k
  rows (built by incremental XOR) and eliminate k columns per pass, turning
  O(n³) into O(n³/log n). This is the SOTA for dense GF(2) linear algebra and is
  cache- and SIMD-shaped. *That* is the real algorithmic optimization — not
  changing the storage.
- **Compiled inner loop:** when the frame becomes a hot pre-pass inside a real
  solver loop (called millions of times), the Python *dispatch* (not the XOR)
  dominates. A Rust/`PyO3` core removes it — packed `u64` limbs, `xor` over slices
  auto-vectorizes to AVX2/AVX-512 (512 GF(2) coordinates per instruction).
- **GPU (batch):** the SIMT win is **batching** — reduce thousands of independent
  GF(2) systems at once (one warp per system, bit-packed rows), or one huge system
  with a parallel M4RI. GF(2) matrices are the ideal GPU payload: no floats, no
  divergence in the XOR, pure bit-parallelism.

### 2. Counting / cardinality — ℤ, but still bit-shaped

The pigeonhole counting bound is `POPCNT` (population count) + a prefix sum over
group memberships — both single-instruction / warp-parallel. The union-find over
the exclusion graph is pointer-chasing (CPU-friendly, not GPU); keep it on CPU.

### 3. Implication / 2-SAT — leave it on the CPU

SCC over the implication graph is pointer-chasing and branch-heavy — genuinely
*not* SIMD/GPU shaped, and small. Don't force it onto the wrong metal.

### 4. Verification (the TCB) — fast *and* trusted

`verify_model` is, per clause, "is ≥1 literal true" = a bitwise OR-reduction over
the packed assignment; whole-formula model checking is AND/OR bit reductions —
SIMD-native. This is the one place to make fast *and* keep in the trusted base.

## The hypercomplex bridge — real, and mostly already in the silicon

- **GF(2ᵏ) is "hypercomplex over the Booleans."** The Cayley–Dickson doubling
  ladder (ℝ→ℂ→ℍ→𝕆→𝕊, dims 1,2,4,8,16) is *the same power-of-two ladder* as SIMD
  register lane counts (a quaternion = one 128-bit register; a sedenion = one
  AVX-512 register). For **floats**, hypercomplex arithmetic is SIMD-native by
  construction (this is why game engines do quaternion math in SSE) — real
  hardware, but a **lens for SAT** (our floats-hypercomplex work did not decide
  SAT; it stays a lens until it earns a frame).
- **The on-path version is GF(2ᵏ):** finite-field extensions of our GF(2) frame,
  with **dedicated instructions** — `PCLMULQDQ` for the multiply, `GFNI` for
  GF(2⁸) matrix/affine ops in a single AVX-512 instruction. If a future frame
  wants field structure over the parity core (Reed–Solomon-style, or GF(2ᵏ)
  Gaussian), the metal already has the ops. This is the genuine, on-topic
  hypercomplex-to-metal bridge.

## Hyperdimensional — the continuous next frame

Hyperdimensional Computing / Vector-Symbolic Architectures (Kanerva) represent
symbols as ~10⁴-dimensional **binary** vectors, with **binding = XOR**, bundling =
majority, permutation = rotation. Binary HDC *is our parity algebra at scale* —
10⁴-bit GF(2) vectors, XOR-bound — and it is explicitly built for SIMD / GPU /
processing-in-memory. It is the most credible "hyperdimensional" bridge to metal
and a real future frame candidate for **encoding formula structure** as
hypervectors (variable = hypervector; a clause = a bound bundle). Contract before
celebration: it earns a place only if such an encoding *decides* or *accelerates*,
measured — not asserted.

## Hyperbolic — honest lens

Hyperbolic geometry's genuine computational edge is **hierarchical / tree data**
(exponential volume ⇒ trees embed with low distortion), and the Lorentz model's
Minkowski inner product is a cheap signed dot product (GPU-friendly). SAT search
*is* tree-shaped, so a hyperbolic branching/decomposition heuristic is conceivable
— but Rung 1 showed geometric embeddings do not carry hardness, so this stays a
**lens** until one earns a frame. No metal work is justified here yet.

## The roadmap (prioritized, contracted)

1. **Do nothing at research scale.** The frames are ~1 ms; Python bigints already
   XOR at C speed; a naive rewrite measured *slower*. (Verified above.)
2. **When scaling up:** implement **M4RI** for the GF(2) frame (algorithmic
   O(n³/log n)); contract = identical verdicts to the current code on a
   differential test, faster only above a measured crossover size.
3. **When embedding as a solver pre-pass:** a Rust/`PyO3` `gf2` core (packed `u64`,
   auto-vectorized XOR, `PCLMULQDQ`/`GFNI` where present) to remove interpreter
   dispatch. Keep the TCB pieces (parser, `verify_model`, the refutations) in this
   fast, *verified* core — differential-tested against the Python reference.
4. **For throughput:** a GPU batched-GF(2) kernel (CUDA/`wgpu`) to reduce many
   instances at once — the SIMT-natural payload.
5. **Never:** claim we out-engineer CDCL. The metal win is making the **sound
   frames and the certification layer** run at silicon speed so the middleware's
   overhead vanishes and the frames become a genuinely *free* pre-pass. That, and
   only that, is the honest target.

The unifying line: **our geometry's job is to find the flat frame; the metal's job
is to XOR it.** We chased curvature to understand hardness; we collapse to
characteristic 2 to compute it; and characteristic 2 is the one algebra the
hardware already loves.

## GPU via CuPy — and where a substrate fabric fits (addendum)

[CuPy](https://github.com/cupy/cupy) is the natural GPU vehicle: a drop-in
NumPy/SciPy for CUDA/ROCm, so the same code runs on device via the standard
`xp = cupy if available else numpy` swap, with `cupy.RawKernel`/`RawModule` for
custom CUDA when a hot loop needs it.

**But the two measurements above and below are the honest guardrail, and they say
the same thing twice:**

| op | Python | naive array rewrite |
|---|---|---|
| single GF(2) 700×700 reduce | 13 ms (bigint) | 27 ms numpy (**0.5×**) |
| batch model-check 4000×800 | 12 ms | 9 ms numpy (**~1.4×**) |

**CuPy does not fix a Python control loop.** Both naive rewrites kept a Python
loop over columns/clauses, so the interpreter dispatch (and, on GPU, per-op
host↔device sync) dominates and the "acceleration" evaporates — a swap of the
array library changes nothing. The GPU win requires *eliminating the loop first*:

- **Loop-free / array-native form** — express the whole op as a handful of dense
  tensor ops with no Python iteration. This is where CuPy is a genuine, clean win,
  and it is exactly the shape of a **KNN distance sweep**: the split-signature
  `(2,2)` metric `⟨q,d⟩ = (q₀d₀+q₁d₁) − (q₂d₂+q₃d₃)` over a whole dataset is a
  single signed matmul — no inner loop — so it maps to one CuPy call and scales
  to GPU trivially. (Our clean targets: batched GF(2) matrix products, the TCB
  model-verify as packed AND/OR reductions, M4RI Gray-code table builds.)
- **`RawKernel`** — for genuinely data-dependent loops (per-system Gaussian
  pivoting), one-system-per-thread-block CUDA, where SIMT tolerates the
  divergence. That is the honest path for batched frame-solving of many instances.

### The substrate layer (external prior art, not vendored)

The complementary question — *where do the bit-matrices live and how do they
reach the GPU at scale* — is a **data-movement / memory-tier** problem, distinct
from compute. The operator's own **NNN Hyperbolic Semantic Memory Fabric**
(© Jesús Vilela Jato, all rights reserved — *referenced, not included*) is a
directly relevant design here: a tiered, geometry-addressed substrate
(RAM/tmpfs → NVMe-ZNS → GPU KV-cache → CXL) behind one Geometric Memory Protocol,
with an honest split between a C++ "simulation profile" core and Python
orchestration (its GPU tier is explicitly flagged `_EMULATED`, which is the right
discipline). Its live idea for *us*: **geometry-aware placement** — shard the
GF(2) row-blocks / clause sets by a locality metric so the pieces a frame needs
are co-resident before the kernel launches (the GPUDirect-Storage / CXL path).
Substrate = data movement; CuPy = compute; our frames = what runs. Three layers,
kept separate and each honest.

### Honest boundary

None of the GPU numbers above exist yet — there is **no GPU in this environment**,
so the CuPy path is *designed and CPU-validated via numpy*, pending hardware, and
should be treated like the Lean obligation: a written contract, not a measured
result, until a device runs it. The first real experiment when a GPU is available:
a loop-free CuPy `(2,2)`-distance KNN (clean win, expected) and a `RawKernel`
batched GF(2) reduce (the real test), each differential-tested against the Python
reference.
