# Visual Regression Testing Strategy

**Status:** Draft - Proposed for Implementation
**Last Updated:** February 2026
**Priority:** High

## Problem Statement

Visual regression tests (snapshots) inherently depend on the rendering engine of the operating system. Fonts, anti-aliasing, and pixel rounding differ significantly between:
- Windows (Local Developer Environment)
- Linux (GitHub Actions CI Environment)
- macOS (Some Developers)

This causes **"flaky" tests**: tests that pass locally but fail in CI, or vice-versa, often requiring high tolerances (e.g., 5%) that mask real UI bugs.

## Proposed Solution: Dockerized Testing Container

To ensure consistency, visual tests should ALWAYS run in the arguably "same" computer. We achieve this by running Playwright inside a **Docker container** which guarantees a Linux environment regardless of the host OS.

### 1. The Strategy

1.  **Local Development (Fast, Functional):**
    - Developers run tests locally (`npm run test:e2e`).
    - Visual assertions are **skipped** or set to **high tolerance** (soft mode) when running natively on Windows/Mac.
    - Focus: Logic verification, interaction testing.

2.  **Visual Verification (Strict, Docker):**
    - Developers run a special command (`npm run test:visual:docker`) before committing.
    - This spins up the *official Playwright Docker image*.
    - It runs the tests inside Linux.
    - Snapshots are generated/compared against the Linux baseline.

3.  **CI/CD (Strict, Native Linux):**
    - GitHub Actions runs on `ubuntu-latest`.
    - It matches the Docker container environment.
    - Tolerance is set to strict (e.g., 1%).

### 2. Implementation Plan

#### Step 1: Create Docker Compose Setup
Create `docker-compose.test.yml` in the root:

```yaml
services:
  playwright:
    image: mcr.microsoft.com/playwright:v1.49.0-jammy
    working_dir: /app
    volumes:
      - .:/app
    command: npx playwright test --project=chromium
    environment:
      - CI=true
```

#### Step 2: Add Convenience Scripts
Add scripts to `package.json`:

```json
"scripts": {
  "test:visual:update": "docker compose -f docker-compose.test.yml run --rm playwright npx playwright test --update-snapshots",
  "test:visual:check": "docker compose -f docker-compose.test.yml run --rm playwright"
}
```

#### Step 3: Standardize Config
In `playwright.config.js`, detect the environment:

```javascript
const isCI = !!process.env.CI;
const isDocker = !!process.env.DOCKER_CONTAINER;

module.exports = {
  // ...
  expect: {
    toHaveScreenshot: {
      // 1% tolerance for CI/Docker (Strict)
      // 5% or skip for local Windows (Loose)
      maxDiffPixelRatio: (isCI || isDocker) ? 0.01 : 0.05,
    },
  },
};
```

### 3. Benefits

- **Zero Flakiness:** Snapshots are always Linux-to-Linux comparisons.
- **Strict Quality Control:** We can lower tolerance from 5% back to <1%.
- **Cross-Platform:** Windows devs generate Linux-compatible snapshots without needing a VM.

## Next Steps

1. [ ] Install Docker Desktop (Prerequisite for devs).
2. [ ] Create the `docker-compose.test.yml` file.
3. [ ] Update `package.json` with Docker scripts.
4. [ ] Regenerate all baselines using the Docker container.

## Previous Strategy (Deprecated)

Previously, we used a tolerance-based approach (5%) to account for Windows/Linux rendering differences. This is now considered a temporary workaround until the Docker strategy is fully implemented.
