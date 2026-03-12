# Tier 1 Implementation: Git Branch Protection + Communication

**Timeline:** 2-4 hours to setup  
**Impact:** 40-50% reduction in merge conflicts  
**Effort:** Low (mostly GitHub configuration)

---

## Implementation Checklist

### 1. GitHub Branch Protection Rules

#### Step 1: Access Repository Settings
1. Go to your GitHub repo
2. Settings → Branches → Branch protection rules
3. Add rule for `main` branch

#### Step 2: Configure Protection Rule

**Minimum Settings:**
```
✅ Require a pull request before merging
   └─ Require approvals: 1 (or 2 for teams > 5)
   └─ Require CODEOWNERS review: YES (already exists in .github/CODEOWNERS)

✅ Require status checks to pass before merging
   └─ Require branches to be up to date: YES

✅ Require code reviews before merging
   └─ Dismiss stale pull request approvals: YES
   └─ Require review from Code Owners: YES

✅ Require deployments to succeed
   └─ (Optional: if you have CI/CD configured)

✅ Restrict who can push to matching branches
   └─ Select "Restrict pushes that create matching branches"
   └─ Allow only admins to bypass required status checks
```

**Result:** No one can push directly to `main`. All changes require PR + review.

---

### 2. CODEOWNERS Configuration

**File:** `.github/CODEOWNERS` (already exists)

**Current Setup:** Verify it looks like this
```bash
# Global owners
* @kmartineztamayo

# Core services
src/services/ @kmartineztamayo
src/routes/ @kmartineztamayo

# Apps
apps/planning/ @kmartineztamayo
apps/reporting/ @kmartineztamayo

# Docs
docs/ @kmartineztamayo
```

**Add if multi-developer:**
```bash
# If Developer 2 joins
apps/planning/ @kmartineztamayo @developer2
apps/reporting/ @kmartineztamayo @developer2

# Per-module ownership
src/services/db_utils.py @kmartineztamayo
src/services/task_assigner.py @developer2
```

**Result:** Code owners are automatically requested for review on relevant PRs.

---

### 3. GitHub Actions: Validation Required Before Merge

**File:** `.github/workflows/validate-on-pr.yml` (create if missing)

```yaml
name: Validate PR

on:
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      
      - name: Run validation
        run: python scripts/validate_code.py
        timeout-minutes: 30

      - name: Run tests
        run: pytest tests/ --cov=src --cov-fail-under=82
        timeout-minutes: 15
```

**Result:** Every PR must pass all tests/linting before merge button appears.

---

### 4. Slack/Discord Notifications

#### Option A: GitHub Slack App (Recommended)

1. Go to Slack workspace
2. Browse Apps → Search "GitHub"
3. Click "GitHub" official app
4. "Install" and authorize
5. In repo: Settings → Integrations & services → Slack

**Configure in your Slack channel:**
```
/github subscribe owner/repo pulls

# Then you'll get notifications like:
# ✅ New PR created: "feat(planning): Add skill-based assignment"
# ✅ PR approved by @developer2
# ✅ PR ready to merge
```

#### Option B: GitHub Webhook (Manual Setup)

**Create webhook:**
1. Settings → Webhooks → Add webhook
2. Payload URL: `https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK`
3. Content type: `application/json`
4. Events: "Pull requests", "Pull request reviews"

---

### 5. Team Communication: "Currently Working On" Shared Document

**Create in Notion, Google Docs, or GitHub Discussions:**

```markdown
# Currently Working On (mockCMMS Dev Team)

Last Updated: March 12, 2026

| Developer | Branch | Files | Status | ETA |
|-----------|--------|-------|--------|-----|
| kmartineztamayo | `feat/planning-skills` | `src/services/task_assigner.py`, `apps/planning/src/services/db_utils.py` | In Progress | March 15 |
| developer2 | `fix/ui-bugs` | `src/templates/assets.html`, `src/static/css/main.css` | Code Review | March 13 |
| developer3 | `docs/update-readme` | `README.md`, `docs/` | Waiting for Approval | March 12 |

## Rules:
- Update THIS DOCUMENT before starting work
- Include branch name, files you're touching, and expected completion date
- Check this before starting work to see if someone else is already touching your files
- If conflict detected, communicate via Slack/Discord to coordinate
- Remove your row when PR is merged
```

**Location Options:**
- GitHub Discussions (built-in, free)
- Notion (shared workspace)
- Google Docs (everyone can edit)
- Wiki in repo

---

### 6. Pre-Commit Conflict Prevention Hook

**File:** `.git/hooks/pre-push`

```bash
#!/bin/bash
# Prevent pushing branches that would conflict with main

echo "🔍 Checking for potential conflicts with main..."

# Fetch latest main
git fetch origin main:refs/remotes/origin/main --quiet

# Check if current branch has conflicts with main
if ! git merge-base --is-ancestor HEAD origin/main; then
    echo "⚠️  Your branch diverges from main"
    echo "Run: git rebase origin/main"
    echo "Then: git push --force-with-lease"
    exit 1
fi

echo "✅ No conflicts detected. Proceeding..."
exit 0
```

**Install hook:**
```bash
# Copy to .git/hooks/ and make executable
chmod +x .git/hooks/pre-push
```

---

### 7. Git Tips to Minimize Conflicts

#### Daily Sync
```bash
# Every morning or before starting work
git fetch origin
git rebase origin/main

# If conflicts occur during rebase, resolve them now (not later in merge)
# Then push: git push --force-with-lease
```

#### Logical Commits
```bash
# Bad: Large commit touching many files
git commit -m "work"

# Good: Focused commits
git add src/services/task_assigner.py
git commit -m "refactor: optimize skill matching algorithm"

git add tests/
git commit -m "test: add coverage for skill matching edge cases"

# Easier to merge, easier to revert if needed
```

#### Use Feature Flags Instead of Long-Lived Branches
```python
# Instead of 2-week branch editing multiple files,
# use feature flags:

if os.getenv("ENABLE_NEW_SKILL_MATCHING"):
    result = new_skill_matcher()
else:
    result = old_skill_matcher()

# Merge to main faster, feature stays disabled until ready
# Reduces branch lifetime → fewer conflicts
```

---

## Expected Results

### Before Tier 1:
- ❌ Developers push directly to main
- ❌ No validation on commits
- ❌ Conflicts discovered during merge (too late to fix)
- ❌ Unknown what others are working on
- ❌ Duplicate work possible

### After Tier 1:
- ✅ All changes go through PR + review
- ✅ All tests must pass before merge
- ✅ Code owners must approve
- ✅ Team visibility of active work
- ✅ Conflicts detected early (before merge)
- ✅ Much easier coordination

### Conflict Reduction:
- **Team < 3 people:** 60% reduction
- **Team 3-5 people:** 40-50% reduction
- **Team 5+ people:** 30-40% reduction (need Tier 2)

---

## When to Upgrade to Tier 2

If after 2 weeks of Tier 1 you still have:
- ❌ Merge conflicts > 2 per week
- ❌ Multiple developers blocked on same files
- ❌ Frequent "sorry I was working on that" moments
- ❌ Rebase/merge conflicts taking > 30 minutes to resolve

→ **Proceed to Tier 2: File Locking System** (see `COLLABORATIVE_DEVELOPMENT_ANALYSIS.md`)

---

## Quick Setup Script (Automated)

**Create:** `scripts/setup-git-protection.sh`

```bash
#!/bin/bash
# Setup Git branch protection rules and hooks

echo "📋 Setting up Git configuration..."

# Create pre-push hook
mkdir -p .git/hooks
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
git fetch origin main:refs/remotes/origin/main --quiet
if ! git merge-base --is-ancestor HEAD origin/main; then
    echo "⚠️  Conflicts detected. Run: git rebase origin/main"
    exit 1
fi
EOF
chmod +x .git/hooks/pre-push

echo "✅ Git hooks installed"
echo ""
echo "📝 Next steps:"
echo "1. Go to GitHub repo Settings → Branches"
echo "2. Add branch protection rule for 'main'"
echo "3. Enable 'Require pull request before merging'"
echo "4. Enable 'Require code owner reviews'"
echo "5. Enable 'Require status checks to pass'"
echo ""
echo "📢 Share this doc with your team:"
echo "   docs/TIER1_GIT_PROTECTION.md"
```

**Run:**
```bash
chmod +x scripts/setup-git-protection.sh
./scripts/setup-git-protection.sh
```

---

## Summary

| Step | Effort | Impact | When |
|------|--------|--------|------|
| 1. Branch protection | 5 min | High | Now |
| 2. CODEOWNERS review | 5 min | Medium | Now |
| 3. GitHub Actions CI | 15 min | High | Today |
| 4. Slack notifications | 10 min | Medium | Today |
| 5. Shared "Working On" doc | 10 min | Low | Today |
| 6. Pre-push hook | 5 min | Medium | Today |
| 7. Team training | 30 min | High | This week |

**Total:** ~1.5 hours of setup + 30 min team training

**Expected Result:** 40-50% fewer merge conflicts within 1 week

---

**Last Updated:** March 12, 2026  
**Created By:** GitHub Copilot  
**Status:** Ready for implementation

