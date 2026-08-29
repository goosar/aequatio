# Phase 1 Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Secure application configuration and user-profile access while preserving JWT Bearer authentication and the current expense-tracker behavior.

**Architecture:** Introduce a small immutable settings object loaded from environment variables, then inject its values into app construction and JWT helpers. Replace arbitrary profile lookup with an authenticated `/users/me` endpoint, return the authenticated user with login, sanitize unexpected failures, and update the login UI to consume the new response directly.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, SQLAlchemy, python-jose, pytest, React 19, TypeScript, Vite, Vitest, React Testing Library

**Spec:** `docs/superpowers/specs/2026-08-30-aequatio-hardening-design.md`

## Global Constraints

- Keep Bearer-token authentication; do not migrate to cookies in this effort.
- Remove the unauthenticated arbitrary user lookup and replace it with an authenticated current-user endpoint.
- Preserve the existing API version prefix `/api/v1`.
- Preserve all unrelated and pre-existing working-tree changes.
- Use test-driven development for behavior changes.
- `SECRET_KEY` must be present, differ from `your-secret-key-change-in-production`, and contain at least 32 characters.
- Unexpected server exceptions must be logged but never returned verbatim.
- Use interactive staging (`git add -p`) in files that already had user changes before this plan: `app/api/v1/routers.py`, `frontend/src/App.tsx`, and `frontend/src/components/LoginForm.tsx`.

---

## File Structure

- `app/core/config.py`: immutable environment settings and validation.
- `app/core/database.py`: construct the database engine from validated settings.
- `app/core/security.py`: sign and validate JWTs using validated settings.
- `main.py`: construct FastAPI and configure CORS from settings.
- `app/api/v1/schemas/auth.py`: define the login response containing token and user.
- `app/api/v1/routers.py`: provide `/users/me`, enriched login response, and sanitized registration failures.
- `tests/test_config.py`: focused settings validation tests.
- `tests/conftest.py`: explicit test-only environment required before application imports.
- `tests/test_auth_endpoints.py`: authenticated-profile, login-response, and error-sanitization tests.
- `tests/test_app.py`: CORS configuration tests.
- `.env.example`: safe environment-variable documentation.
- `docker-compose.yml`: explicit development settings.
- `.github/workflows/ci.yml`: non-secret CI test settings required for application import.
- `Makefile`: explicit local-development secret where local commands launch the API.
- `frontend/src/types.ts`: shared frontend `User` and authentication response types.
- `frontend/src/components/LoginForm.tsx`: consume the user returned by login without JWT decoding or profile lookup.
- `frontend/src/components/LoginForm.test.tsx`: login integration behavior at component level.
- `frontend/src/test/setup.ts`: DOM matcher setup.
- `frontend/vite.config.ts`: Vitest jsdom configuration.
- `frontend/package.json` and `frontend/package-lock.json`: test command and dependencies.

### Task 1: Validated application settings

**Files:**
- Create: `tests/test_config.py`
- Modify: `tests/conftest.py`
- Modify: `app/core/config.py`
- Modify: `app/core/database.py`
- Modify: `app/core/security.py`

**Interfaces:**
- Produces: `Settings(database_url: str, rabbitmq_url: str, secret_key: str, algorithm: str, access_token_expire_minutes: int, cors_origins: tuple[str, ...])`
- Produces: `load_settings(environ: Mapping[str, str] | None = None) -> Settings`
- Produces: module singleton `settings: Settings`
- Consumed by: `app/core/database.py`, `app/core/security.py`, and Task 2 app construction.

- [ ] **Step 1: Establish explicit test-only startup settings**

At the very top of `tests/conftest.py`, before importing `app.core.database`, set only test-process defaults:

```python
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-at-least-32-characters")
```

This is test configuration, not a production fallback. It allows test collection after the application begins rejecting insecure process configuration.

- [ ] **Step 2: Write failing settings tests**

```python
# tests/test_config.py
import pytest

from app.core.config import load_settings


BASE_ENV = {
    "DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "x" * 32,
}


def test_load_settings_requires_secret_key():
    environment = {"DATABASE_URL": BASE_ENV["DATABASE_URL"]}

    with pytest.raises(ValueError, match="SECRET_KEY is required"):
        load_settings(environment)


@pytest.mark.parametrize(
    "secret",
    ["your-secret-key-change-in-production", "too-short"],
)
def test_load_settings_rejects_insecure_secret(secret: str):
    with pytest.raises(ValueError, match="SECRET_KEY"):
        load_settings({**BASE_ENV, "SECRET_KEY": secret})


def test_load_settings_requires_database_url():
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        load_settings({"SECRET_KEY": "x" * 32})


def test_load_settings_parses_cors_origins():
    settings = load_settings(
        {**BASE_ENV, "CORS_ORIGINS": "https://one.example, https://two.example"}
    )

    assert settings.cors_origins == (
        "https://one.example",
        "https://two.example",
    )


def test_load_settings_defaults_to_local_vite_origin():
    settings = load_settings(BASE_ENV)

    assert settings.cors_origins == ("http://localhost:5173",)
```

- [ ] **Step 3: Run the tests and verify the intended failure**

Run: `.venv\Scripts\pytest.exe tests/test_config.py -q`

Expected: collection fails because `load_settings` does not exist.

- [ ] **Step 4: Implement the immutable settings loader**

Replace module-level `os.getenv` constants in `app/core/config.py` with an immutable dataclass. Call `load_dotenv()` before constructing the singleton.

```python
from dataclasses import dataclass
from os import environ as process_environment
from typing import Mapping

from dotenv import load_dotenv


PLACEHOLDER_SECRET = "your-secret-key-change-in-production"


@dataclass(frozen=True)
class Settings:
    database_url: str
    rabbitmq_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    cors_origins: tuple[str, ...]


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    values = process_environment if environ is None else environ
    database_url = values.get("DATABASE_URL", "").strip()
    secret_key = values.get("SECRET_KEY", "")
    if not database_url:
        raise ValueError("DATABASE_URL is required")
    if not secret_key:
        raise ValueError("SECRET_KEY is required")
    if secret_key == PLACEHOLDER_SECRET or len(secret_key) < 32:
        raise ValueError("SECRET_KEY must contain at least 32 characters and must not use the placeholder")

    raw_origins = values.get("CORS_ORIGINS", "http://localhost:5173")
    cors_origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
    if not cors_origins:
        raise ValueError("CORS_ORIGINS must contain at least one origin")

    return Settings(
        database_url=database_url,
        rabbitmq_url=values.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
        secret_key=secret_key,
        algorithm="HS256",
        access_token_expire_minutes=int(values.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        cors_origins=cors_origins,
    )


load_dotenv()
settings = load_settings()
```

Update consumers to import `settings`, using `settings.database_url`, `settings.secret_key`, `settings.algorithm`, and `settings.access_token_expire_minutes`. Do not retain compatibility constants that allow code to bypass the validated object.

- [ ] **Step 5: Run focused and security regression tests**

Run: `.venv\Scripts\pytest.exe tests/test_config.py tests/test_security.py tests/test_auth_endpoints.py -q`

Expected: all tests pass with a valid development environment.

- [ ] **Step 6: Commit only Phase 1 settings hunks**

```powershell
git add tests/conftest.py tests/test_config.py app/core/config.py app/core/database.py app/core/security.py
git commit -m "security: validate application settings"
```

### Task 2: Configuration-driven CORS and deployment environment

**Files:**
- Create: `tests/test_app.py`
- Create: `.env.example`
- Modify: `main.py`
- Modify: `docker-compose.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `Makefile`

**Interfaces:**
- Consumes: `Settings` and `settings` from Task 1.
- Produces: `create_app(app_settings: Settings = settings) -> FastAPI`.

- [ ] **Step 1: Write the failing CORS test**

```python
# tests/test_app.py
from fastapi.testclient import TestClient

from app.core.config import Settings
from main import create_app


def test_create_app_uses_configured_cors_origins():
    app_settings = Settings(
        database_url="sqlite:///:memory:",
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        secret_key="x" * 32,
        algorithm="HS256",
        access_token_expire_minutes=30,
        cors_origins=("https://app.example",),
    )
    client = TestClient(create_app(app_settings))

    response = client.options(
        "/api/v1/",
        headers={
            "Origin": "https://app.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example"
```

- [ ] **Step 2: Run the test and verify the intended failure**

Run: `.venv\Scripts\pytest.exe tests/test_app.py -q`

Expected: `create_app` rejects the settings argument or does not allow the configured origin.

- [ ] **Step 3: Inject settings into app construction**

Change `create_app` to accept `app_settings: Settings = settings` and pass `list(app_settings.cors_origins)` to `CORSMiddleware`. Keep `allow_credentials=True`, `allow_methods=["*"]`, and `allow_headers=["*"]`.

- [ ] **Step 4: Document and inject safe development values**

Create `.env.example` with:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/aequatio
SECRET_KEY=replace-with-at-least-32-random-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:5173
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

Add explicit non-production `SECRET_KEY` and `CORS_ORIGINS` entries to the app service in `docker-compose.yml`. Add job-level `DATABASE_URL=sqlite:///:memory:` and a 32-plus-character CI-only `SECRET_KEY` to `.github/workflows/ci.yml`. Add the same clearly labelled local-only secret to Makefile commands that run Alembic or Uvicorn.

- [ ] **Step 5: Run the CORS and smoke tests**

Run: `.venv\Scripts\pytest.exe tests/test_app.py tests/test_smoke.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit deployment configuration**

```powershell
git add tests/test_app.py .env.example main.py docker-compose.yml .github/workflows/ci.yml Makefile
git commit -m "security: configure validated runtime origins"
```

### Task 3: Authenticated current-user endpoint and enriched login response

**Files:**
- Modify: `tests/test_auth_endpoints.py`
- Modify: `app/api/v1/schemas/auth.py`
- Modify: `app/api/v1/routers.py`

**Interfaces:**
- Produces: `TokenResponse(access_token: str, token_type: str, user: UserResponse)`.
- Produces: authenticated `GET /api/v1/users/me -> UserResponse`.
- Removes: `GET /api/v1/users/{user_id}`.
- Consumes: `get_current_user_id() -> UUID` and `UserApplicationService.get_user_by_id(UUID)`.

- [ ] **Step 1: Add failing login-response and current-user tests**

Append focused tests to `tests/test_auth_endpoints.py`:

```python
def bearer_headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestCurrentUserEndpoint:
    def test_requires_authentication(self, client: TestClient):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403

    def test_returns_authenticated_user(self, client: TestClient, registered_user: User):
        response = client.get(
            "/api/v1/users/me",
            headers=bearer_headers(registered_user),
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(registered_user.id)
        assert response.json()["email"] == registered_user.email

    def test_rejects_token_for_deleted_user(self, client: TestClient):
        missing_user = User.register(
            username="missinguser",
            email="missing@example.com",
            plain_password="SecurePass123!",
        )
        response = client.get(
            "/api/v1/users/me",
            headers=bearer_headers(missing_user),
        )
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"

    def test_arbitrary_user_route_is_removed(self, client: TestClient, registered_user: User):
        response = client.get(f"/api/v1/users/{registered_user.id}")
        assert response.status_code == 404
```

Extend `test_login_with_valid_credentials` to assert:

```python
assert data["user"] == {
    "id": str(registered_user.id),
    "username": registered_user.username,
    "email": str(registered_user.email),
    "is_active": True,
    "created_at": registered_user.created_at.isoformat(),
}
```

- [ ] **Step 2: Run the tests and verify the intended failures**

Run: `.venv\Scripts\pytest.exe tests/test_auth_endpoints.py -q`

Expected: login response lacks `user`, `/users/me` is interpreted as the old UUID route, and arbitrary UUID lookup still succeeds.

- [ ] **Step 3: Extend the login schema**

Import `UserResponse` into `app/api/v1/schemas/auth.py` and add `user: UserResponse` to `TokenResponse`. Update its OpenAPI example to include the user fields.

- [ ] **Step 4: Replace the user route and enrich login**

In `app/api/v1/routers.py`:

```python
return TokenResponse(
    access_token=access_token,
    token_type="bearer",
    user=UserResponse.model_validate(user),
)


@router.get("/users/me", response_model=UserResponse, tags=["Users"])
async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    user_service: UserApplicationService = Depends(get_user_service),
) -> UserResponse:
    user = user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserResponse.model_validate(user)
```

Delete the arbitrary `/users/{user_id}` route completely.

- [ ] **Step 5: Run endpoint and security regression tests**

Run: `.venv\Scripts\pytest.exe tests/test_auth_endpoints.py tests/test_security.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit only the security route hunks**

Use `git add -p app/api/v1/routers.py` and reject the pre-existing expense-list hunk. Then stage the schema and test normally.

```powershell
git add app/api/v1/schemas/auth.py tests/test_auth_endpoints.py
git commit -m "security: scope profile access to bearer identity"
```

### Task 4: Sanitized unexpected registration failures

**Files:**
- Modify: `tests/test_auth_endpoints.py`
- Modify: `app/api/v1/routers.py`

**Interfaces:**
- Produces: module logger named `app.api.v1.routers`.
- Produces: generic `500 {"detail": "Registration failed"}` for unexpected errors.

- [ ] **Step 1: Write the failing exception-disclosure test**

```python
from app.api.v1.routers import get_user_service


def test_registration_hides_unexpected_exception_details(client: TestClient, caplog):
    class FailingUserService:
        def register_user(self, **_kwargs):
            raise RuntimeError("postgres password=do-not-leak")

    app.dependency_overrides[get_user_service] = lambda: FailingUserService()
    response = client.post(
        "/api/v1/users/register",
        json={
            "username": "safeuser",
            "email": "safe@example.com",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Registration failed"}
    assert "do-not-leak" not in response.text
    assert "Unexpected registration failure" in caplog.text
```

- [ ] **Step 2: Run the test and verify sensitive text is currently returned**

Run: `.venv\Scripts\pytest.exe tests/test_auth_endpoints.py::test_registration_hides_unexpected_exception_details -q`

Expected: failure because the response contains `postgres password=do-not-leak`.

- [ ] **Step 3: Log the exception and return a generic response**

Add `logger = logging.getLogger(__name__)` at module scope. Replace the unexpected exception handler with:

```python
except Exception as exc:
    logger.exception("Unexpected registration failure")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Registration failed",
    ) from exc
```

- [ ] **Step 4: Run all authentication endpoint tests**

Run: `.venv\Scripts\pytest.exe tests/test_auth_endpoints.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit only error-handling hunks**

```powershell
git add tests/test_auth_endpoints.py
git add -p app/api/v1/routers.py
git commit -m "security: hide unexpected registration failures"
```

### Task 5: Frontend consumes the authenticated login user

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/components/LoginForm.test.tsx`
- Modify: `frontend/src/components/LoginForm.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

**Interfaces:**
- Produces: `User` and `TokenResponse` frontend types.
- Preserves: `LoginFormProps.onSuccess(user: User, token: string): void`.
- Consumes: the Task 3 login JSON response containing `user`.

- [ ] **Step 1: Install the minimum frontend test dependencies**

Run from `frontend`:

```powershell
npm install --save-dev vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Add `"test": "vitest run"` to scripts, add `test: { environment: 'jsdom', setupFiles: './src/test/setup.ts' }` to `vite.config.ts`, and create:

```typescript
// frontend/src/test/setup.ts
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 2: Write a failing login behavior test**

```tsx
// frontend/src/components/LoginForm.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import LoginForm from './LoginForm'

afterEach(() => vi.restoreAllMocks())

test('uses the user returned by login without requesting an arbitrary profile', async () => {
  const user = userEvent.setup()
  const onSuccess = vi.fn()
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(
      JSON.stringify({
        access_token: 'signed-token',
        token_type: 'bearer',
        user: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          username: 'testuser',
          email: 'test@example.com',
          is_active: true,
          created_at: '2026-08-30T10:00:00Z',
        },
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ),
  )

  render(<LoginForm onClose={() => undefined} onSuccess={onSuccess} />)
  await user.type(screen.getByLabelText('Email'), 'test@example.com')
  await user.type(screen.getByLabelText('Password'), 'SecurePass123!')
  await user.click(screen.getByRole('button', { name: 'Login' }))

  expect(fetchMock).toHaveBeenCalledTimes(1)
  expect(onSuccess).toHaveBeenCalledWith(
    expect.objectContaining({ username: 'testuser' }),
    'signed-token',
  )
})
```

- [ ] **Step 3: Run the test and verify the current two-request flow fails**

Run from `frontend`: `npm test -- src/components/LoginForm.test.tsx`

Expected: failure because the current component decodes the JWT and performs a second `/users/{id}` request instead of consuming `data.user`.

- [ ] **Step 4: Add shared types and simplify login**

Create:

```typescript
// frontend/src/types.ts
export type User = {
  id: string
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export type TokenResponse = {
  access_token: string
  token_type: 'bearer'
  user: User
}
```

Import these types in `LoginForm.tsx` and `App.tsx`. After the successful login request, parse `TokenResponse` and call `onSuccess(data.user, data.access_token)`. Delete JWT payload decoding, fallback user creation, and the `/users/{id}` fetch.

- [ ] **Step 5: Run frontend test, lint, and build**

Run from `frontend`:

```powershell
npm test -- src/components/LoginForm.test.tsx
npm run lint
npm run build
```

Expected: all three commands pass.

- [ ] **Step 6: Commit only authentication-flow hunks**

Stage new/configuration files normally. Use `git add -p` for the two pre-edited frontend source files, selecting only type-import and login-flow hunks.

```powershell
git add frontend/src/types.ts frontend/src/test/setup.ts frontend/src/components/LoginForm.test.tsx frontend/vite.config.ts frontend/package.json frontend/package-lock.json
git add -p frontend/src/components/LoginForm.tsx frontend/src/App.tsx
git commit -m "security: consume authenticated user from login"
```

### Task 6: Phase verification and documentation alignment

**Files:**
- Modify: `README.md`
- Modify: `QUICK_START.md`
- Modify: `JWT_AUTHENTICATION.md`

**Interfaces:**
- Documents: required settings, `/users/me`, enriched login response, and removal of arbitrary user lookup.

- [ ] **Step 1: Update documentation examples**

Document copying `.env.example` to `.env`, generating a random secret with at least 32 characters, comma-separated `CORS_ORIGINS`, the enriched login response, and authenticated `GET /api/v1/users/me`. Remove examples that direct clients to `/users/{user_id}`.

- [ ] **Step 2: Scan for stale insecure guidance**

Run:

```powershell
rg -n "your-secret-key-change-in-production|/users/\{user_id\}|/users/<|allow_origins=\[" README.md QUICK_START.md JWT_AUTHENTICATION.md app main.py
```

Expected: no application fallback, hard-coded CORS list, or arbitrary profile instructions remain. A reference explaining that the old placeholder is rejected is acceptable.

- [ ] **Step 3: Run the complete backend verification suite**

Run:

```powershell
.venv\Scripts\ruff.exe check app tests main.py
.venv\Scripts\ruff.exe format --check app tests main.py
.venv\Scripts\mypy.exe app main.py
.venv\Scripts\pytest.exe -q
```

Expected: Ruff and pytest pass. Mypy must introduce no new errors; the pre-existing expense-model errors belong to Phase 3 and must be recorded exactly if still present.

- [ ] **Step 4: Run the complete frontend verification suite**

Run from `frontend`:

```powershell
npm test
npm run lint
npm run build
```

Expected: all commands pass.

- [ ] **Step 5: Inspect the final diff for ownership and secrets**

Run:

```powershell
git diff --check
git diff --stat
git status --short
git diff -- .env
```

Expected: `.env` is unchanged and untracked secrets are absent. Pre-existing expense and visual-style changes remain present but uncommitted unless the user explicitly asks to include them.

- [ ] **Step 6: Commit documentation only**

```powershell
git add README.md QUICK_START.md JWT_AUTHENTICATION.md
git commit -m "docs: describe secure bearer authentication setup"
```
