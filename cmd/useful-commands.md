# SpendSense — Useful Commands Reference

Quick reference for Railway deployment and Git workflow commands used in this project.

---

## Railway Commands

### Authentication
```bash
# Login (opens browser)
railway login

# Login without browser (browserless mode)
railway login --browserless

# Verify login
railway whoami
```

### Project & Service Management
```bash
# Link local directory to Railway project
railway link
# When prompted: select project → spendsense, environment → production

# List and select a service interactively
railway service

# Check project/service status and get URLs
railway status
```

### Deployment
```bash
# Deploy current directory to active service
railway up --detach

# Deploy to a specific service
railway up --service backend --detach
railway up --service frontend --detach
```

### Logs
```bash
# Follow all logs live (active service)
railway logs

# Follow backend logs
railway logs --service backend

# Follow frontend logs
railway logs --service frontend
```

### Domains & URLs
```bash
# Generate a public domain for active service
railway domain

# Generate domain for a specific service
railway domain --service backend
railway domain --service frontend
```

### Environment Variables
```bash
# Open variables editor in browser for active service
railway variables

# Set a variable from CLI
railway variables set KEY=value

# Set variable for a specific service
railway variables set KEY=value --service backend
```

### Utility
```bash
# Open active service in browser
railway open

# Open specific service
railway open --service frontend

# Check Railway CLI version
railway --version

# Upgrade Railway CLI
brew upgrade railway
```

---

## Git Commands — SpendSense Branching Workflow

### Branch Strategy
```
main      ← production only — Railway auto-deploys on every push
  └── develop ← all day-to-day development happens here
```

### Daily Development
```bash
# Always confirm you're on develop before starting work
git branch --show-current
# expect: develop

# Stage all changes
git add .

# Commit with a descriptive message
git commit -m "feat: description of change"

# Push develop to GitHub
git push
```

### Release to Production (develop → main)
```bash
# Step 1 — ensure develop is clean
git checkout develop
git status
# expect: nothing to commit

# Step 2 — merge to main with a release commit
git checkout main
git merge develop --no-ff -m "release: Sprint X.X description"

# Step 3 — push to trigger Railway deploy
git push origin main
# expect: Railway dashboard shows new deploy within 30 seconds

# Step 4 — immediately switch back to develop
git checkout develop
```

### Feature Branches (for larger pieces of work)
```bash
# Create a feature branch from develop
git checkout develop
git checkout -b feature/sprint2-data-isolation

# Work on the feature, commit as normal
git add .
git commit -m "feat: add user_id to expense table"

# Merge back to develop when done
git checkout develop
git merge feature/sprint2-data-isolation --no-ff
git push

# Delete the feature branch after merging (optional cleanup)
git branch -d feature/sprint2-data-isolation
```

### Useful Git Shortcuts
```bash
# Check current branch and status
git status

# View recent commit history (one line per commit)
git log --oneline -10

# View all branches (local + remote)
git branch -a

# Undo last commit (keeps changes staged)
git reset --soft HEAD~1

# Discard all uncommitted changes ⚠️
git checkout -- .

# Pull latest from remote
git pull origin develop
```

### First-Time Branch Setup (if develop doesn't exist on remote yet)
```bash
git checkout -b develop
git push --set-upstream origin develop
```

---

## Docker Commands

### Start / Stop
```bash
# Start all services in background
docker compose up -d

# Start and rebuild images (after code changes)
docker compose up -d --build

# Stop all services (keeps data)
docker compose down

# Stop and wipe database volume ⚠️ WARNING: deletes all data
docker compose down -v
```

### Logs & Status
```bash
# Check service health
docker compose ps

# Follow all logs live
docker compose logs -f

# Follow backend logs only
docker compose logs -f backend

# Follow frontend logs only
docker compose logs -f frontend
```

### Rebuild
```bash
# Rebuild a single service
docker compose up -d --build backend
docker compose up -d --build frontend

# Full rebuild from scratch (no cache)
docker compose build --no-cache && docker compose up -d
```

### Database (local Docker)
```bash
# Open SQLite shell inside backend container
docker compose exec backend sqlite3 /app/data/expenses.db

# List all tables
docker compose exec backend sqlite3 /app/data/expenses.db ".tables"

# Check users
docker compose exec backend sqlite3 /app/data/expenses.db \
  "SELECT id, email, is_admin, last_login FROM user;"

# Manual backup
docker compose exec backend sqlite3 /app/data/expenses.db \
  ".backup '/app/data/backup_$(date +%Y%m%d).db'"
```

---

## Combined Workflow — Typical Sprint Release

```bash
# 1. Develop on develop branch
git checkout develop
# ... make changes ...
git add .
git commit -m "feat: sprint X changes"
git push

# 2. Verify locally
docker compose up -d
curl http://localhost:8000/health

# 3. Release to production
git checkout main
git merge develop --no-ff -m "release: Sprint X.X description"
git push origin main          # triggers Railway deploy
git checkout develop          # immediately return to develop

# 4. Verify on Railway
railway logs --service backend
railway logs --service frontend
curl https://YOUR-BACKEND.up.railway.app/health
```

---

## Quick Reference Card

| Action | Command |
|---|---|
| Start local app | `./start.sh` |
| Start Docker stack | `docker compose up -d` |
| Stop Docker stack | `docker compose down` |
| Deploy to Railway | `git checkout main && git merge develop --no-ff && git push origin main && git checkout develop` |
| Backend logs (Railway) | `railway logs --service backend` |
| Frontend logs (Railway) | `railway logs --service frontend` |
| Check Railway status | `railway status` |
| Push develop | `git push` |

---

*Last updated: May 2026*
*Owner: Debashish*
