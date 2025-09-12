# SAT Solver Educational Interface

An interactive web application that teaches Boolean satisfiability (SAT) solving concepts through visualization and hands-on experimentation.

**Experience Qualities**:
1. **Educational** - Clear explanations and visual feedback help users understand complex SAT concepts
2. **Interactive** - Real-time formula input and solving with immediate visual results
3. **Professional** - Clean, academic interface that feels trustworthy for learning computer science concepts

**Complexity Level**: Light Application (multiple features with basic state)
- Combines formula input, visualization, and educational content with persistent user preferences

## Essential Features

### CNF Formula Input
- **Functionality**: Text editor for DIMACS CNF format input with syntax highlighting
- **Purpose**: Allow users to input and edit Boolean formulas in standard format
- **Trigger**: User clicks "New Formula" or loads example
- **Progression**: Formula editor opens → User types/pastes CNF → Real-time syntax validation → Formula parsed and ready
- **Success criteria**: Valid CNF formulas are parsed correctly, invalid syntax shows helpful error messages

### Visual Formula Representation
- **Functionality**: Convert CNF formulas into human-readable logical expressions and visual graphs
- **Purpose**: Help users understand the structure of their Boolean formulas
- **Trigger**: Valid formula is entered or example is loaded
- **Progression**: CNF parsed → Clauses extracted → Visual tree/graph generated → Display with highlighting
- **Success criteria**: Users can see their formula as both symbolic logic and visual representation

### Interactive SAT Solving Simulation
- **Functionality**: Step-through visualization of DPLL/CDCL algorithm concepts
- **Purpose**: Teach how SAT solvers work internally through visual simulation
- **Trigger**: User clicks "Solve" or "Step Through"
- **Progression**: Algorithm starts → Variable assignments shown → Clause satisfaction tracked → Conflicts visualized → Final result displayed
- **Success criteria**: Users understand solver decision-making process through visual feedback

### Example Formula Library
- **Functionality**: Curated collection of interesting SAT/UNSAT examples with explanations
- **Purpose**: Provide learning materials and quick experimentation starting points
- **Trigger**: User browses example gallery or clicks category
- **Progression**: Category selected → Examples listed with descriptions → Example chosen → Formula loaded into editor
- **Success criteria**: Examples load correctly and include educational context

### Result Analysis Dashboard
- **Functionality**: Display solving results with model verification and performance metrics
- **Purpose**: Show solution validity and help users understand solver behavior
- **Trigger**: Solving process completes
- **Progression**: Solution found → Model displayed → Verification shown → Statistics presented → Export options available
- **Success criteria**: Clear presentation of satisfying assignments or unsatisfiability proof

## Edge Case Handling

- **Invalid CNF Syntax**: Real-time validation with specific error highlighting and correction suggestions
- **Large Formulas**: Performance warnings and simplified visualization modes for complex inputs
- **Browser Compatibility**: Graceful degradation of visual features on older browsers
- **Memory Constraints**: Limit formula size and provide clear feedback about computational limits

## Design Direction

The interface should feel academic and professional, like a computer science research tool - clean, precise, and focused on clarity over decoration. Minimal visual noise with emphasis on the logical structure and educational content.

## Color Selection

Triadic color scheme emphasizing logic and computation with academic professionalism.

- **Primary Color**: Deep Blue (#1e40af) - Communicates trust, logic, and academic rigor
- **Secondary Colors**: Warm Orange (#ea580c) for highlights and Sage Green (#16a34a) for success states
- **Accent Color**: Bright Orange (#f97316) for call-to-action elements and important interactive features
- **Foreground/Background Pairings**:
  - Background (White #ffffff): Dark Gray text (#1f2937) - Ratio 12.6:1 ✓
  - Card (Light Gray #f9fafb): Dark Gray text (#1f2937) - Ratio 11.9:1 ✓
  - Primary (Deep Blue #1e40af): White text (#ffffff) - Ratio 8.6:1 ✓
  - Secondary (Warm Orange #ea580c): White text (#ffffff) - Ratio 5.1:1 ✓
  - Accent (Bright Orange #f97316): White text (#ffffff) - Ratio 4.7:1 ✓
  - Muted (Cool Gray #f3f4f6): Dark Gray text (#374151) - Ratio 9.2:1 ✓

## Font Selection

Typography should convey precision and readability appropriate for technical content, using a clean monospace font for code and a professional sans-serif for interface text.

- **Typographic Hierarchy**:
  - H1 (App Title): Inter Bold/32px/tight letter spacing
  - H2 (Section Headers): Inter Semibold/24px/normal spacing
  - H3 (Subsections): Inter Medium/20px/normal spacing
  - Body Text: Inter Regular/16px/relaxed line height
  - Code/Formula: JetBrains Mono Regular/14px/monospace for CNF formulas
  - Labels: Inter Medium/14px/uppercase tracking for form labels

## Animations

Subtle, purposeful animations that enhance understanding of logical flow and solver progression - focused on educational value rather than decoration.

- **Purposeful Meaning**: Animations should visualize logical concepts like variable propagation, clause satisfaction, and conflict analysis
- **Hierarchy of Movement**: Formula parsing gets subtle feedback, solver steps get prominent visualization, results get satisfying confirmation animations

## Component Selection

- **Components**: 
  - Textarea for CNF input with syntax highlighting
  - Card components for formula visualization and results
  - Tabs for switching between input/visualization/results views
  - Button variants for different solver actions (step/run/reset)
  - Badge components for variable assignments and clause states
  - Alert components for errors and educational tips

- **Customizations**: 
  - Custom syntax-highlighted code editor using textarea with overlay highlighting
  - Interactive formula visualization using SVG or Canvas within card layouts
  - Custom stepper component for algorithm visualization

- **States**: 
  - Input fields show validation states (valid/invalid/parsing)
  - Solver buttons reflect current state (ready/running/complete)
  - Formula elements highlight during solving steps

- **Icon Selection**: 
  - Play icon for solving, Step-forward for step-by-step, Check for validation
  - Warning triangle for errors, Info circle for educational tips
  - Download for exporting results, Book for example library

- **Spacing**: Consistent 4-unit (16px) spacing between major sections, 2-unit (8px) for related elements, 6-unit (24px) for section separation

- **Mobile**: 
  - Single-column layout with collapsible sections
  - Touch-friendly button sizing (44px minimum)
  - Simplified visualization optimized for smaller screens
  - Progressive disclosure of advanced features