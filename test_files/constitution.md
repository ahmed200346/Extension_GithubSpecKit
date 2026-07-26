# Expense Tracker Constitution

## Core Principles

### I. Local-First & Zero-Auth Architecture
The Expense Tracker is strictly a single-user personal tool. No backend, cloud database, or remote synchronization mechanisms shall be introduced in v1. Authentication features are explicitly banned to preserve user privacy and data immediacy. All data must reside solely in the client browser.

### II. Next.js App Router & Server Components Integrity
The application must adhere strictly to the Next.js App Router paradigm. UI components must leverage React Server Components (RSC) by default to keep client bundles lean. Client-side hydration must be restricted exclusively to components interacting directly with browser APIs.

### III. Client-Side Persistence via LocalStorage
All application state persistence must run through a dedicated client adapter communicating with browser `localStorage`. Hydration of the expense history list and summary metrics must execute immediately upon application initialization without displaying blocking loading states.

### IV. Testing Discipline & Quality Gates (NON-NEGOTIABLE)
No code shall be integrated into the main branch without accompanying automated tests. Implementers must write and validate unit tests for data validation utilities and structural storage adapters prior to submitting a merge request. Every feature validation cycle must achieve successful completion of the Jest test suite.

### V. Strict Accessibility (WCAG AA)
The application user interface must achieve zero critical accessibility violations. All input forms, interactive selectors, and action buttons must include semantic ARIA labels, support full keyboard navigation, and satisfy WCAG AA contrast standards.

## Technical Constraints & Stack

- **Language & Runtime**: TypeScript executing on Node 18+ environment.
- **Framework & Layout**: Next.js (App Router), React, and Tailwind CSS for utility-first responsive styling.
- **Data Schemas**: Strict validation of the `Expense` object attributes (id, amount, currency, category, description, date). The `amount` field must always validate as a positive number greater than zero.
- **Testing Engine**: Jest and React Testing Library for verifying component behaviors and utility performance.

## Development Workflow & Quality Gates

- **Branching Policy**: All work must occur on dedicated feature branches (e.g., `feat/expense-tracker` or `001-expense-tracker`). Direct commits to the main integration branch are strictly forbidden.
- **Merge Requirements**: A feature branch can only be merged if it successfully satisfies three automated gates:
  1. Compilation check completes with zero TypeScript errors.
  2. The linter validates code formatting guidelines without warnings.
  3. All automated tests pass successfully.

## Governance

This Constitution serves as the ultimate authority for development practices within the Expense Tracker repository. Technical decisions, code reviews, and implementation details must comply with these guidelines. 

### Open Questions & Uncertainties
- **TBD**: Should the Jest test runner execute automatically within a pre-commit Git hook, or should validation remain localized entirely inside the CI/CD pipeline environment?

**Version**: 1.0.0 | **Ratified**: 2026-06-22 | **Last Amended**: 2026-06-22