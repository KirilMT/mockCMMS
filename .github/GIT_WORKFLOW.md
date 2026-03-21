# Professional Git Workflow Guide

This document outlines the standard process for contributing to this project.
Following these steps ensures the `main` branch remains stable and all changes
are properly managed.

---

> **⚠️ CRITICAL RULE: NEW BRANCHES REQUIRE A PULL REQUEST**
>
> When you create a **new local branch** that does not exist on GitHub yet:
>
> - **NEVER** use `git push -u origin <branch>` to push it directly
> - **ALWAYS** use `gh pr create` to push AND create a PR in one step
>
> When you are on a branch that **already tracks a remote branch** (you see `[origin/...]` in `git branch -vv`):
>
> - You can use `git push` normally to push additional commits
>
> **Why?** Pushing a new branch without a PR leaves orphan branches on GitHub with no review process.

## Supported Commit Types

The following commit types are supported for release automation and changelog generation:

- feat, fix, chore, refactor, perf, remove, revert, docs, test, style, build, ci

Use only these types in your commit messages for releases.

### 1. Initial Setup (First Time on a New Machine)

If you are starting on a new computer or don't have the project locally, you
need to clone it from GitHub.

```sh
# Clone the repository from GitHub to your local machine
git clone https://github.com/KirilMT/CMMS CMMS

# Navigate into the newly created project directory
cd CMMS
```

---

### 2. Starting New Work (Creating a Feature Branch)

Before starting any new feature, bugfix, or improvement, always create a new
branch from an up-to-date `main`.

**Step 2.1: Sync Your Local `main` Branch**

Make sure your local `main` branch has the latest changes from the remote
repository.

```sh
# Switch to the main branch
git checkout main

# Pull the latest changes from the remote `main`
git pull origin main
```

**Step 2.2: Create Your New Branch**

Create a new branch with a descriptive name (e.g., `fix-login-bug`,
`add-user-profiles`, `refactor-database-queries`).

```sh
# Create a new branch and switch to it in one command
# Replace `new-feature-name` with your actual branch name
git checkout -b new-feature-name
```

---

### 3. During Development (Committing and Pushing)

Now you are on your new branch and can work safely without affecting `main`.

**Step 3.1: The 5-Step Quality Loop (Iterative Process)**
Before you commit, apply this loop to every file you touch:

1.  **Check:** Run linters `ruff check src/`.
2.  **Format:** Run formatters `black src/`.
3.  **Test:** Run `pytest` to ensure no regressions.
4.  **Audit:** Self-review logic and complexity.
5.  **Commit:** Only when 1-4 pass.

_Tip: `python scripts/validate_code.py --quick` does 1-3 for you while honoring your `.env` settings!_

**Step 3.2: Do Your Work and Commit Changes**

Make your code changes, then commit them with clear, descriptive messages. You
can make as many commits as you need.

```sh
# Stage your changed files for the commit
git add .

# Commit the staged files with a message
git commit -m "Add a clear and concise commit message here"
```

**Step 3.2: Keep Your Branch Updated**

To prevent merge conflicts and ensure your feature branch has the latest changes
from `main`, you should sync it regularly. This is especially important before
creating a pull request.

```sh
# Switch to the main branch and pull the latest changes
git checkout main
git pull origin main

# Switch back to your feature branch
git checkout new-feature-name

# Merge the latest main into your feature branch
git merge main

# If there are any conflicts, resolve them now, then commit the merge.
```

**Step 3.3: Verify Tracking Status Before Pushing**

It is **critical** to check whether your branch is already linked to a remote branch.

1.  **Check tracking status:**

    ```sh
    git branch -vv
    ```

    **How to interpret the output:**
    - **Tracked (Can push directly):** You will see the remote branch in brackets.
      _Example:_ `* feature-branch  1234567 [origin/feature-branch] Commit message`
    - **Untracked (Must create PR):** You will **NOT** see any `[origin/...]` reference.
      _Example:_ `* feature-branch  1234567 Commit message`

2.  **Decision Tree:**

    | Branch Status                     | Action Required                            |
    | --------------------------------- | ------------------------------------------ |
    | **Untracked** (no `[origin/...]`) | Use `gh pr create` - creates branch AND PR |
    | **Tracked** (has `[origin/...]`)  | Use `git push` - pushes to existing remote |

**Step 3.4: Push to GitHub**

**Option A: New Branch (Untracked) → Create PR**

⚠️ **NEVER use `git push -u origin <branch>` for new branches!**

```sh
# This pushes the branch AND creates the PR in one step
# ⚠️ Ensure the PR Title strictly follows Conventional Commits! Do NOT use --fill.
gh pr create --base main --head <your-branch-name> --title "feat(scope): your descriptive title" --body "Your detailed PR body"

# Or create as draft if not ready for review
gh pr create --base main --head <your-branch-name> --title "feat(scope): your descriptive title" --body "Your detailed PR body" --draft
```

**Option B: Existing Branch (Tracked) → Push Updates**

If your branch is already tracked (you see `[origin/...]`):

```sh
# Simply push your new commits
git push
```

---

### 4. Versioning and Documentation

This project follows Semantic Versioning (SemVer) and maintains changelogs for
all components. **Before creating a pull request**, you must update version
information:

**Version Format:** `MAJOR.MINOR.PATCH` (e.g., `1.1.0`)

- **MAJOR (`1.x.x`):** Increment for incompatible API changes.
- **MINOR (`x.1.x`):** Increment for new, backward-compatible features.
- **PATCH (`x.x.1`):** Increment for backward-compatible bug fixes.

#### Automated Releases (Google Release Please)

Releases and changelog generation are fully automated by **Google Release Please**:

1. Merge your changes (with Conventional Commits) to `main` via a pull request.
2. The Release Please action runs automatically and opens a **Release PR**.
3. This automated PR contains the updated `CHANGELOG.md` and version bumps for all relevant files (e.g., `pyproject.toml`, `README.md`).
4. Review the Release PR. When you are ready to cut the actual release, simply **merge the Release PR**.
5. Upon merging, the action automatically creates the git tag and the GitHub Release on the repository.

You do **not** need to manually edit `CHANGELOG.md` or version numbers in your feature branches. Release Please assumes control of the versioning based entirely on your commit messages.

#### Why a Two-PR Workflow?

It may seem counter-intuitive to merge your code in one PR, and then have to merge a _second_ "Release PR" to actually publish it. But **this is an industry standard** (used by Google, Node.js, and many others) for several reasons:

1. **Batching:** Instead of releasing `1.1.1`, `1.1.2`, and `1.2.0` on the same day every time a developer merges code, Release Please accumulates all features/fixes into a single running "Release PR."
2. **Review:** The Release PR gives the maintainer a chance to read and review the auto-generated `CHANGELOG.md` _before_ the changelog logic is permanently locked into a Git tag or GitHub Release.
3. **Decoupling Deployment:** Developers can safely merge code to `main` instantly, without throwing the entire project into a live production release loop. Maintainers can release whenever they feel the batch of features is ready by merging the bot's PR.

---

### 5. Finishing Your Work (Pull Request)

If you haven't created a Pull Request yet (e.g., you were working on an existing branch), create one now.

**Step 5.1: Create Pull Request via CLI (Recommended)**

```sh
# Create the PR if not already done
# ⚠️ Ensure the PR Title strictly follows Conventional Commits! Do NOT use --fill.
gh pr create --base main --head <your-branch-name> --title "feat(scope): your descriptive title" --body "Your detailed PR body"
```

**Step 5.2: Mark as Ready (If Draft)**

If you created a Draft PR in Step 3.3, mark it as ready for review:

```sh
gh pr ready
```

---

### 6. Code Review & Merging

**Step 6.1: Automated Checks (CI/CD)**

This repository uses **Branch Protection Rules** to ensure quality.

- **Status Checks:** All GitHub Actions (tests, linting) **must pass** before merging.
- **Merge Blocked:** If checks fail, the "Merge" button will be disabled.
- **Fixing Failures:** If checks fail, fix the code locally, commit, and push again. The PR will update and re-run checks automatically.

**Step 6.2: Review Process**

1.  **Request Review:** Assign reviewers to your PR.
2.  **Address Feedback:** Make changes based on comments.
3.  **Approval:** Wait for approval from code owners.

**Step 6.3: Merge**

Once approved and checks pass:

1.  Click **"Merge pull request"**.
2.  Confirm the merge.

---

### 7. Handling Work-in-Progress (Creating a Draft Pull Request)

If your work is not yet finished but you want to get feedback, or simply want to
see your changes on GitHub, you should create a **Draft Pull Request**. This
signals to others that the work is still in progress.

**Why Use a Draft Pull Request?**

- **Clear Communication:** It makes it obvious that the code is not ready for a
  final review or merging.
- **Early Feedback:** You can ask for feedback on your approach before you are
  too far into the work.
- **Track Your Work:** It provides a clear link between your branch and the
  issue you are working on (e.g., issue #33).

**Step 6.1: How to Create a Draft Pull Request**

1.  Follow the same steps as opening a regular pull request (Step 5.1).
2.  On the "Open a pull request" screen, instead of clicking the "Create pull
    request" button, click the dropdown arrow next to it.
3.  Select **"Create draft pull request"** from the dropdown menu.
4.  In the title or description, it's a good practice to add "WIP:" (Work in
    Progress) and link the issue you are working on (e.g., `Fixes #33`).

**Step 6.2: How to Continue Working on a Draft PR**

1.  Continue to make commits to your local branch as usual
    (`git commit -m "..."`).
2.  When you are ready to update the draft PR on GitHub, simply push your
    changes:
    ```sh
    git push
    ```
3.  Your new commits will be automatically added to the draft pull request.

**Step 6.3: Marking the PR as Ready for Review**

Once you have finished your work and the draft PR is ready for a final review,
you can convert it to a regular pull request.

1.  Go to the pull request page on GitHub.
2.  Click the **"Ready for review"** button.

This will change the status of the PR and notify reviewers that it is ready to
be merged.

---

### 8. Cleaning Up After Merging

After your PR is merged, the final step is to clean up your local and remote
branches.

**Step 8.1: Delete the Remote Branch**

After merging on GitHub, a **"Delete branch"** button will appear. Click it to
delete the remote feature branch. This keeps the repository clean.

**Step 8.2: Update Your Local Repository**

Now, update your local `main` branch with the changes you just merged on
GitHub.

```sh
# Switch back to your local main branch
git checkout main

# Pull the latest changes from the remote (which includes your merged PR)
git pull origin main
```

**Step 8.3: Prune Stale Remote Branches**

Your local repository might still be tracking the remote branch you just
deleted. Run the following command to clean up these stale branches.

```sh
# Fetch the latest remote state and remove any remote-tracking branches that no longer exist
git fetch --prune
```

**Step 8.4: Delete Your Local Branch**

Finally, delete the local feature branch as it is no longer needed.

```sh
# Delete the local branch
git branch -d new-feature-name
```

This completes the workflow. You are now ready to start on the next task by
creating a new branch from your up-to-date `main`.

---

## Commit Message Enforcement & Template

All commits must use the Conventional Commits format. This is enforced by a `commit-msg` hook and a `.gitmessage` template, both set up automatically by `scripts/setup-dev.ps1`.

- **Format Example:**

  ```
  feat(module): add new feature

  Detailed body describing the change.
  ```

See `.github/CONTRIBUTING.md` for the full commit message structure and release process.
