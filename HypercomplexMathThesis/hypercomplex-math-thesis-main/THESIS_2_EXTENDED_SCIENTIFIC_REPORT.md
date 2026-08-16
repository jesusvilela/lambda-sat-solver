# Thesis 2 Extended Scientific Report

## Stratified Algebraic-Geometric Intelligibility, Non-Collapsing Communication, and Projection-Aware Cognition

**Status:** English research continuation of Thesis 2.  
**Scope:** scientific tightening of the Spanish continuation: standard literature-backed components are separated from proposed synthesis.  
**Boundary:** this is not a claim that physical cognition is literally octonionic, sedenionic, or Calabi-Yau. It is a falsifiable modeling program using those structures as algebraic-geometric regimes.

---

## Executive Summary

Thesis 2 strengthens Thesis 1. Intelligibility is not only a non-sequential hypercomplex regime; it is a family of stationary configurations of a composite geometric-algebraic object built from:

- real smooth manifolds stratified by local Cayley-Dickson algebra laws,
- sheaves and cosheaves over finite interfaces,
- fiber bundles with connections,
- Hamiltonian and contact-like dynamics,
- local Hilbert bundles and quantum-amplitude layers,
- toroidal orientation fields of type `360 x 360 x ...`,
- n-ary resonance chambers,
- singularity/compression/renormalization operators,
- and projection families into readable artifacts such as text, code, diagrams, equations, and experiments.

The individual bricks are supported by existing mathematics and machine-learning literature:

- hyperbolic geometry is effective for latent hierarchy and similarity compression;
- sheaf theory formalizes local-to-global compatibility and has concrete Laplacian/diffusion implementations;
- `R, C, H, O` and higher Cayley-Dickson algebras expose commutativity failure, associativity failure, and zero divisors;
- Berry phase is naturally read as holonomy of a connection;
- Calabi-Yau moduli spaces illustrate how compact geometric seeds can unfold into rich families of regimes.

The non-standard contribution is the synthesis:

```math
\boxed{
\text{Cognition/intelligibility is modeled as a non-sequential coherence object } \mathfrak X.
}
```

Validity does not depend on a pipeline, module order, or privileged causal sequence. It depends on simultaneous satisfaction of:

```math
\delta\mathcal A[\mathfrak X]=0
```

and/or:

```math
\Phi(\mathfrak X)=\mathfrak X.
```

Communication is no longer message transfer. It is the existence of an approximate global section over an n-ary resonance chamber `\Lambda_A`, with compatibility error small but nonzero:

```math
0<\varepsilon_A<\tau_A.
```

The strict inequality on the left matters. Perfect identity collapses alterity. Communication is compatible difference, not equality.

---

## 1. Rigor Clause: No Naive Sedenionic Manifolds

The most important correction is this:

```text
Do not speak of "sedenionic manifolds" as if there were a standard, unique differential geometry over sedenionic coordinates.
```

The mathematically defensible formulation is:

```math
\boxed{
\text{use real smooth manifolds with additional algebraic stratification.}
}
```

Each point carries a local product law:

```math
\mu_x:T_xM\otimes T_xM\to T_xM
```

or a product law on an associated state fiber. A selector field:

```math
\chi:\mathcal M\to\{0,\dots,\mathcal N_{\mathrm{CD}}\}
```

chooses the local Cayley-Dickson stratum.

Thus the base differential geometry remains standard:

```math
M_n \text{ is a finite-dimensional paracompact real smooth manifold.}
```

while hypercomplexity is encoded as tensorial algebraic structure:

```math
\mu^{(n)}\in
\Gamma\!\left(T^\ast M_n\otimes T^\ast M_n\otimes TM_n\right).
```

This preserves ordinary calculus while allowing octonionic nonassociativity and sedenionic zero divisors to become controlled model features.

---

## 2. Explicit Assumptions

1. Each base space `M_n` is a real finite-dimensional smooth paracompact manifold.
2. Hypercomplexity is encoded by multiplication tensors, not by informal sedenionic coordinate charts.
3. N-ary resonance chambers `\Lambda_A` are implemented over finite interfaces: posets, hypergraphs, or symmetric simplicial sets.
4. Every readable projection `\Pi_\ell` has an approximate lift `\Pi_\ell^\dagger` in experiments, so structural loss can be measured.
5. Every unspecified constant is an open model parameter, not a hidden theorem.
6. Discretization is computational, not ontological.
7. Solver order is algorithmic, not the native order of the object.

---

## 3. Standard Components Versus Proposed Components

### Literature-backed components

| Component | Status |
|---|---|
| Hyperbolic / Poincare geometry for hierarchy | standard, empirically used |
| Riemannian optimization | standard |
| Sheaves, cosheaves, local-global gluing | standard |
| Sheaf Laplacians and neural sheaf diffusion | active applied literature |
| Holonomy and Berry phase | standard in geometric quantum mechanics |
| Cayley-Dickson sequence through `R,C,H,O` and beyond | standard algebra |
| Octonion nonassociativity | standard |
| Sedenion zero divisors | standard |
| Calabi-Yau moduli spaces | standard in complex/string geometry |

### Proposed by Thesis 2

| Component | Status |
|---|---|
| Algebraically stratified intelligibility manifold `(M,chi,mu)` | proposed synthesis |
| N-ary resonance chamber `\Lambda_A` as communication site | proposed |
| `ProjectionViolence` metric | proposed |
| `HolonomyDrift` as semantic phase-memory drift | proposed |
| `Omnigog` reseeding operator | proposed |
| Non-collapsing communication criterion `0 < epsilon_A < tau_A` | proposed |
| Meaning as readable projection plus active remainder | proposed, now executable in repo |

---

## 4. Core Formal Objects

### 4.1 Cayley-Dickson family

Let `A_n` denote the nth Cayley-Dickson algebra:

```math
D_n=\dim_{\mathbb R}\mathbb A_n=2^n.
```

For:

```math
n=0,1,2,3
```

we recover:

```math
\mathbb R,\quad \mathbb C,\quad \mathbb H,\quad \mathbb O.
```

Higher levels lose properties:

- `O` is alternative but nonassociative.
- For `n >= 4`, zero divisors appear.
- Norm multiplicativity is no longer canonical beyond the Hurwitz division-algebra range.

Therefore the norm family:

```math
|\cdot|_\chi
```

must be part of the model, not assumed universal.

### 4.2 Algebraically stratified plurimanifold

Define:

```math
\mathcal M=\bigsqcup_{n=0}^{\mathcal N_{\mathrm{CD}}}M_n,
\qquad
\chi:\mathcal M\to\{0,\dots,\mathcal N_{\mathrm{CD}}\}.
```

Each stratum has a multiplication tensor:

```math
\mu^{(n)}\in
\Gamma\!\left(T^\ast M_n\otimes T^\ast M_n\otimes TM_n\right).
```

In local frames, `mu^(n)` reproduces the selected Cayley-Dickson structure constants or a chosen representation/subalgebra.

### 4.3 Sheaf, cosheaf, bundle, Hilbert layer

Over `M`:

```math
\mathscr F:\mathrm{Open}(\mathcal M)^{op}\to\mathbf{Vect}_{\mathbb R}
```

is a sheaf of local states, and:

```math
\mathscr C:\mathrm{Open}(\mathcal M)\to\mathbf{Vect}_{\mathbb R}
```

is a cosheaf of residues or obstructions.

State and quantum layers:

```math
E\to\mathcal M,\qquad
\mathcal H\to\mathcal M.
```

The practical implementation can be a finite poset/hypergraph sheaf. The richer categorical reading can be a stack of local models modulo gauge.

### 4.4 Toroidal orientation field

The `360 x 360 x ...` object is formalized as:

```math
\Theta:\mathcal M\to\mathbb T^{m_\Theta}.
```

The discrete implementation:

```math
\Theta_{\mathrm{disc}}:\mathcal M_h\to(\mathbb Z/360\mathbb Z)^{m_\Theta}
```

is only angular sampling.

The swirl operator is:

```math
S_\Theta(x)=
\exp\!\left(
\sum_{a=1}^{m_\Theta}\theta_a(x)J_a(x)
\right),
```

where `J_a` are admissible Lie algebra generators. In octonionic regions, generators in `g_2` are natural because `G_2` preserves the octonionic product structure.

### 4.5 Omnigog seed operator

The seed is not metaphysical first cause. It is a structural prior:

```math
\mathcal U_{\mathrm{seed}}
\in
\{\mathcal U_{\mathrm{Hopf}},
\mathcal U_{\mathrm{Fano}},
\mathcal U_{\mathrm{Hyp}},
\mathcal U_{\mathbb O},
\mathcal U_{\mathrm{CY}}\}.
```

The reseeding operator:

```math
\mathcal G_{\mathrm{omni}}:(p,\mathfrak X)\mapsto p'
```

obeys a trust-region condition:

```math
\|p'-p\|\le\rho_{\mathrm{omni}}.
```

Its role is to reseed geometry after persistent singularity, projection violence, or chamber decoupling.

---

## 5. N-Ary Resonance Chambers

For a finite index set `A subset I`, `|A| >= 2`, define:

```math
\Lambda_A=(P_A,\mathscr F_A,\mathscr C_A,\mathcal H_A,W_A,\Theta_A).
```

Here:

- `P_A` is a finite interface: poset, hypergraph, or symmetric simplicial set;
- `F_A` is an interface sheaf obtained from participants by pullback / homotopy limit;
- `C_A` is a cosheaf of residual obstructions;
- `H_A` is a local Hilbert layer;
- `W_A` contains transport weights;
- `Theta_A` is the local orientation field.

Exact communication would be:

```math
s\in H^0(P_A,\mathscr F_A).
```

Thesis 2 works with approximate non-collapsing communication:

```math
0<\mathcal E_A(s_A^\ast)<\tau_A.
```

This preserves residual alterity.

---

## 6. Transition Operators Between Algebraic Strata

Let `C^(n)` and `C^(m)` be structure tensors for `A_n` and `A_m`. A transition:

```math
\tau_{n\to m}:\mathbb R^{D_n}\to\mathbb R^{D_m}
```

is admissible on an invariant subset `I_{n->m}` if:

```math
\Delta_{n\to m}(\tau)
=
\sup_{x,y\in\mathcal I_{n\to m}}
\frac{
\|\tau(\mu^{(n)}(x,y))-\mu^{(m)}(\tau x,\tau y)\|
}{
\|x\|\,\|y\|+\epsilon_0
}
\le
\varepsilon_{n\to m}.
```

The boundary operator across a stratum interface is:

```math
\mathfrak B_{\chi\to\chi'}(s)
=
\rho_{\chi'}(s)-\tau_{\chi\to\chi'}\rho_\chi(s).
```

`\mathfrak B=0` means structural compatibility. Nonzero `\mathfrak B` is transition tension.

---

## 7. Intrinsic Measures

### 7.1 Associator defect

```math
\operatorname{AssocDefect}(x,y,z)
=
\frac{\|(xy)z-x(yz)\|_\chi}
{\|x\|_\chi\|y\|_\chi\|z\|_\chi+\epsilon_0}.
```

In octonionic regions this is not necessarily an error. It may encode relational bracketing.

### 7.2 Zero-divisor potential

```math
\operatorname{ZDivPotential}(x,y)
=
\mathbf 1_{\|x\|,\|y\|>\delta_Z}
\exp\!\left(
-\frac{\|xy\|_\chi^2}{\sigma_Z^2}
\right).
```

For one element:

```math
\operatorname{ZDivScore}(x)
=
\exp\!\left(
-\frac{\sigma_{\min}(L_x)^2}{\sigma_Z^2}
\right),
\qquad
L_x(y)=xy.
```

### 7.3 Holonomy drift

```math
\operatorname{HolonomyDrift}_A
=
\sum_{\gamma\in\mathcal B_1(P_A)}
w_\gamma
\left\|
\log\operatorname{Hol}^{t+\Delta t}_\gamma(\nabla^{\mathcal H})
-
\log\operatorname{Hol}^{t}_\gamma(\nabla^{\mathcal H})
\right\|_F^2.
```

This measures semantic phase-memory drift.

### 7.4 Projection violence

For a projection `Pi_l` and approximate lift `Pi_l^dagger`:

```math
\begin{aligned}
\operatorname{ProjectionViolence}_{\Pi_\ell}(s)
=&\
\alpha_{\mathrm{rec}}\|s-\Pi_\ell^\dagger\Pi_\ell s\|^2\\
&+\alpha_{\mathrm{coh}}\|\delta^0s-\delta^0(\Pi_\ell^\dagger\Pi_\ell s)\|^2\\
&+\alpha_{\mathrm{curv}}\|K(s)-K(\Pi_\ell^\dagger\Pi_\ell s)\|^2\\
&+\alpha_{\mathrm{top}}\|b(\mathscr F_s)-b(\mathscr F_{\Pi_\ell^\dagger\Pi_\ell s})\|_1.
\end{aligned}
```

Over a projection family:

```math
\operatorname{ProjectionViolence}_{\Pi}(s)
=
\min_{\ell\in\mathcal L}
\operatorname{ProjectionViolence}_{\Pi_\ell}(s).
```

This is a proposed measure. It formalizes the claim that a good human projection should not destroy curvature, cohomology, or local-global harmonicity.

---

## 8. Dynamics and Coherence

The dynamic layer is not ontologically sequential. It is a solver approximation to simultaneous constraints.

### 8.1 Candidate action functional

```math
\begin{aligned}
\mathcal A[\mathfrak X]
=&
\int_{\mathcal M}
\Big[
\alpha_R R_g
+\alpha_F\|F_\nabla\|_g^2
+\alpha_\sigma\|d_\nabla\sigma\|_g^2\\
&+\alpha_\Psi\langle\Psi,\hat H\Psi\rangle
+\alpha_\Theta\|\nabla\Theta\|_g^2
+\alpha_A\operatorname{AssocDefect}^{(\chi)}\\
&+\alpha_Z\operatorname{ZDivPotential}^{(\chi)}
+\alpha_H\mathcal H_{\mathrm{hol}}
+\alpha_P\operatorname{ProjectionViolence}_{\Pi}
+\alpha_G\mathcal U_{\mathrm{seed}}
\Big]\,d\operatorname{Vol}_g\\
&+
\sum_{A\subset I}\beta_A\mathcal E_A.
\end{aligned}
```

### 8.2 Chamber energy

```math
\mathcal E_A(s_A)
=
\langle s_A,L_As_A\rangle
+\lambda_B\|\mathfrak B s_A\|^2
+\lambda_C\Xi_A(\mathscr C_A)
+\lambda_H\operatorname{HolonomyDrift}_A
+\lambda_P\operatorname{ProjectionViolence}_{\Pi}(s_A).
```

The sheaf Laplacian is:

```math
L_A=(\delta_A^0)^\ast W_A\delta_A^0.
```

If `ker L_A` is nontrivial, exact sections exist. If low but nonzero eigenmodes exist, the chamber supports approximate coherence.

### 8.3 Fixed point

```math
\Phi(\mathfrak X)
=
\operatorname{Retr}_{\mathfrak X}
\left(
-\eta\,\operatorname{grad}\mathcal A[\mathfrak X]
\right),
\qquad
\mathfrak X^\ast=\Phi(\mathfrak X^\ast).
```

Solution space modulo gauge:

```math
\mathcal S
=
\{\mathfrak X:
\delta\mathcal A[\mathfrak X]=0,\ 
\Phi(\mathfrak X)=\mathfrak X\}/\mathcal G.
```

Gauge quotienting prevents changes of parametrization, phase, or local basis from being mistaken for ontological change.

---

## 9. Candidate Evolution Equations

For solver dynamics:

```math
\partial_t g
=
-2\operatorname{Ric}(g)
+\lambda_F\mathcal T_F(F_\nabla)
+\lambda_\sigma\mathcal T_\sigma(\sigma)
-\nabla_g\mathcal U_{\mathrm{seed}}.
```

```math
\partial_t\nabla
=
D_\nabla^\ast F_\nabla
+\lambda_\sigma J_\sigma
+\lambda_\Theta J_\Theta.
```

```math
\partial_t\sigma
=
-L_{\mathscr F}\sigma
-\nabla_\sigma V_{\Lambda}
+\xi.
```

```math
i\hbar\,\partial_t\Psi
=
\hat H[g,\nabla,\Theta,\chi]\Psi
+\hat V_{\Lambda}\Psi.
```

```math
\partial_t\Theta
=
\omega_\Theta
+D_\Theta\Delta_g\Theta
-\nabla_\Theta U_\Theta.
```

These are not canonical equations from the literature. They are a synthesis inspired by geometric flows, Yang-Mills type flows, Hamiltonian evolution, Berry-Simon holonomy, and sheaf diffusion.

---

## 10. Phase Memory and Holonomy

Over a Hilbert bundle:

```math
\mathcal H\to\mathcal M,
```

define a connection:

```math
\nabla^{\mathcal H}.
```

For a closed path `gamma`:

```math
\operatorname{Hol}_\gamma(\nabla^{\mathcal H})
=
\mathcal P\exp\!\left(\int_\gamma A\right),
\qquad
A=i\langle\Psi,\nabla^{\mathcal H}\Psi\rangle.
```

Curvature:

```math
F_B=dA+A\wedge A.
```

Semantic interpretation:

```math
\boxed{
\text{two states with the same endpoint may differ by phase-memory history.}
}
```

This is the mathematically disciplined version of semantic memory as holonomy.

---

## 11. Singularity, Compression, and Renormalization

Define local singularity charge:

```math
\kappa_{\mathrm{sing}}(x)
=
\|Rm_g(x)\|
+\|F_\nabla(x)\|
+\Xi(x)
+\operatorname{ProjectionViolence}_{\Pi}(x).
```

If:

```math
\kappa_{\mathrm{sing}}(x)>\delta_{\mathrm{sing}},
```

activate surgery/compression:

```math
\mathfrak S_{x_0,\lambda}(\mathfrak X)
=
\mathcal R_\lambda
\left(
\mathfrak X\circ\beta_{x_0,\lambda}
\right),
\qquad
\beta_{x_0,\lambda}(x)=x_0+\lambda^{-1}x.
```

`\mathcal R_\lambda` coarse-grains degrees of freedom and reoptimizes the seed inside trust region `rho_omni`.

---

## 12. Communication and Stability Criteria

A resonance chamber communicates when:

```math
s_A^\ast=\arg\min_{s_A}\mathcal E_A(s_A)
```

and:

```math
0<\varepsilon_A:=\mathcal E_A(s_A^\ast)<\tau_A.
```

Additional constraints:

```math
R_A(s_A^\ast)>\eta_A,
\qquad
R_A(s)=\frac{\langle s,\mathcal K_A s\rangle}{\|s\|^2}.
```

```math
\operatorname{ProjectionViolence}_\Pi(s_A^\ast)<\nu_A.
```

```math
\operatorname{HolonomyDrift}_A<h_A.
```

```math
\left|\frac{d}{dt}H_A\right|<\gamma_A.
```

Remainder condition:

```math
r_A^-
\le
\operatorname{Remainder}_{\Pi}(s_A^\ast)
:=
\frac{\|s_A^\ast-\Pi^\dagger\Pi s_A^\ast\|}
{\|s_A^\ast\|+\epsilon_0}
\le
r_A^+.
```

The lower bound prevents collapse by perfect translation. The upper bound prevents illegibility.

---

## 13. Computational Recipe

1. Build a discretization `P` as a stratified finite poset, hypergraph, or simplicial set.
2. Attach a vector stalk/fiber `F_v ~= R^{r_v}` to each vertex/cell.
3. Attach interface fibers to hyperedges/chambers.
4. Encode restriction maps `rho_{e<-v}` and cosheaf extension maps for residues.
5. Assemble `delta^0` and the sheaf Laplacian:

```math
L=\delta^{0\ast}W\delta^0.
```

6. Add a Riemannian optimization layer for metric/geometric parameters.
7. Add symplectic/contact integration for Hamiltonian/dissipative dynamics.
8. Implement the local Hilbert bundle with small `q_n` and Krylov/Trotter updates.
9. Cache holonomies over a cycle basis.
10. Trigger singularity surgery when `kappa_sing` exceeds threshold.

---

## 14. Complexity Notes

| Subsystem | Dominant cost per iteration | Status |
|---|---:|---|
| Sheaf Laplacian assembly | `O(m r^2)` to `O(m r^3)` depending on dense maps | engineering estimate |
| Baseline neural sheaf diffusion layer | roughly `O(n c^2 + m c d^2)` | literature pattern |
| Cayley-Dickson multiplication | `O(D_n^2)` naive | engineering estimate |
| Zero-divisor score by dense SVD | `O(D_n^3)` | engineering estimate |
| Local Hilbert evolution | `O(k nnz(H))` with Krylov truncation | engineering estimate |
| Dense local curvature update | `O(N_p d_n^3)` by patch | engineering estimate |

Practical development should be incremental:

```math
\mathbb C
\longrightarrow
\mathbb H
\longrightarrow
\mathbb O
\longrightarrow
\mathbb S.
```

Do not start with sedenions.

---

## 15. Seed Geometry Comparison

| Seed | Natural invariant | Expressivity | Cost | Numerical risk | Best use |
|---|---|---:|---:|---:|---|
| Hopf | fibration, phase, principal connection | 3/5 | 2/5 | low | phase transport and memory |
| Fano | 7-point / 7-line incidence | 3/5 | 2/5 | low | light octonionic coupling |
| Hyperbolic | negative curvature, hierarchy | 4/5 | 3/5 | medium | hierarchical scaling and routing |
| Octonionic | nonassociativity, `G_2`, 3-form | 5/5 | 4/5 | medium-high | rich relational bracketing |
| Calabi-Yau | Kahler/Ricci-flat/moduli/mirror | 5/5 | 5/5 | high | law-space seed and topology transition |

These are design heuristics, not theorems.

---

## 16. Validation Program

| Experiment | Hypothesis | Baselines | Main metrics | Refutation condition |
|---|---|---|---|---|
| Stratified synthetic world | Thesis 2 recovers planted chambers better than binary graphs | GCN, Poincare, NSD | resonance F1, `epsilon_A`, `R_A` | fails to beat NSD/hyperbolic under equal budget |
| Zero-divisor channel | shadow couplings are visible only in higher algebra | no-sedenion models | ZDivPotential, HolonomyDrift, hidden event recall | sedenion layer adds no reproducible signal |
| Phase memory | holonomy separates same-endpoint/different-history loops | no Hilbert/Berry layer | trajectory classification, holonomy drift | no improvement over control |
| Surgery / renormalization | `S` avoids collapse and restores communication | no-surgery flow | time-to-collapse, fixed-point residual, recovery | surgery systematically worsens stability |
| Seed comparison | different seeds dominate different regimes | equal-compute seeds | cost, stability, noncollapse communication | one seed dominates all tasks always |

The validation plan must avoid equating parametric richness with evidence.

---

## 17. Risks and Mitigations

| Risk | Manifestation | Mitigation |
|---|---|---|
| Language bias | plausible text over latent coherence | multiple projections and ProjectionViolence penalty |
| Sequencing bias | solver order mistaken for ontology | report permutation sensitivity |
| Discretization bias | vertices/edges mistaken for reality | atlas/poset/hypergraph refinement tests |
| Conceptual inflation | more algebra gives more degrees of freedom, not truth | incremental algebraic scaling |
| Gauge redundancy | many parameters describe same object | explicit gauge fixing and quotient metrics |
| False resonance positives | thresholds capture noise | randomized controls and planted tasks |
| Pathological surgery | too much surgery destroys dynamics | surgery budget, trust region, entropy logs |

---

## 18. Roadmap

Assuming start in June 2026:

| Phase | Window | Deliverable |
|---|---|---|
| Formalization | Jun-Aug 2026 | axioms, notation, toy proofs, metrics `epsilon`, `R`, PV, HD |
| Minimal prototype | Aug-Nov 2026 | hyperbolic + sheaf + Riemannian solver, Euclidean/Poincare/NSD baselines |
| Algebraic lift | Nov 2026-Feb 2027 | quaternion/octonion layer, holonomy and phase memory |
| Singularity/reseed | Feb-May 2027 | surgery operator, Omnigog trust region, seed ablations |
| Higher strata | May-Jul 2027 | sedenion zero-divisor channels |
| Full validation | Jul-Oct 2027 | complete ablations, paper, formalization package |

The order is methodological, not ontological.

---

## 19. Priority Bibliography

### Sheaves and learning

- Grothendieck, **Sur quelques points d'algebre homologique** (1957).
- Curry, **Sheaves, Cosheaves and Applications** (2013).
- Ayzenberg, Gebhart, Magai, Solomadin, **Sheaf theory: from deep geometry to deep learning** (2025), arXiv:2502.15476.
- Bodnar et al., **Neural Sheaf Diffusion** (2022), arXiv:2202.04579.
- Di Nino, Barbarossa, Di Lorenzo, **Learning Sheaf Laplacian Optimizing Restriction Maps** (2025), arXiv:2501.19207.
- Choi, Kim, Oh, **Hypergraph Neural Sheaf Diffusion** (2025), arXiv:2505.05702.

### Hyperbolic and geometric learning

- Nickel and Kiela, **Poincare Embeddings for Learning Hierarchical Representations** (2017), arXiv:1705.08039.
- Bronstein et al., **Geometric Deep Learning** (2021).
- Miolane et al., **Geomstats** (2020).

### Hypercomplex algebra

- Baez, **The Octonions** (2001), arXiv:math/0105155.
- Elduque, **Composition algebras** (2018).
- Moreno, **The zero divisors of the Cayley-Dickson algebras over the real numbers** (1997).
- Reggiani, **The geometry of sedenion zero divisors** (2024), arXiv:2411.18881.
- Sangwine, **Octonion associators** (2015).
- Szabo, **An Introduction to Nonassociative Physics** (2019).

### Phase, geometry, and seed regimes

- Kato, **On the Adiabatic Theorem of Quantum Mechanics** (1950).
- Simon, **Holonomy, the Quantum Adiabatic Theorem, and Berry's Phase** (1983).
- Berry, **Quantal phase factors accompanying adiabatic changes** (1984).
- Perelman, **The entropy formula for the Ricci flow and its geometric applications** (2002).
- Aspinwall, Greene, Morrison, **The Physics of Calabi-Yau Moduli Space** (1993).
- Greene, **String Theory on Calabi-Yau Manifolds** (1997).
- Mosseri and Dandoloff, **Geometry of entangled states, Bloch spheres and Hopf fibrations** (2001).

---

## 20. Final Thesis 2 Scientific Statement

```math
\boxed{
\begin{gathered}
\text{Intelligibility is a stationary class of stratified algebraic-geometric regimes.}\\
\text{Communication is approximate global sectioning over n-ary resonance chambers.}\\
\text{Semantic memory is holonomy/phase.}\\
\text{Singularity is compression and law-renormalization, not merely failure.}
\end{gathered}
}
```

The operational test is:

```math
0<\varepsilon_A<\tau_A,
\qquad
r_A^-\le\operatorname{Remainder}_\Pi(s_A^\ast)\le r_A^+,
\qquad
\operatorname{ProjectionViolence}_\Pi(s_A^\ast)<\nu_A.
```

If those inequalities cannot be made true in controlled synthetic regimes, Thesis 2 fails as a computational research program.

