# Tasks: Doc Pipeline - doc-pipeline-###

## Phase 1: Preparation & Specification
- [ ] **T001** Initialize specification input file for `doc-pipeline-###`
- [ ] **T002** Trigger automatically via Watcher or manual request (`POST /api/v1/pipeline/run`)

## Phase 2: Parallel Analysis (Agents 1 à 4)
- [ ] **T003** **Parsing Agent**: Evaluate schema adherence & relational integrity
- [ ] **T004** **Summary Agent**: Extract key concepts & maturity alignment (Parallel A)
- [ ] **T005** **Glossary Agent**: Process terms coverage & anti-tautology anchors (Parallel B)
- [ ] **T006** **Diagram Agent**: Validate syntax, cover architecture diagrams & export SVG/PDF (Parallel C)

## Phase 3: Convergence & Drafting (Agent 5)
- [ ] **T007** **DocWriter Agent**: Combine summary, glossary, and diagrams into full Markdown
- [ ] **T008** **DocWriter Agent**: Verify document completeness and diagram embedding validity

## Phase 4: Certification & Publication (Agent 6)
- [ ] **T009** **Layout Agent**: Execute HTML/CSS compilation and page-budget check
- [ ] **T010** **Layout Agent**: Produce certified PDF (`doc-pipeline-###.pdf`) and metrics report (`doc-pipeline-###_eval.json`)
