# SKILL: Spec-Driven Agentic Engineering (SDAE)
## Grounded in Unix Design Principles for Multi-Agent Software Development

### Description
This skill governs software design, architectural specification, task decomposition, wave scheduling, and dual-gate quality enforcement for autonomous multi-agent software engineering systems. It transforms raw natural-language requirements (PRDs) into deterministic, machine-readable specifications (Semantic Software Architecture Trees and Task DAGs) before executing code generation across specialized agent swarms.

---

## 1. Foundational Unix Principles Mapping

| Unix Design Principle | Agentic Engineering Architecture | Operational Mechanism |
| :--- | :--- | :--- |
| **Rule of Representation** | Design Specs as Structured Data | Express repository architecture as JSON/YAML trees (**SSAT**) and task graphs (**DAGs**) to eliminate LLM ambiguity. |
| **Rule of Modularity** | Atomic Task Boundaries | Scope worker tasks strictly to **1–4 hours of bounded work** with explicit file modification boundaries (`files_to_touch`). |
| **Rule of Composition** | Wave-Based Topological Dispatch | Execute independent tasks in parallel waves connected via clean input/output interface contracts rather than dynamic agent chat. |
| **Rule of Separation** | Decouple Control from Generation | Maintain the orchestrator as a deterministic rule-based control spine; treat LLMs as specialized generation/review engines. |
| **Rule of Transparency & Repair** | Dual Validation Gates (95% Bar) | Fail early and noisily via Gate 1 (Planning) and Gate 2 (Code Execution); enforce concise remediation feedback (<= 20 lines). |
| **Rule of Economy** | Human-as-an-Agent (HaaA) | Elevate human developers to System Architects who audit specs, validate Gate 1 plans, and resolve edge-case consultations. |

---

## 2. Input Requirements

1. **Product Requirement Document (PRD)**: High-level prose requirements, user stories, and acceptance criteria.
2. **Repository Standards**: Tech stack rules, linter configs, directory boundaries, and coding conventions (e.g., `.cursorrules` or repository style guides).
3. **Environment Context**: Target language runtime, test runner commands, and static analysis toolchains.

---

## 3. Step-by-Step Workflow Instructions

### Phase 1: Architectural Modeling (SSAT Generation)
*Unix Rule of Representation: "Fold knowledge into data so program logic can be stupid and robust."*

1. **Invoke Architecture Agent (`ArchAgent`)** to convert the PRD into a JSON **Semantic Software Architecture Tree (SSAT)**.
2. The SSAT MUST contain 5 typed node categories defining every structural component of the target codebase:
   - `ModuleNode`: High-level logical sub-systems and namespaces.
   - `FileNode`: Exact physical file paths relative to repository root (`path`, `description`).
   - `GlobalCodeNode`: Module-level constants, global variables, and initializations.
   - `ClassNode`: Classes, inheritance hierarchies, and class-level fields.
   - `FunctionNode`: Function signatures, exact parameter names, type hints, default values, and docstrings.

#### SSAT JSON Standard Schema:
```json
{
  "title": "SemanticSoftwareArchitectureTree",
  "type": "object",
  "required": ["project_name", "root_modules"],
  "properties": {
    "project_name": { "type": "string" },
    "root_modules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "description", "files"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "files": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["name", "path", "description", "functions"],
              "properties": {
                "name": { "type": "string" },
                "path": { "type": "string" },
                "description": { "type": "string" },
                "global_code": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "name": { "type": "string" },
                      "description": { "type": "string" }
                    }
                  }
                },
                "classes": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "name": { "type": "string" },
                      "methods": { "type": "array" }
                    }
                  }
                },
                "functions": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": ["name", "description", "parameters", "return_type"],
                    "properties": {
                      "name": { "type": "string" },
                      "description": { "type": "string" },
                      "parameters": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "name": { "type": "string" },
                            "type": { "type": "string" },
                            "description": { "type": "string" }
                          }
                        }
                      },
                      "return_type": { "type": "string" }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

### Phase 2: Epic Decomposition & Task DAG Construction
*Unix Rules of Modularity & Composition: "Write simple parts connected by clean interfaces."*

1. **Decompose the SSAT into Atomic Task Specifications** stored in YAML format.
2. **Apply the SPOT Rule (Single Point of Truth)**: Every task spec must contain its complete execution context in one file.
3. **Enforce Task Constraints**:
   - Duration: Bounded strictly to **1–4 hours of effort**.
   - Isolation: Self-contained with zero required mid-execution communication with other agents.
   - Boundaries: Explicit `files_to_touch` array restricting edits exclusively to assigned paths.

#### Task Spec YAML Standard Schema:
```yaml
task_id: "TASK-0102"
epic_id: "EPIC-AUTH"
title: "Implement Authentication Handler"
time_estimate_pert:
  optimistic_hours: 1
  realistic_hours: 2
  pessimistic_hours: 4
execution_boundaries:
  files_to_touch:
    - "src/auth/auth_handler.py"
    - "tests/test_auth_handler.py"
dependencies:
  prerequisite_task_ids:
    - "TASK-0101" # Scaffolding & Base Models
interface_contracts:
  inputs:
    - "src/auth/models.py::UserSession"
  outputs:
    - "src/auth/auth_handler.py::verify_token"
    - "src/auth/auth_handler.py::generate_token"
acceptance_criteria:
  checklist:
    - "verify_token decodes valid auth strings and returns UserSession."
    - "verify_token raises SessionExpiredError when timestamp exceeds TTL."
  verification_commands:
    - "pytest tests/test_auth_handler.py --cov=src/auth/auth_handler"
```

4. **Construct Directed Acyclic Graph (DAG)**:
   - Extract prerequisite task relationships.
   - Run topological sorting to calculate execution **Waves ($W$)**:
     $$W(t_i) < W(t_j) \quad orall (t_i, t_j) \in 	ext{Dependencies}$$
   - **Wave 0**: Base models, scaffolding, environment scripts (zero dependencies).
   - **Wave $n$**: Dependent feature modules executed concurrently once Wave $n-1$ passes quality gates.

---

### Phase 3: Gate 1 Validation (Pre-Execution Epic & Plan Review)
*Unix Rule of Repair: "Fail noisily and as soon as possible."*

Before spawning worker agents or writing code, pass the SSAT and Task DAG to the Reviewer Agent (`ReviewerAgent`) for **Gate 1 Evaluation**.

#### Gate 1 Scoring Matrix (Target Score: >= 95/100)
Evaluate each metric from 0 to 10 points:

1. **Vision Clarity**: Are domain boundaries and requirements explicitly bounded?
2. **Architecture Quality**: Is the SSAT component tree complete without unstated modules?
3. **Task Decomposition**: Is every task scoped strictly within 1–4 hours?
4. **Dependency Graph**: Is the DAG free of circular dependencies ($G$ is strictly acyclic)?
5. **Coverage Completeness**: Are 100% of PRD requirements mapped to task deliverables?
6. **Phase Ordering**: Does wave partitioning maximize parallel execution without race conditions?
7. **Scope Coherence**: Do all sub-tasks directly contribute to the parent epic goal?
8. **Success Criteria Quality**: Are verification commands automated, deterministic, and runnable?
9. **Risk Identification**: Are external API rate limits, environment variables, and missing packages flagged?
10. **Integration Strategy**: Is the Git branch merge ordering explicitly defined?

#### Gate 1 Protocol:
- **If Score >= 95%**: Approve plan and proceed to Phase 4.
- **If Score < 95%**: **Fail noisily.** Trigger plan revision loop. Output specific failed metrics with action items. Do NOT proceed to code execution.

---

### Phase 4: Decoupled Multi-Stage Code Generation
*Unix Rule of Separation: "Separate policy from mechanism."*

Execute code generation using a **3-Tier Capability Hierarchy** connected via the **Model Context Protocol (MCP)**:

| Tier | Role | Assigned Duty |
| :--- | :--- | :--- |
| **Tier 1: Worker** | Heavy Generation | Writes code implementation, populates function bodies. |
| **Tier 2: Reviewer** | Quality Gate Scoring | Evaluates Gate 1 plans and Gate 2 pull requests. |
| **Tier 3: Investigator** | Triage & Diagnosis | Inspects stack traces and syntax logs during failure repair. |

#### Generation Execution Lifecycle:
1. **Skeleton Generation (`SkeletonAgent`)**:
   - For all files in the current Wave, generate valid source files containing imports, class declarations, and function signatures with `pass` placeholder bodies.
   - Verify syntax compilation of skeletons across the repository.
2. **Code Filling (`CodeAgent`)**:
   - Dispatch Tier 1 Worker Agents concurrently across the current Wave tasks.
   - Each worker populates implementation bodies within `files_to_touch` limits, following exact function signatures established in the SSAT.

---

### Phase 5: Gate 2 Validation & Noisy Repair
*Unix Rules of Transparency & Silence: "Design for visibility; when a program has nothing surprising to say, say nothing."*

When a Worker Agent completes a task, automatically isolate the changes in a sandbox environment and execute **Gate 2 Evaluation**.

#### Gate 2 Checklist (Pass Threshold: 100% on Hard Gates, >= 95% Overall):
- [ ] **Hard Gate 1: Syntax & Compilation**: 0 compilation or import errors.
- [ ] **Hard Gate 2: Sandbox Test Pass Rate**: 100% pass rate on specified `verification_commands`.
- [ ] **Hard Gate 3: File Modification Compliance**: Changes restricted 100% to `files_to_touch`.
- [ ] **Requirements Fidelity**: All YAML checklist items satisfied.
- [ ] **Security & Static Analysis**: Passes security scanning with 0 critical security flaws and clean linter output.

#### Remediation Protocol (Rule of Silence):
If Gate 2 fails:
1. Dispatch Tier 3 Investigator Agent to analyze the failure log.
2. Emit **Concise Remediation Feedback (<= 20 lines)** formatted as follows:
   ```text
   [GATE 2 FAILURE] Task: TASK-0102
   File: src/auth/auth_handler.py:42
   Error: SessionExpiredError not caught when timestamp exceeds threshold.
   Stack Trace Summary: auth.exceptions.SessionExpiredError at line 42 in verify_token.
   Action Items:
   1. Wrap decode logic with try-except block at src/auth/auth_handler.py:42.
   2. Raise custom SessionExpiredError exception defined in src/auth/models.py.
   3. Re-run: pytest tests/test_auth_handler.py
   ```
3. Pass feedback to Tier 1 Worker Agent for targeted repair (maximum 3 retry loops before escalation).

---

### Phase 6: Human-as-an-Agent (HaaA) Escalation Protocol
*Unix Rule of Economy: "Programmer time is expensive; conserve it in preference to machine time."*

1. **Human Director Role**: The human engineer reviews and signs off on Gate 1 SSAT plans and final Wave PR integrations.
2. **Consultation Request Trigger**:
   An agent MUST pause execution and issue a **Consultation Request** to the human architect if any of the following occur:
   - Unresolvable ambiguity in PRD business logic discovered during SSAT generation.
   - Missing external credentials, API keys, or third-party service dependencies.
   - Gate 2 repair fails 3 consecutive times on the same task spec.
3. **Consultation Format**:
   - State the exact blocking file and line/task ID.
   - Provide 2–3 concrete architectural options with pros/cons.
   - Await human decision before resuming execution.

---

## 4. Execution Flowchart

```
  ┌─────────────────────────────────────────────────────────┐
  │                      PROSE PRD                          │
  └────────────────────────────┬────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │       PHASE 1: SSAT Architectural Model (JSON)          │
  └────────────────────────────┬────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │       PHASE 2: Task Specs (YAML) & DAG Wave Graph       │
  └────────────────────────────┬────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │  PHASE 3: GATE 1 PLAN VALIDATION (Score >= 95% Required) │
  └──────────────┬───────────────────────────┬──────────────┘
                 │ (Pass)                    │ (Fail < 95%)
                 ▼                           ▼
  ┌─────────────────────────────┐  ┌────────────────────────┐
  │ PHASE 4: Skeleton & Code    │  │ Re-draft Spec & DAG    │
  │ Generation (Parallel Waves) │  └────────────────────────┘
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────┐
  │  PHASE 5: GATE 2 CODE VALIDATION (Tests & Static Check) │
  └──────────────┬───────────────────────────┬──────────────┘
                 │ (Pass)                    │ (Fail)
                 ▼                           ▼
  ┌─────────────────────────────┐  ┌────────────────────────┐
  │ Merge Wave PR & Advance     │  │ Rule of Silence Feedback│
  │ to Next Execution Wave      │  │ (<= 20 lines) -> Retry │
  └─────────────────────────────┘  └────────────────────────┘
```
