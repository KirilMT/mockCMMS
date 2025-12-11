# AI Agent Interaction Guide

**Created:** December 11, 2025  
**Purpose:** Instructions for effectively delegating work to AI coding assistants (GitHub Copilot, Gemini, ChatGPT, etc.)

---

## 🤖 Quick Start - How to Delegate Work to AI

### The Magic Phrase Template

Use this template when asking AI to work on the project:

```
I'm working on the mockCMMS project. Please read the Implementation Priority 
Guide (docs/IMPLEMENTATION_PRIORITY_GUIDE.md) and help me with [SPECIFIC TASK].

Context:
- Current Phase: [Week X / Phase X]
- Current Focus: [e.g., "Python Backend Audit" or "Setting up CI/CD"]
- Specific Task: [e.g., "Create PR template" or "Audit app.py for code quality"]

Please:
1. Read the relevant planning documents
2. Understand the standards we're following
3. Propose your approach
4. Wait for my approval before making changes
5. Update progress in the relevant plan document
```

---

## 📋 AI Agent Entry Points (What to Tell AI to Read)

### For New AI Sessions - Start Here

**Tell AI to read these files IN THIS ORDER:**

1. **First:** `docs/IMPLEMENTATION_PRIORITY_GUIDE.md`
   - Complete action plan
   - Shows what phase you're in
   - Explains how everything fits together

2. **Then:** Based on your current work:
   
   **If doing code quality work:**
   ```
   Read: docs/core_code_quality_plan.md
   Focus: [Current Phase - e.g., "Phase 1: Python Backend"]
   ```
   
   **If setting up infrastructure:**
   ```
   Read: docs/mockCMMS_roadmap.md
   Section: "Project Infrastructure & Documentation"
   Focus: [Specific best practice - e.g., "Git Workflow Standards"]
   ```

3. **For standards reference:**
   ```
   Read: .github/copilot-instructions.md
   (or .github/GEMINI.md for Gemini Code Assist)
   ```

---

## 🎯 Example Prompts for Common Tasks

### Week 1: Foundation Setup Tasks

#### Task: Create PR Template
```
I'm on Week 1 (Foundation Setup) of the mockCMMS Implementation Priority Guide.

Task: Create a Pull Request template

Please:
1. Read docs/IMPLEMENTATION_PRIORITY_GUIDE.md (Week 1 section)
2. Read .github/copilot-instructions.md for PR standards
3. Create .github/PULL_REQUEST_TEMPLATE.md
4. Include sections for:
   - Description of changes
   - Type of change (bugfix, feature, docs, etc.)
   - Testing performed
   - Checklist (follows standards, tested, docs updated)
5. Show me the template before creating the file
```

#### Task: Update CONTRIBUTING.md
```
I'm on Day 2 of Week 1 (Foundation Setup).

Task: Update CONTRIBUTING.md with code standards

Please:
1. Read docs/IMPLEMENTATION_PRIORITY_GUIDE.md (Week 1, Day 2 tasks)
2. Read docs/mockCMMS_roadmap.md (GitHub Best Practices sections)
3. Update CONTRIBUTING.md to include:
   - Code style standards (PEP 8, JS best practices)
   - Comment standards (no bug references, professional)
   - Separation of concerns rules
   - Commit message standards (Conventional Commits)
4. Show me the proposed changes before applying
```

#### Task: Create Basic CI Workflow
```
I'm on Day 3 of Week 1 (Foundation Setup).

Task: Create basic GitHub Actions CI workflow

Please:
1. Read docs/IMPLEMENTATION_PRIORITY_GUIDE.md (Week 1, Day 3 tasks)
2. Read docs/mockCMMS_roadmap.md (GitHub Actions CI/CD section)
3. Create .github/workflows/ci.yml with:
   - Python linting (flake8, black)
   - Run pytest
   - Generate coverage report
4. Use Python 3.12 (check run.py or requirements.txt for version)
5. Show me the workflow before creating
```

---

### Week 2: Python Backend Audit

#### Task: Audit app.py
```
I'm on Week 2 (Python Backend Audit) of the Implementation Priority Guide.

Task: Audit src/app.py for code quality issues

Please:
1. Read docs/core_code_quality_plan.md (Phase 1.1: Code Structure & Organization)
2. Read docs/IMPLEMENTATION_PRIORITY_GUIDE.md (Week 2 tasks)
3. Analyze src/app.py for:
   - PEP 8 compliance
   - Proper Flask factory pattern
   - Comment quality (no bug references)
   - Security issues (SECRET_KEY handling)
   - Code duplication
4. List all issues found with severity (Critical, High, Medium, Low)
5. Propose fixes for critical and high priority issues
6. Wait for my approval before making changes
7. After fixes, update docs/core_code_quality_plan.md progress
```

#### Task: Audit db_utils.py
```
I'm on Week 2, working on Python backend audit.

Task: Audit src/services/db_utils.py

Please:
1. Read docs/core_code_quality_plan.md (Phase 1.2: Database Layer)
2. Check for:
   - SQL injection vulnerabilities
   - N+1 query problems
   - Proper use of SQLAlchemy ORM
   - Query optimization opportunities
   - Transaction handling
3. List issues with examples from the code
4. Propose fixes
5. Wait for approval before changing code
6. Update progress tracking in core_code_quality_plan.md
```

---

### Week 3: JavaScript Audit

#### Task: Audit Advanced Table Component
```
I'm on Week 3 (JavaScript Audit) of the Implementation Priority Guide.

Task: Audit src/static/js/advanced-table/ files

Please:
1. Read docs/core_code_quality_plan.md (Phase 2: JavaScript Frontend)
2. Read docs/IMPLEMENTATION_PRIORITY_GUIDE.md (Week 3 tasks)
3. Check all table-*.js files for:
   - Code duplication across files
   - Consistent naming conventions
   - Professional comments (no bug references)
   - ESLint compliance
   - Modern JavaScript practices (ES6+)
4. List issues by file
5. Propose refactoring to eliminate duplication
6. Wait for approval
7. Update progress in core_code_quality_plan.md
```

---

### Week 4: CSS Audit

#### Task: Extract Inline Styles
```
I'm on Week 4 (CSS Audit) working on separation of concerns.

Task: Remove inline styles from templates

Please:
1. Read docs/core_code_quality_plan.md (Phase 3 & 4: CSS and Templates)
2. Read .github/copilot-instructions.md (Separation of Concerns section)
3. Scan src/templates/*.html for:
   - Inline style="..." attributes
   - Inline <style> blocks
4. For each inline style found:
   - Extract to appropriate CSS file (main.css or advanced-table.css)
   - Create semantic CSS class
   - Update template to use class
5. Show me the changes file by file
6. Wait for approval before applying
7. Update both core_code_quality_plan.md and affected template files
```

---

## 🔍 How AI Will Know What to Do

### The Documents Work Together Like This:

```
┌─────────────────────────────────────────────────────────┐
│  IMPLEMENTATION_PRIORITY_GUIDE.md (MASTER PLAN)         │
│  "What to do and when"                                   │
│                                                          │
│  Week 1: Foundation Setup                               │
│  Week 2: Python Audit ──────┐                          │
│  Week 3: JavaScript Audit   │                           │
│  Week 4: CSS Audit          │                           │
│  Week 5: Templates          │                           │
│  Week 6: Polish             │                           │
└──────────────────────────────┼──────────────────────────┘
                               │
                               ↓
         ┌─────────────────────┴─────────────────────┐
         │                                            │
         ↓                                            ↓
┌──────────────────────┐              ┌──────────────���───────────┐
│ core_code_quality_   │              │ mockCMMS_roadmap.md      │
│ plan.md              │              │                          │
│ "HOW to audit code"  │              │ "WHAT standards to use"  │
│                      │              │                          │
│ Phase 1: Python      │              │ GitHub Best Practices:   │
│ Phase 2: JavaScript  │              │ - Git Workflow           │
│ Phase 3: CSS         │              │ - Security Standards     │
│ Phase 4: Templates   │              │ - CI/CD Setup            │
│ Phase 5: Standards   │              │ - Repository Standards   │
└──────────────────────┘              └──────────────────────────┘
```

**AI reads:**
1. **IMPLEMENTATION_PRIORITY_GUIDE.md** → Knows what week/phase you're in
2. **core_code_quality_plan.md** → Knows HOW to audit that phase
3. **mockCMMS_roadmap.md** → Knows WHAT standards to follow
4. **copilot-instructions.md** → Knows project-specific rules

---

## 🚨 How to Prevent AI from Creating Duplicates

### Built-in Safeguards

The documents now have safeguards to prevent duplication:

#### 1. **Cross-References**
Each document references the others:
- Implementation Guide → points to both other plans
- Core Quality Plan → references roadmap for standards
- Roadmap → references core quality plan for audit work

**What to tell AI:**
```
Before making changes:
1. Search all 3 planning documents for related content
2. Check if this task is already tracked elsewhere
3. Update only the relevant document
4. Add cross-references if needed
```

#### 2. **Living Document Guidelines**
All plans have "Avoid Duplicates" sections telling AI:
```
Before adding new issues:
- Search document for existing entries
- Consolidate related issues into single entries
- Cross-reference when necessary
```

#### 3. **Progress Tracking**
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
✅ Good: "I'm on Week 2, Python audit. Please audit app.py following 
         Phase 1.1 of core_code_quality_plan.md. Focus on Flask 
         factory pattern and SECRET_KEY handling."
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
[relevant document]"
"Mark the checkbox [x] for completed items"
"Add completion notes with date and summary"
```

### 5. **One Task at a Time**
```
❌ Bad: "Do everything in Week 1"
✅ Good: "Do Day 1, Task 1: Create PR template"
         (Then after completion)
         "Do Day 1, Task 2: Enable branch protection"
```

---

## 📝 AI Workflow Template

Use this workflow for every task:

### Step 1: Context Setting
```
I'm working on mockCMMS project.
Current: [Week X, Day Y / Phase X]
Task: [Specific task from Implementation Priority Guide]
```

### Step 2: Document References
```
Please read:
1. docs/IMPLEMENTATION_PRIORITY_GUIDE.md ([specific section])
2. docs/core_code_quality_plan.md ([if doing audit work])
3. docs/mockCMMS_roadmap.md ([if setting up infrastructure])
```

### Step 3: Task Instructions
```
Please:
1. [First action - usually analyze/read code]
2. [Second action - usually identify issues]
3. [Third action - usually propose solution]
4. Wait for my approval
5. [After approval: implement changes]
6. Update progress in [relevant document]
```

### Step 4: Review & Approve
```
AI shows you proposed changes
You review and either:
- "Approved, proceed" 
- "Change X before proceeding"
- "Skip this, move to next task"
```

### Step 5: Verification
```
After AI completes:
- Check the changes
- Run tests if applicable
- Verify progress was updated in docs
- Commit with proper message
```

---

## 🔄 Document Update Protocol for AI

When AI updates planning documents, it should:

### For IMPLEMENTATION_PRIORITY_GUIDE.md
```
✅ Update: Week completion status
✅ Update: "Last Updated" date
✅ Add: Notes about deviations from plan
❌ Don't: Change the structure or remove completed items
```

### For core_code_quality_plan.md
```
✅ Mark: [x] for completed file audits
✅ Add: Completion dates and issue counts
✅ Update: Progress tracking section
✅ Add: Links to PRs or commits
❌ Don't: Delete completed phases or remove historical data
```

### For mockCMMS_roadmap.md
```
✅ Mark: [x] for completed best practice tasks
✅ Update: Status fields (Planning → In Progress → Complete)
✅ Move: Completed items to "Recently Completed" section
✅ Update: "Last Updated" date at top
❌ Don't: Remove completed items or change priority structure
```

---

## 🎯 AI Agent Checklist

Before AI starts any task, it should confirm:

```
Pre-Task Checklist:
[ ] Read Implementation Priority Guide for current week/phase
[ ] Read relevant section of core_code_quality_plan.md OR roadmap
[ ] Understand the specific standards to follow
[ ] Know which files to analyze/modify
[ ] Know where to update progress

During Task:
[ ] Search for duplicates before adding new content
[ ] Follow established naming conventions
[ ] Apply coding standards from copilot-instructions.md
[ ] Create changes in feature branch (not main)
[ ] Write proper commit messages

Post-Task:
[ ] Update progress in relevant planning document
[ ] Mark checkboxes [x] for completed items
[ ] Add completion notes with date
[ ] Update "Last Updated" timestamps
[ ] Suggest next task from the plan
```

---

## 💡 Advanced AI Delegation Patterns

### Pattern 1: Multi-Day Tasks
```
For tasks spanning multiple days:

Day 1: "Audit all Python files, create issue list"
Day 2: "Fix Critical and High priority issues from yesterday's list"
Day 3: "Fix Medium priority issues, update documentation"

Each day:
- AI references yesterday's work
- Updates progress continuously
- Commits at end of day with summary
```

### Pattern 2: Iterative Refinement
```
Round 1: "Audit app.py, list all issues"
Round 2: "For issue #1 (SECRET_KEY), propose fix"
Round 3: "Apply approved fix, test, commit"
Round 4: "Move to issue #2..."

Benefits:
- You review each change
- Prevents large, risky changes
- Easier to track progress
```

### Pattern 3: Parallel Tracks
```
Monday AM: "Set up Python linting in CI" (Infrastructure track)
Monday PM: "Audit app.py" (Code quality track)
Tuesday AM: "Test CI on app.py changes" (Integration)
Tuesday PM: "Audit db_utils.py" (Code quality track)

AI manages both tracks:
- Updates both core_code_quality_plan.md and roadmap
- Ensures code changes trigger CI
- Verifies standards are enforced
```

---

## 🚀 Example: Complete Week 1, Day 1 Session

### Your Prompt:
```
I'm starting the mockCMMS Implementation Priority Guide.

Current: Week 1, Day 1 (Foundation Setup)

Please read:
1. docs/IMPLEMENTATION_PRIORITY_GUIDE.md (Week 1, Day 1 section)
2. docs/mockCMMS_roadmap.md (Git Workflow Standards section)
3. .github/copilot-instructions.md (Git workflow section)

Tasks for today:
1. Create .github/PULL_REQUEST_TEMPLATE.md
2. Enable branch protection on main (I'll do this in GitHub UI)
3. Create GitHub Project board structure (I'll do this in GitHub UI)

Please help with Task 1: Create the PR template.

Requirements:
- Include all sections from the Implementation Guide
- Follow conventional commits format for title
- Include testing checklist
- Include standards compliance checklist
- Show me the template before creating the file
```

### AI Response:
```
I've read the planning documents. Here's the proposed PR template:

[Shows template content]

Does this look good? Should I:
1. Create the file?
2. Make any changes first?
```

### You Approve:
```
Looks good! Please:
1. Create the file
2. Update docs/IMPLEMENTATION_PRIORITY_GUIDE.md:
   - Mark [x] for "Create PR template" under Week 1, Day 1
   - Add completion note with today's date
3. Suggest the next task for Day 1
```

### AI Completes:
```
✅ Created .github/PULL_REQUEST_TEMPLATE.md
✅ Updated docs/IMPLEMENTATION_PRIORITY_GUIDE.md
✅ Next task: Enable branch protection (you'll do via GitHub UI)

After you complete branch protection, the next code task is:
Day 2, Task 1: Update CONTRIBUTING.md with code standards

Would you like me to prepare that now, or wait until tomorrow?
```

---

## 🎓 Training AI on Your Project

### First Session with New AI Agent

Use this comprehensive prompt:

```
I'm working on the mockCMMS project, an open-source CMMS (Computerized 
Maintenance Management System) built with Flask.

Project Structure:
- Main app: src/ (Flask app, routes, templates, static files)
- Modular apps: apps/planning, apps/reports
- Documentation: docs/
- Tests: tests/

I'm following a 6-week improvement plan with two parallel tracks:
1. Code quality audit (clean up existing code)
2. Best practices setup (prevent future issues)

The master plan is in: docs/IMPLEMENTATION_PRIORITY_GUIDE.md

Please:
1. Read that file completely
2. Read .github/copilot-instructions.md for project standards
3. Tell me what week/phase you think I should be in based on git history
4. Suggest what task to start with

After you understand the project, I'll give you specific tasks following 
the Implementation Priority Guide.
```

---

## 📊 Progress Tracking for AI

AI should maintain progress tracking like this:

### In IMPLEMENTATION_PRIORITY_GUIDE.md:
```markdown
## Week 1: Foundation Setup
- [x] Day 1: PR Template (Completed 2025-12-11)
- [x] Day 1: Branch Protection (Completed 2025-12-11)
- [x] Day 1: Project Board (Completed 2025-12-11)
- [ ] Day 2: Update CONTRIBUTING.md (In Progress)
- [ ] Day 2: Security Setup
...
```

### In core_code_quality_plan.md:
```markdown
### Phase 1: Python Backend Analysis
- [x] src/app.py - Audited 2025-12-11 (5 issues found, 5 fixed)
- [ ] src/services/db_utils.py - In Progress
- [ ] src/routes/api.py
...
```

### In mockCMMS_roadmap.md:
```markdown
- [x] Implement Git Workflow Standards (Completed 2025-12-11)
  - Created PR template
  - Enabled branch protection
  - Documented commit message standards
- [ ] Implement Security & Access Control Standards (In Progress)
...
```

---

## ✅ Success Criteria

You know AI understands the project when it:

✅ References the correct planning documents without being asked  
✅ Knows what week/phase you're in  
✅ Suggests next tasks from the plan  
✅ Updates progress in correct documents  
✅ Doesn't create duplicate content  
✅ Follows established coding standards  
✅ Asks for approval before major changes  
✅ Writes proper commit messages  
✅ Cross-references related tasks  

---

## 🎯 Quick Reference Commands

### Check Current Status
```
"What week/phase am I on according to the Implementation Priority Guide?"
"What tasks are marked complete vs incomplete in core_code_quality_plan.md?"
"What's the next task I should work on?"
```

### Start New Task
```
"I want to work on [Task Name] from Week [X].
Please read the relevant docs and help me with this task."
```

### Update Progress
```
"We just completed [Task Name].
Please update the progress in all relevant planning documents."
```

### Verify Standards
```
"Check if [file/code] follows the standards in copilot-instructions.md"
"Does this commit message follow conventional commits format?"
```

---

## 🎉 Final Tips

### Do's ✅
- ✅ Always reference specific documents and sections
- ✅ Provide context (week, phase, task)
- ✅ Request approval before changes
- ✅ Ask AI to update progress tracking
- ✅ Work on one task at a time
- ✅ Verify AI read the correct documents

### Don'ts ❌
- ❌ Assume AI remembers previous sessions
- ❌ Give vague instructions ("make it better")
- ❌ Let AI make changes without approval
- ❌ Skip progress tracking updates
- ❌ Work on multiple unrelated tasks simultaneously
- ❌ Forget to verify AI's proposed changes

---

**Remember:** AI is a powerful tool, but YOU are the project owner. AI proposes, you approve. AI implements, you verify. AI updates docs, you review.

**The documents are your contract with the AI** - they ensure consistent, high-quality work across all sessions.

---

**Last Updated:** December 11, 2025  
**Next Review:** After Week 1 completion (adjust based on experience)

