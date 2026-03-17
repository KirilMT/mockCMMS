# How to Contribute

We'd love to accept your patches and contributions to this project. There are
just a few small guidelines you need to follow.

## Commit Message & Release Automation

To ensure high-quality releases and clear project history, all commits and releases must follow these rules:

### Supported Commit Types

The following commit types are supported for release automation and changelog generation:

- feat, fix, chore, refactor, perf, remove, revert, docs, test, style, build, ci

Use only these types in your commit messages for releases.

### Commit Message Standards & Enforcement

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format. This is enforced by a `commit-msg` hook and a pre-filled `.gitmessage` template, which are set up automatically by `scripts/setup-dev.ps1`.

- **Template:** When you run `git commit`, the `.gitmessage` template will be loaded in your editor.
- **Enforcement:** Commits that do not follow the required format will be rejected.

#### Format Example

```
feat(module): add new feature

This is a detailed description of the change.
- Bullet 1
- Bullet 2
```

### Release Process

Releases are managed through the **CI/CD pipeline** using Google Release Please:

1. Merge your changes to `main` via a pull request.
2. The Release Please GitHub Action automatically opens (or updates) a "Release PR" titled "chore(main): release x.y.z".
3. This automated PR gathers all your Conventional Commits and generates the `CHANGELOG.md` and version bumps in `pyproject.toml` and `README.md`.
4. When you are ready to cut a release, simply **merge the Release PR**.
5. GitHub Actions will then automatically tag the commit and create a GitHub Release.

See also: `.github/GIT_WORKFLOW.md` for workflow details (including "Why a Two-PR Workflow?").

> [!NOTE]
> Why the extra PR? Release Please uses a **Two-PR Workflow** (an industry standard used by Google, Node.js, etc.). Instead of cutting a new release instantly every single time a developer merges code, it gathers all changes into a "Release PR" batch. Maintainers can review the drafted changelog there, and release them all at once whenever they are ready.

### Commit Message Structure

#### First line

The first line of the change description is a short one-line summary of the change, following the structure `type(scope): description`:

- **type:** One of the supported commit types above.
- **scope:** The name of the package or component affected by the change (e.g., `planning`, `reporting`, `mockCMMS`, `advanced-table`, `ci`, `docs`), provided in parentheses before the colon.
- **description:** A short summary, written to complete the sentence "This change modifies the codebase to ..." (no capital letter, not a complete sentence, no trailing period).

Keep the first line as short as possible (preferably under 76 characters). Follow the first line by a blank line.

#### Main content

The rest of the commit message should provide context for the change and explain what it does. Write in complete sentences with correct punctuation. Don't use HTML, Markdown, or any other markup language. Add any relevant information, such as benchmark data if the change affects performance.

#### Referencing issues

To automatically close an issue when a pull request (PR) is merged on GitHub, include a **Closing Keyword** followed immediately by the issue number in the PR's description or a commit message.

**Supported Closing Keywords:**

| Keyword      | Example        |
| :----------- | :------------- |
| **Close**    | `Close #12`    |
| **Closes**   | `Closes #12`   |
| **Closed**   | `Closed #12`   |
| **Fix**      | `Fix #12`      |
| **Fixes**    | `Fixes #12`    |
| **Fixed**    | `Fixed #12`    |
| **Resolve**  | `Resolve #12`  |
| **Resolves** | `Resolves #12` |
| **Resolved** | `Resolved #12` |

**Important Rules:**

1.  **Strict Syntax:** The keyword must be followed by the issue number (e.g., `#12`).
2.  **Multiple Issues:** To close multiple issues, repeat the keyword for each one.
    - ✅ **Correct:** `Closes #1, Closes #2, Fixes #3`
    - ❌ **Incorrect:** `Closes #1, #2, #3`
3.  **Real Issue IDs:** Use the integer ID assigned by GitHub (e.g., `#42`), not custom references (e.g., `#R1` or `Bug #42`).
4.  **No "Fix:" Prefix:** The conventional commit type `fix:` does **not** trigger a close. You must still include `Fixes #12` in the body or footer.

**Common Pitfalls (Why your issue didn't close):**

- Using `fix: Bug #12` (The `fix:` prefix is for humans/changelogs, not GitHub automation).
- Using `#R1` instead of `#1`.
- Putting text between the keyword and number: `Fixes critical bug #12` (Will not work).

If the change is a partial step towards the resolution of the issue, write "For `#12345`" instead. This will leave a comment in the issue linking back to the pull request, but it will not close the issue when the change is applied.

## How to Contribute

We'd love to accept your patches and contributions to this project. There are
just a few small guidelines you need to follow.

## 🚀 Getting Started (Onboarding)

New to the project? Follow this learning path to get up to speed:

### Step 1: Understand the Big Picture (1-2 hours)

1.  Read the **[mockCMMS Roadmap](../docs/mockCMMS_roadmap.md)** to understand the project's vision.
2.  If working on a specific app, read its roadmap in `apps/<app_name>/docs/`.
3.  Read this **CONTRIBUTING guide** in its entirety.

### Step 2: Set Up Your Environment (2-3 hours)

1.  Follow the setup instructions in **[README.md](README.md)**.
2.  Run the test suite locally: `python scripts/validate_code.py --backend` (or `pytest`) to ensure everything works.
3.  Familiarize yourself with the **[Git Workflow](.github/GIT_WORKFLOW.md)**.

### Step 3: Dive into the Codebase (4-6 hours)

1.  Start with `src/app.py` to understand the Flask factory pattern.
2.  Explore routes in `src/routes/`.
3.  Review `src/services/db_utils.py` for database interactions.

## Community Guidelines

### Our Pledge

We, as members, contributors, and leaders, pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

### Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

- Demonstrating empathy and kindness toward other people
- Being respectful of differing opinions, viewpoints, and experiences
- Giving and gracefully accepting constructive feedback
- Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
- Focusing on what is best not just for us as individuals, but for the overall
  community

Examples of unacceptable behavior include:

- The use of sexualized language or imagery, and sexual attention or advances of
  any kind
- Trolling, insulting or derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or email address,
  without their explicit permission
- Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards and
will take appropriate and fair corrective action in response to any behavior
that they deem inappropriate, threatening, offensive, or harmful.

Community leaders have the right and responsibility to remove, edit, or reject
comments, commits, code, wiki edits, issues, and other contributions that are
not aligned to this Code of Conduct, and will communicate reasons for moderation
decisions when appropriate.

### Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.
Examples of representing our community include using an official e-mail address,
posting via an official social media account, or acting as an appointed
representative at an online or offline event.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the project team. All complaints will be reviewed and investigated
promptly and fairly.

All community leaders are obligated to respect the privacy and security of the
reporter of any incident.

## Coding Standards

To maintain a high level of code quality, all contributions must adhere to the
following standards.

### 1. Code Style & Formatting

- **Python:** All Python code must follow the
  [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).
- **JavaScript:** All JavaScript code should adhere to the
  [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html).
- **General:** Code should be clear, concise, and well-formatted.

### 2. Separation of Concerns

To ensure the project is maintainable, we strictly enforce the separation of
logic, styling, and structure.

- **No Inline Styles:** Do not use `style="..."` attributes in HTML. Use
  external CSS classes instead.
- **No Inline Scripts:** Do not use `<script>` tags within HTML files. All
  JavaScript must be in external `.js` files.
- **No Inline Event Handlers:** Do not use `onclick="..."` or other inline event
  handlers. Use event listeners in your JavaScript files.

### 3. Comment Standards

Good comments are crucial for explaining the "why" behind the code.

- **Explain Intent, Not Implementation:** Code should be self-explanatory.
  Comments should clarify complex business logic, algorithms, or non-obvious
  decisions.
- **No Issue References:** Do not reference bug or issue numbers in code
  comments (e.g., `// Fix for #123`). Use commit messages for this.
- **Professionalism:** Use proper grammar and punctuation. Avoid commented-out
  code blocks; remove them instead.

## 🛠️ Development Tools & Scripts

We provide automated scripts to make your life easier. Use them!

### 1. `scripts/validate_code.py` (The Validator)

**Simulates the CI pipeline locally.** Runs all linters, formatters, and tests.

```bash
python scripts/validate_code.py            # Health Mode: Force all apps ENABLED
python scripts/validate_code.py --quick    # Developer Mode: Honors .env, skips slow tests
python scripts/validate_code.py --backend  # Python only
python scripts/validate_code.py --frontend # JS/CSS only
```

### 3. `scripts/build_portable.py` (The Packager)

**Generates a zero-installation, portable ZIP distribution of the app.** Use this when you need to send a demo version to management, stakeholders, or testers who don't have Python or Git installed.

```bash
python scripts/build_portable.py
```

It automatically embeds a Python 3.12 interpreter, pre-seeds a fresh database, isolates dependencies, and scripts a one-click `START_mockCMMS.bat` browser-opening interface.

## 🏆 Critical Best Practices (Do's and Don'ts)

### ✅ Do's

- **Run Validation Locally:** `python scripts/validate_code.py` must pass before you commit.
- **Use Feature Branches:** Never work directly on `main`.
- **Write Clear Commits:** Follow the `feat:`, `fix:` conventions.

### ❌ Don'ts

- **Don't Merge Failing Tests:** If CI fails, your PR is not ready.
- **Don't Refactor Without Tests:** Verification is mandatory.
- **Don't Ignore Linters:** Warnings are there for a reason.

### 4. Testing Standards

**As of December 2025, this project follows a strict test-first approach with
comprehensive test coverage.**

#### Testing Philosophy

**Core Principle: Tests are the safety net for all code changes.**

#### When Adding New Code

1. **Check for existing tests** - Search `tests/` directory for related test
   files
2. **Run existing tests** - Verify current tests pass: `pytest tests/`
3. **Create/Update tests FIRST** - Write tests for new functionality before
   implementing
4. **Implement code** - Write the actual feature/fix
5. **Verify tests pass** - All tests (old + new) must pass
6. **Check coverage** - Run `pytest --cov=src tests/` to ensure new code paths
   are tested

#### When Modifying Existing Code

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

#### Test Organization

Tests are organized in 6 categories:

- `tests/unit/` - Fast, isolated component tests
- `tests/functional/` - API and route endpoint tests
- `tests/integration/` - End-to-end workflow tests
- `tests/security/` - Authentication, validation, security
- `tests/performance/` - Scalability and optimization
- `tests/reliability/` - Error handling and robustness

**Separate Test File When:**

- Different testing concern (Performance vs Functionality)
- Different security level (Auth tests need extra scrutiny)
- Different execution timing (Slow integration tests)
- Cross-cutting concern (Validation applies to all components)

**Combine Tests When:**

- Same component/module (All API tests in test_api_routes.py)
- Same testing level (Unit tests for db_utils together)
- Same execution context (Fast unit tests together)
- Natural cohesion (CRUD operations for same resource)

#### Coverage Philosophy

- Coverage isn't about test count—it's about testing all code paths
- Test success cases, failure cases, and edge cases
- **Target**: 80-85% overall coverage (current: 82.99%)
- **Critical paths**: 90%+ coverage (auth, API, database)

#### Modular App Testing

MockCMMS uses a **Smart Collector** logic. Tests for apps in `apps/` (Planning, Reporting, etc.) are dynamically skipped if disabled via environment variables.

- **Development Speed:** Use `$env:PLANNING_ENABLED="false"` to skip tests for modules you aren't changing.
- **Stability Enforcement:** The validation script default (Health Mode) overrides these flags to ensure 100% project health before PR submission.

#### Avoiding Test Duplicates

1. **Search before creating** - Use `findstr /S "def test_" tests\*.py`
   (Windows) or `grep -r "def test_" tests/` (Unix)
2. **Check test names** - Look for similar test names in the same module
3. **Review test file** - Read existing tests in the file you're modifying
4. **Consolidate if needed** - Merge duplicate tests into comprehensive ones

#### Before Submitting a Pull Request

1. Run the full test suite: `pytest tests/`
2. Ensure all tests pass
3. Add tests for new functionality
4. Maintain or improve code coverage: `pytest --cov=src tests/`
5. Verify coverage meets targets (80-85% overall)

**Reference:** See `tests/README.md` for test suite organization and complete
testing strategy.

## Contribution Process

### Before contributing code

Before doing any significant work, open an issue to propose your idea and ensure
alignment. You can either
[file a new issue](https://github.com/KirilMT/CMMS/issues/new/choose), or
comment on an [existing one](https://github.com/KirilMT/CMMS/issues). A pull
request (PR) that does not go through this coordination process may be closed to
avoid wasted effort.

## Checking the issue tracker

We use GitHub issues to track tasks, bugs, and discussions. All changes, except
trivial ones, should start with a GitHub issue. This process gives everyone a
chance to validate the design, helps prevent duplication of effort, and ensures
that the idea fits inside the goals for the language and tools. It also checks
that the design is sound before code is written; the code review tool is not the
place for high-level discussions.

Always include a clear description in the body of the issue. The description
should provide enough context for any team member to understand the problem or
request without needing to contact you directly for clarification.

## Sending a pull request

All code changes must go through a pull request. First-time contributors should
review
[GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow).

Before sending a pull request, it should include tests if there are logic
changes, copyright headers in every file, and a commit message following the
conventions in "Commit messages" section below.

A pull request can be opened from a branch within the repository or from a fork.
External contributors are only able to open pull requests from forks, but team
members with write access can choose to open a pull request from a repository
branch.

If you open a pull request from a personal fork, you should allow repository
maintainers to make edits to your fork by turning on "Allow edits from
maintainers". Please see
[creating a pull request from a fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork)
in the official GitHub documentation for details.

## Personal Access Tokens (PATs)

To push changes to the repository, you must authenticate using a Personal Access
Token (PAT) instead of a password. PATs are more secure and are required for
command-line access to GitHub.

### Creating a PAT

1.  Go to your GitHub **Settings** > **Developer settings** > **Personal access
    tokens**.
2.  Click **Generate new token**.
3.  Give your token a descriptive name (e.g., "mockCMMS-dev").
4.  Select the desired scopes. For repository access, the `repo` scope is
    typically sufficient.
5.  Click **Generate token** and copy the token. **You will not be able to see
    it again.**
6.  Store the token securely in a password manager.

### Using a PAT

When prompted for a password while using Git on the command line, paste your
PAT.

## The review process

This section explains the review process in detail and how to approach reviews
after a pull request has been sent for review.

### Getting a code review

Before creating a pull request, make sure that your commit message follows the
suggested format. Otherwise, it can be common for the pull request to be sent
back with that request without review.

After creating a pull request, request a specific reviewer if relevant, or leave
it for the default group.

### Merging a pull request

Pull request titles and descriptions must follow the
[commit messages](#commit-messages) conventions. This enables approvers to
review the final commit message.

Once the pull request has been approved and all checks have passed, click the
[Squash and Merge](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-commits)
button. The resulting commit message will be based on the pull request's title
and description.

### Reverting a pull request

If a merged pull request needs to be undone, for reasons such as breaking the
build, the standard process is to
[revert it through the GitHub interface](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/reverting-a-pull-request).
To revert a pull request:

1.  Navigate to the merged pull request on GitHub.
2.  Click the **Revert** button. This action automatically creates a new branch
    and a pull request containing the revert commit.
3.  Edit the pull request title and description to comply with the
    [commit message guidelines](#commit-messages).
4.  The newly created revert pull request should be reviewed and merged
    following the same process as any other pull request.

Using the GitHub "Revert" button is the preferred method over manually creating
a revert commit using `git revert`.

### Keeping the pull request dashboard clean

We aim to keep https://github.com/KirilMT/CMMS/pulls clean so that we can
quickly notice and review incoming changes that require attention. Given that
goal, please do not open a pull request unless you are ready for a code review.
Draft pull requests and ones without author activity for more than one business
day may be closed (they can always be reopened later). If you're still working
on something, continue iterating on your branch without creating a pull request
until it’s ready for review.

### Addressing code review comments

Creating additional commits to address reviewer feedback is generally preferred
over amending and force-pushing. This makes it easier for reviewers to see what
has changed since their last review. Pull requests are always squashed and
merged. Before merging, please review and edit the resulting commit message to
ensure it clearly describes the change.

After pushing,
[click the button](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/requesting-a-pull-request-review#requesting-reviews-from-collaborators-and-organization-members)
to ask a reviewer to re-request your review.

## Leaving a TODO

When adding a TODO to the codebase, always include a link to an issue, no matter
how small the task. Use the format:

''' // TODO(https://github.com/KirilMT/CMMS/issues/): explain what needs to be
done '''

This helps provide context for future readers and keeps the TODO relevant and
actionable as the project evolves.
