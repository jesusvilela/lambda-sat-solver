import { useState } from 'react'
import { useKV } from '@github/spark/hooks'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Toaster } from '@/components/ui/sonner'
import { Play, FastForward, ArrowCounterClockwise, Book, CheckCircle, XCircle, Info, Function } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { 
  createSolverPipeline, 
  DEFAULT_HEURISTICS, 
  DEFAULT_BUDGETS,
  type Heuristic,
  type Budget 
} from '@/lib/lambda-middleware'

// Example CNF formulas for learning
const examples = {
  simple_sat: {
    name: "Simple SAT (3 variables)",
    cnf: "p cnf 3 3\n1 2 0\n-1 3 0\n-2 -3 0",
    description: "A simple satisfiable formula with 3 variables and 3 clauses"
  },
  simple_unsat: {
    name: "Simple UNSAT",
    cnf: "p cnf 2 4\n1 0\n-1 0\n2 0\n-2 0",
    description: "Unsatisfiable formula where each variable must be both true and false"
  },
  pigeonhole: {
    name: "Pigeonhole Principle (3→2)",
    cnf: "p cnf 6 10\n1 2 0\n3 4 0\n5 6 0\n-1 -3 0\n-1 -5 0\n-3 -5 0\n-2 -4 0\n-2 -6 0\n-4 -6 0\n1 3 5 0",
    description: "Classical unsatisfiable problem: placing 3 pigeons in 2 holes"
  }
}

interface CNFFormula {
  variables: number
  clauses: number[][]
}

interface SolverState {
  assignments: Record<number, boolean>
  step: number
  satisfied: boolean[]
  conflicts: number[]
}

function parseCNF(text: string): CNFFormula | null {
  try {
    const lines = text.trim().split('\n').filter(line => line.trim() && !line.startsWith('c'))
    const headerLine = lines.find(line => line.startsWith('p cnf'))
    
    if (!headerLine) return null
    
    const [, , vars, clauseCount] = headerLine.split(' ')
    const variables = parseInt(vars)
    
    const clauses: number[][] = []
    for (const line of lines) {
      if (line.startsWith('p cnf') || line.startsWith('c')) continue
      const literals = line.trim().split(' ').map(n => parseInt(n)).filter(n => n !== 0)
      if (literals.length > 0) clauses.push(literals)
    }
    
    return { variables, clauses }
  } catch {
    return null
  }
}

function formatClause(clause: number[]): string {
  return clause.map(lit => lit > 0 ? `x${lit}` : `¬x${Math.abs(lit)}`).join(' ∨ ')
}

function evaluateClause(clause: number[], assignments: Record<number, boolean>): boolean | null {
  let satisfied = false
  let hasUnassigned = false
  
  for (const literal of clause) {
    const variable = Math.abs(literal)
    const value = assignments[variable]
    
    if (value === undefined) {
      hasUnassigned = true
      continue
    }
    
    const literalValue = literal > 0 ? value : !value
    if (literalValue) {
      satisfied = true
      break
    }
  }
  
  if (satisfied) return true
  if (hasUnassigned) return null
  return false
}

function solveDPLL(formula: CNFFormula): { satisfiable: boolean; model?: Record<number, boolean>; steps: SolverState[] } {
  const steps: SolverState[] = []
  const assignments: Record<number, boolean> = {}
  
  function backtrack(level: number): boolean {
    // Record current state
    const satisfied = formula.clauses.map(clause => evaluateClause(clause, assignments))
    const conflicts = formula.clauses.map((clause, idx) => satisfied[idx] === false ? idx : -1).filter(idx => idx !== -1)
    
    steps.push({
      assignments: { ...assignments },
      step: level,
      satisfied: satisfied.map(s => s === true),
      conflicts
    })
    
    // Check for conflicts
    if (conflicts.length > 0) return false
    
    // Check if all clauses are satisfied
    if (satisfied.every(s => s === true)) return true
    
    // Find unassigned variable
    let unassigned = -1
    for (let i = 1; i <= formula.variables; i++) {
      if (assignments[i] === undefined) {
        unassigned = i
        break
      }
    }
    
    if (unassigned === -1) return satisfied.every(s => s !== false)
    
    // Try assigning true
    assignments[unassigned] = true
    if (backtrack(level + 1)) return true
    
    // Try assigning false
    assignments[unassigned] = false
    if (backtrack(level + 1)) return true
    
    // Backtrack
    delete assignments[unassigned]
    return false
  }
  
  const satisfiable = backtrack(0)
  return {
    satisfiable,
    model: satisfiable ? { ...assignments } : undefined,
    steps
  }
}

function App() {
  const [cnfText, setCnfText] = useKV("cnf-input", examples.simple_sat.cnf)
  const [formula, setFormula] = useState<CNFFormula | null>(null)
  const [solverResult, setSolverResult] = useState<ReturnType<typeof solveDPLL> | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [isAutoSolving, setIsAutoSolving] = useState(false)
  const [selectedHeuristic, setSelectedHeuristic] = useKV("selected-heuristic", "conservative")
  const [selectedBudget, setSelectedBudget] = useKV("selected-budget", "standard")
  const [useLambdaMiddleware, setUseLambdaMiddleware] = useKV<boolean>("use-lambda-middleware", false)

  const handleParseCNF = () => {
    const parsed = parseCNF(cnfText || "")
    if (parsed) {
      setFormula(parsed)
      setSolverResult(null)
      setCurrentStep(0)
      toast.success("Formula parsed successfully!")
    } else {
      toast.error("Invalid CNF format. Please check your input.")
    }
  }

  const handleSolve = async () => {
    if (!formula) return
    
    setIsAutoSolving(true)
    
    try {
      if (useLambdaMiddleware) {
        // Use lambda middleware wrapper
        const heuristic = DEFAULT_HEURISTICS[selectedHeuristic as keyof typeof DEFAULT_HEURISTICS]
        const budget = DEFAULT_BUDGETS[selectedBudget as keyof typeof DEFAULT_BUDGETS]
        
        const pipeline = createSolverPipeline(heuristic, budget)
        const result = await pipeline.execute(formula)
        
        // Convert middleware result to UI format
        const uiResult = {
          satisfiable: result.status === 'SAT',
          model: result.status === 'SAT' ? result.model : undefined,
          steps: [{ 
            assignments: result.status === 'SAT' ? result.model || {} : {},
            step: 0,
            satisfied: formula.clauses.map(() => result.status === 'SAT'),
            conflicts: result.status === 'UNSAT' ? [0] : []
          }]
        }
        
        setSolverResult(uiResult)
        setCurrentStep(0)
        
        toast.success(`Lambda middleware: ${result.status}`, {
          description: result.status === 'ERROR' ? result.message : undefined
        })
      } else {
        // Use original DPLL solver
        const result = solveDPLL(formula)
        setSolverResult(result)
        setCurrentStep(result.steps.length - 1)
        
        toast.success(result.satisfiable ? "Formula is satisfiable!" : "Formula is unsatisfiable!")
      }
    } catch (error) {
      toast.error("Solver failed", {
        description: error instanceof Error ? error.message : "Unknown error"
      })
    } finally {
      setIsAutoSolving(false)
    }
  }

  const handleStepSolve = () => {
    if (!formula) return
    
    if (!solverResult) {
      const result = solveDPLL(formula)
      setSolverResult(result)
      setCurrentStep(0)
    } else if (currentStep < solverResult.steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleReset = () => {
    setSolverResult(null)
    setCurrentStep(0)
    toast.info("Solver reset")
  }

  const loadExample = (key: string) => {
    const example = examples[key as keyof typeof examples]
    setCnfText(example.cnf)
    setFormula(null)
    setSolverResult(null)
    setCurrentStep(0)
    toast.info(`Loaded: ${example.name}`)
  }

  const currentState = solverResult?.steps[currentStep]

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">SAT Solver Educational Interface</h1>
          <p className="text-muted-foreground">Learn Boolean satisfiability solving through interactive visualization</p>
        </header>

        <Tabs defaultValue="input" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="input">Input & Examples</TabsTrigger>
            <TabsTrigger value="lambda">Lambda Config</TabsTrigger>
            <TabsTrigger value="visualization">Visualization</TabsTrigger>
            <TabsTrigger value="solving">Solving</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
          </TabsList>

          <TabsContent value="input" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>CNF Formula Input</CardTitle>
                  <CardDescription>
                    Enter your Boolean formula in DIMACS CNF format
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    value={cnfText}
                    onChange={(e) => setCnfText(e.target.value)}
                    placeholder="p cnf 3 3&#10;1 2 0&#10;-1 3 0&#10;-2 -3 0"
                    className="font-mono text-sm min-h-32"
                  />
                  <Button onClick={handleParseCNF} className="w-full">
                    Parse Formula
                  </Button>
                  {formula && (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        Parsed: {formula.variables} variables, {formula.clauses.length} clauses
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Book className="h-5 w-5" />
                    Example Formulas
                  </CardTitle>
                  <CardDescription>
                    Load pre-made examples to explore SAT concepts
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries(examples).map(([key, example]) => (
                    <Card key={key} className="p-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium">{example.name}</h4>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => loadExample(key)}
                          >
                            Load
                          </Button>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {example.description}
                        </p>
                      </div>
                    </Card>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="lambda" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Function className="h-5 w-5" />
                    Lambda Middleware Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure the functional abstraction layer for SAT solver operations
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded">
                    <div>
                      <h4 className="font-medium">Use Lambda Middleware</h4>
                      <p className="text-sm text-muted-foreground">
                        Enable functional composition and effect management
                      </p>
                    </div>
                    <Button
                      variant={useLambdaMiddleware ? "default" : "outline"}
                      onClick={() => setUseLambdaMiddleware(!useLambdaMiddleware)}
                    >
                      {useLambdaMiddleware ? "Enabled" : "Disabled"}
                    </Button>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Heuristic Strategy</label>
                    <Select value={selectedHeuristic} onValueChange={setSelectedHeuristic}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="conservative">Conservative (VSIDS, Geometric restarts)</SelectItem>
                        <SelectItem value="aggressive">Aggressive (LRB, Luby restarts, Vivify)</SelectItem>
                        <SelectItem value="random">Random (Random branching)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Resource Budget</label>
                    <Select value={selectedBudget} onValueChange={setSelectedBudget}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="quick">Quick (1s, 64MB)</SelectItem>
                        <SelectItem value="standard">Standard (30s, 256MB)</SelectItem>
                        <SelectItem value="thorough">Thorough (300s, 1GB)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {useLambdaMiddleware && (
                    <Alert>
                      <Function className="h-4 w-4" />
                      <AlertDescription>
                        Lambda middleware will wrap solver operations in a functional abstraction with type checking and effect management.
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Pipeline Architecture</CardTitle>
                  <CardDescription>
                    Overview of the lambda function composition
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm font-mono">
                    <div className="p-3 bg-muted rounded">
                      <span className="text-muted-foreground">λ cnf.</span>
                      <span className="text-foreground">solve(cnf, heuristic, budget)</span>
                    </div>
                    <div className="text-center text-muted-foreground">↓</div>
                    <div className="p-3 bg-muted rounded">
                      <span className="text-muted-foreground">Type Check:</span>
                      <span className="text-foreground"> CNF → Result</span>
                    </div>
                    <div className="text-center text-muted-foreground">↓</div>
                    <div className="p-3 bg-muted rounded">
                      <span className="text-muted-foreground">Effects:</span>
                      <span className="text-foreground"> {useLambdaMiddleware ? 'ENABLED' : 'DISABLED'}</span>
                    </div>
                    <div className="text-center text-muted-foreground">↓</div>
                    <div className="p-3 bg-muted rounded">
                      <span className="text-muted-foreground">Result:</span>
                      <span className="text-foreground"> SAT | UNSAT | TIMEOUT</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Middleware Features</CardTitle>
                <CardDescription>Functional programming benefits for SAT solving</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="p-4 border rounded">
                    <h4 className="font-medium mb-2">Type Safety</h4>
                    <p className="text-sm text-muted-foreground">
                      Lambda expressions are type-checked before execution to prevent runtime errors
                    </p>
                  </div>
                  <div className="p-4 border rounded">
                    <h4 className="font-medium mb-2">Effect Management</h4>
                    <p className="text-sm text-muted-foreground">
                      Pure functional core with controlled side effects for solver operations
                    </p>
                  </div>
                  <div className="p-4 border rounded">
                    <h4 className="font-medium mb-2">Composability</h4>
                    <p className="text-sm text-muted-foreground">
                      Pipeline stages can be composed and reused across different solving strategies
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="visualization" className="space-y-6">
            {formula ? (
              <Card>
                <CardHeader>
                  <CardTitle>Formula Structure</CardTitle>
                  <CardDescription>
                    Visual representation of your CNF formula
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="text-sm">
                      <span className="font-medium">Variables:</span> {formula.variables} | 
                      <span className="font-medium ml-2">Clauses:</span> {formula.clauses.length}
                    </div>
                    <div className="space-y-2">
                      {formula.clauses.map((clause, idx) => (
                        <div 
                          key={idx} 
                          className={`p-3 rounded border ${
                            currentState?.satisfied[idx] 
                              ? 'bg-green-50 border-green-200' 
                              : currentState?.conflicts.includes(idx)
                              ? 'bg-red-50 border-red-200'
                              : 'bg-card border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-sm">
                              ({formatClause(clause)})
                            </span>
                            {currentState && (
                              <Badge variant={
                                currentState.satisfied[idx] ? 'default' : 
                                currentState.conflicts.includes(idx) ? 'destructive' : 'secondary'
                              }>
                                {currentState.satisfied[idx] ? 'SAT' : 
                                 currentState.conflicts.includes(idx) ? 'UNSAT' : 'UNKNOWN'}
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Please parse a CNF formula first to see the visualization.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="solving" className="space-y-6">
            {formula ? (
              <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Solver Controls</CardTitle>
                    <CardDescription>
                      Run the SAT solver step-by-step or automatically
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex gap-2">
                      <Button 
                        onClick={handleSolve} 
                        disabled={isAutoSolving}
                        className="flex-1"
                      >
                        <Play className="h-4 w-4 mr-2" />
                        {useLambdaMiddleware ? 'Solve (λ)' : 'Solve'}
                      </Button>
                      <Button 
                        onClick={handleStepSolve} 
                        variant="outline"
                        disabled={currentStep >= (solverResult?.steps.length || 0) - 1 || useLambdaMiddleware}
                      >
                        <FastForward className="h-4 w-4 mr-2" />
                        Step
                      </Button>
                      <Button onClick={handleReset} variant="outline">
                        <ArrowCounterClockwise className="h-4 w-4" />
                      </Button>
                    </div>
                    {useLambdaMiddleware && (
                      <Alert>
                        <Function className="h-4 w-4" />
                        <AlertDescription>
                          Using lambda middleware with {selectedHeuristic} heuristic and {selectedBudget} budget.
                        </AlertDescription>
                      </Alert>
                    )}
                    {solverResult && (
                      <div className="text-sm space-y-2">
                        <div>Step: {currentStep + 1} / {solverResult.steps.length}</div>
                        <div className="flex items-center gap-2">
                          Status: 
                          {currentStep === solverResult.steps.length - 1 ? (
                            <Badge variant={solverResult.satisfiable ? 'default' : 'destructive'}>
                              {solverResult.satisfiable ? 'SATISFIABLE' : 'UNSATISFIABLE'}
                            </Badge>
                          ) : (
                            <Badge variant="secondary">SOLVING...</Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Current Assignments</CardTitle>
                    <CardDescription>
                      Variable assignments at current step
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {currentState ? (
                      <div className="grid grid-cols-3 gap-2">
                        {Array.from({ length: formula.variables }, (_, i) => i + 1).map(variable => {
                          const value = currentState.assignments[variable]
                          return (
                            <div key={variable} className="flex items-center justify-between p-2 rounded border">
                              <span className="text-sm font-mono">x{variable}</span>
                              <Badge variant={
                                value === true ? 'default' : 
                                value === false ? 'secondary' : 'outline'
                              }>
                                {value === true ? 'T' : value === false ? 'F' : '?'}
                              </Badge>
                            </div>
                          )
                        })}
                      </div>
                    ) : (
                      <div className="text-muted-foreground text-sm">
                        Start solving to see variable assignments
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Please parse a CNF formula first to start solving.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="results" className="space-y-6">
            {solverResult ? (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {solverResult.satisfiable ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                      Solution Result
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <Alert className={solverResult.satisfiable ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
                        <AlertDescription>
                          <strong>Result:</strong> The formula is {solverResult.satisfiable ? 'SATISFIABLE' : 'UNSATISFIABLE'}
                          {solverResult.satisfiable && ' - a valid assignment exists that makes all clauses true.'}
                          {!solverResult.satisfiable && ' - no assignment can satisfy all clauses simultaneously.'}
                        </AlertDescription>
                      </Alert>
                      
                      {solverResult.satisfiable && solverResult.model && (
                        <div>
                          <h4 className="font-medium mb-2">Satisfying Assignment:</h4>
                          <div className="grid grid-cols-4 gap-2">
                            {Object.entries(solverResult.model).map(([variable, value]) => (
                              <div key={variable} className="flex items-center justify-between p-2 rounded border bg-green-50">
                                <span className="text-sm font-mono">x{variable}</span>
                                <Badge variant="default">{value ? 'TRUE' : 'FALSE'}</Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div>
                        <h4 className="font-medium mb-2">Solving Statistics:</h4>
                        <div className="text-sm space-y-1">
                          <div>Total steps: {solverResult.steps.length}</div>
                          <div>Variables: {formula?.variables}</div>
                          <div>Clauses: {formula?.clauses.length}</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Solve a formula to see detailed results and analysis.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>
        </Tabs>
      </div>
      <Toaster />
    </div>
  )
}

export default App