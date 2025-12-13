# AI Agent Guide - Code Quality Audit

**Created:** December 13, 2025  
**Last Updated:** December 13, 2025  
**Purpose:** AI prompts for all 49 tasks in core_code_quality_plan.md

---

## 📚 Quick Links

**Related Documentation:**
- 📋 [core_code_quality_plan.md](core_code_quality_plan.md) - The audit structure (49 tasks, 6 phases)
- 🗓️ [IMPLEMENTATION_PRIORITY_GUIDE.md](IMPLEMENTATION_PRIORITY_GUIDE.md) - Overall timeline (7 weeks)
- 🗺️ [mockCMMS_roadmap.md](mockCMMS_roadmap.md) - Strategic vision and standards
- ✅ [comprehensive_testing_plan.md](comprehensive_testing_plan.md) - Testing foundation (210 tests complete)

**Update After Each Task:**
- ✏️ Mark `[x]` in [core_code_quality_plan.md](core_code_quality_plan.md) for completed tasks
- 📝 Add completion notes with date and issue count
- 🔄 Update "ACTIVE WORK" in [mockCMMS_roadmap.md](mockCMMS_roadmap.md) when phases complete

---

## 📋 Overview

This guide provides ready-to-use prompts for AI assistants working on the mockCMMS code quality audit. Each prompt corresponds to a task in `core_code_quality_plan.md`.

**Structure:** 49 tasks across 6 phases
- **Phase 1:** Python Backend (6 tasks)
- **Phase 2:** JavaScript Frontend (13 tasks)
- **Phase 3:** CSS Styling (3 tasks)
- **Phase 4:** HTML Templates (16 tasks)
- **Phase 5:** Root-Level Files (7 tasks)
- **Phase 6:** Cross-Cutting Concerns (4 tasks)

**Workflow per task:** Lint → Format → Test → Manual Audit → Loop or Commit

---

## Phase 1: Python Backend Analysis (6 tasks)

### Task 1.1: API Routes (`src/routes/api.py`)

```
I'm on Week 3, Phase 1, Task 1.1 of the mockCMMS code quality audit.

Task: Audit src/routes/api.py using the 5-step iterative loop

Please:

**Step 1: Format/Lint Check**
- Run: flake8 src/routes/api.py
- Fix any problems found
- Proceed to Step 2

**Step 2: Auto-Formatting**
- Run: black src/routes/api.py
- Review changes
- Proceed to Step 3

**Step 3: Functional Testing**
- Run: pytest tests/
- Verify all 210 tests pass
- ✅ Checkpoint: After this step, linting/formatting/functionality should all pass

**Step 4: Manual Audit**
Focus on logic and architecture (not style):
- [ ] Verify RESTful conventions (proper HTTP methods, status codes)
- [ ] Check input validation and sanitization
- [ ] Review error responses and status codes
- [ ] Ensure proper authentication/authorization
- [ ] Check for duplicate code across endpoints
- [ ] Verify proper use of Flask patterns
- [ ] Review database query efficiency
- [ ] Check for SQL injection vulnerabilities

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- Document what was changed and why
- 🔄 Loop back to Step 1 and repeat until file is perfect

If Step 4 resulted in NO modifications:
- Mark task as COMPLETE ✅
- Commit with message: `refactor(api): audit and improve api.py [Phase 1.1]`
- Update [core_code_quality_plan.md](core_code_quality_plan.md): Mark Task 1.1 [x]
- Move to Task 1.2

Show me your findings and proposed changes before implementing.
```

---

### Task 1.2: Web Routes (`src/routes/main.py`)

```
I'm on Week 3, Phase 1, Task 1.2 of the mockCMMS code quality audit.

Task: Audit src/routes/main.py using the 5-step iterative loop

Please:

**Step 1: Format/Lint Check**
- Run: flake8 src/routes/main.py
- Fix any problems found
- Proceed to Step 2

**Step 2: Auto-Formatting**
- Run: black src/routes/main.py
- Review changes
- Proceed to Step 3

**Step 3: Functional Testing**
- Run: pytest tests/
- Verify all 210 tests pass
- ✅ Checkpoint: After this step, linting/formatting/functionality should all pass

**Step 4: Manual Audit**
Focus on logic and architecture:
- [ ] Review route organization and naming
- [ ] Check form handling and validation
- [ ] Verify proper use of flash messages
- [ ] Review redirect logic and status codes
- [ ] Check for duplicate code across routes
- [ ] Verify proper template rendering
- [ ] Review session management
- [ ] Check authorization on protected routes

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- Document what was changed and why
- 🔄 Loop back to Step 1 and repeat until file is perfect

If Step 4 resulted in NO modifications:
- Mark task as COMPLETE ✅
- Commit with message: `refactor(routes): audit and improve main.py [Phase 1.2]`
- Move to Task 1.3

Show me your findings and proposed changes before implementing.
```

---

### Task 1.3: Database Utilities (`src/services/db_utils.py`)

```
I'm on Week 3, Phase 1, Task 1.3 of the mockCMMS code quality audit.

Task: Audit src/services/db_utils.py using the 5-step iterative loop

Please:

**Step 1: Format/Lint Check**
- Run: flake8 src/services/db_utils.py
- Fix any problems found
- Proceed to Step 2

**Step 2: Auto-Formatting**
- Run: black src/services/db_utils.py
- Review changes
- Proceed to Step 3

**Step 3: Functional Testing**
- Run: pytest tests/
- Verify all 210 tests pass
- ✅ Checkpoint: After this step, linting/formatting/functionality should all pass

**Step 4: Manual Audit**
Focus on database logic:
- [ ] Review model definitions and relationships
- [ ] Check for proper use of SQLAlchemy patterns
- [ ] Verify cascade delete configurations
- [ ] Review index definitions for performance
- [ ] Check for N+1 query problems
- [ ] Verify proper use of transactions
- [ ] Review password hashing implementation
- [ ] Check model method implementations

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- Document what was changed and why
- 🔄 Loop back to Step 1 and repeat until file is perfect

If Step 4 resulted in NO modifications:
- Mark task as COMPLETE ✅
- Commit with message: `refactor(db): audit and improve db_utils.py [Phase 1.3]`
- Move to Task 1.4

Show me your findings and proposed changes before implementing.
```

---

### Task 1.4: Database Seeding (`src/services/db_seeding.py`)

```
I'm on Week 3, Phase 1, Task 1.4 of the mockCMMS code quality audit.

Task: Audit src/services/db_seeding.py using the 5-step iterative loop

Please:

**Step 1: Format/Lint Check**
- Run: flake8 src/services/db_seeding.py
- Fix any problems found
- Proceed to Step 2

**Step 2: Auto-Formatting**
- Run: black src/services/db_seeding.py
- Review changes
- Proceed to Step 3

**Step 3: Functional Testing**
- Run: pytest tests/
- Verify all 210 tests pass
- ✅ Checkpoint: After this step, linting/formatting/functionality should all pass

**Step 4: Manual Audit**
Focus on seeding logic:
- [ ] Review function organization and naming
- [ ] Check for code duplication across seed functions
- [ ] Verify proper error handling
- [ ] Review data generation logic
- [ ] Check for hardcoded values that should be configurable
- [ ] Verify idempotency of seed operations
- [ ] Review function complexity
- [ ] Check docstring completeness

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- Document what was changed and why
- 🔄 Loop back to Step 1 and repeat until file is perfect

If Step 4 resulted in NO modifications:
- Mark task as COMPLETE ✅
- Commit with message: `refactor(db): audit and improve db_seeding.py [Phase 1.4]`
- Move to Task 1.5

Show me your findings and proposed changes before implementing.
```

---

### Task 1.5: Shift Utilities (`src/services/shift_utils.py`)

```
I'm on Week 3, Phase 1, Task 1.5 of the mockCMMS code quality audit.

Task: Audit src/services/shift_utils.py using the 5-step iterative loop

Please:

**Step 1: Format/Lint Check**
- Run: flake8 src/services/shift_utils.py
- Fix any problems found
- Proceed to Step 2

**Step 2: Auto-Formatting**
- Run: black src/services/shift_utils.py
- Review changes
- Proceed to Step 3

**Step 3: Functional Testing**
- Run: pytest tests/
- Verify all 210 tests pass
- ✅ Checkpoint: After this step, linting/formatting/functionality should all pass

**Step 4: Manual Audit**
Focus on shift calculation logic:
- [ ] Review shift rotation algorithm
- [ ] Check date/time handling
- [ ] Verify edge case handling (year boundaries, etc.)
- [ ] Review function naming and clarity
- [ ] Check for magic numbers (use constants)
- [ ] Verify docstring accuracy
- [ ] Review test coverage completeness
- [ ] Check for potential timezone issues

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- Document what was changed and why
- 🔄 Loop back to Step 1 and repeat until file is perfect

If Step 4 resulted in NO modifications:
- Mark task as COMPLETE ✅
- Commit with message: `refactor(services): audit and improve shift_utils.py [Phase 1.5]`
- Move to Task 1.6

Show me your findings and proposed changes before implementing.
```

---

### Task 1.6: Flask Application Factory (`src/app.py`)

```
I'm on Week 3, Phase 1, Task 1.6 of the mockCMMS code quality audit.

Task: Audit src/app.py using the 5-step iterative loop

Please:

**Step 1: Format/Lint Check**
- Run: flake8 src/app.py
- Fix any problems found
- Proceed to Step 2

**Step 2: Auto-Formatting**
- Run: black src/app.py
- Review changes
- Proceed to Step 3

**Step 3: Functional Testing**
- Run: pytest tests/
- Verify all 210 tests pass
- ✅ Checkpoint: After this step, linting/formatting/functionality should all pass

**Step 4: Manual Audit**
Focus on application factory pattern:
- [ ] Verify proper Flask factory pattern implementation
- [ ] Review configuration loading
- [ ] Check SECRET_KEY handling (must be from env)
- [ ] Verify database initialization
- [ ] Review blueprint registration logic
- [ ] Check error handler registration
- [ ] Verify logging configuration
- [ ] Review module loading for apps/planning and apps/reports

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- Document what was changed and why
- 🔄 Loop back to Step 1 and repeat until file is perfect

If Step 4 resulted in NO modifications:
- Mark task as COMPLETE ✅
- Commit with message: `refactor(app): audit and improve app.py [Phase 1.6]`
- Phase 1 COMPLETE - Move to Phase 2

Show me your findings and proposed changes before implementing.
```

---

## Phase 1 Final Verification

After all 6 tasks complete:
- [ ] Run full test suite: `pytest tests/` (all 210 tests must pass)
- [ ] Check coverage: `pytest --cov=src tests/` (maintain 82.99%+)
- [ ] Run pylint: `pylint src/` (maintain 9.15/10+)
- [ ] Verify application starts: `python run.py`
- [ ] Document findings in audit report
- [ ] Mark Phase 1 COMPLETE ✅

**Deliverable:** 6 commits, all Python backend files audited and improved


---

## Phase 2: JavaScript Frontend Analysis (13 tasks)

### Task 2.1: Advanced Table Core (`src/static/js/advanced-table/table-core.js`)

```
I'm on Week 3, Phase 2, Task 2.1 of the mockCMMS code quality audit.

Task: Audit table-core.js using the 5-step iterative loop

Please:

**Step 1: Format/Lint Check**
- Run: eslint src/static/js/advanced-table/table-core.js
- Fix any problems found
- Proceed to Step 2

**Step 2: Auto-Formatting**
- Run: prettier --write src/static/js/advanced-table/table-core.js
- Review changes
- Proceed to Step 3

**Step 3: Functional Testing**
- Load application in browser
- Test Advanced Table functionality
- Check browser console for errors
- ✅ Checkpoint: ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture:
- [ ] Review class structure and encapsulation
- [ ] Check for circular dependencies
- [ ] Verify proper initialization patterns
- [ ] Review event listener cleanup (memory leaks)
- [ ] Check naming conventions (camelCase)
- [ ] Remove console.log() statements
- [ ] Remove bug reference comments
- [ ] Add JSDoc comments for public methods
- [ ] Review error handling

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- Document what was changed and why
- 🔄 Loop back to Step 1 and repeat until file is perfect

If Step 4 resulted in NO modifications:
- Mark task as COMPLETE ✅
- Commit with message: `refactor(table): audit and improve table-core.js [Phase 2.1]`
- Move to Task 2.2

Show me your findings and proposed changes before implementing.
```

---

### Task 2.2: Table Initialization (`src/static/js/advanced-table/table-init.js`)

```
I'm on Week 3, Phase 2, Task 2.2 of the mockCMMS code quality audit.

Task: Audit table-init.js using the 5-step iterative loop

Please follow the same 5-step process as Task 2.1:
1. ESLint check
2. Prettier formatting
3. Browser testing
4. Manual audit focusing on:
   - [ ] Initialization logic clarity
   - [ ] Configuration validation
   - [ ] Error handling during init
   - [ ] Remove console.log()
   - [ ] Remove bug references
   - [ ] Add JSDoc comments
5. Document & loop or commit

Commit message: `refactor(table): audit and improve table-init.js [Phase 2.2]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.3: Table Rendering (`src/static/js/advanced-table/table-render.js`)

```
I'm on Week 3, Phase 2, Task 2.3 of the mockCMMS code quality audit.

Task: Audit table-render.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review HTML generation patterns
- [ ] Check for XSS vulnerabilities
- [ ] Verify proper escaping of user data
- [ ] Review template literal usage
- [ ] Check for duplicate rendering logic
- [ ] Verify accessibility (ARIA labels)
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-render.js [Phase 2.3]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.4: Table Data Operations (`src/static/js/advanced-table/table-data.js`)

```
I'm on Week 3, Phase 2, Task 2.4 of the mockCMMS code quality audit.

Task: Audit table-data.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review filtering logic efficiency
- [ ] Check sorting algorithm performance
- [ ] Verify pagination calculations
- [ ] Review data transformation logic
- [ ] Check for immutability violations
- [ ] Verify edge case handling (empty data, null values)
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-data.js [Phase 2.4]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.5: Table Configuration (`src/static/js/advanced-table/table-config.js`)

```
I'm on Week 3, Phase 2, Task 2.5 of the mockCMMS code quality audit.

Task: Audit table-config.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review localStorage usage patterns
- [ ] Check for storage quota handling
- [ ] Verify JSON serialization safety
- [ ] Review configuration validation
- [ ] Check for race conditions
- [ ] Verify default configuration handling
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-config.js [Phase 2.5]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.6: Table Events (`src/static/js/advanced-table/table-events.js`)

```
I'm on Week 3, Phase 2, Task 2.6 of the mockCMMS code quality audit.

Task: Audit table-events.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review event delegation patterns
- [ ] Check for memory leaks (listener cleanup)
- [ ] Verify event handler organization
- [ ] Review debouncing/throttling usage
- [ ] Check for duplicate event bindings
- [ ] Verify proper event.preventDefault() usage
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-events.js [Phase 2.6]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.7: Table Export (`src/static/js/advanced-table/table-export.js`)

```
I'm on Week 3, Phase 2, Task 2.7 of the mockCMMS code quality audit.

Task: Audit table-export.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review CSV generation logic
- [ ] Check for proper escaping of special characters
- [ ] Verify encoding handling (UTF-8)
- [ ] Review file download implementation
- [ ] Check for browser compatibility
- [ ] Verify large dataset handling
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-export.js [Phase 2.7]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.8: Table Sidebar (`src/static/js/advanced-table/table-sidebar.js`)

```
I'm on Week 3, Phase 2, Task 2.8 of the mockCMMS code quality audit.

Task: Audit table-sidebar.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review sidebar toggle implementation
- [ ] Check state persistence
- [ ] Verify filter UI logic
- [ ] Review column visibility controls
- [ ] Check for duplicate code
- [ ] Verify accessibility
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-sidebar.js [Phase 2.8]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.9: Table Resize (`src/static/js/advanced-table/table-resize.js`)

```
I'm on Week 3, Phase 2, Task 2.9 of the mockCMMS code quality audit.

Task: Audit table-resize.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review column resize algorithm
- [ ] Check for performance issues during drag
- [ ] Verify minimum/maximum width constraints
- [ ] Review mouse event handling
- [ ] Check for memory leaks
- [ ] Verify state persistence
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-resize.js [Phase 2.9]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.10: Table Loading States (`src/static/js/advanced-table/table-loading.js`)

```
I'm on Week 3, Phase 2, Task 2.10 of the mockCMMS code quality audit.

Task: Audit table-loading.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review loading indicator implementation
- [ ] Check for proper show/hide logic
- [ ] Verify spinner positioning
- [ ] Review timeout handling
- [ ] Check for race conditions
- [ ] Verify accessibility (ARIA live regions)
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-loading.js [Phase 2.10]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.11: Table Retry Logic (`src/static/js/advanced-table/table-retry.js`)

```
I'm on Week 3, Phase 2, Task 2.11 of the mockCMMS code quality audit.

Task: Audit table-retry.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review exponential backoff implementation
- [ ] Check retry limit configuration
- [ ] Verify error handling
- [ ] Review promise chain logic
- [ ] Check for infinite retry loops
- [ ] Verify user feedback during retries
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(table): audit and improve table-retry.js [Phase 2.11]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.12: Toast Notifications (`src/static/js/toast-notification.js`)

```
I'm on Week 3, Phase 2, Task 2.12 of the mockCMMS code quality audit.

Task: Audit toast-notification.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review notification queue management
- [ ] Check for memory leaks (DOM cleanup)
- [ ] Verify auto-dismiss timing
- [ ] Review accessibility (ARIA roles)
- [ ] Check for duplicate notifications
- [ ] Verify z-index and positioning
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

Commit message: `refactor(js): audit and improve toast-notification.js [Phase 2.12]`

Show me your findings and proposed changes before implementing.
```

---

### Task 2.13: Flash Messages Handler (`src/static/js/flash-messages.js`)

```
I'm on Week 3, Phase 2, Task 2.13 of the mockCMMS code quality audit.

Task: Audit flash-messages.js using the 5-step iterative loop

Manual audit focus:
- [ ] Review Flask flash message integration
- [ ] Check category mapping logic
- [ ] Verify DOM ready handling
- [ ] Review error handling
- [ ] Check for duplicate message display
- [ ] Verify proper cleanup
- [ ] Remove console.log()
- [ ] Remove bug references
- [ ] Add JSDoc comments

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- Document what was changed and why
- 🔄 Loop back to Step 1 and repeat until file is perfect

If Step 4 resulted in NO modifications:
- Mark task as COMPLETE ✅
- Commit with message: `refactor(js): audit and improve flash-messages.js [Phase 2.13]`
- Phase 2 COMPLETE - Move to Phase 3

Show me your findings and proposed changes before implementing.
```

---

## Phase 2 Final Verification

After all 13 tasks complete:
- [ ] Load application in browser
- [ ] Test all Advanced Table features
- [ ] Check browser console (no errors)
- [ ] Verify toast notifications work
- [ ] Test flash messages from Flask
- [ ] Run ESLint on all JS files
- [ ] Document findings in audit report
- [ ] Mark Phase 2 COMPLETE ✅

**Deliverable:** 13 commits, all JavaScript files audited and improved


---

## Phase 3: CSS Styling Analysis (3 tasks)

### Task 3.1: Main Styles (`src/static/css/main.css`)

```
I'm on Week 4, Phase 3, Task 3.1 of the mockCMMS code quality audit.

Task: Audit main.css using the 5-step iterative loop

Please:

**Step 1: Format/Lint Check**
- Run: stylelint src/static/css/main.css
- Fix any problems found

**Step 2: Auto-Formatting**
- Run: prettier --write src/static/css/main.css
- Review changes

**Step 3: Visual Testing**
- Load application in browser
- Verify styles render correctly
- Test responsive breakpoints

**Step 4: Manual Audit**
- [ ] Review file structure and organization
- [ ] Check for logical grouping of styles
- [ ] Verify CSS custom properties usage
- [ ] Review color consistency
- [ ] Check for magic numbers
- [ ] Remove duplicate styles
- [ ] Verify mobile-first approach
- [ ] Check breakpoint consistency
- [ ] Remove unused vendor prefixes
- [ ] Optimize selectors

**Step 5: Document & Loop or Commit**

Commit message: `refactor(css): audit and improve main.css [Phase 3.1]`

Show me your findings before implementing.
```

---

### Task 3.2: Advanced Table Styles (`src/static/css/advanced-table.css`)

```
I'm on Week 4, Phase 3, Task 3.2 of the mockCMMS code quality audit.

Task: Audit advanced-table.css using the 5-step iterative loop

Manual audit focus:
- [ ] Review component-specific styles
- [ ] Check for naming consistency (BEM or similar)
- [ ] Verify responsive table behavior
- [ ] Review z-index usage
- [ ] Check for duplicate styles
- [ ] Verify color scheme consistency
- [ ] Review animation performance
- [ ] Check accessibility (focus states, contrast)

Commit message: `refactor(css): audit and improve advanced-table.css [Phase 3.2]`

Show me your findings before implementing.
```

---

### Task 3.3: Form Styles (`src/static/css/forms.css`)

```
I'm on Week 4, Phase 3, Task 3.3 of the mockCMMS code quality audit.

Task: Audit forms.css using the 5-step iterative loop

Manual audit focus:
- [ ] Review form element styling
- [ ] Check input validation styles
- [ ] Verify error message styling
- [ ] Review button styles consistency
- [ ] Check for duplicate form styles
- [ ] Verify accessibility (labels, focus)
- [ ] Review responsive form behavior
- [ ] Check color contrast ratios

**Step 5: Document & Loop or Commit**

Commit message: `refactor(css): audit and improve forms.css [Phase 3.3]`
Phase 3 COMPLETE - Move to Phase 4

Show me your findings before implementing.
```

---

## Phase 3 Final Verification

After all 3 tasks complete:
- [ ] Load all pages in browser
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Verify color consistency
- [ ] Check accessibility (contrast, focus states)
- [ ] Run stylelint on all CSS files
- [ ] Document findings
- [ ] Mark Phase 3 COMPLETE ✅

**Deliverable:** 3 commits, all CSS files audited and improved

---

## Phase 4: HTML Templates Analysis (16 tasks)

### Task 4.1: Base Template (`src/templates/base.html`)

```
I'm on Week 4, Phase 4, Task 4.1 of the mockCMMS code quality audit.

Task: Audit base.html using the 5-step iterative loop

**Step 1: Format/Lint Check**
- Run: djlint src/templates/base.html --reformat
- Fix any problems

**Step 2: Auto-Formatting**
- Review djlint changes
- Verify proper indentation

**Step 3: Functional Testing**
- Load application
- Verify template renders correctly
- Check all pages using base template

**Step 4: Manual Audit**
- [ ] Remove inline styles (move to CSS)
- [ ] Remove inline scripts (move to JS files)
- [ ] Remove bug reference comments
- [ ] Verify proper Jinja2 syntax
- [ ] Check for hardcoded values
- [ ] Review meta tags
- [ ] Verify accessibility (lang, ARIA)
- [ ] Check for duplicate blocks

**Step 5: Document & Loop or Commit**

Commit message: `refactor(templates): audit and improve base.html [Phase 4.1]`

Show me your findings before implementing.
```

---

### Task 4.2-4.16: Individual Templates

For each template (index.html, assets.html, asset_detail.html, maintenance_orders.html, mo_detail.html, spare_parts.html, spare_part_detail.html, users.html, user_detail.html, login.html, register.html, 404.html, 500.html, components/table.html, components/filters.html):

```
I'm on Week 4, Phase 4, Task 4.[X] of the mockCMMS code quality audit.

Task: Audit [TEMPLATE_NAME] using the 5-step iterative loop

Follow same process as Task 4.1:
1. djlint formatting
2. Review changes
3. Browser testing
4. Manual audit:
   - [ ] Remove inline styles
   - [ ] Remove inline scripts
   - [ ] Remove bug references
   - [ ] Check Jinja2 syntax
   - [ ] Verify form handling
   - [ ] Check CSRF tokens
   - [ ] Review accessibility
   - [ ] Check for duplicate code
5. Document & loop or commit

Commit message: `refactor(templates): audit and improve [TEMPLATE_NAME] [Phase 4.X]`

Show me your findings before implementing.
```

---

## Phase 4 Final Verification

After all 16 tasks complete:
- [ ] Load all pages in browser
- [ ] Test all forms
- [ ] Verify no inline styles remain
- [ ] Verify no inline scripts remain
- [ ] Check for console errors
- [ ] Run djlint on all templates
- [ ] Document findings
- [ ] Mark Phase 4 COMPLETE ✅

**Deliverable:** 16 commits, all templates audited and improved

---

## Phase 5: Root-Level Files Analysis (7 tasks)

### Task 5.1: Application Entry Point (`run.py`)

```
I'm on Week 5, Phase 5, Task 5.1 of the mockCMMS code quality audit.

Task: Audit run.py using the 5-step iterative loop

**Step 1-3:** flake8 → black → pytest (all 210 tests pass)

**Step 4: Manual Audit**
- [ ] Review application startup logic
- [ ] Check environment variable handling
- [ ] Verify proper error handling
- [ ] Review debug mode configuration
- [ ] Check for hardcoded values
- [ ] Verify logging setup
- [ ] Review docstring

**Step 5: Document & Loop or Commit**

Commit message: `refactor(root): audit and improve run.py [Phase 5.1]`

Show me your findings before implementing.
```

---

### Task 5.2: Requirements (`requirements.txt`)

```
I'm on Week 5, Phase 5, Task 5.2 of the mockCMMS code quality audit.

Task: Audit requirements.txt

**Step 1: Dependency Check**
- Run: pip-audit
- Check for security vulnerabilities

**Step 2: Version Review**
- Check for outdated packages
- Verify version pinning strategy

**Step 3: Functional Testing**
- Create fresh venv
- Install requirements
- Run application

**Step 4: Manual Audit**
- [ ] Remove unused dependencies
- [ ] Verify all dependencies needed
- [ ] Check version compatibility
- [ ] Review security advisories
- [ ] Organize by category (comments)
- [ ] Pin critical versions

**Step 5: Document & Loop or Commit**

Commit message: `chore(deps): audit and improve requirements.txt [Phase 5.2]`

Show me your findings before implementing.
```

---

### Task 5.3: Environment Configuration (`.env.example`)

```
I'm on Week 5, Phase 5, Task 5.3 of the mockCMMS code quality audit.

Task: Audit .env.example

**Step 4: Manual Audit**
- [ ] Verify all env vars documented
- [ ] Check for sensitive data
- [ ] Review default values
- [ ] Verify variable naming
- [ ] Add descriptions/comments
- [ ] Check consistency with code
- [ ] Verify app enable flags

Commit message: `docs(config): audit and improve .env.example [Phase 5.3]`

Show me your findings before implementing.
```

---

### Task 5.4: Documentation (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`)

```
I'm on Week 5, Phase 5, Task 5.4 of the mockCMMS code quality audit.

Task: Audit documentation files

**Step 4: Manual Audit**
- [ ] Verify README accuracy
- [ ] Check setup instructions
- [ ] Review feature descriptions
- [ ] Verify links work
- [ ] Check CONTRIBUTING standards
- [ ] Review CHANGELOG format
- [ ] Update version numbers
- [ ] Check for outdated info

Commit message: `docs: audit and improve documentation [Phase 5.4]`

Show me your findings before implementing.
```

---

### Task 5.5: GitHub Configuration (`.github/` files)

```
I'm on Week 5, Phase 5, Task 5.5 of the mockCMMS code quality audit.

Task: Audit GitHub configuration files

**Step 4: Manual Audit**
- [ ] Review issue templates
- [ ] Check PR template
- [ ] Verify workflow files
- [ ] Review CODEOWNERS
- [ ] Check funding.yml
- [ ] Verify dependabot.yml
- [ ] Review security policy

Commit message: `docs(github): audit and improve GitHub configuration [Phase 5.5]`

Show me your findings before implementing.
```

---

### Task 5.6: Test Infrastructure (`tests/conftest.py`, `test_data/dummy_data.json`)

```
I'm on Week 5, Phase 5, Task 5.6 of the mockCMMS code quality audit.

Task: Audit test infrastructure

**Step 1-3:** flake8 → black → pytest

**Step 4: Manual Audit**
- [ ] Review pytest configuration
- [ ] Check fixture organization
- [ ] Verify test data validity
- [ ] Review coverage configuration
- [ ] Check for duplicate fixtures
- [ ] Verify fixture scope

Commit message: `test: audit and improve test infrastructure [Phase 5.6]`

Show me your findings before implementing.
```

---

### Task 5.7: Scripts (`scripts/setup.ps1`)

```
I'm on Week 5, Phase 5, Task 5.7 of the mockCMMS code quality audit.

Task: Audit setup.ps1

**Step 1: Lint Check**
- Run: PSScriptAnalyzer on setup.ps1

**Step 3: Functional Testing**
- Run script in test environment

**Step 4: Manual Audit**
- [ ] Review functionality
- [ ] Check error handling
- [ ] Verify cross-platform notes
- [ ] Check for hardcoded paths
- [ ] Review user feedback messages
- [ ] Verify idempotency

**Step 5: Document & Loop or Commit**

Commit message: `chore(scripts): audit and improve setup.ps1 [Phase 5.7]`
Phase 5 COMPLETE - Move to Phase 6

Show me your findings before implementing.
```

---

## Phase 5 Final Verification

After all 7 tasks complete:
- [ ] Run setup script from scratch
- [ ] Verify all documentation links
- [ ] Run pip-audit
- [ ] Test application startup
- [ ] Document findings
- [ ] Mark Phase 5 COMPLETE ✅

**Deliverable:** 7 commits, all root files audited

---

## Phase 6: Cross-Cutting Concerns (4 tasks)

### Task 6.1: Naming Conventions Audit

```
I'm on Week 5, Phase 6, Task 6.1 of the mockCMMS code quality audit.

Task: Audit naming conventions across entire codebase

**Step 1: Automated Check**
- Run naming convention checker

**Step 2: Generate Report**
- Create report of violations
- Categorize by severity

**Step 3: Verify No Regressions**
- Run all tests (210 must pass)

**Step 4: Manual Audit**
- [ ] Files & Directories (Python: snake_case, JS: kebab-case)
- [ ] Variables & Functions (Python: snake_case, JS: camelCase)
- [ ] Classes (PascalCase)
- [ ] Constants (UPPER_SNAKE_CASE)
- [ ] Database (snake_case)
- [ ] Document violations

**Step 5: Document & Loop or Commit**

Commit message: `refactor(naming): standardize naming conventions [Phase 6.1]`

Show me your findings before implementing.
```

---

### Task 6.2: Environment Configuration Audit

```
I'm on Week 5, Phase 6, Task 6.2 of the mockCMMS code quality audit.

Task: Audit environment configuration usage

**Step 1: Scan Codebase**
- Find all environment variable usage

**Step 2: Generate Report**
- List all env vars used
- Compare with .env.example

**Step 3: Verify No Regressions**
- Run all tests

**Step 4: Manual Audit**
- [ ] Review .env.example completeness
- [ ] Check for sensitive data in git
- [ ] Verify all vars documented
- [ ] Review default values
- [ ] Cross-reference with code

**Step 5: Document & Loop or Commit**

Commit message: `refactor(config): audit and standardize environment configuration [Phase 6.2]`

Show me your findings before implementing.
```

---

### Task 6.3: Code Duplication Analysis

```
I'm on Week 5, Phase 6, Task 6.3 of the mockCMMS code quality audit.

Task: Analyze code duplication

**Step 1: Run Duplicate Detector**
- Run: jscpd across entire codebase

**Step 2: Generate Report**
- List duplicate blocks
- Prioritize by size/impact

**Step 3: Verify No Regressions**
- Run all tests

**Step 4: Manual Audit**
- [ ] Review jscpd report
- [ ] Identify refactoring opportunities
- [ ] Check Python/JavaScript duplicates
- [ ] Verify no duplicate CSS rules
- [ ] Check duplicate template blocks

**Step 5: Document & Loop or Commit**

Commit message: `refactor(duplication): remove code duplicates [Phase 6.3]`

Show me your findings before implementing.
```

---

### Task 6.4: Final Consistency Check

```
I'm on Week 5, Phase 6, Task 6.4 of the mockCMMS code quality audit.

Task: Final consistency check across all code

**Step 1: Run All Linters**
- flake8, pylint, eslint, stylelint, djlint

**Step 2: Generate Final Report**
- Create audit summary
- List remaining issues

**Step 3: Verify No Regressions**
- Run all 210 tests
- Verify all pass

**Step 4: Manual Audit**
- [ ] Verify naming consistency
- [ ] Check for remaining duplicates
- [ ] Review overall organization
- [ ] Verify standards applied
- [ ] Check for missed issues

**Step 5: Document & Loop or Commit**

Commit message: `refactor(final): final consistency check [Phase 6.4]`
ALL PHASES COMPLETE ✅

Show me your findings before implementing.
```

---

## Phase 6 Final Verification

After all 4 tasks complete:
- [ ] Run all linters one final time
- [ ] Run all 210 tests (100% pass)
- [ ] Verify 82.99%+ coverage maintained
- [ ] Test application end-to-end
- [ ] Create final audit report
- [ ] Mark Phase 6 COMPLETE ✅
- [ ] Mark ALL 49 TASKS COMPLETE ✅

**Deliverable:** 4 commits, comprehensive audit complete

---

## 🔍 How AI Will Know What to Do

### The Documents Work Together Like This:

```
┌─────────────────────────────────────────────────────────┐
│  IMPLEMENTATION_PRIORITY_GUIDE.md (MASTER PLAN)         │
│  "What to do and when"                                   │
│                                                          │
│  Week 1: Foundation Setup                               │
│  Week 2: Testing ────────┐                              │
│  Week 3: Code Quality    │                              │
│  Week 4-5: Audit         │                              │
│  Week 6-7: Polish        │                              │
└──────────────────────────┼──────────────────────────────┘
                           │
                           ↓
         ┌─────────────────┴─────────────────────┐
         │                                        │
         ↓                                        ↓
┌──────────────────────┐          ┌─────────────────────────┐
│ core_code_quality_   │          │ mockCMMS_roadmap.md      │
│ plan.md              │          │                          │
│ "HOW to audit code"  │          │ "WHAT standards to use"  │
│                      │          │                          │
│ Phase 1: Python      │          │ GitHub Best Practices:   │
│ Phase 2: JavaScript  │          │ - Git Workflow           │
│ Phase 3: CSS         │          │ - Security Standards     │
│ Phase 4: Templates   │          │ - CI/CD Setup            │
│ Phase 5: Root Files  │          │ - Repository Standards   │
│ Phase 6: Cross-Cut   │          │                          │
└──────────────────────┘          └──────────────────────────┘
```

**AI reads:**
1. **IMPLEMENTATION_PRIORITY_GUIDE.md** → Knows what week/phase you're in
2. **AI_AGENT_GUIDE.md** (this file) → Gets exact prompts for each task
3. **core_code_quality_plan.md** → Understands the audit structure
4. **mockCMMS_roadmap.md** → Knows WHAT standards to follow

---

## 🚨 How to Prevent AI from Creating Duplicates

### Built-in Safeguards

#### 1. **Cross-References**
Each document references the others:
- Implementation Guide → points to both other plans
- Core Quality Plan → references roadmap for standards
- Roadmap → references core quality plan for audit work

**What to tell AI:**
```
Before making changes:
1. Search all planning documents for related content
2. Check if this task is already tracked elsewhere
3. Update only the relevant document
4. Add cross-references if needed
```

#### 2. **Progress Tracking**
Each plan has checkboxes `[ ]` and `[x]`:
```
AI should:
- Mark [x] when task complete
- Add completion notes
- Never delete completed items
- Keep historical context
```

---

## ✅ Best Practices for AI Delegation

### 1. **Always Provide Context**
```
❌ Bad: "Fix app.py"
✅ Good: "I'm on Phase 1, Task 1.6. Please audit app.py following 
         the prompt in AI_AGENT_GUIDE.md Task 1.6."
```

### 2. **Reference Specific Sections**
```
❌ Bad: "Read the roadmap"
✅ Good: "Read mockCMMS_roadmap.md section 'Implement Git Workflow 
         Standards' under Project Infrastructure & Documentation"
```

### 3. **Request Approval Before Changes**
```
Always include:
"Show me your proposed changes before applying them"
"Wait for my approval before modifying files"
"List all issues found before fixing"
```

### 4. **Request Progress Updates**
```
Always include:
"After completing this task, update the progress tracking in 
core_code_quality_plan.md"
"Mark the checkbox [x] for completed items"
"Add completion notes with date"
```

### 5. **One Task at a Time**
```
❌ Bad: "Do all of Phase 1"
✅ Good: "Do Task 1.1: API Routes"
         (Then after completion)
         "Do Task 1.2: Web Routes"
```

---

## 📝 AI Workflow Template

Use this workflow for every task:

### Step 1: Context Setting
```
I'm working on mockCMMS code quality audit.
Current: Phase [X], Task [X.Y]
Task: [Task name from core_code_quality_plan.md]
```

### Step 2: Get the Prompt
```
Please use the prompt from AI_AGENT_GUIDE.md Task [X.Y]
```

### Step 3: AI Executes
```
AI will:
1. Run linters/formatters
2. Run tests
3. Perform manual audit
4. Show you findings
5. Wait for approval
```

### Step 4: Review & Approve
```
You review and either:
- "Approved, proceed with fixes"
- "Change X before proceeding"
- "Skip this, move to next task"
```

### Step 5: Verification
```
After AI completes:
- Check the changes
- Run tests (210 must pass)
- Verify progress updated in core_code_quality_plan.md
- Commit with proper message
```

---

## 🔄 Document Update Protocol for AI

When AI updates planning documents:

### For core_code_quality_plan.md
```
✅ Mark: [x] for completed tasks
✅ Add: Completion dates and issue counts
✅ Update: Progress tracking section
❌ Don't: Delete completed phases or remove historical data
```

### For mockCMMS_roadmap.md
```
✅ Update: "ACTIVE WORK" section status
✅ Update: "Last Updated" date at top
✅ Move: Completed sprints to "Recently Completed"
❌ Don't: Remove completed items or change structure
```

---

## 🎯 AI Agent Checklist

Before AI starts any task:

```
Pre-Task Checklist:
[ ] Read AI_AGENT_GUIDE.md for the specific task prompt
[ ] Read core_code_quality_plan.md for context
[ ] Understand which files to analyze/modify
[ ] Know where to update progress

During Task:
[ ] Follow the 5-step iterative loop
[ ] Run all automated checks first
[ ] Show findings before implementing fixes
[ ] Apply coding standards from copilot-instructions.md
[ ] Write proper commit messages

Post-Task:
[ ] Update progress in core_code_quality_plan.md
[ ] Mark checkbox [x] for completed task
[ ] Add completion notes with date
[ ] Suggest next task from the plan
```

---

## 💡 Advanced AI Delegation Patterns

### Pattern 1: Iterative Refinement
```
Round 1: "Run Step 1-3 of Task 1.1, show me lint/format/test results"
Round 2: "Now do Step 4 manual audit, list all issues found"
Round 3: "Fix issues 1-3, then loop back to Step 1"
Round 4: "No more issues? Commit and move to Task 1.2"

Benefits:
- You review each change
- Prevents large, risky changes
- Easier to track progress
```

### Pattern 2: Batch Similar Tasks
```
"Complete all Phase 2 JavaScript table-*.js files (Tasks 2.1-2.11)"

AI will:
- Execute each task sequentially
- Show findings for each file
- Wait for approval before moving to next
- Commit after each task
```

---

## 🎓 Training AI on Your Project

### First Session with New AI Agent

```
I'm working on the mockCMMS project code quality audit.

We're following a structured 49-task audit plan across 6 phases.

Please read:
1. docs/AI_AGENT_GUIDE.md (this file - has prompts for all 49 tasks)
2. docs/core_code_quality_plan.md (the audit structure)
3. docs/IMPLEMENTATION_PRIORITY_GUIDE.md (overall timeline)

Current status:
- Phase 0: Complete (automated analysis done)
- Phase 1: In Progress (Task 1.1 complete, working on 1.2)

Tell me:
1. What task should we work on next?
2. What's the prompt for that task?
```

---

## 📊 Progress Tracking Example

### In core_code_quality_plan.md:
```markdown
### Phase 1: Python Backend Analysis
- [x] Task 1.1: API Routes (Completed 2025-12-13, 3 issues fixed)
- [ ] Task 1.2: Web Routes (In Progress)
- [ ] Task 1.3: Database Utilities
...
```

---

## 📊 Current Status (December 13, 2025)

| Document | Status | Progress |
|----------|--------|----------|
| **AI_AGENT_GUIDE.md** | ✅ Complete | All 49 prompts ready |
| **core_code_quality_plan.md** | 🔄 In Progress | Phase 0 ✅, Phase 1 started |
| **comprehensive_testing_plan.md** | ✅ Complete | 210/210 tests ✅ |
| **mockCMMS_roadmap.md** | 📚 Reference | Strategic context |

**Current Task:** Phase 1, Task 1.2 (Web Routes)

---

## ✅ Success Criteria

You know AI understands the project when it:

✅ Uses prompts from AI_AGENT_GUIDE.md without being asked  
✅ Follows the 5-step loop for each task  
✅ Shows findings before implementing fixes  
✅ Updates progress in core_code_quality_plan.md  
✅ Writes proper commit messages  
✅ Suggests next task after completion  

---

## 🎯 Quick Reference Commands

### Start a Task
```
"Please execute Task [X.Y] from AI_AGENT_GUIDE.md"
```

### Check Status
```
"What's the current task status in core_code_quality_plan.md?"
"What's the next task I should work on?"
```

### Update Progress
```
"We just completed Task [X.Y].
Please update core_code_quality_plan.md and suggest next task."
```

---

## 🎉 Final Tips

### Do's ✅
- ✅ Use the prompts from this guide (copy-paste ready)
- ✅ One task at a time
- ✅ Review findings before approving fixes
- ✅ Verify all 210 tests pass after each task
- ✅ Update progress tracking

### Don'ts ❌
- ❌ Skip the 5-step loop
- ❌ Let AI make changes without showing findings first
- ❌ Skip progress tracking updates
- ❌ Work on multiple tasks simultaneously

---

**Remember:** This guide provides ready-to-use prompts for all 49 tasks. Just reference the task number, and AI knows exactly what to do.

---

**Last Updated:** December 13, 2025  
**Next Review:** After Phase 1 completion
