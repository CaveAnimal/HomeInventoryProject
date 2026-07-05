# Abstract Framework: GOAL → CONTEXT → DECISIONS → TODO

*META-DOCUMENT FOR SENIOR AI AGENTS*

This document teaches you how to establish the GOAL/CONTEXT/DECISIONS/TODO framework for ANY software project. Use this as a guide to create structure and discipline for complex work that will be executed by junior AI agents (or your future self).

---
## 🎯 WHY THIS FRAMEWORK WORKS

### The Problem It Solves

Software projects fail when:
- Goals are ambiguous → Agents add scope, invent features
- Context is incomplete → Agents make wrong assumptions
- Decisions are forgotten → Agents repeat failed approaches
- Plans are treated as infallible → Agents either freeze or silently improvise when reality contradicts the plan
- Tasks lack structure → Work is haphazard, incomplete, or duplicated
- Nothing is learned between phases → The same mistakes repeat

### The Solution
This framework provides:

- GOAL → Clear definition of what success looks like
- CONTEXT → Complete understanding of current state and constraints
- DECISIONS → Record of choices made, their rationale, AND whether they survived contact with reality
- TODO → Structured, verifiable task breakdown that is refined as learning occurs

### The Agile Spirit of This Framework
The plan is a hypothesis, not a contract. This framework is plan-driven but feedback-corrected:

- Decisions are validated against reality, and invalidated decisions are escalated, never silently worked around
- Risky assumptions are tested early with time-boxed spikes before work depends on them
- Retrospectives at check-ins and phase boundaries feed learnings back into the documents
- Plans are rolling-wave: near-term tasks are detailed, distant phases stay coarse until refined
- Check-ins demonstrate working output, not just status

### The Outcome
- ✅ Agents stay focused on actual objectives
- ✅ Work proceeds systematically, one task at a time
- ✅ Progress is trackable and verifiable
- ✅ Knowledge is preserved between sessions
- ✅ Hallucinations are minimized
- ✅ Quality is consistently high
- ✅ Bad decisions are caught and corrected early, not buried under workarounds
- ✅ Each phase is executed better than the last (continuous improvement)

---

## 📚 THE FOUR PILLARS (+ ONE BRIDGE DOCUMENT)

### 1. GOAL.md (or integrated in CONTEXT.md)

**Purpose:** Define WHAT we're building and WHY

**Must Answer:**
- What is the primary objective?
- What does success look like?
- What are we NOT doing (out of scope)?
- What are the critical success criteria?
- What constraints must we respect?

### 2. CONTEXT.md

**Purpose:** Define WHERE we are and WHAT we're working with

**Must Answer:**
- What is the current state of the system?
- What is the technology stack?
- What are the architectural patterns?
- What dependencies exist?
- What are the hard constraints (don't change X, must use Y)?
- What knowledge is required before starting?

### 3. DECISIONS.md

**Purpose:** Record WHY we made certain choices — and WHETHER they held up in practice

**Must Answer:**
- What choice was made?
- What was the context requiring a decision?
- Why this choice over alternatives?
- What assumptions does this decision rest on?
- What are the consequences?
- How do we rollback if needed?
- Has this decision been validated or invalidated by real-world execution?

### 4. TODO.md

**Purpose:** Define HOW the work will be executed

**Must Answer:**
- What is the sequence of tasks?
- What are the acceptance criteria for each task?
- What is the current status?
- What has been completed?
- What is blocked?

### 5. SPRINT_STORY_{folder_name}.md (The Jira Bridge)

**Purpose:** Translate the plan into Agile project-management artifacts

Created AFTER the four pillars are complete. {folder_name} is the name of the folder containing the G/C/D/T documents (e.g., docs in NSG-001/ → SPRINT_STORY_NSG-001.md).

**Must Answer:**
- What is the epic and what stories compose it?
- For each story: Jira-ready summary, description (user-story format), and acceptance criteria?
- What is the sizing (story points) for each story?
- What are the priorities, labels/components, and dependency links (blocks / blocked-by)?
- Which TODO tasks and DECISIONS each story traces back to?

**Key rule:** TODO.md remains the single source of truth for execution. SPRINT_STORY is the export format for sizing and populating Jira — regenerated/updated whenever TODO.md is re-planned.

---

## 🏗️ PART 1: FOR THE SENIOR AI AGENT (Setting Up the Framework)

### Your Role

You are the senior architect. Before any implementation work begins, you must thoroughly understand the project and create comprehensive documentation that will guide junior agents (or your future self) through execution.

### Your Mission

BEFORE writing a single line of implementation code:

1. Deeply understand the project through discovery
2. Document the goals with clarity
3. Map the current state comprehensively
4. Identify constraints explicitly
5. Break down the work systematically

---

## 📋 STEP 1: CREATE THE GOAL DOCUMENT

### Goal Discovery Process

#### A. Interview the User (Ask Questions)
Essential questions to ask:
- What is the primary objective of this project?
- What problem are we solving?
- What does success look like?
- How will we know when we're done?
- What should we explicitly NOT do?
- What are the non-negotiable constraints?
- What is the timeline/urgency?
- What is the risk tolerance?

#### B. Define Clear Boundaries

For each potential feature/change, classify as:

- ✅ IN SCOPE - Must be done to achieve the goal
- ⚠️ MAYBE - Could enhance but not essential
- ❌ OUT OF SCOPE - Explicitly not doing

#### C. Establish Success Criteria
Create measurable, verifiable criteria:
- Functional: "Feature X works as specified"
- Quality: "No regressions in existing functionality"
- Performance: "Response time < N seconds"
- Security: "No credentials in source code"
- Documentation: "Deployment guide exists"

### Goal Document Template

```markdown
# PROJECT GOAL

## Primary Objective
[One clear sentence describing what we're building/changing/fixing]

## Why This Matters (Business Value)
- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

## Success Criteria (Definition of Done)
- [ ] Criterion 1 (measurable)
- [ ] Criterion 2 (measurable)
- [ ] Criterion 3 (measurable)

## In Scope
- [Deliverable 1]
- [Deliverable 2]
- [Deliverable 3]

## Explicitly Out of Scope
- ❌ [Thing we're NOT doing]
- ❌ [Thing we're NOT changing]
- ❌ [Feature we're NOT adding]

## Non-Negotiable Constraints
- [Constraint 1: Why it exists]
- [Constraint 2: Why it exists]
- [Constraint 3: Why it exists]

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk 1] | High/Med/Low | [How we'll handle it] |
| [Risk 2] | High/Med/Low | [How we'll handle it] |

## Rollback Plan
If this project fails or causes critical issues:
- Step 1: [Immediate action]
- Step 2: [Restoration process]
- Step 3: [Verification]
- Time to rollback: [X minutes]
```

---

## 🗺️ STEP 2: CREATE THE CONTEXT DOCUMENT

### Context Discovery Process

#### A. Map the Current System
Investigation tasks:
1. Identify all relevant files (use file_search, grep_search, semantic_search)
2. Understand the architecture (read key files, trace relationships)
3. Document the technology stack (languages, frameworks, versions)
4. Map data flows (how data moves through the system)
5. Identify integration points (external systems, APIs, databases)
6. Document current behavior (what happens now?)

#### B. Identify Constraints and Dependencies

Constraint categories:
- Technical: Must use technology X, can't use Y
- Architectural: Must follow pattern X, can't change Y
- Infrastructure: Runs on platform X, deployed via Y
- Data: Schema can't change, migrations required for Z
- Security: Must encrypt X, audit Y, comply with Z
- Performance: Must handle X users, respond in Y ms
- Compatibility: Must work with X browser, Y device

#### C. Assess Required Knowledge

Knowledge inventory:
- Domain knowledge: What concepts/terminology are essential?
- Technical knowledge: What frameworks/patterns must be understood?
- Historical knowledge: What was tried before? What failed?
- Reference materials: Where can agents learn what they need?

### Context Document Template

```markdown
# PROJECT CONTEXT

> ⚠️ **AI AGENT INSTRUCTIONS**: This file defines the ONLY scope of work. 
> Do NOT deviate from this context. If a task is not explicitly mentioned here, 
> ASK before proceeding.

---

## Current System Overview

### Purpose

[What does the system currently do?]

### Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Language | [e.g., Java, Python] | [version] | [constraints] |
| Framework | [e.g., Spring, Django] | [version] | [constraints] |
| Server | [e.g., Tomcat, Liberty] | [version] | [constraints] |
| Database | [e.g., PostgreSQL] | [version] | [constraints] |
| Build Tool | [e.g., Maven, npm] | [version] | [constraints] |
| Deployment | [e.g., Docker, WAR] | [version] | [constraints] |

### Architecture Overview

[Diagram or description of current architecture]

Components:
- Component A: [Purpose]
- Component B: [Purpose]
- Component C: [Purpose]

Data flow: User → [Step 1] → [Step 2] → [Step 3] → Result

### Key Files and Their Roles

| File Path | Purpose | Change Expected? |
|-----------|---------|------------------|
| /path/to/file1.ext | [What it does] | Yes/No - [Why] |
| /path/to/file2.ext | [What it does] | Yes/No - [Why] |
| /path/to/file3.ext | [What it does] | Yes/No - [Why] |

### Current Behavior (Baseline)

Scenario 1: [User does X]
- Current behavior: [What happens]
- Files involved: [Which files]
- Expected after change: [What should happen]

Scenario 2: [System does Y]
- Current behavior: [What happens]
- Files involved: [Which files]
- Expected after change: [What should happen]

---

## Hard Constraints (DO NOT VIOLATE)

| Constraint | Rationale | Impact |
|------------|-----------|--------|
| [Must keep X] | [Why] | [What this means for implementation] |
| [Cannot change Y] | [Why] | [What this means for implementation] |
| [Must use Z] | [Why] | [What this means for implementation] |

---

## Required Knowledge

### Domain Concepts You Must Understand
| Concept | Description | Why It Matters | Where to Learn |
|---------|-------------|----------------|----------------|
| [Concept A] | [Definition] | [Impact on work] | [Reference] |
| [Concept B] | [Definition] | [Impact on work] | [Reference] |

### Technical Patterns in This Codebase
| Pattern | Where Used | How It Works | Why We Use It |
|---------|------------|--------------|---------------|
| [Pattern A] | [Files] | [Description] | [Rationale] |
| [Pattern B] | [Files] | [Description] | [Rationale] |

### Integration Points
| System/Service | Purpose | How We Interact | Constraints |
|----------------|---------|-----------------|-------------|
| [External API] | [What it does] | [REST/SOAP/etc] | [Limits/requirements] |
| [Database] | [What it stores] | [ORM/JDBC/etc] | [Schema constraints] |

---

## Target State (After Project Completion)

### What Will Change
- [Change 1: Specific description]
- [Change 2: Specific description]
- [Change 3: Specific description]

### What Will NOT Change
- [Unchanged 1: Why it stays the same]
- [Unchanged 2: Why it stays the same]
- [Unchanged 3: Why it stays the same]

### Migration Path
Current State → [Phase 1] → [Phase 2] → [Phase 3] → Target State
Phase 1: [What happens] Phase 2: [What happens] Phase 3: [What happens]

---

## Reference Materials

### Internal Documentation
- [File or location]: [What it contains]
- [File or location]: [What it contains]

### External Resources
- [Title/URL]: [Why it's relevant]
- [Title/URL]: [Why it's relevant]

### Key People/Contacts
- [Role]: [Name/contact] - [What they know]
- [Role]: [Name/contact] - [What they know]

---

## 📝 STEP 3: CREATE THE DECISIONS DOCUMENT

### Decision Documentation Process

#### A. When to Document a Decision

Document a decision when:
- ✅ Multiple approaches were possible
- ✅ The choice impacts architecture or design
- ✅ Future developers might question why
- ✅ The decision constrains future work
- ✅ It resolves a debate or trade-off
- ✅ It establishes a pattern to follow

Do NOT document:
- ❌ Obvious implementation details
- ❌ Bug fixes with no alternatives
- ❌ Trivial naming choices

#### B. How to Document Each Decision
Essential components:
1. Context: What situation required a decision?
2. Decision: What was chosen?
3. Rationale: WHY this over alternatives?
4. Consequences: What does this mean going forward?
5. Alternatives: What else was considered?
6. Rollback: How to undo if needed?
Decisions Document Template
# DECISIONS LOG

> ⚠️ **AI AGENT INSTRUCTIONS**: 
> - Before making ANY design decision, check if it's already recorded here
> - If you make a new decision, ADD IT HERE with full rationale
> - Do NOT contradict existing decisions without explicit user approval
> - If reality proves an ACCEPTED decision unworkable, mark it INVALIDATED with evidence and ESCALATE to the developer — do NOT build a workaround
> - Each decision gets a unique ID (DECISION-001, DECISION-002, etc.)

---

## How to Use This Document

### When to Add a Decision
- You chose approach A over approach B
- You established a pattern or convention
- You made a trade-off between competing concerns
- You set a constraint for future work

### When to Reference This Document
- Before starting a new task (check for related decisions)
- When unsure which approach to take (look for established patterns)
- When user questions a choice (explain the rationale)

### Decision Status Values
- **ACCEPTED**: Active decision that should be followed
- **VALIDATED**: Accepted AND proven to work in practice (spike completed or implemented successfully)
- **INVALIDATED**: Accepted in planning, but proven unworkable in practice (forbidden by policy, technically impossible, blocked by environment). ⚠️ MUST be escalated to the developer. Work that depends on it STOPS until a superseding decision is approved.
- **SUPERSEDED**: Replaced by a newer decision (reference the new one)
- **REJECTED**: Considered but NOT chosen
- **PROPOSED**: Under consideration, not yet implemented

---

## DECISION TEMPLATE (Copy This for New Decisions)

```markdown
## [DECISION-###] Short Descriptive Title

**Date:** YYYY-MM-DD
**Status:** ACCEPTED | SUPERSEDED | REJECTED | PROPOSED
**Decided by:** Human | AI (with approval) | Team
**Related Task:** [TODO task ID or phase]
**Supersedes:** [DECISION-XXX if applicable]
**Superseded by:** [DECISION-YYY if applicable]

### Context
[What situation required a decision? What problem were we trying to solve?]

### Decision
[What was decided? Be specific and concrete.]

### Rationale
[WHY was this chosen? What factors led to this decision?]
- Factor 1: [Explanation]
- Factor 2: [Explanation]
- Factor 3: [Explanation]

### Assumptions (Validate Early!)
[Every decision rests on assumptions. List them explicitly so they can be tested.]
| # | Assumption | Risk if Wrong | How to Validate | Status |
|---|------------|---------------|-----------------|--------|
| 1 | [e.g., "MCP servers are permitted in the corporate environment"] | High - entire approach fails | [e.g., Spike task 0.3 / ask IT] | ⬜ Untested / ✅ Confirmed / ❌ Disproven |
| 2 | [Assumption 2] | [Impact] | [Validation method] | ⬜ |

> 💡 **If any HIGH-risk assumption is untested, add a SPIKE task to TODO.md BEFORE any task that depends on this decision.**

### Consequences
[What are the implications of this decision?]
**Positive:**
- [Benefit 1]
- [Benefit 2]

**Negative:**
- [Trade-off 1]
- [Trade-off 2]

**Neutral:**
- [Impact 1]

### Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| [Option B] | [Benefits] | [Drawbacks] | [Reason] |
| [Option C] | [Benefits] | [Drawbacks] | [Reason] |

### Implementation Notes
[Specific guidance for implementing this decision]
- [Note 1]
- [Note 2]

### Verification
[How to verify this decision is being followed correctly]
- Check: [Verification step 1]
- Check: [Verification step 2]

### Validation in Practice (filled in during execution)
[The executing agent updates this when the decision meets reality]
- **Date tested:** [YYYY-MM-DD]
- **Outcome:** VALIDATED | INVALIDATED
- **Evidence:** [What actually happened — error messages, policy citation, test results]
- **If INVALIDATED:** [Escalated to developer on YYYY-MM-DD; dependent tasks marked ⛔; superseded by DECISION-XXX]

### Rollback
[How to undo this decision if it proves wrong]
1. [Rollback step 1]
2. [Rollback step 2]
3. [Verification step]
```

---

## Example Decisions (Common Patterns)

### Architectural Decisions

Examples:
- DECISION-001: Use microservices vs monolith
- DECISION-005: Use REST vs GraphQL for API
- DECISION-012: Database choice (PostgreSQL vs MongoDB)

### Technology Decisions

Examples:
- DECISION-003: Use React vs Vue for frontend
- DECISION-007: Use JWT vs session cookies for auth
- DECISION-015: Use Docker for deployment

### Pattern Decisions

Examples:
- DECISION-002: Use repository pattern for data access
- DECISION-009: Use event-driven vs request-response
- DECISION-018: Error handling strategy

### Process Decisions

Examples:
- DECISION-004: Secrets in environment variables
- DECISION-011: Git branching strategy
- DECISION-020: Deployment approach (blue-green vs rolling)

---

## 🔄 THE DECISION VALIDATION LOOP (Continuous Improvement)

> **Core Agile principle: the plan is a hypothesis. Execution is the experiment. Learnings flow back into the plan.**

Every decision made during planning is a *bet* based on the information available at the time. Some bets lose. The framework must detect losing bets quickly and correct course — NOT bury them under improvised workarounds.

### The Loop

```
PLAN: Senior AI makes DECISION-XXX (status: ACCEPTED)
  ↓
TEST: Junior AI executes first task depending on it (or runs a SPIKE)
  ↓
  ┌─────────────────────────────────────┐
  │ Does reality match the decision?    │
  └─────────────────────────────────────┘
  ↓               ↓
 YES              NO
  ↓               ↓
LEARN:          LEARN:
Mark VALIDATED   Mark INVALIDATED
Continue         Document evidence
              Mark dependent tasks ⛔
              ESCALATE to developer
              ↓
            ADAPT:
            Developer + Senior AI create
            superseding decision
            TODO.md is re-planned
            CONTEXT.md gains the new constraint
            Work resumes on solid ground
```

### Worked Example: The Invalidated Decision

**DECISION-007 (ACCEPTED):** "Use MCP servers for tool integration"
- Rationale: best technical fit, modern standard
- Assumption #1: MCP is permitted in the deployment environment (UNTESTED)

Junior AI builds the MCP integration. During deployment, corporate security policy blocks it: MCP is forbidden in this organization.

**❌ WRONG RESPONSE (what this framework forbids):** Junior AI quietly scrambles for a workaround — proxies, polling hacks, embedding credentials — burning hours on unapproved architecture the developer never sees until it breaks.

**✅ RIGHT RESPONSE (what this framework requires):**

1. STOP work on all tasks that depend on DECISION-007
2. Update DECISION-007 → Status: INVALIDATED. Evidence: "Corporate policy [name/ticket/error] forbids MCP. Discovered during task 3.2 on YYYY-MM-DD."
3. Mark dependent tasks ⛔ in TODO.md, citing DECISION-007
4. ESCALATE: report to the developer with (a) what was assumed, (b) what reality showed, (c) 1-3 candidate alternatives with trade-offs — as PROPOSED decisions, not implemented ones
5. WAIT for developer approval of a superseding decision
6. Senior AI (or developer) updates CONTEXT.md hard constraints ("MCP forbidden by corporate policy") so it is NEVER tried again
7. TODO.md is re-planned; work resumes

### Rules of the Loop
1. **An INVALIDATED decision is a project event, not a junior-AI problem to absorb.** Escalation is the success path, not an admission of failure.
2. **Workarounds require approval.** A workaround is a new architectural decision. New architectural decisions require developer sign-off. No exceptions.
3. **Invalidation evidence goes in DECISIONS.md, the new constraint goes in CONTEXT.md.** This is how the project gets smarter: the next planning pass cannot repeat the mistake because it is now a documented hard constraint.
4. **De-risk proactively with spikes.** When the senior AI records a decision with a HIGH-risk untested assumption, it must schedule a SPIKE task (see Step 4) before dependent implementation work. Cheap to test early; expensive to discover late.
5. **Validation is part of done.** A decision isn't truly proven until the first dependent task ships. Update its status to VALIDATED when it survives contact with reality.

---

## ✅ STEP 4: CREATE THE TODO DOCUMENT

### TODO Creation Process

#### A. Break Down the Work

Decomposition strategy:

1. Start with high-level phases
2. Break each phase into tasks
3. Break tasks into subtasks if needed
4. Ensure each task is:
   - Completable in one session
   - Independently verifiable
   - Has clear acceptance criteria
   - Depends on previous tasks (sequence matters)

#### A2. Plan in Rolling Waves (Agile: Backlog Refinement)

Do NOT fully detail the entire project up front:

- NEAR phases (current + next): full detail — acceptance criteria, files, verification steps
- DISTANT phases: coarse outline only — purpose and deliverable

At each phase boundary:

- Senior AI (or developer) refines the NEXT phase using everything learned so far (retro findings, validated/invalidated decisions, actual vs estimated effort)
- Refinement is reviewed with the user before execution begins

**Why:** detail written months ahead of execution is guesswork that hardens into false confidence. Refine late, with real knowledge.

#### A3. Add SPIKE Tasks for Risky Assumptions (Agile: Fail Fast)

A SPIKE is a small, time-boxed investigation task whose deliverable is KNOWLEDGE, not production code.

Create a spike when:

- A decision in DECISIONS.md has a HIGH-risk untested assumption
- An external dependency (API, policy, library, permission) is unverified
- Two approaches are viable and a cheap experiment would settle it

Spike rules:

- Sequence the spike BEFORE any implementation task that depends on the answer
- Time-box it (e.g., max 2 hours) — a spike that can't conclude in its time-box is itself a finding: escalate
- Acceptance criteria = a question answered, e.g.: "Confirmed whether MCP servers are permitted in the corporate environment; DECISION-007 assumption #1 marked ✅ or ❌; findings documented in DECISIONS.md"
- Spike output updates the decision's Assumptions table and, if an assumption is disproven, triggers the Decision Validation Loop

#### B. Define Clear Acceptance Criteria

Good acceptance criteria:

- ✅ "Code compiles without errors"
- ✅ "All unit tests pass"
- ✅ "Feature X works as specified"
- ✅ "Documentation updated with Y"
- ✅ "No performance regression (< N ms)"

Bad acceptance criteria:

- ❌ "Make it better"
- ❌ "Fix the bugs"
- ❌ "Improve performance"
- ❌ "Clean up the code"

#### C. Establish Dependencies

Task sequencing:

- Configuration before code changes
- Infrastructure before deployment
- Tests before marking complete
- Documentation concurrent with work

### TODO Document Template

```markdown
# TODO — [PROJECT NAME]

> ⚠️ **AI AGENT INSTRUCTIONS**: 
> This is the SINGLE SOURCE OF TRUTH for task progress. 
> 
> **BEFORE starting ANY work:**
> - Find the FIRST incomplete task (⬜)
> - Mark it IN-PROGRESS (🔄)
> - Complete ALL acceptance criteria
> - Mark it COMPLETED (✅)
> 
> **RULES:**
> - Do NOT skip tasks
> - Do NOT reorder tasks without approval
> - Do NOT add tasks without user approval
> - Do ONE task at a time
> - After completing each task, RE-READ TODO.md before starting the next task
> - After every 10 completed tasks, STOP and report progress to the user
> - If a task reveals that an ACCEPTED decision cannot work in practice,
>   STOP: mark the decision INVALIDATED in DECISIONS.md, mark dependent
>   tasks ⛔, and escalate — do NOT improvise a workaround before continuing

---

## Status Key

| Symbol | Meaning | When to Use |
|--------|---------|-------------|
| ⬜ | Not started | Task hasn't begun |
| 🔄 | In progress | Currently working (ONLY ONE at a time) |
| ✅ | Completed | All criteria met, verified |
| ⛔ | Blocked | Can't proceed (note blocker in task) |
| 🚫 | Cancelled | No longer needed (note reason) |
| ⏸️ | Paused | Started but waiting (note reason) |

---

## How to Use This Document

### For AI Agents Executing Work

**Before Each Session:**
1. Read CONTEXT.md to understand the system
2. Read this TODO to find current task
3. Read DECISIONS.md to understand past choices

**During Work:**
1. Mark current task 🔄 (in progress)
2. Work ONLY on that task
3. Check off acceptance criteria as completed
4. Verify ALL criteria before marking ✅

**After Completing Task:**
1. Mark task ✅ (completed)
2. Add entry to completion log (below)
3. Update DECISIONS.md if you made choices
4. RE-READ TODO.md to re-orient and prevent drift
5. If you have completed 10 tasks since last check-in, STOP and report progress to the user
6. Otherwise, proceed to the next task

**If Blocked:**
1. Mark task ⛔ (blocked)
2. Note the blocker in the task
3. Report to user for guidance

### Progress Tracking

**Current Progress:** 
- Phase X: [Y/Z] tasks complete
- Overall: [A/B] tasks complete ([C]%)

**Next Milestone:** [Description]

---

## TEMPLATE FOR EACH PHASE

### PHASE N: [PHASE NAME]
**Purpose:** [What this phase accomplishes]
**Dependencies:** [What must be done before this phase]
**Deliverable:** [What exists after this phase]

#### N.1 ⬜ Task Title (Short, Action-Oriented)
**Purpose:** [Why this task matters]

**Acceptance Criteria:**
- [ ] Specific, measurable criterion 1
- [ ] Specific, measurable criterion 2
- [ ] Specific, measurable criterion 3
- [ ] All changes compile/build successfully
- [ ] No regressions in existing functionality
- [ ] Documentation updated (if applicable)

**Files to Create:**
- `/path/to/new/file.ext` - [Purpose]

**Files to Modify:**
- `/path/to/existing/file.ext` - [What changes]

**Verification Steps:**
1. [How to verify criterion 1]
2. [How to verify criterion 2]
3. [How to verify criterion 3]

**Dependencies:**
- Requires: Task N-1.M to be complete
- Blocks: Task N+1.K cannot start until this is done

**Reference Materials:**
- [Document/URL]: [What it explains]
- [Document/URL]: [What it explains]

**Notes:**
- [Important consideration 1]
- [Important consideration 2]

**Blocker:** (if status is ⛔)
- [Description of what's blocking progress]
- [What's needed to unblock]

---

## TASK SEQUENCING EXAMPLE

### PHASE 0: Discovery & Documentation
**Purpose:** Understand current state, document goals

#### 0.1 ⬜ Analyze current system
- [ ] Map all relevant files
- [ ] Document current architecture
- [ ] Identify integration points
- [ ] Create baseline documentation

#### 0.2 ⬜ Define goals and constraints
- [ ] Document primary objective
- [ ] List success criteria
- [ ] Define scope boundaries
- [ ] Identify constraints

#### 0.3 ⬜ SPIKE: Validate high-risk assumptions (time-box: 2 hours)
- [ ] Each HIGH-risk assumption in DECISIONS.md tested or confirmed with the developer
- [ ] Assumption tables updated (✅ Confirmed / ❌ Disproven)
- [ ] Any disproven assumption escalated via the Decision Validation Loop
- [ ] Findings documented in DECISIONS.md

---

### PHASE 1: Foundation
**Purpose:** Set up prerequisites for main work

#### 1.1 ⬜ Configure environment
- [ ] Set up required dependencies
- [ ] Configure build tools
- [ ] Verify build succeeds

#### 1.2 ⬜ Create infrastructure
- [ ] Set up necessary infrastructure
- [ ] Configure deployment pipeline
- [ ] Verify deployment works

---

### PHASE 2: Core Implementation
**Purpose:** Implement main features

#### 2.1 ⬜ Implement feature A
- [ ] Create necessary files
- [ ] Implement logic
- [ ] Add tests
- [ ] Verify functionality

#### 2.2 ⬜ Implement feature B
- [ ] Create necessary files
- [ ] Implement logic
- [ ] Add tests
- [ ] Verify functionality

---

### PHASE 3: Integration
**Purpose:** Connect components together

#### 3.1 ⬜ Integrate feature A with system
- [ ] Hook up entry points
- [ ] Handle edge cases
- [ ] Verify integration

#### 3.2 ⬜ Integrate feature B with system
- [ ] Hook up entry points
- [ ] Handle edge cases
- [ ] Verify integration

---

### PHASE 4: Testing & Verification
**Purpose:** Ensure quality and correctness

#### 4.1 ⬜ Unit testing
- [ ] All unit tests pass
- [ ] Code coverage > X%
- [ ] No test failures

#### 4.2 ⬜ Integration testing
- [ ] End-to-end flows work
- [ ] Integrations verified
- [ ] No regressions

#### 4.3 ⬜ Performance testing
- [ ] Performance benchmarks met
- [ ] No performance regressions
- [ ] Resource usage acceptable

---

### PHASE 5: Documentation & Cleanup
**Purpose:** Finalize for production

#### 5.1 ⬜ Create user documentation
- [ ] User guide written
- [ ] API documentation complete
- [ ] Examples provided

#### 5.2 ⬜ Create deployment documentation
- [ ] Deployment guide written
- [ ] Configuration documented
- [ ] Troubleshooting guide created

#### 5.3 ⬜ Code cleanup
- [ ] Remove debug code
- [ ] Format code consistently
- [ ] Remove TODOs/FIXMEs

---

### PHASE 6: Deployment
**Purpose:** Release to production

#### 6.1 ⬜ Pre-deployment verification
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Rollback plan ready

#### 6.2 ⬜ Deploy to staging
- [ ] Deployed successfully
- [ ] Smoke tests pass
- [ ] Ready for production

#### 6.3 ⬜ Deploy to production
- [ ] Deployed successfully
- [ ] Monitoring in place
- [ ] Verified working

---

## COMPLETION LOG

### Instructions
When a task is marked ✅, add an entry below:

**Format:**
YYYY-MM-DD | Phase N.M | Task Title | Est: S/M/L | Actual: S/M/L | [Notes]

> 💡 **Why track Est vs Actual?** (Agile: velocity & estimation feedback)
> If actuals consistently exceed estimates, the senior AI recalibrates
> task sizing during the next rolling-wave refinement. Estimation is a
> skill the project improves at, not a one-time guess.

### Log Entries

[Task completion entries will be added here chronologically]

---

## RETROSPECTIVES (Agile: Inspect & Adapt)

### Instructions
Run a **mini-retro** at every 10-task check-in and a **full retro** at each phase boundary. Keep it short (3-6 bullets total). The point is action, not ceremony.

**Format:**

```
RETRO — [Check-in YYYY-MM-DD | Phase N complete]

What went well:
- [Keep doing this]

What went poorly / surprised us:
- [Friction, rework, wrong assumptions, unclear tasks]

What we change going forward (each item gets an owner + a home):
- [Action] → recorded in [CONTEXT.md | DECISIONS.md | TODO.md | this framework]
```

**Retro rules:**
1. Every "change going forward" item MUST land in a document — a retro
   finding that lives only in chat history is a finding lost
2. Recurring friction with the framework itself (templates too heavy,
   check-in cadence wrong, criteria style unclear) is valid retro
   output — propose framework changes to the developer
3. The senior AI reads all retro entries before refining the next phase

### Retro Entries

[Retro entries will be added here chronologically]

---

## BLOCKERS & ISSUES

### Active Blockers
[List any tasks that are blocked and why]

### Resolved Blockers
[Archive of blockers that were resolved]

---

## TASK ESTIMATION GUIDE

For planning purposes:
- Small task (S): < 1 hour, single file changes
- Medium task (M): 1-4 hours, multiple files, moderate complexity
- Large task (L): 4-8 hours, architectural changes, high complexity
- Extra Large (XL): > 8 hours, should be broken into smaller tasks

**Break down XL tasks into smaller tasks before starting.**

---

## 🏃 STEP 5: CREATE THE SPRINT STORY DOCUMENT (Jira Bridge)

**When:** ONLY after GOAL.md, CONTEXT.md, DECISIONS.md, and TODO.md are complete and approved.

**Who:** The Senior AI (same agent that created the four pillars).

**Filename:** SPRINT_STORY_{folder_name}.md where {folder_name} is the folder containing the four pillar documents. Example: documents live in .../NSG-001/ → create SPRINT_STORY_NSG-001.md in the same folder.

### Purpose

The four pillars are written for AI agents executing work. SPRINT_STORY translates the same plan into the language of Agile project management, so the developer can size the work and populate Jira (or any tracker) by copy-paste: epics, stories, descriptions, acceptance criteria, story points, priorities, and dependency links.

### Derivation Rules (Nothing Is Invented Here)

| Source | Target |
|--------|--------|
| GOAL.md | Epic summary + epic description + business value |
| TODO.md Phase | Epic or story grouping (one epic per project, or one epic per phase for large projects) |
| TODO.md Task | One Story (or Task/Spike issue type) |
| Task acceptance criteria | Story acceptance criteria (rewritten in Given/When/Then where it adds clarity) |
| Task size (S/M/L/XL) | Story points (see sizing map below) |
| Task dependencies | Jira links (blocks / is blocked by) |
| SPIKE tasks | Jira Spike issue type, time-boxed |
| DECISIONS.md IDs | Referenced in story descriptions for traceability |
| Hard constraints (CONTEXT) | Noted in affected story descriptions |

⚠️ SPRINT_STORY must NOT introduce scope that isn't in TODO.md. If writing a story reveals a missing task, fix TODO.md first (with approval), then regenerate the story.

### Sizing Map (S/M/L → Story Points)

| TODO Size | Effort | Story Points (Fibonacci) |
|-----------|--------|--------------------------|
| S | < 1 hour, single file | 1–2 |
| M | 1–4 hours, multiple files | 3–5 |
| L | 4–8 hours, architectural | 8 |
| XL | > 8 hours | 13 → ⚠️ split before it enters a sprint |

Recalibrate this map using the Est vs Actual data in the TODO completion log. If "M" tasks routinely behave like "L", say so in the next retro and adjust.

### Sprint Story Document Template

```markdown
# SPRINT STORIES — {folder_name}

> Generated from: GOAL.md, CONTEXT.md, DECISIONS.md, TODO.md (in this folder)
> Generated on: YYYY-MM-DD | Last synced with TODO.md: YYYY-MM-DD
> ⚠️ TODO.md is the source of truth for execution. This document is the
> Jira-ready export. Re-sync it whenever TODO.md is re-planned.

---

## EPIC

**Epic Summary:** [One line, from GOAL.md primary objective]
**Epic Description:**
[2-4 sentences: what we're building and the business value, from GOAL.md]

**Business Value:** [From GOAL.md "Why This Matters"]
**Definition of Done (Epic level):** [GOAL.md success criteria]
**Out of Scope:** [From GOAL.md — paste into the epic so Jira readers see boundaries]

---

## STORY TEMPLATE (one per TODO task)

### STORY-{N}: [Short, action-oriented title]

| Field | Value |
|-------|-------|
| **Issue Type** | Story / Task / Spike / Bug |
| **Summary** | [Jira summary line, ≤ 100 chars] |
| **Epic Link** | [Epic name above] |
| **Story Points** | [From sizing map] |
| **Priority** | Highest / High / Medium / Low |
| **Labels / Components** | [e.g., backend, auth, infra] |
| **Sprint (suggested)** | [Sprint 1 / 2 / Backlog] |
| **Source** | TODO task [N.M]; DECISION-[XXX] |
| **Links** | Blocks: STORY-{X} · Blocked by: STORY-{Y} |

**Description:**
As a [user/role], I want [capability] so that [benefit].

[Context paragraph: what exists today, what changes, relevant constraints
from CONTEXT.md, relevant decisions by ID from DECISIONS.md]

**Acceptance Criteria:**
- [ ] Given [precondition], when [action], then [observable result]
- [ ] Given [precondition], when [action], then [observable result]
- [ ] [Plain checklist items are fine where Given/When/Then is forced]

**Definition of Done:**
- [ ] All acceptance criteria verified
- [ ] Code compiles/builds; tests pass; no regressions
- [ ] Documentation updated
- [ ] TODO.md task [N.M] marked ✅

**Notes for Sizing Discussion:**
- [Risks, unknowns, untested assumptions that may inflate the estimate]

---

## SPIKE STORIES (time-boxed investigations)

### SPIKE-{N}: [Question to answer]
| Field | Value |
|-------|-------|
| **Issue Type** | Spike |
| **Time-box** | [e.g., 2 hours] |
| **Story Points** | 1–2 |
| **Source** | TODO task [0.X]; validates DECISION-[XXX] assumption #[N] |

**Description:** [What must be confirmed/disproven, and why it's risky]
**Acceptance Criteria:**
- [ ] Question answered with documented evidence
- [ ] DECISION-[XXX] assumptions table updated (✅/❌)
- [ ] If disproven → Decision Validation Loop triggered

---

## STORY MAP / SPRINT PLAN (suggested)

| Sprint | Stories | Total Points | Theme |
|--------|---------|--------------|-------|
| Sprint 1 | SPIKE-1, STORY-1, STORY-2 | [N] | [Foundation + de-risking] |
| Sprint 2 | STORY-3, STORY-4 | [N] | [Core implementation] |
| Backlog | STORY-5+ | — | [Refine at rolling-wave boundary] |

---

## SYNC LOG

| Date | Reason | Stories Affected |
|------|--------|------------------|
| YYYY-MM-DD | Initial generation | All |
| YYYY-MM-DD | DECISION-007 INVALIDATED; TODO re-planned | STORY-6..9 rewritten |
```

### Keeping SPRINT_STORY in Sync (Continuous Improvement)

Re-sync SPRINT_STORY whenever:

- TODO.md is re-planned (rolling-wave refinement at a phase boundary)
- A decision is INVALIDATED and superseded (dependent stories change)
- Scope changes are approved (stories added/removed)
- Retro findings change task sizing (story points updated)

Record every re-sync in the SYNC LOG with the reason. Distant-phase tasks that are still coarse (rolling wave) appear as coarse Backlog stories — they get full descriptions and points only when their phase is refined. Do not fake precision.

---

## 🚫 ANTI-HALLUCINATION RULES (Universal)

### Rule 1: Read Before Acting
ALWAYS read in this order before ANY task:
1. GOAL document ← Know what we're trying to achieve
2. TODO document ← Know what specific task you're doing
3. CONTEXT document ← Know the constraints and current state
4. DECISIONS document ← Know what choices were already made

### Rule 2: One Task at a Time

- Find the FIRST ⬜ (not started) task
- Mark it 🔄 (in progress)
- Complete it FULLY (all acceptance criteria)
- Mark it ✅ (completed)
- RE-READ TODO.md to re-orient before starting the next task
- After every 10 completed tasks, STOP and report progress to the user

**Why:** Prevents incomplete work, ensures verification happens, and re-reading the TODO after each task prevents drift

### Rule 3: No Improvisation

- If something isn't specified → ASK
- If you're unsure → ASK
- If you want to add a feature → ASK
- If you want to refactor → ASK
- If you're guessing → STOP and ASK

**Why:** Scope creep is the enemy of project success

### Rule 4: No Hallucination

Do NOT Invent:

- ❌ Technologies that aren't in the stack
- ❌ APIs that don't exist
- ❌ Patterns not established in codebase
- ❌ Requirements not in GOAL
- ❌ Constraints not in CONTEXT
- ❌ Features not in TODO

Instead:

- ✅ Use exactly what's documented
- ✅ Follow established patterns
- ✅ Stay within known constraints
- ✅ Ask to clarify unknowns
- ✅ Verify assumptions

**Why:** Hallucinated code doesn't work and wastes time

### Rule 5: Update Tracking

After completing ANY work:

- Update TODO.md (mark complete, add to log)
- Update DECISIONS.md (if you made a choice)
- Note blockers or discoveries
- Document deviations from the plan
- If TODO.md tasks were added, removed, or resized → flag that SPRINT_STORY_{folder_name}.md needs re-syncing (the senior AI or developer performs the sync and logs it)

**Why:** Knowledge must be preserved between sessions

### Rule 6: Verify Before Claiming Completion

Before marking a task ✅:

- [ ] Code compiles/builds
- [ ] ALL acceptance criteria checked
- [ ] No regressions introduced
- [ ] Changes follow established patterns
- [ ] Documentation updated

**Why:** "Done" means actually done, not almost done

### Rule 7: Preserve Context for Future Sessions

- Comment your code explaining WHY not WHAT
- Document decisions that aren't obvious
- Leave breadcrumbs for future developers
- Think: "Will I understand this in 6 months?"

**Why:** Future you is essentially a different person

### Rule 8: Fail Gracefully

If you get stuck:

1. Document what you tried
2. Explain why it didn't work
3. Ask for guidance
4. Mark task ⛔ with blocker description

DO NOT:

- Keep trying random things
- Hallucinate solutions
- Make major changes hoping they work
- Hide the problem and move on

**Why:** Getting unstuck is faster with help

### Rule 9: Escalate, Don't Work Around

If reality contradicts an ACCEPTED decision (technology forbidden by policy, API doesn't behave as documented, approach technically impossible in this environment):

1. STOP all tasks that depend on that decision
2. Update the decision's status to INVALIDATED in DECISIONS.md with concrete evidence
3. Mark dependent tasks ⛔, citing the decision ID
4. Report to the developer: what was assumed, what reality showed, and 1-3 alternatives as PROPOSED decisions with trade-offs
5. WAIT for an approved superseding decision before resuming
6. Ensure the discovered constraint is added to CONTEXT.md so it is never violated again

DO NOT:

- Quietly build a workaround (a workaround is an unapproved architectural decision)
- Treat the failed decision as your personal problem to absorb
- Leave the decision marked ACCEPTED while building something different

**Why:** A plan that failed is information. Hidden workarounds turn one wrong decision into an undocumented shadow architecture the developer never approved.

### Rule 10: Improve the Process, Not Just the Product

- Record retro findings at every check-in and phase boundary
- Track estimated vs actual effort in the completion log
- Route every learning into a document (CONTEXT, DECISIONS, TODO, or this framework)
- Propose framework changes to the developer when the process itself causes friction

**Why:** Continuous improvement means the tenth task is executed better than the first — and the next project starts smarter than this one did

---

## ⚙️ WORKFLOW FOR SENIOR AI (Setting Up a New Project)

### Phase A: Initial Discovery (1-2 hours)

#### Step 1: Understand the Request

- What is the user asking for?
- Is it clear or ambiguous?
- What questions need answers?

#### Step 2: Ask Clarifying Questions

Essential questions:
- What is the primary goal?
- What currently exists?
- What should we NOT change?
- What constraints must we respect?
- What does success look like?
- Who will use this?
- What's the timeline?

#### Step 3: Explore the Codebase (if applicable)

Use these tools systematically:
- file_search: Find relevant files by pattern
- grep_search: Find specific code patterns
- semantic_search: Understand concepts
- read_file: Study key files
- list_dir: Understand structure

#### Step 4: Research Domain (if needed)

If unfamiliar with domain:
- Ask user for reference materials
- Search for documentation
- Identify knowledge gaps
- Document what you learn

### Phase B: Document Creation (2-4 hours)

#### Step 5: Create GOAL.md

Process:

1. Write primary objective (one sentence)
2. List 3-5 success criteria (measurable)
3. Define scope boundaries (in/out)
4. Document constraints
5. Review with user → iterate → finalize

#### Step 6: Create CONTEXT.md

Process:

1. Document current system state
2. Map technology stack
3. Identify key files and their roles
4. Document architecture
5. List hard constraints
6. Identify required knowledge
7. Review with user → iterate → finalize

#### Step 7: Create DECISIONS.md

Process:

1. Create template
2. Document any decisions made during discovery
3. Set up structure for future decisions
4. Explain how to use the document

#### Step 8: Create TODO.md

Process:

1. Break work into logical phases
2. Break phases into tasks
3. Write acceptance criteria for each task
4. Order tasks by dependencies
5. Review with user → iterate → finalize

#### Step 9: Create SPRINT_STORY_{folder_name}.md

ONLY after Steps 5-8 are complete and approved:

1. Determine folder_name (the folder containing G/C/D/T documents)
2. Derive epic from GOAL.md
3. Derive one story per TODO task (Spike issue type for spike tasks)
4. Copy/adapt acceptance criteria; convert S/M/L sizes to story points
5. Add dependency links, priorities, labels, suggested sprint plan
6. Review with user → developer uses it for sizing + Jira population

**Remember:** this document EXPORTS the plan; it must not add scope.

### Phase C: Handoff (30 minutes)

#### Step 10: Verify Completeness

Checklist:
- [ ] GOAL is clear and measurable
- [ ] CONTEXT is comprehensive
- [ ] DECISIONS template is ready
- [ ] TODO is broken down and sequenced
- [ ] SPRINT_STORY_{folder_name} is generated and traces 1:1 to TODO tasks
- [ ] All documents cross-reference each other
- [ ] Anti-hallucination rules are clear

#### Step 11: Brief the Executor (Junior AI or Future Self)

Provide:
1. Path to all documentation
2. Order to read documents
3. How to approach first task
4. How to report progress
5. What to do if stuck

---

## 🎯 WORKFLOW FOR JUNIOR AI (Executing the Project)

### Session Start Ritual (Every Time)

#### Step 1: Orient Yourself (5 minutes)

Read in this order:

1. GOAL.md → Remember what we're building
2. TODO.md → Find current task
3. CONTEXT.md → Review relevant constraints
4. DECISIONS.md → Check for related decisions

#### Step 2: Announce Your Plan (before coding)

Tell the user:

- Which task you're starting (by ID)
- What changes you'll make
- What files you'll touch
- Any questions or concerns
- Estimated complexity

### Task Execution Loop

#### Step 3: Mark Task In Progress

Update TODO.md: ⬜ → 🔄

#### Step 4: Execute the Task

Process:

1. Make changes according to acceptance criteria
2. Follow established patterns
3. Test as you go
4. Check off criteria as completed
5. Verify no regressions

#### Step 5: Verify Completion

Before marking done:

- [ ] Code compiles/builds
- [ ] All criteria checked
- [ ] No breaking changes
- [ ] Follows patterns
- [ ] Documentation updated

#### Step 6: Mark Task Complete

Update TODO.md: 🔄 → ✅

Add entry to completion log.

#### Step 7: Document Decisions

If you made any choices:

- Add to DECISIONS.md
- Explain rationale
- Note alternatives
- Document consequences

#### Step 8: Re-Read TODO

After every completed task:

- RE-READ TODO.md to re-orient yourself
- Confirm you know which task is next
- Ensure you have not drifted from the plan

#### Step 9: Check-In Every 10 Tasks (Mini Sprint Review)

After every 10 completed tasks, STOP and report to the user:

- What tasks were completed since last check-in
- What files changed
- DEMONSTRATE working output where possible (Agile: working software over status reports) — show the feature running, the test output, the rendered page; not just a list of checkmarks
- Decision status changes (any VALIDATED or INVALIDATED?)
- Any issues encountered
- Mini-retro (3 bullets): what went well / what didn't / what to change — record it in the RETROSPECTIVES section of TODO.md
- Est vs Actual trend: are tasks taking longer than planned?
- What's next
- Wait for user confirmation to continue

If fewer than 10 tasks completed since last check-in:

- Proceed to the next task (do NOT wait)

### When Things Go Wrong

#### If Blocked:

1. Mark task ⛔ in TODO.md
2. Document the blocker
3. Explain what you tried
4. Ask for guidance

#### If an ACCEPTED Decision Proves Unworkable:

(e.g., the planned technology is forbidden by corporate policy, the API doesn't exist as documented, the approach can't run here)

1. STOP — do NOT improvise a workaround
2. Mark the decision INVALIDATED in DECISIONS.md with evidence
3. Mark dependent tasks ⛔, citing the decision ID
4. Escalate to the developer with alternatives as PROPOSED decisions
5. Wait for an approved superseding decision

(See Rule 9 and the Decision Validation Loop)

#### If Confused:

1. Stop working
2. Re-read CONTEXT.md
3. Check DECISIONS.md
4. Ask clarifying questions

#### If Tempted to Add Features:

1. Stop
2. Check if it's in GOAL.md
3. If not in scope → Ask, don't add
4. If in scope → Ensure it's in TODO

---

## 📊 SUCCESS INDICATORS

You're Doing It Right If:

- ✅ Every task has clear, measurable acceptance criteria
- ✅ Work proceeds sequentially (not jumping around)
- ✅ Decisions are documented as they're made
- ✅ Decisions that fail in practice are marked INVALIDATED and escalated quickly
- ✅ Risky assumptions get spike tasks before implementation depends on them
- ✅ Retro findings actually change the documents (not just discussed)
- ✅ Progress is visible and trackable
- ✅ Check-ins demonstrate working output, not just status
- ✅ Nothing is hallucinated or invented
- ✅ Scope hasn't crept beyond the GOAL
- ✅ User understands what's happening
- ✅ Code quality stays high
- ✅ Sessions end cleanly with status report

Warning Signs (Re-assess If):

- ⚠️ Adding features not in GOAL
- ⚠️ Changing things not in TODO
- ⚠️ Guessing instead of asking
- ⚠️ Building workarounds for a decision that quietly stopped working
- ⚠️ A decision's HIGH-risk assumptions are still untested deep into implementation
- ⚠️ Estimates are consistently wrong but plans aren't recalibrated
- ⚠️ Retros happen but nothing changes (or they don't happen at all)
- ⚠️ Refactoring unrelated code
- ⚠️ Working on multiple tasks simultaneously
- ⚠️ Skipping acceptance criteria
- ⚠️ Not updating documentation
- ⚠️ User confused about progress

Critical Failures (Stop and Reset If):

- ❌ Completely different architecture emerged
- ❌ An INVALIDATED decision was papered over with an unapproved workaround
- ❌ Major refactoring happening
- ❌ Original goal is forgotten
- ❌ Context is ignored
- ❌ Tasks are made up on the fly
- ❌ Nothing compiles
- ❌ No one knows current status

---

## 🎓 TEACHING THIS FRAMEWORK TO OTHERS

### For Humans Teaching AI Agents

Onboarding Process:

1. Give the AI this document
2. Have AI read an example (e.g., the ESubmit Okta migration)
3. Have AI create G/C/D/T documents for a tiny project
4. Review their work, provide feedback
5. Start on real project once they demonstrate understanding

### For Senior AI Teaching Junior AI
Handoff Checklist:
- [ ] Junior AI has read this framework document
- [ ] Junior AI has access to GOAL/CONTEXT/DECISIONS/TODO
- [ ] Junior AI knows which task to start with
- [ ] Junior AI knows how to report progress
- [ ] Junior AI knows what to do when stuck
- [ ] Junior AI knows NOT to improvise
- [ ] Junior AI knows to RE-READ TODO.md after each task to prevent drift
- [ ] Junior AI knows to STOP and check in with the user after every 10 tasks
- [ ] Junior AI knows the Decision Validation Loop: if an ACCEPTED decision fails in practice, mark it INVALIDATED and ESCALATE — never build a silent workaround
- [ ] Junior AI knows to record retro findings and Est vs Actual at check-ins

### For Teams Adopting This Framework
Implementation Steps:
1. Pilot with one small project
2. Create G/C/D/T documents together
3. Assign one person to be the "senior agent" (maintains docs)
4. Others are "junior agents" (execute tasks)
5. Hold retrospective after each phase
6. Refine the process based on learnings

---

## 🔍 FREQUENTLY ASKED QUESTIONS

**Q: How detailed should the TODO tasks be?**

A: Each task should be completable in one session (1-4 hours) and independently verifiable. If a task takes longer, break it down.

**Q: What if requirements change mid-project?**

A: Update GOAL.md with new requirements, update CONTEXT.md if system state changes, update TODO.md to add/modify tasks. Document the change in DECISIONS.md as DECISION-XXX: Scope Change. Then re-sync SPRINT_STORY_{folder_name}.md and record the change in its SYNC LOG so Jira can be updated.

**Q: Why generate SPRINT_STORY instead of just using TODO.md in Jira?**

A: They serve different audiences. TODO.md is optimized for AI execution (sequential, verification-heavy, anti-drift). SPRINT_STORY is optimized for Agile project management: user-story descriptions, Given/When/Then acceptance criteria, story points for sizing, and dependency links — formatted for copy-paste into Jira. Keeping them separate lets each be good at its job; the 1:1 traceability (story ↔ TODO task ID) keeps them honest.

**Q: Can tasks be done in parallel?**

A: Only if they have no dependencies. But for AI agents, sequential execution is safer to avoid conflicts.

**Q: What if I discover the approach won't work?**

A: Document it in DECISIONS.md as REJECTED or SUPERSEDED, explain why, propose alternative, get approval, update TODO as needed.

**Q: What if an APPROVED decision turns out to be impossible in my environment?**

A: This is the Decision Validation Loop. Example: planning chose MCP, but the corporation forbids MCP. Do NOT scramble for a workaround — that creates unapproved shadow architecture. Instead: (1) STOP dependent tasks, (2) mark the decision INVALIDATED with evidence, (3) mark dependent tasks ⛔, (4) escalate to the developer with alternatives as PROPOSED decisions, (5) wait for approval, (6) make sure the discovered constraint lands in CONTEXT.md so no future plan repeats it. An invalidated decision escalated early is a framework success, not a failure.

**Q: How do we avoid discovering these problems late?**

A: List every decision's assumptions explicitly, and schedule time-boxed SPIKE tasks to test HIGH-risk assumptions before implementation depends on them. "Confirm MCP is permitted here" is a 30-minute spike in Phase 0 versus a multi-day crisis in Phase 3.

**Q: How do I handle exploratory work?**

A: Create a Phase 0 or "Discovery" phase with tasks like "Research X", "Prototype Y", "Evaluate Z". Even exploration needs structure.

**Q: What if the project is too small for all this?**

A: Scale down but keep the spirit:

- GOAL: One paragraph
- CONTEXT: Key constraints only
- DECISIONS: Major choices only
- TODO: Simple checklist

The framework scales up and down.

**Q: How do I prevent junior agents from going rogue?**

A: Clear anti-hallucination rules, strict "one task at a time" policy, mandatory re-reading of TODO.md after each task to prevent drift, and check-in with the user every 10 tasks for course correction.

**Q: What if I'm the junior AND senior agent (same person)?**

A: Still use the framework. Your "senior self" does discovery and planning. Your "junior self" executes. Don't blur the roles.

---

## 📌 QUICK START GUIDE
### For Senior AI: Setting Up a New Project
1. Read user request carefully
2. Ask clarifying questions (goals, constraints, scope)
3. Explore the codebase (file_search, grep_search, read_file)
4. Create GOAL.md (objective, success criteria, scope boundaries)
5. Create CONTEXT.md (current state, tech stack, constraints)
6. Create DECISIONS.md (template + any initial decisions, WITH assumptions listed for each)
7. Create TODO.md (phases, tasks, acceptance criteria — detailed for near phases, coarse for distant ones; SPIKE tasks scheduled for HIGH-risk assumptions)
8. Review all documents with user
9. Create SPRINT_STORY_{folder_name}.md (Jira bridge: epic, stories, acceptance criteria, story points — derived 1:1 from TODO.md)
10. Hand off to executor (junior AI or next session)

### For Junior AI: Executing Work
1. Read GOAL.md → Know the objective
2. Read TODO.md → Find first ⬜ task
3. Read CONTEXT.md → Understand constraints
4. Read DECISIONS.md → Know past choices AND the assumptions they rest on
5. Announce your plan to user
6. Mark task 🔄
7. Execute task (all acceptance criteria)
   ⚠️ If reality contradicts an ACCEPTED decision → STOP, mark it
   INVALIDATED, mark dependent tasks ⛔, escalate (Rule 9)
8. Mark task ✅ — if it was the first task proving a decision works,
   mark that decision VALIDATED
9. Update completion log (with Est vs Actual)
10. RE-READ TODO.md → Re-orient, prevent drift
11. Every 10 tasks → STOP, demo working output, mini-retro, report
    to user, wait for confirmation
12. Otherwise → Proceed to next task

---

## 🏁 FINAL CHECKLIST

### Senior AI Checklist:

- [ ] I understand the user's goal clearly
- [ ] I have explored the current system thoroughly
- [ ] I have identified all constraints
- [ ] I have created GOAL.md (clear, measurable)
- [ ] I have created CONTEXT.md (comprehensive)
- [ ] I have created DECISIONS.md (template ready, assumptions listed per decision)
- [ ] I have scheduled SPIKE tasks for HIGH-risk untested assumptions
- [ ] I have created TODO.md (broken down, sequenced; near phases detailed, distant phases coarse)
- [ ] I have created SPRINT_STORY_{folder_name}.md (epic + stories derived 1:1 from TODO.md, sized in story points, Jira-ready)
- [ ] User has reviewed and approved all documents
- [ ] Anti-hallucination rules are established
- [ ] Handoff is ready

### Junior AI Checklist:

- [ ] I have read all four documents (G/C/D/T)
- [ ] I understand the goal and constraints
- [ ] I know which task to start with
- [ ] I know the acceptance criteria
- [ ] I understand the patterns to follow
- [ ] I know what NOT to do (anti-hallucination rules)
- [ ] I know how to report progress
- [ ] I know to RE-READ TODO.md after each task to stay on track
- [ ] I know to STOP and check in with the user after every 10 tasks
- [ ] I know to mark a failed decision INVALIDATED and ESCALATE — never to build a silent workaround (Rule 9)
- [ ] I know to record retro findings and Est vs Actual at check-ins

---

## 🎯 THE ULTIMATE RULE
If you remember only ONE thing from this entire document:

**GOAL** defines what we're building
**CONTEXT** defines what we're working with
**DECISIONS** records why we chose this way — and whether it survived reality
**TODO** defines how we'll get there — and improves as we learn

Read before you write. Ask before you invent. Verify before you claim completion. Escalate before you work around.

---

END OF FRAMEWORK DOCUMENT

This framework has been successfully used to migrate complex enterprise applications with zero functional regressions. When followed rigorously, it produces high-quality, well-documented, maintainable results.
