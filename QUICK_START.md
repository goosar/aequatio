# Quick Start Guide - Local Development

## Complete Local Development Setup

### Prerequisites
- Docker Desktop running
- Node.js and npm installed
- Python with uv installed

---

## Option 1: One-Command Setup (Recommended)

### Start Everything Locally

**Terminal 1 - Database & Migrations:**
```bash
make local
```
This will:
- Start PostgreSQL in Docker (port 5432)
- Run database migrations
- Wait for database to be ready

**Terminal 2 - Backend:**
```bash
make run-local
```
- Starts FastAPI at http://localhost:8000
- Hot reload enabled
- API docs at http://localhost:8000/docs

**Terminal 3 - Frontend:**
```bash
make run-frontend
```
- Starts React dev server at http://localhost:5173
- Hot reload enabled
- Connects to backend at localhost:8000

---

## Option 2: Docker Everything

```bash
make dev
```
This starts:
- PostgreSQL in Docker
- FastAPI in Docker (http://localhost:8000)
- React frontend in Docker (http://localhost:5173)

---

## Quick Commands Reference

### Setup & Running
```bash
make local           # Setup: db + migrations
make run-local       # Run FastAPI locally
make run-frontend    # Run React dev server
```

### Docker
```bash
make up              # Start all services in Docker
make down            # Stop all containers
make dev             # Full Docker dev environment
make ps              # Show running containers
```

### Database
```bash
make db-only         # Only start PostgreSQL
make migrate-local   # Run migrations (localhost)
make migrate         # Run migrations (Docker)
make psql            # Open PostgreSQL shell
```

### Code Quality
```bash
make lint            # Run ruff linter
make lint-fix        # Auto-fix linting issues
make typecheck       # Run mypy
make test            # Run pytest
make check           # Run all checks (lint + typecheck + test)
```

---

## Testing the Registration Feature

### 1. Start All Services
```bash
# Terminal 1
make local

# Terminal 2
make run-local

# Terminal 3
make run-frontend
```

### 2. Open Frontend
Navigate to: http://localhost:5173

### 3. Test Registration
1. Click the "Register" button in the header
2. Fill out the form:
   - Username: `test_user`
   - Email: `test@example.com`
   - Password: `TestPass123!`
   - Confirm Password: `TestPass123!`
3. Click "Register"
4. Should see: "Welcome, test_user! Registration successful."

### 4. Verify in Database
```bash
make psql
```
Then in the PostgreSQL shell:
```sql
SELECT id, username, email, is_active, created_at FROM users;
```

---

## URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React app |
| Backend API | http://localhost:8000 | FastAPI app |
| API Docs | http://localhost:8000/docs | Interactive API docs |
| Welcome Endpoint | http://localhost:8000/api/v1/ | API welcome message |
| PostgreSQL | localhost:5432 | Database (inside Docker) |

---

## Common Issues

### Frontend can't connect to backend
**Problem:** CORS error or connection refused

**Solution:**
- Check backend is running: http://localhost:8000/api/v1/
- CORS is configured for localhost:5173 in `main.py`

### Database connection error
**Problem:** "could not translate host name 'db'"

**Solution:**
- Using `run-local`? Use `LOCAL_DB_URL=localhost:5432`
- Using Docker? Use `DB_URL=db:5432`
- Check database is running: `docker ps`

### Port already in use
**Problem:** "Address already in use"

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or stop Docker containers
make down
```

### Frontend packages missing
**Problem:** Module not found errors

**Solution:**
```bash
cd frontend
npm install
```

---

## Development Workflow

### Making Backend Changes
1. Edit Python files in `app/`
2. Server auto-reloads (if using `run-local`)
3. Check http://localhost:8000/docs for API updates

### Making Frontend Changes
1. Edit React files in `frontend/src/`
2. Browser auto-refreshes (if using `run-frontend`)
3. Check browser console for errors

### Database Changes
1. Create migration:
   ```bash
   make alembic-revision M="description"
   ```
2. Edit the migration file in `alembic/versions/`
3. Apply migration:
   ```bash
   make migrate-local
   ```

---

## Stopping Services

### Stop Frontend
- Press `Ctrl+C` in the terminal running `make run-frontend`

### Stop Backend
- Press `Ctrl+C` in the terminal running `make run-local`

### Stop Database
```bash
make down
```

---

## Full Reset

To start completely fresh:

```bash
# Stop everything
make down

# Remove database volume (WARNING: deletes all data)
docker volume rm aequatio_pgdata

# Start fresh
make local
make run-local
make run-frontend
```

---

## Next Steps

1. ✅ Test user registration
2. ✅ Implement login functionality
3. ✅ Add JWT authentication
4. ✅ Build expense tracking features
5. ✅ Add group management

Happy coding! 🚀
