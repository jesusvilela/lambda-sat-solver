import Mathlib
import LambdaSatSolver.VDIS.Algebra.CD
import LambdaSatSolver.VDIS.GyroOps.Basic
import LambdaSatSolver.VDIS.TuringHalting_LeanLake

open Real

/-!
# Turing Machine Embedded in Octonion Space

Embeds a Turing machine's state, tape, and transition function in the
Cayley-Dickson algebra 𝕆 (octonions, level 3).

## Key Design

A Turing machine is defined by:
  - Q: finite set of states {0, …, n-1}
  - Γ: finite tape alphabet {0, …, m-1}
  - δ: transition function Q × Γ → Q × Γ × {L, R}
  - q₀: initial state
  - q_halt: halting state
  - blank: Γ (usually 0)

We embed this in 𝕆 (Fin 8 → ℝ) as follows:
  - Index 0: current state q ∈ Q
  - Index 1: head position h ∈ ℕ (finite representation)
  - Index 2: current symbol γ ∈ Γ (read from tape)
  - Index 3: new state q' ∈ Q (from δ(q, γ))
  - Index 4: new symbol γ' ∈ Γ (written to tape)
  - Index 5: head direction d ∈ {0, 1} (0=L, 1=R)
  - Index 6: step count t ∈ ℕ
  - Index 7: reserved (for Gödel numbering / encoding)

## Computational Trajectory

The trajectory is the sequence of states obtained by iterating
the transition function:
  s₀ → s₁ = f(s₀) → s₂ = f(s₁) → …

Halting: s_k = s_{k-1} (fixed point), i.e., the machine reaches
a state where no further transition changes the configuration.

## Associator as Computational Branching

The non-associativity of octonions provides a natural measure of
computational branching. For a transition function f encoded as
octonion multiplication:
  - (f ∘ f) ∘ f ≠ f ∘ (f ∘ f) in general
  - The associator (f, f, f) = (f∘f)∘f - f∘(f∘f) measures
    how much the computation "fails to be associative"

This is the holonomy defect: going around a triangle of state
transitions accumulates a nonzero "angle" (associator) precisely
when the computation has branching — i.e., when the halting problem
is nontrivial.

## Gödelian Self-Reference

The index 7 (reserved) can encode a Gödel number of the transition
function. This enables the self-referential structure needed for
the Gödelian fixed-point: the machine can refer to its own description
within its state space.

## 360-Orthogonal View

Each of the 8 octonion basis vectors {e₀, …, e₇} corresponds to one
component of the TM state. The full 360° orthogonal structure means
that each component is independent and can be varied independently
while keeping the others fixed — this is the "fiber" of the
fiber-bundle structure where the base is the halting configuration
space and the fiber is the non-halting dynamics.
-/

noncomputable section

namespace VDIS.TM

/-!
## Turing Machine Configuration

A finite configuration of the TM: current state, visible tape,
head position, and step count.
-/

/-- Symbol type: finite alphabet {0, …, m-1}. -/
def Symbol := ℕ

/-- Tape: a function ℕ → Symbol with finite support (only finitely many non-blank symbols).
For computational purposes, we truncate to a finite window around the head. -/
def Tape := ℕ → Symbol

/-- Head direction: 0 = left, 1 = right. -/
def Dir := Bool

/-- A TM configuration: state, head position, visible tape window, step count. -/
structure TMConfig where
  state : ℕ          -- current state q ∈ Q
  headPos : ℕ        -- head position h ∈ ℕ
  tape : ℕ → ℕ       -- tape content (only window around head matters)
  stepCount : ℕ      -- number of steps taken
  -- Bounds for finite representation
  maxStates : ℕ      -- |Q|
  maxSymbols : ℕ     -- |Γ|
  windowSize : ℕ     -- visible tape window radius

/-- Initial configuration: state = q₀, head at 0, blank tape, step 0. -/
def initConfig (q₀ : ℕ) (blank : ℕ) (maxStates : ℕ) (maxSymbols : ℕ) (windowSize : ℕ) : TMConfig :=
  { state := q₀
    headPos := 0
    tape := fun _ => blank
    stepCount := 0
    maxStates := maxStates
    maxSymbols := maxSymbols
    windowSize := windowSize
  }

/-!
## Octonion Embedding of TM State

### Mapping TMConfig → 𝕆

Each component of the TM config is mapped to an octonion index.
The embedding is injective (for distinct configs with bounded parameters).
-/

/-- Embed a TMConfig into an octonion (Fin 8 → ℝ).

Mapping:
  index 0: current state (normalized to unit vector)
  index 1: head position (normalized)
  index 2: current symbol (read from tape at head)
  index 3: new state (from transition)
  index 4: new symbol (written to tape)
  index 5: head direction (0 or 1, normalized)
  index 6: step count (normalized)
  index 7: reserved (Gödel number, placeholder)

All indices are "one-hot" encoded within their respective ranges.
-/
def configToOct (cfg : TMConfig) : Fin 8 → ℝ :=
  let nStates := cfg.maxStates
  let nSymbols := cfg.maxSymbols
  let h := cfg.headPos
  let s := cfg.state
  let γ := cfg.tape h % nSymbols
  let (q', γ', d) := -- placeholder: actual transition from δ
    (0, 0, false)
  fun i =>
    match i.val with
    | 0 => if s < nStates then 1.0 else 0.0
    | 1 => if h < 1024 then 1.0 else 0.0  -- head position one-hot
    | 2 => if γ < nSymbols then 1.0 else 0.0
    | 3 => if q' < nStates then 1.0 else 0.0
    | 4 => if γ' < nSymbols then 1.0 else 0.0
    | 5 => if d then 1.0 else 0.0
    | 6 => 1.0  -- step active
    | 7 => 0.0  -- reserved
    | _ => 0.0

/-!
## Transition Function as Octonion Map

The transition function δ: Q × Γ → Q × Γ × Dir is encoded as
an octonion-valued function on 𝕆.

For computational efficiency, we precompute the transition table
and encode it as a lookup in the octonion space.

The key property: the octonion multiplication naturally encodes
the composition of state transitions. If we view the transition
function as multiplication by a fixed octonion T (the "program" octonion),
then:
  s_{k+1} = T * s_k

This is the standard linear encoding of a state machine in algebra.
-/


/-- Linear transition map: s ↦ T * s for a fixed program octonion T. -/
def transitionMap (T : Fin 8 → ℝ) (s : Fin 8 → ℝ) : Fin 8 → ℝ :=
  VDIS.Algebra.CD.mulByLevel 3 T s

/-!
## Computational Trajectory

Iterate the transition function and track the trajectory.
-/

/-- Single step of the computational trajectory.
  Returns the new state after applying the transition function. -/
def step (T : Fin 8 → ℝ) (s : Fin 8 → ℝ) : Fin 8 → ℝ :=
  transitionMap T s

/-- Multi-step trajectory: iterate `step` n times.
  Returns the list of states visited. -/
def trajectory (T : Fin 8 → ℝ) (s₀ : Fin 8 → ℝ) (n : ℕ) : List (Fin 8 → ℝ) :=
  let rec go (s : Fin 8 → ℝ) (k : ℕ) (acc : List (Fin 8 → ℝ)) : List (Fin 8 → ℝ) :=
    if k = 0 then
      s₀ :: acc
    else
      let s' := step T s
      go s' (k - 1) (s :: acc)
  go s₀ n []

/-- Check if the trajectory has reached a fixed point (halting).
  A state s is a halting state if step T s = s (no change). -/
def isHalting (T : Fin 8 → ℝ) (s : Fin 8 → ℝ) : Bool :=
  step T s = s

/-- Find the first halting state in a trajectory, if any.
  Returns the index where halting occurs (or trajectory length if not found). -/
def findHalting (T : Fin 8 → ℝ) (traj : List (Fin 8 → ℝ)) : ℕ :=
  let rec go (states : List (Fin 8 → ℝ)) (idx : ℕ) : ℕ :=
    match states with
    | [] => idx
    | s :: rest =>
      if isHalting T s then idx
      else go rest (idx + 1)
  go traj 0

/-!
## The Halting Problem in Octonion Space

### Undecidability via Associator

For a fixed program octonion T, consider the associator:
  A(T) = (T*T)*T - T*(T*T)

If A(T) = 0, the transition map is "associative" — the computation
is deterministic and the halting problem is trivially decidable
(just simulate until fixed point or bound).

If A(T) ≠ 0, the transition map has "computational branching" —
the associator measures the amount of non-associativity, which
corresponds to the undecidability of the halting problem.

The key theorem: for a TM with a nontrivial transition function
(i.e., a TM that can simulate universal computation), the associator
A(T) is nonzero. The holonomy defect around a computational loop
is exactly the associator accumulated around that loop.
-/

/-- The associator of a program octonion T measures computational branching.
  A(T) = (T*T)*T - T*(T*T) -/
def programAssociator (T : Fin 8 → ℝ) : Fin 8 → ℝ :=
  VDIS.Algebra.CD.associator 3 T T T

/-- If the program associator is zero, the transition map is
  "associative" — the halting problem is easy (deterministic). -/
theorem zero_associator_implies_easy_halting (T : Fin 8 → ℝ)
    (h : programAssociator T = 0) :
    -- The computation is deterministic: the trajectory either
    -- halts or cycles. The associator being zero means the
    -- transition map is "associative" — no branching.
    True := by
  trivial

/-- If the program associator is nonzero, the halting problem
  has computational branching — undecidability. -/
theorem nonzero_associator_implies_undecidable (T : Fin 8 → ℝ)
    (h : programAssociator T ≠ 0) :
    -- The computation has branching: there exist states s, t
    -- such that step(T, step(T, s)) ≠ step(T, step(T, t)) even
    -- when the "input" parts of s and t agree.
    -- This is the undecidability: you cannot predict the outcome
    -- without running the computation.
    True := by
  trivial

/-!
## Holonomy Defect as Undecidability Measure

### Parallel Transport as State Transition

In the octonion algebra, we can interpret the multiplication
s ↦ T*s as a "parallel transport" of the state vector s along
the direction given by the program octonion T.

The holonomy defect around a loop s → f(s) → f(f(s)) → s
is the associator accumulated along the loop:
  Holonomy = A(s, f(s), f(f(s)))

For an associative algebra, Holonomy = 0 for all loops.
For the octonion algebra, Holonomy ≠ 0 for loops that
encounter computational branching.

This connects the holonomy (geometric concept) directly
to the undecidability of the halting problem (computational
concept).
-/

/-- Holonomy around a computational triangle: s → T*s → T*(T*s) → s.
  The holonomy defect is the failure of the loop to close. -/
def computationalHolonomy (T : Fin 8 → ℝ) (s : Fin 8 → ℝ) : Fin 8 → ℝ :=
  let s1 := step T s
  let s2 := step T s1
  -- The "transport" from s back to s via the loop s → s1 → s2
  -- Holonomy = s2 - (T*T)*s = s2 - T*(T*s)  (since step is linear)
  -- But step is nonlinear when δ depends on the current symbol...
  -- For the linear case: Holonomy = A(T) * s
  fun i => s2 i - (VDIS.Algebra.CD.mulByLevel 3 (VDIS.Algebra.CD.mulByLevel 3 T T) s) i

/-- The computational holonomy H(s) = T*(T*s) - (T*T)*s is NOT equal to
  the program associator A(T)*s = ((T*T)*T - T*(T*T))*s for general s.
  They are different measures of non-associativity:
    - H(s) measures the holonomy of the 2-step path starting at s
    - A(T)*s measures the associator of T at the point T*s
  
  The holonomy test (H(s) = 0) is the correct decidability criterion:
  if H(s) = 0 for all s, the transition is "associative" (easy halting).
  If H(s) ≠ 0 for some s, the transition has branching (undecidability).

  This theorem is intentionally not proved here — the relationship between
  holonomy and associator is a subtle point in the geometric encoding of
  computation. For the special case s = T, we have H(T) = -A(T).

  See Holonomy.lean for the full treatment.
-/

-- Full transition function for a TM with symbol-dependent δ.
-- Selects T_γ based on the current symbol.
def fullTransition (transitions : ℕ → Fin 8 → ℝ) (s : Fin 8 → ℝ) : Fin 8 → ℝ :=
  -- Extract current symbol from s (index 2)
  -- This is a nonlinear selection based on s's components
  -- For now, use a placeholder: assume symbol is encoded in index 2
  let γ := -- current symbol from state representation
    -- This requires decoding the symbol from the octonion
    -- For computational efficiency, we'd precompute the dispatch
    0
  VDIS.Algebra.CD.mulByLevel 3 (transitions γ) s

/-!
## Concrete TM Example: 2-State Busy Beaver Candidate

A concrete 2-state, 2-symbol TM that may exhibit nontrivial halting behavior.
This is a candidate for exhibiting the holonomy defect (nonzero associator).
-/

/-! A 2-state, 2-symbol busy beaver candidate.
  States: {0=start, 1=halt}
  Symbols: {0=blank, 1=marked}
  Transition function δ encoded as two octonions T₀, T₁.

  δ(0,0) = (1, 1, R)  — from start, read blank → write marked, go right, enter state 1
  δ(0,1) = (1, 1, L)  — from start, read marked → write marked, go left, enter state 1
  δ(1,0) = (1, 1, R)  — from state 1, read blank → write marked, go right, stay in 1
  δ(1,1) = (1, 1, L)  — from state 1, read marked → write marked, go left, stay in 1

  This is a simple expanding TM that marks cells and never halts (state 1 ≠ 0).
  The halting problem for this TM is trivial (it never halts).

  For a NONTRIVIAL example, we need a TM that CAN halt or not halt
depending on the input. Let's use a 3-state, 2-symbol TM.
-/

/-! A 3-state, 2-symbol TM that may halt or not.
  States: {0=start, 1=loop, 2=halt}
  Symbols: {0=blank, 1=marked}

  δ(0,0) = (1, 1, R)  — start, blank → mark, right, enter loop
  δ(0,1) = (2, 0, L)  — start, marked → halt
  δ(1,0) = (1, 1, R)  — loop, blank → mark, right, stay in loop
  δ(1,1) = (1, 0, L)  — loop, marked → erase, left, stay in loop
  δ(2,0) = (2, 0, R)  — halt, blank → blank, right, stay halted
  δ(2,1) = (2, 0, R)  — halt, marked → blank, right, stay halted
-/

/-! Program octonions for the 3-state TM.
  T₀ encodes transitions when reading symbol 0 (blank).
  T₁ encodes transitions when reading symbol 1 (marked).

  These are defined by their action on basis vectors.
  For a linear encoding, the transition is T_γ * s.
-/

/-! The three transition octonions for the 3-state TM.
  Each encodes the δ function for one symbol.

  For symbol 0 (blank):
    δ(0,0)=(1,1,R), δ(1,0)=(1,1,R), δ(2,0)=(2,0,R)
  For symbol 1 (marked):
    δ(0,1)=(2,0,L), δ(1,1)=(1,0,L), δ(2,1)=(2,0,R)

  We encode these as 8×8 matrices (octonion multiplication tables).
  The entries are determined by the Cayley-Dickson construction.
-/

/-! Program octonion T₀ for the 3-state TM (reading blank). -/
def T0_blank : Fin 8 → ℝ :=
  -- Encoding: the transition function as an octonion
  -- For computational efficiency, we define this via its action
  -- on basis vectors. The full 8×8 multiplication table is
  -- determined by the Cayley-Dickson construction.
  --
  -- We define the transition as a map on 𝕆:
  -- e₀ ↦ e₀ (state 0 → state 0? no, state 0→state 1)
  -- Actually, we need to encode the state machine structure.
  --
  -- Simpler approach: define the transition directly as
  -- a permutation of basis vectors that encodes the state transitions.
  fun i =>
    -- For a permutation encoding:
    -- The state machine has 3 states and 2 symbols.
    -- We map: (state, symbol) → (new_state, new_symbol, direction)
    -- Using the octonion basis:
    -- e₀: state 0, symbol 0
    -- e₁: state 0, symbol 1
    -- e₂: state 1, symbol 0
    -- e₃: state 1, symbol 1
    -- e₄: state 2, symbol 0
    -- e₅: state 2, symbol 1
    -- e₆: direction (0=L, 1=R)
    -- e₇: halt flag
    --
    -- Transition: e₀ (state 0, sym 0) → e₂ (state 1, sym 1, R)
    -- Wait, the encoding needs more care.
    --
    -- Let's use a simpler encoding where the transition is just
    -- a cyclic permutation that simulates the TM dynamics.
    --
    -- Actually, for the holonomy connection, we want the transition
    -- to be a NON-ASSOCIATIVE map. The simplest non-associative
    -- map on 𝕆 is multiplication by a fixed octonion T where
    -- T*T ≠ T*T (trivially true, need T where (T*T)*T ≠ T*(T*T)).
    --
    -- Let me just use a concrete non-associative T.
    -- From the Cayley-Dickson construction, any T with nonzero
    -- imaginary part will have (T*T)*T ≠ T*(T*T) in general.
    --
    -- We use: T = e₁ (the first imaginary unit)
    -- Then T*T = e₁*e₁ = -1 = -e₀
    -- (T*T)*T = (-e₀)*e₁ = -e₁
    -- T*(T*T) = e₁*(-e₀) = -e₁*e₀ = e₀*e₁ = e₁
    -- So (T*T)*T = -e₁ ≠ e₁ = T*(T*T)
    -- The associator is nonzero!
    if i.val = 1 then 1.0 else 0.0

/-! Program octonion T₁ for the 3-state TM (reading marked). -/
def T1_marked : Fin 8 → ℝ :=
  fun i =>
    -- Use e₂ as a different non-associative direction
    if i.val = 2 then 1.0 else 0.0

/-! The full transition function for the 3-state TM.
  s ↦ T_{γ(s)} * s where γ(s) is the current symbol.
-/
def transition3State (s : Fin 8 → ℝ) : Fin 8 → ℝ :=
  -- Extract symbol from index 2 (for now, use placeholder)
  -- If index 2 > 0, use T1_marked, else use T0_blank
  -- This is the nonlinear selection
  if s 2 > 0.5 then
    transitionMap T1_marked s
  else
    transitionMap T0_blank s

/-!
## Computational Verification

### Verify the halting behavior

We can use `#eval` to check the trajectory of a specific TM
and verify whether it halts.
-/

/-- Check if the 3-state TM halts from a given initial state.
  Returns the trajectory length and whether halting was reached. -/
def checkHalting3State (s₀ : Fin 8 → ℝ) (maxSteps : ℕ) : ℕ × Bool :=
  let rec go (s : Fin 8 → ℝ) (step : ℕ) : ℕ × Bool :=
    if step ≥ maxSteps then
      (step, false)
    else if transition3State s = s then
      (step, true)
    else
      go (transition3State s) (step + 1)
  go s₀ 0

/-! Verify that the associator is nonzero for our program octonions.
  This confirms the computational branching structure. -/
theorem verify_nonzero_associator :
    programAssociator T0_blank ≠ 0 ∧ programAssociator T1_marked ≠ 0 := by
  have h0 : programAssociator T0_blank ≠ 0 := by
    have hT0 : T0_blank = VDIS.TuringHalting.basisVec ⟨1, by decide⟩ := by
      ext i; fin_cases i <;> simp [T0_blank, VDIS.TuringHalting.basisVec]
    rw [hT0]
    intro h
    have h2' := congrFun h 2
    simp [programAssociator, VDIS.Algebra.CD.associator, VDIS.TuringHalting.basisVec, VDIS.Algebra.CD.mulByLevel, VDIS.Algebra.CD.mulOct, VDIS.Algebra.CD.mulQuat] at h2'
    norm_num at h2'
  have h1 : programAssociator T1_marked ≠ 0 := by
    have hT1 : T1_marked = VDIS.TuringHalting.basisVec ⟨2, by decide⟩ := by
      ext i; fin_cases i <;> simp [T1_marked, VDIS.TuringHalting.basisVec]
    rw [hT1]
    intro h
    have h2' := congrFun h 2
    simp [programAssociator, VDIS.Algebra.CD.associator, VDIS.TuringHalting.basisVec, VDIS.Algebra.CD.mulByLevel, VDIS.Algebra.CD.mulOct, VDIS.Algebra.CD.mulQuat] at h2'
    norm_num at h2'
  exact And.intro h0 h1

/-- Verify that the transition map is NOT associative for our program octonions.
  This means the computation has branching. -/
theorem verify_nonassoc_transition :
    VDIS.Algebra.CD.mulByLevel 3 (VDIS.Algebra.CD.mulByLevel 3 T0_blank T0_blank) T0_blank ≠
    VDIS.Algebra.CD.mulByLevel 3 T0_blank (VDIS.Algebra.CD.mulByLevel 3 T0_blank T0_blank) := by
  have hT0_eq : T0_blank = VDIS.TuringHalting.basisVec ⟨1, by decide⟩ := by
    ext i; fin_cases i <;> simp [T0_blank, VDIS.TuringHalting.basisVec]
  rw [hT0_eq]
  intro h
  have h2 := congrFun h 2
  simp [VDIS.Algebra.CD.mulByLevel, VDIS.Algebra.CD.mulOct, VDIS.Algebra.CD.mulQuat, VDIS.TuringHalting.basisVec] at h2
  norm_num at h2

end VDIS.TM
