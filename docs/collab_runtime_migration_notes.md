# Collab Runtime Migration Notes (Phase 4)

## What Changed

- Default app workflows no longer depend on in-repo collab internals.
- Setup provisions an installed collab runtime and verifies command readiness.
- Git hook templates now live in `scripts/hooks/` and call `collab ...`.
- Default formatting/validation/CI scope no longer includes `.collab` source trees.

## Command Migration

Use installed runtime commands:

```bash
collab active
collab status path/to/file.py
collab acquire path/to/file.py --reason "work item"
collab release path/to/file.py
collab release-all
collab daemon-start
collab daemon-stop
collab daemon-status
collab dashboard
```

Legacy command mappings:

- `python collab.py active` -> `collab active`
- `python collab.py status <file>` -> `collab status <file>`
- `python collab.py daemon-start` -> `collab daemon-start`
- `python collab.py dashboard` -> `collab dashboard`

## Setup Notes

- `scripts/setup-dev.ps1` installs collab runtime using `COLLAB_RUNTIME_SPEC`.
- `COLLAB_RUNTIME_SPEC` is required to avoid ambiguous package resolution.
- If installation fails, setup prints actionable remediation guidance.

Example override in PowerShell:

```powershell
$env:COLLAB_RUNTIME_SPEC = "your-org-collab==1.0.0"
.\scripts\setup-dev.ps1
```

## Validation Scope Changes

Default app validation now targets app code and tests:

- Included: `src/`, `apps/`, `tests/`, `scripts/`, `run.py`, `conftest.py`
- Removed from default path: `.collab/` internals and `collab.py` source validation

Lock behavior is protected through runtime smoke/contract checks rather than in-repo collab-internal suites.
