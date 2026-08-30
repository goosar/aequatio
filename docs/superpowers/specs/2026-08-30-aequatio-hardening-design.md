# Aequatio Hardening Design

## Purpose

Improve Aequatio in five ordered, independently releasable phases: security, money correctness, quality gates, frontend API/authentication, and expense functionality. Each phase must leave the application working and testable. Existing uncommitted changes are user-owned and must be preserved.

## Current System

Aequatio is a FastAPI and SQLAlchemy application backed by PostgreSQL, with a React/Vite frontend. It authenticates users with short-lived JWT Bearer tokens and currently supports registration, login, expense creation, and expense listing. The backend has broad unit coverage, while frontend automated tests are absent. The repository also contains an outbox publisher that is not currently operated as a service.

## Global Constraints

- Keep Bearer-token authentication; do not migrate to cookies in this effort.
- Remove the unauthenticated arbitrary user lookup and replace it with an authenticated current-user endpoint.
- Preserve the existing API version prefix `/api/v1`.
- Preserve all unrelated and pre-existing working-tree changes.
- Use test-driven development for behavior changes.
- Store monetary values exactly; binary floating-point is not acceptable for persisted money.
- Every expense mutation must enforce ownership using the authenticated user ID, never a client-supplied owner ID.
- Complete phases in the order defined below.

## Phase 1: Security

### Configuration

Application settings will be centralized and validated at startup. `SECRET_KEY` is required, must not equal the existing placeholder, and must contain at least 32 characters. `DATABASE_URL` remains required. `CORS_ORIGINS` is read as a comma-separated list and defaults only to `http://localhost:5173` for local development. Startup failure must state which setting is invalid without printing secret values.

An `.env.example` will document required and optional variables with non-secret examples. Docker Compose will inject a development-only secret explicitly rather than relying on an application fallback.

### Authenticated profile

`GET /api/v1/users/{user_id}` will be removed. `GET /api/v1/users/me` will require a valid Bearer token and return the `UserResponse` for the token subject. A valid token whose user no longer exists returns `401`, because the authenticated identity is no longer valid.

The login response will contain `access_token`, `token_type`, and `user`. This removes the frontend's need to decode the JWT or issue an arbitrary user-ID lookup. Existing clients that only read the original two fields remain compatible.

### Error handling

Expected domain and validation failures retain specific 4xx responses. Unexpected registration failures are logged with a stack trace and return a generic `500` response: `Registration failed`. Database details, exception text, credentials, and internal paths must not be returned to clients.

### Security tests

Tests will prove startup rejects absent, placeholder, and short secrets; accepts a valid secret; enforces configurable CORS origins; rejects unauthenticated `/users/me`; returns only the authenticated user; rejects deleted users; includes the user in login responses; and hides unexpected exception details.

## Phase 2: Money Correctness

### Domain and persistence

Expense amounts will use `Decimal` in Pydantic/domain models and SQLAlchemy `Numeric(precision=19, scale=4)`. Four fractional digits preserve imported or foreign-currency values while the UI may format according to a currency's normal display precision. Inputs must be positive, finite decimal values with no more than four fractional digits.

An Alembic migration will convert the existing `FLOAT` column to `NUMERIC(19,4)` using an explicit PostgreSQL cast. Downgrade will cast back to floating point and will be documented as lossy.

API JSON will represent amounts as strings to preserve exact decimal values across JavaScript boundaries. The typed frontend model will therefore use `amount: string`, converting to a decimal-safe representation only for validated display and aggregation.

### Currency totals

The expense list will group totals by ISO currency. It will never add values of different currencies. No exchange-rate conversion is included.

### Money tests

Tests will cover exact decimal round trips, rejection of excessive scale and non-finite values, migration metadata, API serialization, and separate frontend totals for multiple currencies.

## Phase 3: Quality Gates and Modernization

### Backend typing and deprecations

SQLAlchemy models will use SQLAlchemy 2 typed declarations with `Mapped[...]` and `mapped_column()`. Repository mappings must pass mypy without blanket suppressions. Pydantic models will use `ConfigDict`. All application UTC timestamps will be timezone-aware via `datetime.now(timezone.utc)`.

### Continuous integration

CI will install from the lock file where practical and run these mandatory checks without failure suppression:

- Ruff check and format check
- Mypy
- Pytest
- Frontend clean install
- Frontend ESLint
- Frontend TypeScript/Vite production build
- Frontend unit tests

The build is successful only if every check passes.

### Frontend test foundation

Vitest, React Testing Library, user-event, and jsdom will provide component tests. Tests will initially cover auth validation, login failure, expense creation, loading/error presentation, and multi-currency totals.

## Phase 4: Frontend API and Authentication State

### Typed API client

A focused API module will own the base URL, JSON parsing, standard error conversion, Bearer headers, and response types. The base URL comes from `VITE_API_URL`, defaulting to `http://localhost:8000` only in development. Components will not contain absolute API URLs.

### Session lifecycle

The frontend will persist the Bearer token in `localStorage` for this iteration, acknowledging that an XSS vulnerability could expose it. On startup, the app loads the token and calls `/users/me`; success restores the user, while `401` clears the token and presents a session-expired state. Logout clears all local authentication and expense state. Other unauthorized API responses use the same centralized expiration path.

### UI states

Authentication restoration and expense loading will use explicit loading, success, empty, and error states. Network failures show retry controls. Modals receive dialog semantics, focus management, Escape handling, focus restoration, and background-scroll protection.

## Phase 5: Expense Functionality

### API

Add owner-scoped endpoints:

- `PATCH /api/v1/expenses/{expense_id}` updates supplied mutable fields.
- `DELETE /api/v1/expenses/{expense_id}` deletes an expense and returns `204`.
- `GET /api/v1/expenses` accepts optional date, category, vendor, search, sort, page, and page-size parameters.
- `GET /api/v1/expenses/export.csv` exports the authenticated user's filtered expenses.

An expense belonging to another user returns `404`, avoiding disclosure of its existence. Page size defaults to 50 and is capped at 100. Search covers title, vendor, and description. Allowed sort fields are expense date, created time, title, and amount.

### Frontend

Users can choose the expense date, edit and delete their own expenses, confirm destructive deletion, filter and sort the list, navigate pages, and export the active filtered result set. Optimistic updates are not required; the server response remains authoritative.

### Functional tests

Backend tests cover CRUD, filters, pagination boundaries, CSV escaping, and cross-user isolation. Component tests cover edit/delete interactions, filter state, and error recovery. One Playwright end-to-end flow covers registration, login, create, edit, filter, export request, delete, and logout.

## Outbox Boundary

Operating RabbitMQ and the outbox dispatcher is intentionally excluded from these five phases because there is no current event consumer. The existing transactional event recording must continue to work. A later operational design can add a dedicated dispatcher service, publisher confirms, retry limits, and dead-letter handling when a consumer exists.

## Delivery Strategy

Each phase is a separate review and commit boundary. Within a phase, each behavior follows red-green-refactor: add a focused failing test, verify the intended failure, implement the smallest behavior, and rerun focused plus relevant regression tests. Database migrations are tested against PostgreSQL before the money phase is considered complete.

## Success Criteria

- A known or missing secret cannot start the application.
- No unauthenticated endpoint exposes arbitrary user profiles or internal exception text.
- Persisted and aggregated money remains exact and totals never combine currencies.
- Backend lint, formatting, typing, and tests pass without ignored failures or deprecation warnings introduced by application code.
- Frontend lint, build, and unit tests are enforced in CI.
- Authentication survives refresh, expires coherently, and displays actionable loading/error states.
- Expense CRUD, filtering, pagination, and export are owner-scoped and covered from API through one end-to-end workflow.
