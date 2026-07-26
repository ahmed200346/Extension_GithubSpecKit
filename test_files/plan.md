# Implementation Plan: Expense Tracker

**Branch**: `feat/expense-tracker` | **Date**: 2026-06-22 | **Spec**: specs/001-expense-tracker/spec.md

## Summary

Small single-user Expense Tracker built with Next.js App Router. UI and persistence run in the browser using localStorage. Use server folder under `src/server` for shared types and validation utilities; route handlers and server actions are included as future-ready contracts but persistence remains client-side per requirements.

## Technical Context

**Language/Version**: TypeScript (Node 18+/Next.js latest from package.json)

**Primary Dependencies**: Next.js (App Router), React, Tailwind CSS, Jest + React Testing Library for tests.

**Storage**: localStorage (client). Server folder `src/server` will host types and validation only.

**Testing**: Jest + React Testing Library (unit tests for validators and component behaviour).

**Target Platform**: Web (modern browsers).

**Project Type**: Web application (frontend-focused) with optional minimal backend route handlers for future server persistence.

**Performance Goals**: Small bundle, responsive UI, preserve Next.js server components where possible.

**Constraints**: No authentication. Follow project constitution (clean code, Next.js App Router, testing discipline).

## Constitution Check

Gates from constitution:
- Next.js App Router & Server Components: using App Router — OK.
- Testing Discipline: plan includes unit tests; implementers must add tests before merge.
- Performance & Accessibility: keep UI light and accessible; use Tailwind for responsive styles.

No gate violations are expected. Tests are required in Phase 2 and must meet repository guidelines.

## Project Structure

```text
src/
├── server/
│   ├── types.ts
│   └── validators.ts
app/
├── components/
│   ├── ExpenseForm.tsx
│   ├── ExpenseList.tsx
│   └── Summary.tsx
└── page.tsx
specs/001-expense-tracker/
├── plan.md        # this file
├── research.md    # Phase 0 output
├── data-model.md  # Phase 1 output
├── quickstart.md  # Phase 1 output
└── contracts/
    └── expenses-api.md
```

**Structure Decision**: Single-project structure with `src/server` for shared types/validators and `app/` for Next.js App Router code.

## Complexity Tracking

No constitution violations requiring exception justification.

---

Phase 0 is next: research.md will resolve any minor technical unknowns and record decisions.
