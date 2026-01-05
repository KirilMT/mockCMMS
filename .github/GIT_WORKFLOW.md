# Professional Git Workflow Guide

This document outlines the standard process for contributing to this project.
Following these steps ensures the `master` branch remains stable and all changes
are properly managed.

---

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
branch from an up-to-date `master`.

**Step 2.1: Sync Your Local `master` Branch**

Make sure your local `master` branch has the latest changes from the remote
repository.

```sh
# Switch to the master branch
git checkout master

# Pull the latest changes from the remote `master`
git pull origin master
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

Now you are on your new branch and can work safely without affecting `master`.

**Step 3.1: Do Your Work and Commit Changes**

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
from `master`, you should sync it regularly. This is especially important before
creating a pull request.

```sh
# Switch to the master branch and pull the latest changes
git checkout master
git pull origin master

# Switch back to your feature branch
git checkout new-feature-name

# Merge the latest master into your feature branch
git merge master

# If there are any conflicts, resolve them now, then commit the merge.
```

**Step 3.3: Verify Tracking Status**

It is **critical** to ensure your local branch is tracking the remote branch.

1.  **Check tracking status:**
    ```sh
    git branch -vv
    ```
    **How to interpret the output:**
    -   **Tracked (Good):** You will see the remote branch in brackets next to the branch name.
        *Example:* `* feature-branch  1234567 [origin/feature-branch] Commit message`
    -   **Untracked (Needs Action):** You will **NOT** see any `[origin/...]` reference in brackets.
        *Example:* `* feature-branch  1234567 Commit message`

2.  **Action for Untracked Branches:**
    If your branch is **untracked**, do NOT use `git push`. You must use `gh pr create` to push the branch and create the PR simultaneously.

    ```sh
    # Pushes the branch AND creates the PR
    # Use --draft if you are not ready for review
    gh pr create --base main --head <your-branch-name> --fill
    ```

**Step 3.4: Push Changes (Tracked Branches Only)**

If your branch is already tracked (you see `[origin/...]`), you can simply push updates:

```sh
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

#### Automated Version Management (Recommended)

**Use the release manager script to automate version updates:**

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

#### Manual Version Updates (If Not Using Script)

**Required Updates:**

1. **Update CHANGELOG.md** (follow
   [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format):
   - Main app: `/CHANGELOG.md`
   - planning: `/apps/planning/CHANGELOG.md`
   - Add new version entry with date and categorized changes
     (Added/Changed/Removed/Fixed)

2. **Update README.md version footer**:
   - Main app: `/README.md`
   - planning: `/apps/planning/README.md`
   - Ensure version numbers match between CHANGELOG.md and README.md
   - Update "Last Updated" date

**Example:**

```markdown
**Version:** 1.2.1 | **Last Updated:** January 27, 2025
```

This version information will be used for creating Git tags and releases.

---

### 5. Finishing Your Work (Pull Request)

If you haven't created a Pull Request yet (e.g., you were working on an existing branch), create one now.

**Step 5.1: Create Pull Request via CLI (Recommended)**

```sh
# Create the PR if not already done
gh pr create --base main --head <your-branch-name> --fill
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

Now, update your local `master` branch with the changes you just merged on
GitHub.

```sh
# Switch back to your local master branch
git checkout master

# Pull the latest changes from the remote (which includes your merged PR)
git pull origin master
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
creating a new branch from your up-to-date `master`.
