# GitHub Repository Strategy - Embedding Recommender SaaS

## 🎯 Repository Architecture Decision

For maximum scalability and team collaboration, we'll use a **Monorepo + Polyrepo Hybrid Strategy**.

### Strategy: Main Monorepo + Optional Component Subrepos

```
Main Repository (PRIMARY - All code lives here)
├── embedding-recommender-saas (Monorepo)
│   ├── backend-api/
│   ├── ml-engine/
│   ├── data-pipeline/
│   ├── frontend/
│   ├── backoffice/
│   ├── control-plane/
│   ├── observability/
│   ├── infrastructure/
│   ├── docs/
│   └── docker-compose.yml

Optional (For Advanced Teams - Mirror specific components)
├── embedding-backend-api (Optional)
├── embedding-ml-engine (Optional)
└── embedding-frontend (Optional)
```

## ✅ **Recommended: Single Monorepo** (Start Here)

### Advantages
✅ **Atomic commits** - Change multiple services in one commit
✅ **Simplified dependencies** - Shared libraries, configs
✅ **Easier local development** - Single clone, docker-compose up
✅ **Consistent versioning** - Tag releases across all services
✅ **Better code sharing** - Reuse components, utilities
✅ **Single CI/CD pipeline** - Build all services together
✅ **Easier refactoring** - Cross-service changes in one PR

### Repository Structure
```
embedding-recommender-saas/
├── .github/
│   ├── workflows/
│   │   ├── backend-api.yml       # CI for backend
│   │   ├── ml-engine.yml         # CI for ML
│   │   ├── frontend.yml          # CI for frontend
│   │   ├── docker-publish.yml    # Push images
│   │   └── deploy.yml            # Deploy to k8s
│   ├── CODEOWNERS                # Auto-assign reviewers
│   └── dependabot.yml            # Auto-dependency updates
├── backend-api/
├── ml-engine/
├── data-pipeline/
├── frontend/
├── backoffice/
├── control-plane/
├── observability/
├── infrastructure/
├── docs/
├── scripts/
├── .gitignore
├── docker-compose.yml
├── README.md
└── CONTRIBUTING.md
```

## 🔧 Git Workflow

### Branch Strategy (GitHub Flow - Simple & Effective)

```
main (protected)
  ├── feature/backend-auth
  ├── feature/ml-lightgcn
  ├── feature/frontend-dashboard
  ├── fix/rate-limiting-bug
  └── release/v1.0.0
```

**Rules**:
- `main` is always deployable
- Create feature branches from `main`
- PR required to merge to `main`
- Auto-deploy on merge to `main` (staging)
- Tags for production releases (`v1.0.0`)

### Commit Convention (Conventional Commits)

```bash
# Format: <type>(<scope>): <description>

# Examples:
feat(backend): add JWT authentication
fix(ml-engine): resolve FAISS index build error
docs(readme): update installation instructions
chore(deps): bump fastapi to 0.110.0
refactor(data-pipeline): extract validation logic
perf(ml-engine): optimize embedding cache
test(backend): add rate limiting tests
ci(github): add docker build workflow
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, no logic change)
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `test` - Add/update tests
- `chore` - Maintenance tasks
- `ci` - CI/CD changes

**Scopes**:
- `backend` - Backend API
- `ml-engine` - ML Engine
- `data-pipeline` - Data Pipeline
- `frontend` - Customer Frontend
- `backoffice` - Admin Back Office
- `control-plane` - Airflow orchestration
- `observability` - Monitoring stack
- `infra` - Infrastructure
- `docs` - Documentation

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Feature
- [ ] Bug fix
- [ ] Refactoring
- [ ] Documentation
- [ ] Performance improvement

## Component
- [ ] Backend API
- [ ] ML Engine
- [ ] Data Pipeline
- [ ] Frontend
- [ ] Back Office
- [ ] Infrastructure

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manually tested locally
- [ ] Tested in staging

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex logic
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Added tests
- [ ] All tests pass
- [ ] Updated CHANGELOG.md

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #123
```

## 🏷️ Tagging & Releases

### Semantic Versioning
```
v1.0.0 - Major.Minor.Patch

Major: Breaking changes
Minor: New features (backwards compatible)
Patch: Bug fixes
```

### Release Process
```bash
# 1. Create release branch
git checkout -b release/v1.0.0

# 2. Update version in all services
# - backend-api/pyproject.toml
# - ml-engine/pyproject.toml
# - frontend/package.json
# - CHANGELOG.md

# 3. Create PR to main
gh pr create --title "Release v1.0.0"

# 4. After merge, tag main
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 5. GitHub Actions auto-deploys tagged versions to production
```

## 🔐 Branch Protection Rules

### `main` Branch Protection
```yaml
Required:
  ✅ Require pull request before merging
  ✅ Require 1 approval
  ✅ Dismiss stale reviews when new commits pushed
  ✅ Require status checks to pass
    - backend-api tests
    - ml-engine tests
    - frontend tests
    - linting
    - docker build
  ✅ Require conversation resolution
  ✅ Require signed commits (optional but recommended)
  ✅ Include administrators
  ✅ Restrict force pushes
  ✅ Restrict deletions
```

## 👥 CODEOWNERS File

```
# Backend API
/backend-api/ @team-backend

# ML Engine
/ml-engine/ @team-ml @team-backend

# Data Pipeline
/data-pipeline/ @team-data @team-ml

# Frontend
/frontend/ @team-frontend
/backoffice/ @team-frontend

# Infrastructure
/infrastructure/ @team-devops
/control-plane/ @team-devops
/observability/ @team-devops
/docker-compose.yml @team-devops

# Documentation
/docs/ @team-leads
README.md @team-leads
```

## 🤖 GitHub Actions CI/CD

### Workflow: Backend API
```yaml
# .github/workflows/backend-api.yml
name: Backend API CI/CD

on:
  push:
    branches: [main]
    paths:
      - 'backend-api/**'
      - '.github/workflows/backend-api.yml'
  pull_request:
    paths:
      - 'backend-api/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: cd backend-api && uv sync

      - name: Run tests
        run: cd backend-api && uv run pytest tests/ -v --cov

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint
        run: cd backend-api && uv run ruff check .

  docker:
    needs: [test, lint]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./backend-api
          push: true
          tags: |
            yourorg/backend-api:latest
            yourorg/backend-api:${{ github.sha }}
```

## 📦 Dependency Management

### Dependabot Configuration
```yaml
# .github/dependabot.yml
version: 2
updates:
  # Backend API (Python/UV)
  - package-ecosystem: "pip"
    directory: "/backend-api"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  # ML Engine (Python/UV)
  - package-ecosystem: "pip"
    directory: "/ml-engine"
    schedule:
      interval: "weekly"

  # Frontend (npm)
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## 📊 Repository Labels

### Category Labels
```
Type:
- type: feature (green)
- type: bug (red)
- type: enhancement (blue)
- type: documentation (purple)
- type: refactor (yellow)

Component:
- component: backend (orange)
- component: ml-engine (pink)
- component: frontend (cyan)
- component: data-pipeline (brown)
- component: infra (gray)

Priority:
- priority: critical (dark red)
- priority: high (red)
- priority: medium (yellow)
- priority: low (green)

Status:
- status: in-progress (blue)
- status: blocked (red)
- status: needs-review (yellow)
- status: ready-to-merge (green)
```

## 🔍 Monorepo Tools (Optional)

For larger teams, consider:

### Nx (Recommended)
```bash
npm install -g nx

# Run only affected services
nx affected:test
nx affected:build

# Run specific service
nx serve frontend
nx test backend-api
```

### Turborepo
```bash
npm install turbo --global

# Fast builds with caching
turbo build
turbo test
```

## 🚀 Deployment Strategy

### Environments
```
Development   → Local (docker-compose)
Staging       → Kubernetes (auto-deploy on merge to main)
Production    → Kubernetes (manual deploy from tagged release)
```

### GitOps with ArgoCD
```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: embedding-saas-production
spec:
  source:
    repoURL: https://github.com/yourorg/embedding-recommender-saas
    path: infrastructure/kubernetes/production
    targetRevision: v1.0.0
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## 📈 Metrics & Analytics

### GitHub Insights to Track
- Code frequency (commits per week)
- Pull request merge time
- Contributor activity
- Code review coverage
- Deployment frequency
- Change failure rate

### Repository Health
- [ ] README with badges (build, coverage, license)
- [ ] CONTRIBUTING.md guide
- [ ] CODE_OF_CONDUCT.md
- [ ] LICENSE file
- [ ] Issue templates
- [ ] PR templates
- [ ] Security policy (SECURITY.md)
- [ ] Changelog (CHANGELOG.md)

## 🎯 Recommended Setup Order

1. ✅ Create main monorepo
2. ✅ Add .gitignore
3. ✅ Add README.md
4. ✅ Push initial code
5. ✅ Set up branch protection
6. ✅ Add CODEOWNERS
7. ✅ Create PR template
8. ✅ Add GitHub Actions workflows
9. ✅ Configure Dependabot
10. ✅ Add labels
11. ✅ Create first release (v0.1.0)

---

## Alternative: Polyrepo Strategy (If Team Grows)

If you later need separate repos:

```
embedding-backend-api       → Backend API team
embedding-ml-engine         → ML team
embedding-data-pipeline     → Data engineering team
embedding-frontend          → Frontend team
embedding-infrastructure    → DevOps team
embedding-shared-libs       → Shared utilities
```

**When to split**:
- Team size > 20 engineers
- Services have different release cycles
- Need strict access control per service
- Different tech stacks require separate tooling

**Trade-offs**:
- ❌ More complex dependency management
- ❌ Harder to make cross-service changes
- ❌ More CI/CD pipelines to maintain
- ✅ Clearer ownership boundaries
- ✅ Independent deployment schedules
- ✅ Smaller repositories (faster clones)

---

## 🎉 Summary

**Recommended**: Single monorepo with path-based CI/CD

**Repository**: `embedding-recommender-saas`

**Workflow**: GitHub Flow (main + feature branches)

**CI/CD**: GitHub Actions (path-based triggers)

**Versioning**: Semantic versioning with tags

**Protection**: Branch protection + CODEOWNERS + required reviews

This strategy balances simplicity (monorepo) with scalability (CI/CD per component).
