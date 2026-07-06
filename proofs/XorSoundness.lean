/-
  Soundness of the GF(2) / XOR refutation used by
  `backend/xor_extraction.py::gf2_xor_refutation` (and the UNSAT branch of
  `gf2_xor_solve`).

  ┌────────────────────────────────────────────────────────────────────────┐
  │ STATUS: DRAFT — NOT COMPILER-VERIFIED IN THIS ENVIRONMENT.               │
  │ The sandbox has no Lean toolchain and blocks the download (github        │
  │ release assets return 403 through the agent proxy). Verify locally with  │
  │     lean proofs/XorSoundness.lean                                        │
  │ or point Leanstral / `vibe --agent lean` at it. It is mathlib-free and   │
  │ self-contained, so a bare `lean` binary suffices. Until it compiles,     │
  │ treat every theorem below as a PROOF OBLIGATION, not an established fact  │
  │ (Charter: a name is not a proof).                                        │
  └────────────────────────────────────────────────────────────────────────┘

  What it captures: the refutation XOR-combines parity constraints (rows over
  GF(2)) to derive the contradiction `0 = 1`. Soundness is the principle that
  makes that valid — if any XOR-combination of the constraints is `0 = 1`, then
  no assignment satisfies all of them, so the formula is UNSAT.
-/

namespace XorSoundness

variable {A : Type}

/-- A parity constraint over assignments of type `A`: the left-hand parity as a
    Boolean function of the assignment, together with its right-hand side. -/
structure Constraint (A : Type) where
  lhs : A → Bool
  rhs : Bool

/-- `a` satisfies `c` iff its parity equals the right-hand side. -/
def Sat (c : Constraint A) (a : A) : Prop := c.lhs a = c.rhs

/-- GF(2) row addition: XOR the parities and XOR the right-hand sides. -/
def combine (c d : Constraint A) : Constraint A where
  lhs := fun a => Bool.xor (c.lhs a) (d.lhs a)
  rhs := Bool.xor c.rhs d.rhs

/-- Homomorphism: an assignment satisfying two constraints satisfies their XOR. -/
theorem Sat_combine {c d : Constraint A} {a : A}
    (hc : Sat c a) (hd : Sat d a) : Sat (combine c d) a := by
  simp only [Sat, combine] at *
  rw [hc, hd]

/-- The contradiction `0 = 1`: parity constantly `false`, right-hand side `true`. -/
def contra : Constraint A where
  lhs := fun _ => false
  rhs := true

/-- No assignment satisfies `0 = 1`. -/
theorem not_Sat_contra (a : A) : ¬ Sat (contra (A := A)) a := by
  simp [Sat, contra]

/-- XOR-combine a list of constraints (the empty combination is `0 = 0`). -/
def combineAll : List (Constraint A) → Constraint A
  | []      => { lhs := fun _ => false, rhs := false }
  | c :: cs => combine c (combineAll cs)

/-- If `a` satisfies every constraint in `cs`, it satisfies their XOR-fold. -/
theorem Sat_combineAll {a : A} :
    ∀ cs : List (Constraint A), (∀ c, c ∈ cs → Sat c a) → Sat (combineAll cs) a
  | [], _ => by simp [Sat, combineAll]
  | c :: cs, h => by
      have hc : Sat c a := h c (List.mem_cons_self c cs)
      have hcs : Sat (combineAll cs) a :=
        Sat_combineAll cs (fun x hx => h x (List.mem_cons_of_mem c hx))
      exact Sat_combine hc hcs

/-- **Soundness.** If some XOR-combination of `cs` is the contradiction `0 = 1`,
    then no assignment satisfies all of `cs`: the constraint system is UNSAT.
    This is exactly what `gf2_xor_refutation` exploits — Gaussian elimination
    finds such a combination, and its existence proves unsatisfiability. -/
theorem refutation_sound (cs : List (Constraint A))
    (h : combineAll cs = contra) : ¬ ∃ a, ∀ c, c ∈ cs → Sat c a := by
  rintro ⟨a, ha⟩
  have hsat : Sat (combineAll cs) a := Sat_combineAll cs ha
  rw [h] at hsat
  exact not_Sat_contra a hsat

end XorSoundness
