# Development Tools Guide

## 📦 Tool Categories

### ESSENTIAL (Install Always)
These tools run on every commit/push:

```bash
pip install black flake8 ruff pytest pytest-cov
```

**Why:**
- `black` - Auto-formats code (no arguments needed)
- `flake8` - Catches style violations
- `ruff` - Fast linter (replaces multiple tools)
- `pytest` + `pytest-cov` - Testing and coverage

**Usage:**
```bash
black src/                    # Format code
flake8 src/                   # Check style
ruff check src/ --fix         # Lint and auto-fix
pytest --cov=src tests/       # Run tests with coverage
```

### OPTIONAL (Periodic Audits)
Run these during code reviews or monthly audits:

```bash
pip install pylint radon bandit mypy
```

**Why:**
- `pylint` - Deep code analysis (slower but thorough)
- `radon` - Complexity metrics
- `bandit` - Security scanning
- `mypy` - Type checking

**Usage:**
```bash
pylint src/                   # Comprehensive analysis
radon cc src/ -a              # Complexity report
bandit -r src/                # Security scan
mypy src/                     # Type check
```

### JAVASCRIPT (If Needed)
Only if you modify JavaScript files:

```bash
npm install -g eslint jscpd
```

## 🚀 Recommended Setup

### Option 1: Minimal (Fastest)
```bash
pip install -r requirements.txt
pip install black flake8 ruff pytest pytest-cov
```

### Option 2: Full Development (Recommended)
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### Option 3: CI/CD Only
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
# Tools run automatically in GitHub Actions
```

## 🔄 Pre-commit Hooks (DISABLED - Future Phase)

**Status:** Currently disabled to prevent automatic code reformatting.

**When to enable:** After Phase 2 (Code Formatting) is complete.

**To enable later:**
```bash
# Rename config file
ren .pre-commit-config.yaml.DISABLED .pre-commit-config.yaml

# Install hooks
pip install pre-commit
pre-commit install
```

**What it will do:**
- Runs `black` to format code (will change many files!)
- Runs `ruff` to check style
- Runs `flake8` to validate
- Prevents commits with issues

## 📋 Daily Workflow

### Before Committing
```bash
black src/                    # Format
ruff check src/ --fix         # Lint
pytest tests/                 # Test
git add .
git commit -m "feat: ..."     # Pre-commit runs automatically
```

### Weekly/Monthly Audit
```bash
pylint src/ --score=y         # Get quality score
radon cc src/ -a              # Check complexity
bandit -r src/                # Security scan
```

## 🎯 Recommendations

**For Solo Development:**
- Install: `black`, `flake8`, `ruff`, `pytest`
- Use pre-commit hooks
- Run `pylint` monthly

**For Team Development:**
- Install all tools in `requirements-dev.txt`
- Enforce pre-commit hooks
- Run full audit before releases
- Add tools to CI/CD

**For Production:**
- Only `requirements.txt` needed
- Dev tools NOT required on server
- CI/CD runs all checks

## ⚠️ Important Notes

1. **Don't add dev tools to `requirements.txt`**
   - Keeps production dependencies clean
   - Reduces deployment size
   - Separates concerns

2. **Use `requirements-dev.txt` for development**
   - Install with: `pip install -r requirements-dev.txt`
   - Only on development machines
   - Not on production servers

3. **Pre-commit hooks are optional but recommended**
   - Catches issues before commit
   - Saves time in code review
   - Maintains consistent quality

4. **Periodic audits are important**
   - Run `pylint` monthly
   - Run `bandit` before releases
   - Check complexity with `radon`
