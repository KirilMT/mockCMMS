# How to Contribute

Welcome to the internal development guide for the **mockCMMS** project.

This document is intended for the **private organization team** working on this repository. It outlines our standards, workflows, and best practices for collaborating effectively.

> [!IMPORTANT]
> **Confidentiality:** This is a private repository. Do not share code, secrets, or internal documentation publicly.

---

## 📹 Video Tutorials & Media

> **🚧 Under Construction:** We are currently building a library of video tutorials to help new team members get up to speed.

- **[Coming Soon]** Project Overview & Architecture Walkthrough
- **[Coming Soon]** Setting Up Your Development Environment
- **[Coming Soon]** How to Create a New Modular App

---

## 🏗️ Architecture Note: Complexity Management

**Guideline:** If a component within the core `src/` directory becomes too complex or isolated in its functionality, it should be migrated to its own modular application in `apps/`.

**Triggers for Migration:**
- The component requires its own database tables that are loosely coupled to the core.
- The component has a distinct set of routes and views.
- The component is becoming a "mini-app" within the main app.

**Process:**
1. Create a new directory in `apps/<new-app-name>`.
2. Follow the modular app structure (see `apps/planning` for reference).
3. Move logic, templates, and static assets.
4. Register the new app in `src/app.py` behind a feature flag.

---

## 💻 Development Setup

### Prerequisites

- **Python 3.12** or higher
- **Node.js** (for JavaScript tools)
- **Git**

### Step 1: Initial Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mockCMMS
   ```

2. **Run the setup script:**
   ```powershell
   .\scripts\setup.ps1
   ```
   This script creates the virtual environment and installs core dependencies.

3. **Activate the environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

### Step 2: Install Development Tools

To install testing tools (Playwright, Jest) and linters:

```powershell
.\scripts\setup-dev.ps1
```

### Step 3: Run the Application

```bash
python run.py
```
Access at `http://127.0.0.1:5000`.

---

## 🤝 Community Guidelines (Internal Team)

### Our Pledge

We pledge to make participation in our team a harassment-free experience for everyone. We value **collaboration, respect, and constructive feedback**.

### Our Standards

- **Empathy:** Be kind and patient with team members.
- **Constructive Code Reviews:** Focus on the code, not the person. explain *why* a change is requested.
- **Responsibility:** Own your mistakes and learn from them.
- **Privacy:** Protect internal data and secrets.

---

## 📝 Coding Standards

### 1. Code Style & Formatting

- **Python:** Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/). We use `black` for formatting and `flake8` for linting.
- **JavaScript:** Follow the [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html).
- **General:** Code should be clear, concise, and well-documented.

### 2. Separation of Concerns

- **No Inline Styles:** Use `.css` files.
- **No Inline Scripts:** Use `.js` files.
- **No Inline Event Handlers:** Use `addEventListener`.

### 3. Comment Standards

- **Explain "Why":** Comments should explain intent, not implementation.
- **No Issue References:** Do not put `// Fix for #123` in code. Use commit messages.
- **Professionalism:** Use proper grammar. Remove commented-out code.

### 4. Testing Standards

**Core Principle: Tests are the safety net.**

1. **Run Tests Locally:** Always run `pytest tests/` before pushing.
2. **Write Tests First:** Create tests for new features before implementing them.
3. **Maintain Coverage:** Aim for >85% coverage.

---

## 🔄 Contribution Process

### 1. Issue Tracking
All work starts with a GitHub Issue.
- **Bug Reports:** Use the Bug Report template.
- **Feature Requests:** Use the Feature Request template.

### 2. Branching Strategy
- **Main Branch:** `main` (Protected, production-ready).
- **Feature Branches:** `feature/<name>` or `bugfix/<issue-id>`.
- **Never push directly to `main`.**

### 3. Pull Requests (PRs)
- Open a PR for every change.
- Fill out the PR template completely.
- Request a review from a team member.
- Ensure all CI checks pass.

### 4. Commit Messages
Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
`type(scope): description`

Examples:
- `feat(planning): add shift rotation logic`
- `fix(core): resolve startup crash in db_utils`
- `docs(readme): update installation steps`

---

## 🔑 Personal Access Tokens (PATs)

To push to this repository, use a PAT with `repo` scope.
1. Settings > Developer settings > Personal access tokens.
2. Generate new token (classic).
3. Select `repo` scope.
4. Use this token as your password when pushing.

---

## ❓ Getting Help

- **Team Chat:** [Internal Link]
- **Documentation:** See `docs/` directory.
- **Issues:** Search existing GitHub issues.
