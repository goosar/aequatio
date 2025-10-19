# Troubleshooting Guide

## Common Issues and Solutions

### 1. Bcrypt/Passlib Error

**Error:**
```
File "...\passlib\handlers\bcrypt.py", line 620, in _load_backend_mixin
    version = _bcrypt.__about__.__version__
              ^^^^^^^^^^^^^^^^^
AttributeError: module '_bcrypt' has no attribute '__about__'
```

**Cause:** 
- Outdated bcrypt library or compatibility issue between passlib and bcrypt

**Solution:**
```bash
# 1. Update bcrypt
uv add "bcrypt>=4.0.0"

# 2. Restart the server
# Press Ctrl+C to stop
make run-local
```

**Already Fixed In Project:**
- ✅ `pyproject.toml` already has `bcrypt>=4.0.0`
- ✅ `passlib[bcrypt]>=1.7.4` is installed

**If Error Persists:**
```bash
# Remove and reinstall dependencies
rm -rf .venv
uv sync
make run-local
```

---

### 2. Database Connection Error

**Error:**
```
could not translate host name "db" to address
```

**Solution:**
- When running locally, use `make run-local` (uses localhost:5432)
- When running in Docker, use `make dev` (uses db:5432)
- Make sure database is running: `docker ps`

---

### 3. Port Already in Use

**Error:**
```
Address already in use: 8000
```

**Solution (Windows):**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process (replace <PID>)
taskkill /PID <PID> /F
```

**Or stop Docker containers:**
```bash
make down
```

---

### 4. Frontend Can't Connect to Backend

**Error:**
```
Failed to fetch
CORS error
```

**Solution:**
1. Verify backend is running: http://localhost:8000/api/v1/
2. Check CORS settings in `main.py` (should allow localhost:5173)
3. Verify both servers are running:
   - Backend: `make run-local`
   - Frontend: `make run-frontend`

---

### 5. Migration Errors

**Error:**
```
Can't locate revision identified by 'xxxx'
```

**Solution:**
```bash
# Check current revision
docker exec -it aequatio-db-1 psql -U postgres -d aequatio -c "SELECT * FROM alembic_version;"

# If needed, reset migrations (WARNING: deletes all data)
make down
docker volume rm aequatio_pgdata
make local
```

---

### 6. Email Validator Missing

**Error:**
```
ImportError: email-validator is not installed
```

**Solution:**
```bash
uv add email-validator
```

**Already Fixed:** ✅ Project already has `email-validator` in dependencies

---

### 7. TypeScript/Frontend Build Errors

**Error:**
```
Module not found
Cannot find module 'react'
```

**Solution:**
```bash
cd frontend
npm install
npm run dev
```

---

### 8. Hot Reload Not Working

**Backend (FastAPI):**
- Make sure using `--reload` flag (included in `make run-local`)
- Check file changes are being detected in console

**Frontend (React):**
- Vite auto-reloads by default
- Clear browser cache (Ctrl+Shift+R)
- Check console for errors

---

## Quick Fixes

### Full Reset
```bash
# Stop everything
make down

# Remove database (WARNING: deletes data)
docker volume rm aequatio_pgdata

# Remove Python venv
rm -rf .venv

# Reinstall and restart
uv sync
make local
make run-local
make run-frontend
```

### Check All Services
```bash
# Check Docker containers
docker ps

# Check FastAPI
curl http://localhost:8000/api/v1/

# Check Frontend
curl http://localhost:5173
```

### View Logs
```bash
# Docker logs
make logs

# Database logs
docker logs aequatio-db-1

# Backend logs (visible in terminal running make run-local)
# Frontend logs (visible in terminal running make run-frontend)
```

---

## Debugging Tips

### 1. Check Server is Running
```powershell
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5173
netstat -ano | findstr :5432
```

### 2. Test API Directly
```powershell
# Test welcome endpoint
Invoke-WebRequest http://localhost:8000/api/v1/

# Test registration
$body = @{username='test'; email='test@test.com'; password='Test123!'} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/api/v1/users/register -Method POST -Body $body -ContentType 'application/json'
```

### 3. Check Database
```bash
make psql
```
Then:
```sql
-- List all tables
\dt

-- Check users
SELECT * FROM users;

-- Check migrations
SELECT * FROM alembic_version;
```

### 4. Python Environment
```bash
# Check Python version
python --version

# Check installed packages
uv pip list

# Verify bcrypt installation
uv pip show bcrypt
```

---

## Getting Help

1. **Check logs** - Most errors will show in terminal output
2. **API Documentation** - http://localhost:8000/docs
3. **Database Console** - `make psql`
4. **Browser Console** - F12 in browser for frontend errors

---

## Prevention

### Best Practices:
1. Always run `make local` before `make run-local`
2. Keep dependencies updated: `uv sync`
3. Stop services properly (Ctrl+C) rather than killing terminal
4. Use separate terminals for backend/frontend
5. Check `docker ps` before starting local servers

### Before Committing:
```bash
make lint        # Check code style
make typecheck   # Check types
make test        # Run tests (if available)
```

---

## Current Fix Required

**For the bcrypt error you're experiencing:**

1. **Stop the running server:**
   - Find the terminal running `make run-local`
   - Press `Ctrl+C`

2. **Restart the server:**
   ```bash
   make run-local
   ```

The bcrypt dependency has already been updated in your project, so a simple restart should fix the issue! 🚀
