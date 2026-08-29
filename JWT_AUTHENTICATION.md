# JWT Authentication Implementation Summary

## Overview
Successfully implemented JWT-based authentication for the Aequatio API, allowing users to login with email and password and receive an access token for subsequent API requests.

## Changes Made

### 1. Dependencies
**File**: `pyproject.toml`
- Added `python-jose[cryptography]>=3.3.0` for JWT token generation and validation

### 2. Configuration
**File**: `app/core/config.py`
- `SECRET_KEY`: required JWT signing secret with at least 32 characters; the
  insecure placeholder is rejected
- Added `ALGORITHM`: HS256 for JWT signing
- Added `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30 minutes)
- `CORS_ORIGINS`: comma-separated list of allowed frontend origins

### 3. Security Module
**File**: `app/core/security.py`
- `create_access_token(data, expires_delta)`: Creates JWT token with expiration
- `verify_token(token)`: Validates and decodes JWT, returns payload or None
- `get_current_user_id(credentials)`: FastAPI dependency to extract user ID from Bearer token

### 4. Authentication Schemas
**File**: `app/api/v1/schemas/auth.py` (NEW)
- `LoginRequest`: Email (EmailStr) and password input
- `TokenResponse`: JWT access token, token type, and authenticated user's
  public profile

### 5. Application Service
**File**: `app/application/services/user_service.py`
- `authenticate_user(email, password)`: Validates credentials and returns User entity
  - Retrieves user by email
  - Verifies password hash
  - Checks if user is active
  - Returns User or None

### 6. API Endpoint
**File**: `app/api/v1/routers.py`
- `POST /api/v1/auth/login`: Login endpoint
  - Accepts: `LoginRequest` (email, password)
  - Returns: `TokenResponse` (access_token, token_type: "bearer", user)
  - Status: 200 OK on success, 401 Unauthorized on failure
  - Headers: WWW-Authenticate: Bearer on 401
- `GET /api/v1/users/me`: authenticated current-user profile endpoint

### 7. Test Suite
**Files**: 
- `tests/test_auth_service.py` (NEW): tests for authentication service
  - Valid/invalid credentials
  - Inactive users
  - Edge cases (SQL injection, special chars, Unicode)
  
- `tests/test_auth_endpoints.py` (NEW): tests for login endpoint
  - Valid/invalid login scenarios
  - Token validation and expiration
  - Integration tests (register + login)
  - Security behavior (timing attacks, password leakage)

## API Usage

### Login
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "user@example.com",
    "is_active": true,
    "created_at": "2025-10-18T10:30:00Z"
  }
}

# Error Response (401 Unauthorized)
{
  "detail": "Incorrect email or password"
}
```

### Using the Token
```bash
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

This endpoint returns only the authenticated user's public profile. The API
does not provide arbitrary user-profile lookup routes.

## Environment Variables
Create `.env` from the tracked template, then set a unique secret:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add the generated value to `.env`; it must contain at least 32 characters and
must never be committed. Configure allowed origins as a comma-separated list:

```env
SECRET_KEY=<generated-random-secret-with-at-least-32-characters>
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:5173,https://app.example.com
```

## Next Steps

### 1. Install Dependencies
```powershell
# You may need to restart VS Code to release file locks, then run:
uv sync
```

### 2. Run Tests
```powershell
pytest tests/test_auth_service.py -v
pytest tests/test_auth_endpoints.py -v
```

### 3. Secure the Secret Key
- Generate a secure random key for production:
  ```python
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- Add to `.env` and **never commit** this to version control

### 4. Current-user endpoint

Call `GET /api/v1/users/me` with `Authorization: Bearer <access_token>` to
retrieve the identity represented by the token. This replaces arbitrary
user-profile lookups.

## Architecture Benefits

### Clean Separation of Concerns
1. **API Layer** (`routers.py`): Handles HTTP, validation, status codes
2. **Application Service** (`user_service.py`): Orchestrates use case, manages transactions
3. **Domain Layer** (`entities/user.py`): Business rules, password validation
4. **Security Module** (`security.py`): JWT creation/validation, password hashing
5. **Repository** (`user_repository.py`): Database access

### Security Features
- ✅ Password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ Configurable token expiration
- ✅ Email validation with Pydantic
- ✅ Active user check
- ✅ SQL injection protection (ORM)
- ✅ No password leakage in responses

## Test Coverage
- **Service Layer**: tests covering authentication logic
- **API Layer**: tests covering endpoint behavior, security, and integration
- **Authentication coverage**: service and endpoint tests

## Known Issues
⚠️ **File Lock Issue**: `uv sync` encountered permission errors during dependency installation. This typically happens when:
- Python process is still running
- VS Code extension has files locked
- Another terminal has the virtual environment activated

**Solution**: Restart VS Code and run `uv sync` again.

## Documentation
- OpenAPI docs available at `/docs` after starting the server
- Login endpoint appears under "Authentication" tag
- Interactive testing available through Swagger UI
