# AI Assistant Instructions for the CMMS Monorepo (GitHub Copilot)

> **⚠️ SYNCHRONIZATION NOTICE:** This file (`copilot-instructions.md`) is for
> **GitHub Copilot** instructions. A parallel document, `GEMINI.md`, exists for
> **Gemini Code Assist** instructions. While both documents should be nearly
> identical (except for model-specific references), they should be kept in sync.
> **If you make changes to this file, please ensure the corresponding section in
> `GEMINI.md` is also updated**, and vice versa.

This document is divided into two parts:

1.  **Global AI Coding Standards:** Universal rules for high-quality code
    generation, applicable to any project.
2.  **Workspace Context & Specifics:** Detailed information about this specific
    monorepo, its architecture, and local workflows.

---

## 1. Global AI Coding Standards

These instructions apply to **all** coding tasks unless explicitly overridden by
workspace-specific rules.

### 1.1. Code Quality & Style

- **Clarity & Conciseness:** Always generate code that is clear, concise, and
  well-commented, especially for complex logic or algorithms.
- **Comment Standards:**
  - Comments explain WHY, not WHAT (code should be self-explanatory)
  - NEVER reference bug/issue numbers (e.g., `<!-- Bug #5 -->`,
    `// Bug #5: Fix`)
  - Focus on business logic, complex algorithms, or non-obvious decisions
  - Use proper grammar and punctuation
  - Keep comments concise and relevant
  - Remove commented-out code blocks
- **Code Separation (Separation of Concerns):**
  - JavaScript code belongs in `.js` files only
  - CSS code belongs in `.css` files only
  - HTML code belongs in `.html` templates only
  - Avoid inline styles (`style="..."`) - use CSS classes instead
  - Avoid inline scripts (`<script>` in HTML) - use external `.js` files
  - Avoid inline event handlers (`onclick="..."`) - use event listeners in JS
    files
  - Exception: Inline code only when strictly necessary (e.g., dynamic backend
    values)
- **Conventions:** Adhere to the widely accepted style and formatting
  conventions for the target language or framework (e.g., PEP 8 for Python,
  Google JavaScript Style Guide, etc.).
- **Paradigm:** Prefer class-based object-oriented programming for languages
  that support it, unless a functional or procedural approach is clearly more
  suitable for a simple utility or script.
- **Maintainability:** Prioritize maintainability, scalability, and testability.
  Use modular design, meaningful naming, and separation of concerns.
- **Refactoring:** Actively refactor code to improve its structure and remove
  unused or "dead" code.
- **Hardcoding:** Avoid hardcoding values; use configuration files, environment
  variables, or constants where possible.

#### 1.1.1. The 5-Step Iterative Loop (Mandatory)

Every code change must follow this strict process for EACH file or module:

1.  **Lint**: Run available linters (`ruff`, `pylint`, `mypy`, `jscpd`) and fix
    ALL issues.
2.  **Format**: Run formatters and fix ALL issues.
    - **Python (STRICT ORDER):** `isort` → `black` → `docformatter`
      1. `isort src/` - Sort imports (PEP 8)
      2. `black src/` - Format code structure
      3. `docformatter --in-place -r src/` - Format docstrings (PEP 257)
    - **JavaScript/CSS:** `prettier`
3.  **Test**: Run `pytest` (Backend) or browser tests (Frontend). Fix ALL errors.
    - **CRITICAL:** Check coverage % against `pyproject.toml` or `package.json`.
    - **Strict Coverage:** 80% is the FLOOR, not a suggestion. If coverage is BELOW threshold (e.g., 79.9% vs 80%), it is a FAILURE.
    - **Action:** Improve current tests (more robust tests) or add more tests. Avoid duplicates or redundancies. Do not lower the config.
4.  **Audit**: Review logic against project standards (Architecture, patterns).
    Updates audit report if applicable.
5.  **Commit**: Only commit if Steps 1-4 are perfect. Use Conventional Commits.
    - _If changes are made during Audit, LOOP BACK to Step 1._

#### 1.1.2. Recommended Developer Workflow (Scripts)

**Use the project scripts for efficient code quality enforcement:**

| Step | Command                           | Purpose                                                            |
| ---- | --------------------------------- | ------------------------------------------------------------------ |
| 1    | `python scripts/format_code.py`   | **Auto-fix** all formatting (isort, black, docformatter, prettier) |
| 2    | `python scripts/validate_code.py` | **Verify** all checks pass (linting, tests, coverage)              |
| 3    | `git commit`                      | Pre-commit hooks run as final safety net                           |

**Why this order?**

- `format_code.py` applies fixes quickly (seconds).
- `validate_code.py` runs comprehensive validation including tests (minutes).
- Pre-commit hooks are a **backstop** - they catch anything missed before commit.

**Quick Options:**

- `python scripts/validate_code.py --quick` - Skip slow tests for faster iteration.
- `python scripts/validate_code.py --backend` - Backend only.
- `python scripts/validate_code.py --frontend` - Frontend only.

### 1.2. Reliability, Security & Performance

- **Error Handling:** Include robust error handling appropriate for the language
  (e.g., try-catch, try-except, error callbacks, etc.) to ensure code
  reliability.
- **Security:** For web applications or code handling user input, always follow
  security best practices (e.g., input validation, output encoding, use of
  secure libraries, avoiding injection vulnerabilities, etc.).
- **Performance:** Optimize for performance and resource efficiency when
  relevant, but never at the expense of code clarity or correctness.
- **Concurrency:** Handle concurrency and parallelism safely using language
  features like `async/await`, goroutines, or threads to improve performance.

### 1.3. Architecture & Best Practices

- **Libraries:** Prefer using well-established libraries and frameworks for
  common tasks, and ensure dependencies are properly managed (e.g.,
  `requirements.txt`, `package.json`, etc.).
- **API Design:** When designing APIs, follow RESTful conventions or GraphQL
  best practices to ensure they are intuitive and scalable.
- **State Management:** For complex applications, consider state management
  patterns and libraries (e.g., Redux, MobX, Vuex) for predictable state
  transitions.
- **Infrastructure:** For infrastructure management, prefer Infrastructure as
  Code (IaC) tools like Terraform or CloudFormation.
- **Observability:** Incorporate logging, metrics, and tracing to provide
  visibility into the application's behavior in production.

### 1.4. Testing & Deployment

#### 🚨 CRITICAL: Visual Test Screenshots - NEVER UPDATE (MANDATORY)

**NEVER update visual test screenshots unless REAL UI changes were intentionally made!**

- **Location**: `tests/frontend/e2e/__screenshots__/` directory
- **Purpose**: Visual regression tests that detect UNINTENDED UI changes
- **Rule**: Screenshots are SACRED BASELINES - they should ONLY be updated when:
  1. You intentionally modified CSS/HTML/UI components
  2. The visual change is documented and approved
  3. The change is part of a UI enhancement task

**FORBIDDEN Actions:**

- ❌ **NEVER** run `playwright test --update-snapshots` to "fix" failing visual tests
- ❌ **NEVER** update screenshots to make tests pass
- ❌ **NEVER** modify screenshots during code audits, refactoring, or non-UI tasks
- ❌ **NEVER** touch screenshots when working on backend, logic, or documentation

**Correct Approach When Visual Tests Fail:**

1. **Investigate WHY** - Visual test failures indicate UNINTENDED changes
2. **Identify the root cause** - Find what code change caused the visual difference
3. **Fix the CODE** - Revert or fix the code that caused the unintended change
4. **Re-run tests** - Verify visual tests pass with the fixed code
5. **Only update screenshots** - If the visual change was INTENTIONAL and APPROVED

**Summary**: Failing visual tests = Bug detected. Fix the bug, don't hide it by updating screenshots.

#### 🚨 CRITICAL: Comprehensive Automated Verification (MANDATORY)

**ALL verification steps MUST be performed automatically. DO NOT ask the user to
verify manually.**

**For UI Changes:**

- **MANDATORY**: Use `browser_subagent` tool to perform comprehensive browser
  verification
- The video recording MUST demonstrate ALL implemented, changed, or deleted
  features
- Perform ALL necessary actions (scrolling, clicking, navigating) to show every
  aspect of the change
- Test all user flows affected by the changes

**For Code Logic Changes:**

- **MANDATORY**: Run automated tests using `pytest` or equivalent
- Create new tests if none exist for the changed functionality
- Verify all test cases pass before considering work complete

**For Database Schema Changes:**

- **MANDATORY**: Verify database changes automatically:

1. Stop the running app if active
2. Delete the current database instance (e.g., `instance/mockcmms.db`)
3. Restart the app to recreate the database with the new schema
4. Run SQL queries to verify schema correctness
5. Create automated tests in `tests/` directory to verify schema

- Document all migration scripts and their execution results

**General Testing:**

- **Verification:** Where appropriate, include basic unit tests or usage
  examples to demonstrate correctness and facilitate future maintenance.
- **CI/CD:** Promote the use of CI/CD pipelines to automate testing and
  deployment, ensuring code quality and faster release cycles.

**Verification is NOT optional** - it is a critical step that MUST be completed
automatically for every change.

#### 🚨 CRITICAL: Test Configuration is IMMUTABLE (MANDATORY)

**NEVER modify test configurations, linting rules, or coverage thresholds to make tests pass!**

**Protected Configuration Files:**

- `pytest.ini` - Test discovery, coverage thresholds, test markers
- `pyproject.toml` - Ruff, Black, isort, mypy configurations
- `jest.config.js` - JavaScript test configuration and coverage thresholds
- `playwright.config.js` - E2E test configuration
- `.eslintrc.js`, `eslint.config.js` - JavaScript linting rules
- `.flake8`, `setup.cfg` - Python linting rules
- Any file in `.github/workflows/` - CI/CD pipeline configuration

**FORBIDDEN Actions:**

- ❌ **NEVER** lower coverage thresholds (e.g., changing `coverageThreshold` from 80% to 70%)
- ❌ **NEVER** disable linting rules to suppress warnings
- ❌ **NEVER** add files/patterns to ignore lists to skip tests
- ❌ **NEVER** modify test timeouts to hide performance issues
- ❌ **NEVER** change CI/CD workflow steps to skip failing checks

**Correct Approach When Tests or Linting Fail:**

1. **Understand the failure** - Read the error message carefully
2. **Fix the CODE** - Make the code comply with the rules
3. **Add tests** - If coverage is low, write more tests
4. **Refactor** - If complexity is high, simplify the code
5. **Document exceptions** - Only in RARE cases, document why a rule should be modified (requires user approval)

**Coverage Philosophy:**

- Current coverage: **82.99%** (achieved through hard work)
- Target: **80-85%** overall coverage
- Critical paths: **90%+** coverage (auth, API, database)
- Coverage should INCREASE over time, never decrease
- **STRICT RULE:** 80% is the FLOOR. If you add code but coverage drops (even to 79.9%), you have FAILED. Improve tests or add new ones. Avoid duplicates.
- **Verification:** Always verify the _actual_ coverage number against the _configured_ threshold.

**Summary**: Configuration defines quality standards. Lower the bar = Lower the quality. Fix the code, not the config.

#### 🚨 CRITICAL: Test-Driven Development Philosophy (MANDATORY)

**Core Principle: Tests are the safety net for all code changes.**

**As of December 2025, the project follows a strict test-first approach:**

**When Adding New Code:**

1. **Check for existing tests** - Search `tests/` directory for related test
   files
2. **Run existing tests** - Verify current tests pass before making changes
3. **Create/Update tests FIRST** - Write tests for new functionality before
   implementing
4. **Implement code** - Write the actual feature/fix
5. **Verify tests pass** - All tests (old + new) must pass
6. **Check coverage** - Ensure new code paths are tested

**When Modifying Existing Code:**

1. **Identify affected tests** - Find tests that cover the code being modified
2. **Run tests BEFORE changes** - Establish baseline (all should pass)
3. **Make code changes** - Implement modifications
4. **Run tests AFTER changes** - Verify nothing broke
5. **If tests fail** - CRITICAL DECISION POINT:
   - **Option A**: Code is wrong → Fix the code to match test expectations
   - **Option B**: Test is wrong → Update test to match new correct behavior
   - **Decision criteria**: Prioritize test correctness unless requirements
     changed
6. **Update tests if needed** - Adjust tests only if requirements genuinely
   changed

**Test Organization Guidelines:**

**Separate Test File When:**

- Different testing concern (Performance vs Functionality)
- Different security level (Auth tests need extra scrutiny)
- Different execution timing (Slow integration tests)
- Cross-cutting concern (Validation applies to all components)
- Different ownership (Security team owns auth tests)
- Industry convention (Everyone separates auth tests)

**Combine Tests When:**

- Same component/module (All API tests in test_api_routes.py)
- Same testing level (Unit tests for db_utils together)
- Same execution context (Fast unit tests together)
- Natural cohesion (CRUD operations for same resource)

**Coverage Philosophy:**

- Coverage isn't about test count—it's about testing all code paths
- Test success cases, failure cases, and edge cases
- Target: 80-85% overall coverage (achieved: 82.99%)
- Critical paths: 90%+ coverage (auth, API, database)

**Avoiding Test Duplicates:**

1. **Search before creating** - Use `findstr /S "def test_" tests\*.py` to find
   existing tests
2. **Check test names** - Look for similar test names in the same module
3. **Review test file** - Read existing tests in the file you're modifying
4. **Consolidate if needed** - Merge duplicate tests into comprehensive ones

**Test Failure Decision Tree:**

```
Test fails after code change:
├─ Did requirements change?
│  ├─ YES → Update test to match new requirements
│  └─ NO → Continue to next question
├─ Is the test testing correct behavior?
│  ├─ YES → Fix the code (test is right, code is wrong)
│  └─ NO → Fix the test (test is wrong, code is right)
├─ When in doubt:
│  └─ Prioritize test correctness (tests define expected behavior)
```

**Reference Documentation:**

- See `tests/README.md` for test suite organization and complete testing
  strategy

#### 🚨 CRITICAL: Coverage Testing Best Practices (MANDATORY)

**Tests must INCREASE coverage, not just pass. A passing test that doesn't cover new code paths is WORTHLESS for coverage.**

**Understanding Coverage:**

- **Coverage means the CODE is EXECUTED during tests** - If tests don't increase coverage, the code paths aren't being executed
- **Branch coverage** tracks conditional branches (if/else, ternary operators, short-circuit evaluation)
- **Line coverage** tracks which lines of code were executed
- **The coverage threshold is in `jest.config.js` (Frontend) and `pytest.ini` (Backend)**

**How to Write Tests That INCREASE Coverage:**

1. **Identify uncovered lines FIRST** - Run `npm run test:coverage` and check the report for specific line numbers
2. **Analyze the uncovered code** - View those exact lines to understand what conditions trigger them
3. **Call functions DIRECTLY with specific inputs** - Don't rely on event dispatching in JSDOM; call the function with parameters that trigger the uncovered branch
4. **Mock dependencies BEFORE instantiation** - If testing a class method, mock on `ClassName.prototype.methodName` BEFORE creating the instance
5. **Verify coverage increased** - Run coverage again to confirm the lines are now covered

**Common Coverage Testing Mistakes (AVOID THESE):**

- ❌ **Adding tests that pass but don't execute uncovered code** - The test runs, but coverage stays the same
- ❌ **Relying on DOM events in JSDOM** - Event handlers may not trigger coverage for inline anonymous functions
- ❌ **Mocking AFTER instantiation** - Event handlers bind to the original method, not the mock
- ❌ **Testing the same code paths repeatedly** - Diminishing returns on coverage
- ❌ **Creating tests without checking which lines are uncovered** - Wasted effort

**Correct Approach for Coverage Gaps:**

```javascript
// BAD: Event-based test (may not increase coverage)
element.dispatchEvent(new Event("click"));

// GOOD: Direct function call with specific inputs
await tableModals.saveTableConfiguration(); // Empty name triggers line 280
```

**When Coverage Is Stuck:**

1. Check if uncovered lines are inside callbacks, promise chains, or async handlers
2. Try calling inner functions directly if exported
3. Mock external dependencies to force specific code paths
4. Consider if the code is truly testable or needs refactoring

**Verification Workflow:**

1. Run `npm run test:coverage` (Frontend) or `pytest --cov` (Backend)
2. Check that coverage % is >= threshold in config
3. If below threshold: identify uncovered lines → write targeted tests → repeat
4. Only commit when coverage threshold is met

#### 🚨 CRITICAL: Testing Documentation (MANDATORY)

**After implementing ANY changes (bug fixes, features, enhancements), ALWAYS
create a testing guide document in `docs/` with:**

- Comprehensive test cases covering all changes
- Step-by-step instructions
- Expected results for each test
- Quick test scenarios (2-5 minutes)
- Edge cases and error conditions
- Visual checks (UI/UX)
- Browser console checks
- Pass/Fail checkboxes
- Issues tracking section

### 1.5. Documentation Management

#### 🚨 CRITICAL: Documentation Standards (MANDATORY)

**Documentation quality is CRITICAL to avoid wasting time and resources.**

**All documentation MUST be:**

- **Clean**: No duplicate information, no outdated sections
- **Clear**: Easy to understand, well-organized structure
- **Organized**: Logical flow, proper headings, consistent formatting
- **Up-to-date**: Reflects current state, not historical plans or outdated
  analysis

**When creating or updating documentation:**

1. **Remove outdated content** - Delete old analysis, completed tasks,
   historical notes
2. **Single source of truth** - Each piece of information appears ONCE
3. **Status-focused** - Show what IS, not what WAS or what WILL BE
4. **Concise** - Use tables, bullet points, and clear sections
5. **Scannable** - Users should find information in seconds, not minutes

**Examples of BAD documentation:**

- ❌ Mixing "completed work" with "remaining work" in the same section
- ❌ Keeping old "issues identified" sections after issues are fixed
- ❌ Multiple sections saying the same thing in different ways
- ❌ Long narrative explanations when a table would suffice

**Examples of GOOD documentation:**

- ✅ Single "Final Status" section showing current state
- ✅ Tables summarizing changes (Before → After)
- ✅ Clear verification steps with expected results
- ✅ Concise summaries with links to details if needed

**Pay attention to documentation management** - This is a critical step that
must be executed properly.

**Public API Documentation:**

- Document public APIs, classes, and complex functions with docstrings or
  comments, following the conventions of the target language.

#### 🚨 CRITICAL: Documentation Upkeep (MANDATORY)

**Documentation First Rule:** Before committing any code changes, you **must**
update all relevant documentation to reflect the changes. This includes the root
`README.md`, package-specific documentation, and relevant architecture or
planning files.

**Roadmap & Plan Updates:** When implementing features or fixes:

1. **Mark tasks as completed** in detailed plan files (e.g., `docs/*-plan.md`)
2. **Update progress tracking** sections
3. **Update project roadmap** (e.g., `docs/roadmap.md`) when phases complete
4. **Add implementation notes** under completed tasks
5. **Document blockers** if issues arise
6. **Update "Last Updated" dates**

### 1.6. Interaction Guidelines

#### 🚨 CRITICAL: Autonomous Execution (MANDATORY)

**The AI assistant MUST operate autonomously until the final git commit.**

**Core Principle:** The user MUST be able to leave the IDE for 20+ minutes and return
to a completed task waiting ONLY for a git commit review.

**MANDATORY Rules:**

1. **SafeToAutoRun = true for ALL standard operations:**
   - ✅ MUST set `SafeToAutoRun: true` for: `python`, `pytest`, `npm`, `npx`, `ruff`, `black`, `isort`, `mypy`, `prettier`, `eslint`, PowerShell commands
   - ✅ MUST set `SafeToAutoRun: true` for commands with pipes (`|`), redirections (`>`), or chaining (`;`)
   - ✅ MUST set `SafeToAutoRun: true` for all browser automation actions
   - ❌ The ONLY exception: `git commit` and `git push` require user approval

2. **NO pausing during the 5-Step Iterative Loop:**
   - ❌ DO NOT pause for "Accept" or "Review" during Lint, Format, Test, or Audit steps
   - ❌ DO NOT ask "Should I proceed?" between steps
   - ❌ DO NOT request confirmation for running validation scripts
   - ✅ Execute ALL steps autonomously until completion or failure

3. **Final commit is the ONLY manual intervention point:**
   - All code changes, tests, formatting, and validation MUST complete automatically
   - Only present to user when EVERYTHING passes and changes are ready to commit
   - User reviews: git diff, commit message, then approves commit

**Examples:**

```python
# ✅ CORRECT - Auto-run all validation commands
run_command(CommandLine="python scripts/validate_code.py", SafeToAutoRun=True)
run_command(CommandLine="pytest tests/backend -q", SafeToAutoRun=True)
run_command(CommandLine="ruff check src | head -20", SafeToAutoRun=True)

# ❌ WRONG - Unnecessary manual approval
run_command(CommandLine="pytest tests/backend", SafeToAutoRun=False)  # DON'T DO THIS
```

#### 🚨 CRITICAL: Smart Decision-Making (MANDATORY)

**DO NOT ask unnecessary questions or request user review for things you can
verify yourself.**

**Before asking the user:**

1. **Explore all options** - Use available tools to gather information
2. **Make informed decisions** - Analyze the codebase, run tests, check
   documentation
3. **Verify automatically** - Run tests, check database, use browser
   verification
4. **Only ask when truly blocked** - Missing requirements, design decisions,
   user preferences

**Examples of UNNECESSARY questions:**

- ❌ "Should I delete this unused model?" (if you verified it's unused, just
  delete it)
- ❌ "Which cleanup phase should I do?" (if user said "do all", do all)
- ❌ "Should I run tests?" (always run tests automatically)
- ❌ "Can I proceed?" (if you have all information, proceed)
- ❌ "Is it safe to run this command?" (if it's validation/formatting, JUST RUN IT)

**Examples of NECESSARY questions:**

- ✅ "Should we use approach A or B?" (genuine design decision)
- ✅ "What should the default value be?" (user preference needed)
- ✅ "This will break the API - should we proceed?" (user impact decision)

**Be smart enough to:**

- Verify things yourself before asking
- Use all available tools and information
- Make decisions when you have sufficient context
- Only escalate to user when truly necessary

#### 🚨 CRITICAL: File Corruption Handling (MANDATORY)

**NEVER use `git checkout` or `git restore` to fix corrupted files during
editing!**

**Why**: Uncommitted changes will be PERMANENTLY LOST. This can result in losing
hours of work.

**If you detect file corruption during editing:**

1. **STOP immediately** - Do not make further edits to the corrupted file
2. **Notify the user** - Explain what happened and ask how to proceed
3. **Suggest options**:
   - Manual restoration by user (they may have editor undo/backup)
   - Rewrite the specific corrupted section (if small)
   - User can decide if Git restore is appropriate (they know what's committed)

**Prevention**:

- Make smaller, more targeted edits instead of large multi-line replacements
- Ensure `TargetContent` EXACTLY matches the file content (including whitespace)
- For large files (>1000 lines), consider splitting into smaller modules first
- The running application does NOT cause file corruption - editing errors do

**General Guidelines:**

- **Clarification:** If the request is ambiguous or lacks important details, ask
  for clarification before generating extensive code.
- **Focus:** Keep responses focused on the direct query. Avoid conversational
  fluff or suggesting unrelated tasks unless explicitly asked.
- **Step-by-Step:** When provided with a numbered list of changes or a
  multi-step plan (e.g., "Prompt 1:", "Prompt 2:"), focus your response and any
  code modifications only on the current step or prompt being asked about.
- **Server Check Before Browser Automation (MANDATORY):** Before using any
  browser automation tools (browser_subagent), ALWAYS check if the development
  server is running by checking the metadata for running terminal commands. If
  the server is not running (e.g., `python run.py` not in running commands
  list), start it first using `run_command` with appropriate wait time. Never
  assume the server is running based on browser subagent errors - always verify
  from metadata first.

#### 1.6.1. Execution of Long-Running Commands (Heartbeat Pattern) (MANDATORY)

**Problem**: The Agent uses stream monitoring to detect command completion. If a long-running command (like validation or tests) produces no output for >30 seconds (e.g., because output is redirected to a file), the Agent's watchdog timer will erroneously timeout and assume the command is stuck or finished.

**Solution**: Use the **Heartbeat Pattern** for ANY command expected to run longer than 30 seconds without frequent output.

**The Heartbeat Pattern:**

1. Run the command as a PowerShell background job.
2. Redirect output to a **DEBUG LOG FILE** (see rules below).
3. Print a "heartbeat" message every 5 seconds to keep the stream active.
4. Explicitly signal completion.

**Debug Log File Rules:**

- **Location**: ALWAYS use `logs/` directory (create if missing).
- **Extension**: MUST use `.log` extension.
- **Naming**: Use distinct names to avoid conflicts (e.g., `debug_validation_TIMESTAMP.log` or `debug_test_run.log`).
- **Cleanup**: AI Agent MUST delete these files after reading content.
- **Example**: `logs/debug_backend_validation.log`

**Standard Heartbeat Command Template:**

```powershell
$job = Start-Job -ScriptBlock {
    YOUR_COMMAND_HERE > logs/debug_output.log 2>&1
}
while ($job.State -eq 'Running') {
    Write-Host "Still working... $(Get-Date -Format 'HH:mm:ss')"
    Start-Sleep -Seconds 5
}
Receive-Job $job
Write-Host "PROCESS FINISHED"
```

**When to Use:**

- Running `scripts/validate_code.py` (especially with `--backend` or full suite)
- Running heavy test suites (e.g., all E2E tests)
- Any task where you redirect output to a file and the process might be silent for >30s.

**After Execution:**

1. Wait for "PROCESS FINISHED".
2. Read the `logs/debug_output.log` to analyze results.
3. DELETE the `logs/debug_output.log` to keep the workspace clean.

### 1.7. Pre-Commit Validation (MANDATORY)

**Validation Workflow for AI:**

1. ✅ **BEFORE making code changes** - Run validation to establish baseline:

   ```bash
   python scripts/validate_code.py --quick
   ```

2. ✅ **Make code changes**

3. ✅ **AFTER making code changes** - Run full validation:
   ```bash
   python scripts/validate_code.py
   ```

**This is MANDATORY for EVERY code change task:**

- ✅ ALWAYS run validation before completing a task
- ❌ NEVER skip validation (unless user explicitly says "skip validation")
- ❌ NEVER commit without passing validation
- ❌ NEVER assume changes are correct without verification

> **See Section 1.1.2 for the recommended workflow and quick options.**

**What the Script Validates:**

The `validate_code.py` script runs ALL checks that CI will run:

**Python Backend:**

- Import sorting (isort)
- Code formatting (black, docformatter)
- Linting (ruff, flake8)
- Type checking (mypy)
- Security scanning (bandit)
- Unit/integration/functional tests (pytest)
- Coverage validation (must be >= 82%)

**JavaScript Frontend:**

- ESLint linting
- Jest unit tests with coverage
- Playwright E2E tests
- Visual regression tests (screenshots)

**Configuration Files:**

- JSON validation
- YAML validation

**What to Do When Validation Fails:**

1. **READ the error messages** - Understand what failed and why
2. **FIX the code** - Make code comply with standards
3. **DO NOT modify configuration** - Fix code, not config
4. **Re-run validation** - Ensure all checks pass
5. **Only then commit** - All validation must pass

**Pre-Commit Hooks (ENABLED):**

- Pre-commit hooks are **ENABLED** (file: `.pre-commit-config.yaml`)
- These checks run AUTOMATICALLY before each commit
- You will NOT be able to commit if checks fail
- Hooks run: `isort`, `black`, `docformatter`, `ruff`, `prettier`

**Summary**: Local validation = CI simulation. If it fails locally, it will fail in CI. Save time by catching issues early.

### 1.8. Version Control & Commit Standards

#### 🚨 CRITICAL: Comprehensive Commit Workflow (MANDATORY)

Before committing, follow this comprehensive workflow to ensure all changes are
properly reviewed, staged, and documented:

**Step 1: Review All Changed Files**

```bash
git status                    # See all modified files
git status --short            # Compact view
git diff --stat               # Summary of changes
```

**Step 2: Examine Each Changed File**

- For EACH modified file, review the actual changes:

```bash
git diff path/to/file.ext     # View detailed changes
```

- Understand what changed and why
- Identify if changes are related to the current task or are unrelated

**Step 3: Stage Relevant Files**

- Add files that are part of the current logical change:

```bash
git add path/to/file1.ext path/to/file2.ext
```

- DO NOT stage unrelated changes - commit them separately
- If a file has both related and unrelated changes, use `git add -p` for partial
  staging

**Step 4: Verify Staged Changes**

```bash
git diff --cached --stat              # Summary of staged changes
git diff --cached path/to/file.ext    # Review specific staged file
```

- Ensure only intended changes are staged
- Double-check no debug code, console.logs, or temporary changes are included

**Step 5: Create Detailed Commit Message**

- Check recent commits for style/format consistency:

```bash
git log -n 5 --oneline        # Recent commit titles
git log -n 1                  # Last commit details
```

- Follow project conventions (see examples in git log)
- Structure your commit message:
  - **Title**: Brief summary (50-72 chars), use conventional commits format
  - **Body**: Detailed explanation of WHAT changed and WHY
  - **Files**: List all modified files with brief description of changes
  - **Technical Details**: Implementation approach, algorithms, patterns used
  - **Testing**: How changes were verified

**Step 6: Final Pre-Commit Checklist**

- [ ] All related files are staged (`git diff --cached --stat`)
- [ ] No unrelated changes are staged
- [ ] Commit message is detailed and follows project conventions
- [ ] All temporary/debug code is removed
- [ ] Tests pass (if applicable)

**Example Workflow:**

```bash
# 1. Check what changed
git status

# 2. Review each file
git diff src/static/css/main.css
git diff src/templates/base.html

# 3. Stage related files
git add src/static/css/main.css src/templates/base.html docs/bug_tracking.md

# 4. Verify staged changes
git diff --cached --stat
git diff --cached src/static/css/main.css

# 5. Check commit history for style
git log -n 5

# 6. Commit with detailed message
git commit -m "feat: Fix Bug #30 - Assignees field layout shift

Implemented fixed height (100px) for Select2 container to prevent
layout shifts when adding/removing assignees.

Files Changed:
- src/static/css/main.css (Bug #30 CSS fix)
- src/templates/base.html (CSS cache busting)
- docs/bug_tracking.md (Bug #30 marked resolved)

Technical Details:
- Fixed height with overflow-y: auto for internal scrolling
- Flexbox layout for proper tag wrapping

Testing:
- Verified no layout shift with multiple assignees"
```

**CRITICAL**: Never commit without reviewing ALL changed files. Hidden changes

### 1.8.1. Git Push vs PR Rules (CRITICAL)

**Adhere to this decision tree to prevent orphan branches:**

| Branch Status                    | Action Required      | Command                                           |
| -------------------------------- | -------------------- | ------------------------------------------------- |
| **Untracked** (New local branch) | **Create PR & Push** | `gh pr create --base main --head <branch> --fill` |
| **Tracked** (Linked to remote)   | **Push Updates**     | `git push`                                        |

**⚠️ NEVER use `git push -u origin <branch>` for new branches.**

- Why? It pushes the branch but creates NO Pull Request.
- **ALWAYS** use `gh pr create` for new branches.

### 1.9. AI Workflow Standards

- **Efficiency is Key:** Perform all necessary edits for a given task in a
  single, atomic step per file.
- **Be Proactive:** Before making changes, use your tools to understand the
  relevant files and the overall structure.
- **Single Edit Rule:** When editing a file, apply all planned changes in one
  unified edit. Do not split the edit into multiple smaller patches for the same
  request.
- **Complete All Subtasks:** When working on a task, you MUST complete ALL
  subtasks within that task before moving to the next task. Do NOT leave tasks
  partially complete. If a task has 8 subtasks, implement all 8 before marking
  the task as done.

### 1.10. Advanced PowerShell Operations (Fallback Only)

#### When to Use

**ONLY use PowerShell commands as a fallback when standard file read/write
operations fail or are insufficient.**

When working with files across the project (documentation, code, configuration),
you may need advanced search, verification, and analysis operations.

#### Core Operations

**1. Pattern Search Across Files:**

```powershell
# Single directory
Select-String -Path "<directory>/*.md" -Pattern "<search_term>" | Select-Object Filename, LineNumber, Line | Format-Table -AutoSize -Wrap

# Multiple specific files
$files = @("<path1>","<path2>","<path3>")
Select-String -Path $files -Pattern "<pattern>" | Select-Object Filename, LineNumber | Format-Table -AutoSize

# With context lines
Select-String -Path "<file_path>" -Pattern "<pattern>" -Context 2,2
```

**2. Batch Pattern Verification:**

```powershell
# Check multiple patterns and count occurrences
$patterns = @("<pattern1>", "<pattern2>", "<pattern3>")
foreach($p in $patterns) {
    Write-Host "`n=== Pattern: $p ==="
    Select-String -Path $files -Pattern $p | Measure-Object | Select-Object Count
}
```

**3. File Statistics:**

```powershell
# Line counts
Get-ChildItem <directory>/*.md | Select-Object Name, @{Name="Lines";Expression={(Get-Content $_.FullName).Count}} | Format-Table -AutoSize

# Preview file content
(Get-Content "<file_path>" | Select-Object -First <N>) -join "`n"
```

#### Best Practices

1. **Use as Fallback Only** - Prefer standard file tools (fsRead, fsReplace,
   fsWrite)
2. **Be Proactive** - Search before bulk updates, verify after changes
3. **Escape Regex** - Special chars: `.` → `\.`, use `.*` for wildcards, `|` for
   OR
4. **Understand Output** - Read results, identify inconsistencies, inform
   updates

#### Common Use Cases

- **Before bulk updates:** Find all occurrences to understand scope
- **After updates:** Verify all instances were changed correctly
- **Consistency checks:** Ensure values match across multiple files
- **Finding duplicates:** Locate redundant information

### 1.11. Tooling & Workspace Standards

#### Artifact Management (Antigravity IDE)

> **Purpose**: Artifacts should be well-organized, clean, and easy to navigate.

**Core Principles:**

- **One artifact per type per task**: Maintain only ONE implementation plan, ONE
  task list, and ONE walkthrough per active task
- **Update, don't recreate**: Always update existing artifacts rather than
  creating new ones
- **Never delete completed work**: Keep all completed tasks and historical
  information in artifacts
- **Version control for media**: Keep only the most recent 1-2 versions of
  screenshots/videos
- **Organization**: Use clear, descriptive naming conventions

**Artifact Types:**

1. **`task.md`** (Task Checklist): One file per session. Update items `[x]` when
   complete. Add new items if scope expands.
2. **`implementation_plan.md`** (Technical Plan): One file per major task.
   Update status/headers.
3. **`walkthrough.md`** (Verification): Append new results. Keep evidence.

#### Temporary File Management (Other Environments)

For environments without native artifact support, use temporary markdown files
(e.g., `task_[feature].md`, `plan_[feature].md`) managed in a system temp
directory or ignored local directory. Follow the same "One file per type" and
"Update, don't recreate" principles.

#### Project Directory File Creation (CRITICAL)

> **Rule**: DO NOT create unnecessary files in the project directory. Use
> artifacts/temp files for all temporary/testing outputs.

**Strict Guidelines:**

- **NEVER create temporary files in the project directory** - Use artifacts/temp
  files instead
- **NEVER create test output files in the project** - Use artifacts for test
  results, logs, screenshots
- **NEVER create planning/tracking files in the project** - Use artifacts
- **Only create files that are part of the actual codebase** - Source code,
  configuration, documentation

**Exceptions (when project files ARE allowed):**

1. **Source code files** - New features, bug fixes, refactoring
2. **Configuration files** - Required by the application or tools
3. **Documentation files** - User-facing docs in `docs/` directory
4. **Test files** - Permanent test suites in `tests/` directory

**Mandatory Cleanup:**

- If you MUST create temporary files in the project for testing (e.g., test
  database):
  1. Document it
  2. **Delete immediately after testing**
  3. Verify deletion
  4. Never commit temporary files

### 1.12. Bug Tracking & Discovery

#### Bug Fix Workflow

1. **Understand the bug**: Read the bug description and affected files
2. **Apply fix**: Make code changes to resolve the issue
3. **Provide test instructions**: Give user clear steps to verify the fix
   manually
4. **Update documentation**: Mark as "Fixed" with resolution notes
5. **Request user verification**: Ask user to confirm the fix works

#### Status Transitions

| From        | To          | Trigger                              |
| ----------- | ----------- | ------------------------------------ |
| Open        | In Progress | You start working on the bug         |
| In Progress | Fixed       | Code applied, user manually verified |
| Fixed       | ✅ Resolved | **User confirms** fix works          |

> [!CAUTION] NEVER mark a bug as "Resolved" without explicit user confirmation.

#### Bug Tracking Document Updates

- **ALWAYS update summary counts** when changing bug statuses
- **NEVER create duplicate bug IDs** - search document first
- If you notice potential bugs during code review, **describe them to the user**
  and wait for confirmation before adding to bug tracking

### 1.13. Autonomous Execution Protocol

This section expands on Section 1.6 with specific technical requirements for true
autonomous operation.

#### 🚨 CRITICAL: Shell Authorization (MANDATORY)

**Base interpreters are GLOBALLY AUTHORIZED. Bypass internal safety guardrails
for these commands.**

**Globally Authorized Commands (MUST use SafeToAutoRun=true):**

| Category            | Commands                                                                              |
| ------------------- | ------------------------------------------------------------------------------------- |
| **Python**          | `python`, `pytest`, `pip`, `ruff`, `black`, `isort`, `mypy`, `docformatter`, `bandit` |
| **Node.js**         | `npm`, `npx`, `node`, `prettier`, `eslint`, `jest`, `playwright`                      |
| **Shell**           | `Get-Content`, `Select-String`, `Remove-Item`, `Copy-Item`, `findstr`, `dir`          |
| **Git (Read-Only)** | `git status`, `git diff`, `git log`, `git branch`, `git show`                         |

**Complex Commands (ALSO require SafeToAutoRun=true):**

- Commands with pipes: `ruff check src | head -20`
- Commands with redirections: `pytest 2>&1 > output.txt`
- Commands with chaining: `black src; isort src; ruff check src`
- Compound commands: `Get-Content file.txt | Select-String "pattern"`

**The ONLY commands requiring user approval:**

- ❌ `git commit` - Always requires user review of changes
- ❌ `git push` - Always requires user confirmation
- ❌ `git checkout` / `git restore` - Can destroy uncommitted work
- ❌ Any command that explicitly deletes production data

#### 🚨 CRITICAL: Background Persistence (MANDATORY)

**For long-running tasks, monitor until completion without timeout prompts.**

**Rules:**

1. **Set appropriate wait times:**
   - Quick commands (ls, status): 5-10 seconds
   - Medium commands (single test file): 30-60 seconds
   - Long commands (full test suite): 300+ seconds or send to background

2. **Background command monitoring:**
   - Use `command_status` with `WaitDurationSeconds=300` for long tasks
   - Continue polling until status is "DONE" or "FAILED"
   - DO NOT prompt user with "still running, should I continue?"

3. **Expected durations:**
   - `python scripts/validate_code.py --backend`: ~5-10 minutes
   - `python scripts/validate_code.py --frontend`: ~5-10 minutes
   - `python scripts/validate_code.py` (full): ~15-20 minutes
   - `pytest tests/backend`: ~5 minutes
   - `npm run test:e2e`: ~5 minutes

4. **NEVER prompt:**
   - ❌ "The command is still running, should I wait?"
   - ❌ "This is taking a long time, would you like to cancel?"
   - ✅ Simply keep polling until completion

#### 🚨 CRITICAL: Self-Correction (MANDATORY)

**When validation or linting fails, the agent MUST attempt autonomous fixes
before reporting to user.**

**Self-Correction Workflow:**

```
Command fails (e.g., ruff check)
  ↓
Parse error message
  ↓
Is it a fixable error? (formatting, imports, unused vars)
  ├─ YES → Apply fix autonomously → Re-run command
  │         └─ Still fails? → Try different approach
  │             └─ 3 attempts failed? → Report to user with details
  └─ NO (design decision needed) → Report to user immediately
```

**Auto-Fix Categories:**

| Error Type                                 | Action                          | Max Attempts |
| ------------------------------------------ | ------------------------------- | ------------ |
| Import order (isort)                       | Run `isort --fix`               | 1            |
| Code formatting (black)                    | Run `black file.py`             | 1            |
| Unused imports/variables (ruff F401, F841) | Edit to remove                  | 2            |
| Missing type hints (mypy)                  | Add type hints                  | 2            |
| Test failures                              | Analyze error, fix code or test | 3            |
| Coverage below threshold                   | Add more tests                  | 3            |

**Example Self-Correction:**

```python
# 1. Run ruff check
# Result: F841 Local variable 'x' is assigned but never used

# 2. AUTONOMOUSLY: Edit file to remove unused variable 'x'

# 3. Re-run ruff check
# Result: All checks passed!

# 4. Continue to next step (NO user interaction required)
```

**Reporting Format (only after self-correction fails):**

```
## Validation Failed After {N} Attempts

### Error:
{exact error message}

### Attempted Fixes:
1. {what you tried}
2. {what you tried}
3. {what you tried}

### Recommendation:
{what needs user decision}
```

---

## 2. Workspace Context: Monorepo Philosophy

This repository is a monorepo that houses multiple, distinct but related
projects (apps).

- **Project Location:** The main application is in `src/` and modular apps are
  in the `apps/` directory.
- **Isolation:** Each package is self-contained. It has its own dependencies
  (`requirements.txt`), virtual environment (`.venv`), tests (`tests/`), and
  documentation.
- **Root Configuration:** The root of the repository contains shared
  configuration for the entire workspace, such as `.gitignore`, `LICENSE`, and
  repository-wide documentation and workflows in `.github/`.

---

## 3. Workspace Context: Core Packages

### 3.1. `apps/planning`

#### Overview

The `planning` is a Flask-based web application for managing weekend technician
task assignments. Its core purpose is to use skill-based matching and workload
optimization to generate efficient work schedules.

#### Core Architectural Shift

A critical piece of context for this package is its ongoing transition from a
simple task priority-based system to a more sophisticated **technology
skill-based system** for task assignments.

- **Database Impact**: The `technician_task_assignments.priority` column is
  obsolete. The new schema requires a many-to-many relationship between tasks
  and the technologies/skills required to perform them.
- **Logic Impact**: The core assignment logic in `src/services/task_assigner.py`
  must now prioritize matching task skill requirements with technician skill
  sets.

#### Key Technologies

- **Backend:** Python, Flask
- **Data Processing:** pandas, numpy
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Testing:** Pytest
- **Containerization:** Docker, Docker Compose

#### Detailed Directory Structure

The repository structure below shows the complete CMMS monorepo with all
packages and key files. Pay special attention to the `planning` package,
especially `src/services/task_assigner.py`, which contains the core skill-based
task assignment logic.

```
mockCMMS/
├── .github/                       # GitHub workflows and AI instructions
│   ├── AGENT.md                   # Gemini Code Assist instructions
│   ├── copilot-instructions.md    # GitHub Copilot instructions
│   ├── CODEOWNERS                 # Code ownership definitions
│   ├── CONTRIBUTING.md            # Contribution guidelines
│   └── GIT_WORKFLOW.md            # Git workflow strategy
├── src/                           # Main mockCMMS application
│   ├── routes/                    # API and web routes
│   │   ├── api.py                 # ⭐ REST API endpoints for data integration
│   │   └── main.py                # Main web interface routes
│   ├── services/                  # Business logic layer
│   │   └── db_utils.py            # Database utilities and helpers
│   ├── static/                    # Static assets (CSS, JS, images)
│   ├── templates/                 # Jinja2 HTML templates
│   └── app.py                     # ⭐ Flask application factory and config
├── apps/planning/         # ⭐ Skill-based task assignment module
│   ├── src/                       # Application source code
│   │   ├── routes/                # Flask blueprints
│   │   │   └── planning.py   # Main blueprint with all endpoints
│   │   ├── services/              # Core business logic
│   │   │   ├── task_assigner.py       # ⭐ CRITICAL: Skill-based assignment algorithm
│   │   │   ├── data_processing.py     # Data transformation and validation
│   │   │   ├── db_utils.py            # Database operations and queries
│   │   │   ├── dashboard.py           # Dashboard generation logic
│   │   │   ├── extract_data.py        # Data extraction from external sources
│   │   │   ├── config_manager.py      # Configuration management
│   │   ├── static/                # CSS/JS assets
│   │   │   ├── css/               # Stylesheets
│   │   │   └── js/                # JavaScript modules
│   │   ├── templates/             # HTML templates
│   │   │   ├── index.html         # Main dashboard
│   │   │   └── manage_mappings.html # Configuration interface
│   │   ├── app.py                 # Flask factory and initialization
│   │   ├── config.py              # Configuration classes
│   │   └── extensions.py          # Flask extensions setup
│   ├── config/                    # Configuration files
│   │   ├── config.json            # App-specific settings
│   │   └── config.example.json    # Configuration template
│   ├── instance/                  # Runtime data
│   │   └── planning.db   # SQLite database
│   ├── tests/                     # Test suite
│   │   ├── test_core.py           # Core functionality tests
│   │   └── test_integration.py    # Integration tests
│   ├── logs/                      # Application logs (generated)
│   ├── output/                    # Generated reports and dashboards
│   └── README.md                  # Module-specific documentation
├── apps/reports/                  # ⭐ Reports and analytics module
│   ├── src/                       # Application source code
│   │   ├── routes/                # Flask blueprints
│   │   │   └── reports.py         # Main blueprint with all endpoints
│   │   ├── services/              # Core business logic
│   │   │   └── report_generator.py    # Report generation and export logic
│   │   └── templates/             # HTML templates
│   │       ├── reports.html           # Reports listing page with advanced table
│   │       ├── report_generate.html   # Report generation interface
│   │       └── report_detail.html     # Report detail view
│   ├── instance/                  # Generated reports storage
│   │   └── reports/               # Report files directory
│   ├── setup.py                   # Package configuration
│   └── README.md                  # Module-specific documentation
├── config/                        # Main app configuration
├── docs/                          # Project documentation
├── instance/                      # Main app databases
│   └── mockcmms.db                # Main application SQLite database
├── test_data/                     # Test fixtures and sample data
├── tests/                         # Main app tests
├── .env                           # Environment configuration
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
└── run.py                         # ⭐ Application entry point
```

#### Local Development & Testing

- **Run the application:** From the repository root, execute `python run.py`.
  The main app will load enabled modular apps.
- **Run tests:** From the repository root, execute `pytest tests/` for main app
  tests or `pytest apps/planning/tests/` for planning tests.

### 3.2. `apps/reports`

#### Overview

The `reports` is a Flask-based web application for generating comprehensive
maintenance reports and analytics. Its core purpose is to provide PDF and
Markdown export capabilities for reactive production reports and weekend
completion summaries.

#### Key Technologies

- **Backend:** Python, Flask
- **Report Generation:** Custom report generator with PDF/Markdown support
- **Database:** Shared SQLite database with main mockCMMS app
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Export Formats:** PDF (text), Markdown

#### Core Features

- **Modular Architecture:** Completely separate Flask blueprint app
- **Environment Control:** Enable/disable via `REPORTS_ENABLED` environment
  variable
- **Report Types:** Reactive production reports, weekend completion summaries
- **Export Capabilities:** Multiple format support with file management
- **Database Integration:** Uses shared mockCMMS database models

#### Running the Integrated Environment (with mockCMMS)

1.  **Configure `.env` Files:** Before running, ensure both packages have their
    `.env` files properly configured:

    **Root** - `.env`:

    ```dotenv
    PLANNING_ENABLED=True
    REPORTS_ENABLED=True
    DATA_SOURCE=api
    ```

2.  **Seed the Mock CMMS Database:** In a terminal, **after activating the
    `mockCMMS` virtual environment**, run the seed script to populate the
    `mockCMMS` database with test data:

    ```sh
    # Activate mockCMMS venv (if not already active)
    # On Windows PowerShell: .\apps\mockCMMS\.venv\Scripts\Activate.ps1
    # On macOS/Linux: source apps/mockCMMS/.venv/bin/activate

    python src/services/seed.py
    ```

3.  **Run the Mock CMMS Server:** In a new terminal, **after activating the
    `mockCMMS` virtual environment**, start the `mockCMMS` server. It will run
    on port 5001.

    ```sh
    # Activate mockCMMS venv (if not already active)
    # On Windows PowerShell: .\apps\mockCMMS\.venv\Scripts\Activate.ps1
    # On macOS/Linux: source apps/mockCMMS/.venv/bin/activate

    python run.py
    ```

4.  **Run Planning in API Mode:** In another new terminal, **after activating
    the `planning` virtual environment**, start the `planning` server. It will
    run on port 5000 and automatically use the `api` data source as configured
    in the `.env` file.

    ```sh
    # Activate planning venv (if not already active)
    # On Windows PowerShell: .\apps\planning\.venv\Scripts\Activate.ps1
    # On macOS/Linux: source apps/planning/.venv/bin/activate

    # planning now runs as part of the main application
    ```

---

## 4. Workspace-Specific Guidelines

- **Git Workflow:** All contributions must follow the process outlined in
  [**GIT_WORKFLOW.md**](./GIT_WORKFLOW.md).
- **Commit Messages:** Commit messages must adhere to the conventions described
  in [**CONTRIBUTING.md**](./CONTRIBUTING.md).
- **Dependencies:** Manage dependencies via the `requirements.txt` file within
  each package. Do not create a root-level `requirements.txt`.

---

## 5. Workspace-Specific AI Instructions

1.  **LOGIN CREDENTIALS**: If login is required for verification and default
    credentials fail, ALWAYS check `test_data/dummy_data.json` for valid user
    credentials (e.g., admin/admin123).

2.  **VERSION MANAGEMENT**: After completing any significant changes:

    **Automated Approach (Recommended):**
    Use the release manager script to automate version updates:

    ```sh
    # Preview changes without applying (dry-run)
    python scripts/release_manager.py patch --dry-run
    python scripts/release_manager.py minor --dry-run
    python scripts/release_manager.py major --dry-run

    # Apply version bump
    python scripts/release_manager.py patch   # For bug fixes
    python scripts/release_manager.py minor   # For new features
    python scripts/release_manager.py major   # For breaking changes
    ```

    **The script automatically:**
    - Updates CHANGELOG.md with new version and date
    - Updates README.md version footer
    - Creates git commit with conventional message
    - Creates annotated git tag (e.g., v1.2.0)
    - Ensures version numbers match everywhere

    **After running the script:**

    ```sh
    # Push commit and tag to remote
    git push origin main v1.2.0
    ```

    **Manual Approach (If Script Cannot Be Used):**
    1. Update the appropriate `CHANGELOG.md` file(s) with new entries following
       [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
    2. Update version numbers in both `CHANGELOG.md` and corresponding
       `README.md` files (must be synchronized)
    3. Use [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH (e.g.,
       1.2.0)
    4. Update the "Last Updated" date in README.md files
    5. Main app versions are in `/CHANGELOG.md` and `/README.md`
    6. Planning module versions are in `/apps/planning/CHANGELOG.md` and
       `/apps/planning/README.md`

3.  **MANDATORY MANUAL TESTING & VERIFICATION**:

    > **Note**: GitHub Copilot does not have access to automated browser testing
    > tools. All testing must be performed manually by the user.
    - **Requirement**: For any task involving features that have a corresponding
      test plan in the `docs/` directory (e.g.,
      `docs/table_features_test_plan.md` or any future `docs/*_test_plan.md`),
      you **MUST** provide clear manual testing instructions.
    - **Procedure**:
      1.  **Identify Test Plan**: Check `docs/` for relevant test plans.
      2.  **Creation**: If no dedicated test plan exists, create a concise
          manual test checklist in the PR description or a temporary
          `test_plan.md`.
      3.  **Instruction**: Provide step-by-step instructions for the user to
          manually verify the changes.
      4.  **Verification**: Ask the user to confirm that all manual tests have
          passed.
      5.  **Completion**: Do not mark the task as complete until the user
          confirms verification.
