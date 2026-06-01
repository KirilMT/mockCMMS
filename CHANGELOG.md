<!-- markdownlint-disable MD024 -->

<!-- prettier-ignore -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.8.0](https://github.com/KirilMT/mockCMMS/compare/v2.7.0...v2.8.0) (2026-06-01)


### ✨ Features

* **docs:** stamp persistent docs and attach portable release builds ([#151](https://github.com/KirilMT/mockCMMS/issues/151)) ([41b814b](https://github.com/KirilMT/mockCMMS/commit/41b814b794e7b6c1e34b4888963243d183b93a3a))

## [2.7.0](https://github.com/KirilMT/mockCMMS/compare/v2.6.2...v2.7.0) (2026-05-31)

### ✨ Features

- **phase4.5:** adopt published collab-runtime package (pinned 0.2.9) ([#138](https://github.com/KirilMT/mockCMMS/issues/138)) ([1e5e7a9](https://github.com/KirilMT/mockCMMS/commit/1e5e7a9d2575d4f44914205bee806bc258887c2c))
- **phase4:** remove in-repo collab, decouple app validation ([#136](https://github.com/KirilMT/mockCMMS/issues/136)) ([6c18fcc](https://github.com/KirilMT/mockCMMS/commit/6c18fccd363249c9c2c817685ebabf505fa58e55))
- **scripts:** improve setup-dev for Cursor and document agent venv usage ([#142](https://github.com/KirilMT/mockCMMS/issues/142)) ([7ef6533](https://github.com/KirilMT/mockCMMS/commit/7ef653338982394387d6b95567e4aedfe3038383))

### 🐛 Bug Fixes

- **hooks:** point missing collab message to collab-runtime ([#143](https://github.com/KirilMT/mockCMMS/issues/143)) ([62b9297](https://github.com/KirilMT/mockCMMS/commit/62b929721ff74c332f769c85fd5cf0a7a133c42a))

### 📝 Documentation

- **collab:** close out migration and align agent lock guidance ([#146](https://github.com/KirilMT/mockCMMS/issues/146)) ([bf16fbb](https://github.com/KirilMT/mockCMMS/commit/bf16fbbed4c00c4ae8414a02e2a28aedd162c667))

## [2.6.2](https://github.com/KirilMT/mockCMMS/compare/v2.6.1...v2.6.2) (2026-05-12)

### 🐛 Bug Fixes

- **deps:** install formatters from requirements-dev.txt not unpinned pip ([#128](https://github.com/KirilMT/mockCMMS/issues/128)) ([c1d930b](https://github.com/KirilMT/mockCMMS/commit/c1d930b0fd51e783eb5a5b159b0c244ffe7448db))

## [2.6.1](https://github.com/KirilMT/mockCMMS/compare/v2.6.0...v2.6.1) (2026-05-07)

### 📝 Documentation

- **config:** add shell compatibility guidance ([#122](https://github.com/KirilMT/mockCMMS/issues/122)) ([f37b5aa](https://github.com/KirilMT/mockCMMS/commit/f37b5aabe1e969f5ebc39b71b0765d7e364b30ed))

## [2.6.0](https://github.com/KirilMT/mockCMMS/compare/v2.5.3...v2.6.0) (2026-05-03)

### ✨ Features

- **collab:** supabase realtime locks ([#102](https://github.com/KirilMT/mockCMMS/issues/102)) ([430200a](https://github.com/KirilMT/mockCMMS/commit/430200ad8ab86ad9874a39d27e88896b1ec30644))

## [2.5.3](https://github.com/KirilMT/mockCMMS/compare/v2.5.2...v2.5.3) (2026-03-21)

### 📝 Documentation

- **ci:** strict PR formatting and lean release formatting ([f819867](https://github.com/KirilMT/mockCMMS/commit/f819867cfd3cd1fdd0ae5b8f174beab89292c461))
- **ci:** strict PR formatting and lean release formatting ([a99c013](https://github.com/KirilMT/mockCMMS/commit/a99c0132b3582488e56c37ba7516fa82f7c8ba79))

## [2.5.2](https://github.com/KirilMT/mockCMMS/compare/v2.5.1...v2.5.2) (2026-03-21)

### ⚡ Performance Improvements

- **ci:** optimize release please action workflow overhead ([ae121d3](https://github.com/KirilMT/mockCMMS/commit/ae121d3c765ac5c98d80ae638a4a64bde608cf5f))
- **ci:** optimize release please action workflow overhead ([9a11cd1](https://github.com/KirilMT/mockCMMS/commit/9a11cd1ae9b52514496ee2824e91e3e86a653318))

## [2.5.1](https://github.com/KirilMT/mockCMMS/compare/v2.5.0...v2.5.1) (2026-03-21)

### 🐛 Bug Fixes

- **ci:** configure prettier defaults and align release workflow ([607e7ea](https://github.com/KirilMT/mockCMMS/commit/607e7ea65d11832ac707466baa1fe47a5a63f428))
- **ci:** configure prettier defaults and align release workflow ([944a340](https://github.com/KirilMT/mockCMMS/commit/944a340171a35fd30a7537921efe7e3de5073aab))
- **ci:** extract Release PR branch from JSON and stop changelog wrap ([c75979e](https://github.com/KirilMT/mockCMMS/commit/c75979e43e75abde0bb4c1b106c0fded8ceae3b4))
- **ci:** extract Release PR branch from JSON and stop changelog wrap ([fa5c1bf](https://github.com/KirilMT/mockCMMS/commit/fa5c1bf4c602fd53232838e64bee46486a5c90de))
- **ci:** yamllint / line-length and truthy directive for release workflow ([45d920e](https://github.com/KirilMT/mockCMMS/commit/45d920ef2e192a289eb2472b3d17b635029813ca))

## [2.5.0](https://github.com/KirilMT/mockCMMS/compare/v2.4.0...v2.5.0) (2026-03-20)

### Features

- **format:** avoid duplicate check command execution in check-only mode ([f126c4a](https://github.com/KirilMT/mockCMMS/commit/f126c4a2693309d604c2008c726224323a1efe90))
- release please prettier changelog fix ([a553b3a](https://github.com/KirilMT/mockCMMS/commit/a553b3a9ef907179a01ca8824cd848ad1ac39d4b))
- **workflow:** correct workflow_dispatch mapping in release workflow ([fdd4857](https://github.com/KirilMT/mockCMMS/commit/fdd485770675ff4b4bd89866d497e2da2ed65d67))
- **workflow:** ensure CHANGELOG.md is always Prettier-formatted in Release PRs ([c0bf58c](https://github.com/KirilMT/mockCMMS/commit/c0bf58cbee74acb837b6a647d62a405858a31bd8))
- **workflow:** fix for release please ([f4c8620](https://github.com/KirilMT/mockCMMS/commit/f4c8620c21d0ae9d499ae92b3bfadb95e7b94067))

### Bug Fixes

- **ci:** use pull_request event for semantic PR validation (avoid duplicate runs) ([e443493](https://github.com/KirilMT/mockCMMS/commit/e44349352438ff4a0b56e7c4e8b8733f0f48d90e))
- **format:** standardize YAML/prettier/yamllint output and update tests ([fe3dde3](https://github.com/KirilMT/mockCMMS/commit/fe3dde323c83ee898fec68e8b02b317f653f0169))

## [2.4.0](https://github.com/KirilMT/mockCMMS/compare/v2.3.0...v2.4.0) (2026-03-19)

### Features

- **workflow:** add explicit checkout step to release workflow ([a73a189](https://github.com/KirilMT/mockCMMS/commit/a73a1894b0ac954400ef3bfd49ebb08012ad1ab8))

## [2.3.0](https://github.com/KirilMT/mockCMMS/compare/v2.2.0...v2.3.0) (2026-03-18)

### Features

- **chore:** release manager, format_code.py and setup-dev.py improvements ([04bee96](https://github.com/KirilMT/mockCMMS/commit/04bee965b35568e4cdce95749b5a4ea996e7d622))

## [2.2.0](https://github.com/KirilMT/mockCMMS/compare/v2.1.0...v2.2.0) (2026-03-18)

### Features

- finalize release automation and verify sync ([4486bfd](https://github.com/KirilMT/mockCMMS/commit/4486bfd062e163c9797e15f7bbc724a0017be5e6))
- finalize release automation and verify sync ([da013d4](https://github.com/KirilMT/mockCMMS/commit/da013d4f3f1c89b485febf4b8475b9ac5a92adbf))

## [2.1.0](https://github.com/KirilMT/mockCMMS/compare/v2.0.0...v2.1.0) (2026-03-18)

### Features

- test release automation and readme sync ([7838f04](https://github.com/KirilMT/mockCMMS/commit/7838f043d58728260ce499be136f0f7373100213))
- test release automation and readme sync ([949ddcf](https://github.com/KirilMT/mockCMMS/commit/949ddcfcbf0ddd5719f2af88702b518a72b71d31))

## [2.0.0](https://github.com/KirilMT/mockCMMS/compare/v1.2.3...v2.0.0) (2026-03-18)

### ⚠ BREAKING CHANGES

- This is a breaking change example for testing.
- Environment variable WORKFORCE_MANAGER_ENABLED renamed to PLANNING_ENABLED

### Features

- **.github:** add issue and pull request templates ([7bad7ec](https://github.com/KirilMT/mockCMMS/commit/7bad7ec4b3767560eefeeb7779ef8bde0e2c7871))
- Add a Windows setup script (`setup.ps1`) to automate Python and Git installation via winget and update the README to reflect these new automated setup instructions. ([81adb4b](https://github.com/KirilMT/mockCMMS/commit/81adb4be26255c8f3c3c2416e274b724896c2d9d))
- Add agent execution protocol and Phase 5 HTML template audit prompts. ([b6bf576](https://github.com/KirilMT/mockCMMS/commit/b6bf5765b26b80f3c0d45f0eaa69013dbffd3629))
- add automated release system and update documentation ([3eccf65](https://github.com/KirilMT/mockCMMS/commit/3eccf6526f12820bc538e963ad6d7b2a601f53fd))
- add automated release system and update documentation ([4ce3821](https://github.com/KirilMT/mockCMMS/commit/4ce3821b6cc0ed24e6fd5d0e01c3a7f3c9a755dc))
- Add comprehensive AI assistant instructions for GitHub Copilot and synchronize Gemini instructions. ([8d2afc9](https://github.com/KirilMT/mockCMMS/commit/8d2afc9dd208782c76de7bcfe4fb71afd66b4294))
- Add comprehensive logging configuration, structured JSON formatting, performance monitoring, and request timing for the application. ([36b792f](https://github.com/KirilMT/mockCMMS/commit/36b792f440f1a44153bb0b9ebe61af1b6e85b179))
- Add Copilot instructions and project roadmap, update Gemini instructions and project dependencies. ([927a3b3](https://github.com/KirilMT/mockCMMS/commit/927a3b394cccc4d0a1f3712d2b6db8fd5eaba6b7))
- Add Dependabot configuration ([9fca1b9](https://github.com/KirilMT/mockCMMS/commit/9fca1b977505943bc2fd6720916cb95d6554ff63))
- Add jscpd to package.json and enhance Node.js check in setup-dev.ps1 ([a21f372](https://github.com/KirilMT/mockCMMS/commit/a21f37284732d5366b5b59ee1c6125b55555daaf))
- add line conditions for new inspection tasks in dummy data ([06d2572](https://github.com/KirilMT/mockCMMS/commit/06d25728b3e6eba6e9477ff514e0d162c7887b9c))
- Add line conditions to planning module ([a4932f0](https://github.com/KirilMT/mockCMMS/commit/a4932f0442fdedfd9be7bf4b59818cc014b4d446))
- Add PowerShell script to automate project setup and dependency installation on Windows. ([f402023](https://github.com/KirilMT/mockCMMS/commit/f4020238fade68f85d9612e7b05a699a639b6868))
- Add Simulation Tools sidebar link and update roadmap ([5a5df6d](https://github.com/KirilMT/mockCMMS/commit/5a5df6d7f18ec4d7bde82876478de43dc5376de0))
- Add Team column to Users table ([7b494d7](https://github.com/KirilMT/mockCMMS/commit/7b494d7060d50e6f6a455b562cd4ca36454f9db7))
- Add visual validation for table filters (Task 2.1) ([0a998cd](https://github.com/KirilMT/mockCMMS/commit/0a998cda6dcde25b4521034a473fa18ce115a675))
- **advanced-table:** Complete Task 2.2 sub-tasks 2.2a & 2.2b - Sidebar structure and filters with bug fixes ([21ba18f](https://github.com/KirilMT/mockCMMS/commit/21ba18f05d60e21700bf9478a6e2a0d58630dbe5))
- **advanced-table:** Complete Task 2.2c - Move columns and configs to sidebar with Update View and auto-apply filters ([ef1aaf0](https://github.com/KirilMT/mockCMMS/commit/ef1aaf00880f16dd064e99112b04fff97b2b0a58))
- automate installation with setup script ([f642278](https://github.com/KirilMT/mockCMMS/commit/f642278819662ce7c1d50664b7bdcc24187367bb))
- **backend:** Complete Phase 2 Python Backend Audit and Refactoring ([dcc3ae4](https://github.com/KirilMT/mockCMMS/commit/dcc3ae4f45a3b16d578dc542ae9effa9233029c4))
- **backend:** Complete Phase 2 Python Backend Audit and Refactoring ([b846039](https://github.com/KirilMT/mockCMMS/commit/b84603928928bb469ee1fe6dec6ba48e8af143a5))
- **backend:** Complete Phase 2 Python Backend Audit and Refactoring ([8f57372](https://github.com/KirilMT/mockCMMS/commit/8f57372724932364c9f8aa7c3c9e9353851cad94))
- **backend:** Complete Phase 2 Python Backend Audit and Refactoring ([d176020](https://github.com/KirilMT/mockCMMS/commit/d176020b1f3f175ba29258b0deed265c6c6a4df5))
- **backend:** Complete Phase 2 Python Backend Audit and Refactoring ([8c36348](https://github.com/KirilMT/mockCMMS/commit/8c36348f7a0045208866fbc1dab13962ee158fe5))
- Complete Python Code Quality Audit and Fix Critical Bugs ([f483d3e](https://github.com/KirilMT/mockCMMS/commit/f483d3eb48b25263a5e50a3010d00dece9d0472d))
- Complete Python Code Quality Audit and Initial Test Fixes ([42477c7](https://github.com/KirilMT/mockCMMS/commit/42477c7a0789cf6ac8eeb9b35be93a421b6795a7))
- Complete Task 1.1 - Save/Load View Configuration & Dropdown Fixes ([be146e8](https://github.com/KirilMT/mockCMMS/commit/be146e8e1ba00a50c1575718191e24eab6b43de6))
- Complete Task 1.2 - Fix Global Search Functionality (FINAL) ([aec5d2a](https://github.com/KirilMT/mockCMMS/commit/aec5d2afc30585a217419b1b0e60a71f6dd684fa))
- Complete Task 1.3 - Implement AND/OR Filter Logic ([8857edf](https://github.com/KirilMT/mockCMMS/commit/8857edf6380e6cff93e0fdd2a4b288f0e7954f75))
- Complete Task 1.4 - Constrain Filter Apply Button ([8636ad3](https://github.com/KirilMT/mockCMMS/commit/8636ad32b188a2321f8fc60ce97556592875e421))
- Comprehensive Reports App Refactor + Core MO Enhancement + Frontend Testing Overhaul ([275c3f1](https://github.com/KirilMT/mockCMMS/commit/275c3f1bba7fb5e0d50db92d0bcc49222ce8fe71))
- Comprehensive test infrastructure improvements and database isolation ([4a08994](https://github.com/KirilMT/mockCMMS/commit/4a089947792ac7961b650e5d337f6fe44a1d4ba5))
- **core:** implement portable distribution and improve test robustness ([94b95e3](https://github.com/KirilMT/mockCMMS/commit/94b95e3192f494235f5eea841638e3a5e0ce90ce))
- **docs:** add advanced table component bug fixes and enhancements plan ([6f38fe8](https://github.com/KirilMT/mockCMMS/commit/6f38fe8e902d7a4f9fb51cd0fad75caee6b8ca18))
- enable html coverage report in local validation script ([1b46f22](https://github.com/KirilMT/mockCMMS/commit/1b46f22a10d23d3c57b92500172bbbd2013293cd))
- establish modular apps infrastructure and cross-browser visual regression baselines ([ae189ae](https://github.com/KirilMT/mockCMMS/commit/ae189aef5f41d24ac1466afd943f33554dc5e2f4))
- Fix Bug [#30](https://github.com/KirilMT/mockCMMS/issues/30) - Assignees field layout shift ([01cddcb](https://github.com/KirilMT/mockCMMS/commit/01cddcb82a041ac288b372bf8384fcb07984e14c))
- Fix sticky header (Bug [#31](https://github.com/KirilMT/mockCMMS/issues/31)), autofill styles (Bug [#24](https://github.com/KirilMT/mockCMMS/issues/24)), and status field (Bug [#15](https://github.com/KirilMT/mockCMMS/issues/15)) ([4a2b24b](https://github.com/KirilMT/mockCMMS/commit/4a2b24b277c1215892cf358cc739d55c79695308))
- Implement code quality fixes and update roadmap with logging/CI plans ([eae2871](https://github.com/KirilMT/mockCMMS/commit/eae287158a7e75768bfe7302268d35cd7a899992))
- Implement comprehensive code validation infrastructure and optimize repository ([7e047a6](https://github.com/KirilMT/mockCMMS/commit/7e047a6dccf5468e34adbdc27500fb15091e537c))
- implement data simulation service and CLI command ([10a0e26](https://github.com/KirilMT/mockCMMS/commit/10a0e2608599511f46fb9c09fd8202d9b72ab93e))
- implement global settings interface for managing line conditions in planning module ([0eef4c4](https://github.com/KirilMT/mockCMMS/commit/0eef4c4045710d426d4650020715f960d950b49f))
- implement line conditions for planning tasks and update dummy data ([cd9baff](https://github.com/KirilMT/mockCMMS/commit/cd9baff88be98fea0a084e2fd9fb92a62c2b2c9f))
- implement Phase 1 frontend unit tests with Jest ([19d3e22](https://github.com/KirilMT/mockCMMS/commit/19d3e22d54332d3beb2aefce2aab342bbd05d99d))
- implement Phase 2-4 of Frontend Testing (E2E & Visual) ([2ffe944](https://github.com/KirilMT/mockCMMS/commit/2ffe944b12c5ea8dfa84c3880ccf9f17d13e907b))
- **logging:** implement structured logging and performance monitoring ([9a654fd](https://github.com/KirilMT/mockCMMS/commit/9a654fde7fd638bb8844acfd46a889429daeb617))
- **mockCMMS:** implement advanced table system and reports app (v1.1.0) ([c13093a](https://github.com/KirilMT/mockCMMS/commit/c13093a3006d28d2702c7034736e79096af4fad7))
- **planning:** add action plan and roadmap for workforce manager integration ([3caf7cc](https://github.com/KirilMT/mockCMMS/commit/3caf7ccf62e91c11fdc94d0e9a8eb366dae799a6))
- **planning:** advance phase 3 UI, planning engine, and documentation refactor ([bcf5538](https://github.com/KirilMT/mockCMMS/commit/bcf5538d86d973a7df19ae51ae63076dd6cb8a01))
- **planning:** complete Phase 3 critical fixes and enhancements - Nov 20, 2025 ([93ac84c](https://github.com/KirilMT/mockCMMS/commit/93ac84ca060938513ac487e2fa3c76f032fcf446))
- **planning:** Complete Phases 0-2 and Phase 3 (partial) - Planning Module Core Implementation ([bf0fd89](https://github.com/KirilMT/mockCMMS/commit/bf0fd8940c6178f5136246e1afbd42d2874eedcc))
- **planning:** Update Planning App and add Phase 2 audit artifacts ([ec83a27](https://github.com/KirilMT/mockCMMS/commit/ec83a27fc5c6b9757478433f8a49e224deea0962))
- Polish advanced table column resizing with Excel-like behavior ([a234b91](https://github.com/KirilMT/mockCMMS/commit/a234b916a651c03c0ac18bbd980bac6c97947058))
- Refine Bulk Data Generator (Config Validation, Roles, Spare Parts) ([60426a4](https://github.com/KirilMT/mockCMMS/commit/60426a40b6c09a54a91cfd80c67583f171d24aee))
- **reports:** consolidate backend tests and resolve mypy conflicts ([a9a4c90](https://github.com/KirilMT/mockCMMS/commit/a9a4c90edb990d92218964a58b3b0e602920b6cf))
- restructure monorepo from packages/ to apps/ architecture ([9ee545e](https://github.com/KirilMT/mockCMMS/commit/9ee545e75bbecd9c65e2ed488e522c334b1226ea))
- **scripts:** add smart test targeting to --quick mode ([c94e91b](https://github.com/KirilMT/mockCMMS/commit/c94e91bcce6b7c3f420e190825a3fadbfc7d3fc4))
- Shift Calendar Redesign - Grid layout and Visual improvements ([5fdbbc9](https://github.com/KirilMT/mockCMMS/commit/5fdbbc9aa6e0bab1fde8aa93d816163ae598eecc))
- Shift Calendar Redesign - Grid layout and Visual improvements ([0c71060](https://github.com/KirilMT/mockCMMS/commit/0c7106009a017839fd93f3cb48e049d2e03bca99))
- test changelog population with new commit [release:patch] ([3083651](https://github.com/KirilMT/mockCMMS/commit/30836517e56676f62bc4f2a88f1199d7ff3b9d4b))
- **testing:** add pytest scaffold generator and integrate docs ([355017f](https://github.com/KirilMT/mockCMMS/commit/355017f81efb48d6046762dd4a77c8f93f0030b8))
- **testing:** Implement robust E2E test infrastructure with isolated database ([94456f3](https://github.com/KirilMT/mockCMMS/commit/94456f3f56c08abbeec73e2f368365b3553f55c6))
- **tooling:** add ruff --fix to format_code.py ([601978a](https://github.com/KirilMT/mockCMMS/commit/601978a6a1e41b2a18478cf0845dc31f114aff5f))

### Bug Fixes

- Add mypy overrides for apps to ignore import errors ([3cfd336](https://github.com/KirilMT/mockCMMS/commit/3cfd336f6b66fd04608da4888cf92311608d2e2c))
- Align local validation with CI and fix Unicode errors ([0da8b93](https://github.com/KirilMT/mockCMMS/commit/0da8b93bd044236a623ad47c1e905b01d5842109))
- Bug [#17](https://github.com/KirilMT/mockCMMS/issues/17) OR Filter logic and Bug [#32](https://github.com/KirilMT/mockCMMS/issues/32) Add Filter validation ([fe88038](https://github.com/KirilMT/mockCMMS/commit/fe88038b7af5f08b2c6b95f108f00c28ac91e11c))
- **bug-35:** replace system popups with custom modals for delete and update actions ([92aa843](https://github.com/KirilMT/mockCMMS/commit/92aa8435638386b9f76d1bb2ca76d77917155582))
- **ci/planning:** implement ironclad validation and restore absolute visual parity ([86bd585](https://github.com/KirilMT/mockCMMS/commit/86bd5850a662d7e13935c335914a5eefb2544d80))
- **ci:** Resolve CI failures and define Visual Testing Strategy ([086b8cb](https://github.com/KirilMT/mockCMMS/commit/086b8cbf65fcab08da5139bfa0f3c69f105db997))
- **ci:** Resolve CI failures in run.py and Jest coverage ([1273ad0](https://github.com/KirilMT/mockCMMS/commit/1273ad03280c7ca362265373ebfd653e3908e41b))
- **ci:** simplify commit-msg hook and fix pre-commit output batching ([20ec833](https://github.com/KirilMT/mockCMMS/commit/20ec833c795069c89e44e1675e7db35ddaa1df83))
- **ci:** standardize test discovery and harden local tools ([d361684](https://github.com/KirilMT/mockCMMS/commit/d36168466423cd1cd55d5d4eeacb264ee7df565d))
- Comprehensive resolution of backend/frontend linting, testing, and API stability issues ([b15edcd](https://github.com/KirilMT/mockCMMS/commit/b15edcdf1f2b10d88dedff5ae0b28a9a1391e768))
- Configure mypy properly via pyproject.toml to check all Python code ([a7bb709](https://github.com/KirilMT/mockCMMS/commit/a7bb70986422b63316329cc543442cd9318ad06a))
- **conflicts:** resolve merge conflicts and fix test regressions ([1369161](https://github.com/KirilMT/mockCMMS/commit/1369161c85fc1029623a86f12f9a77e73b8315f5))
- Disable pagination globally in AdvancedTable & fix Windows encoding in validation script ([20f8431](https://github.com/KirilMT/mockCMMS/commit/20f84317be49e81570823077552595db8a989936))
- Disable pagination on Maintenance Orders table ([c02c7cc](https://github.com/KirilMT/mockCMMS/commit/c02c7cc6f7b46e7a94c9b1919fdae66b0a438bfb))
- Disable pagination on Maintenance Orders table ([e4d494e](https://github.com/KirilMT/mockCMMS/commit/e4d494efd0b7c83e4569dbbcc688aa2b72f7d2dc))
- **e2e:** Fix addInitScript timing with DOMContentLoaded check ([6eaa260](https://github.com/KirilMT/mockCMMS/commit/6eaa260f5b27cdc417fc48488c36cb31092b2a23))
- **e2e:** Relax visual regression thresholds for CI ([5824ec3](https://github.com/KirilMT/mockCMMS/commit/5824ec398cc7dd2e64ab3e42b1b7f92a7fc16a89))
- **e2e:** Use addInitScript for persistent CSS injection across navigations ([f859b93](https://github.com/KirilMT/mockCMMS/commit/f859b93d099126f7f5eda6435198a6f07d018fe0))
- Enforce LF line endings to resolve CI docformatter failures ([f85ed8a](https://github.com/KirilMT/mockCMMS/commit/f85ed8aefd366088a0492ff22a90e6b21b333e49))
- **github:** Remove invalid YAML frontmatter from PR template ([ed60ac4](https://github.com/KirilMT/mockCMMS/commit/ed60ac4dccc68ead7ad5b3c4fb75c940114dbd4d))
- **gitignore:** correct .testmondata ignore rule (inline comments unsupported) ([c1f3871](https://github.com/KirilMT/mockCMMS/commit/c1f3871cfa15b44030678f63bb4b2bc38e88a409))
- Handle mocked FileHandler in isinstance check (CI fix) ([72100da](https://github.com/KirilMT/mockCMMS/commit/72100daaac272f7db979bbcd56deee95ea13e97d))
- Implement Assignees dropdown with Select2 and improve MO data handling ([6eb943a](https://github.com/KirilMT/mockCMMS/commit/6eb943acb7c856cb33fc51f456266a84a8806413))
- **logging:** resolve flake8 error and update roadmap ([7757bb7](https://github.com/KirilMT/mockCMMS/commit/7757bb7fe11d7fb66ac53a654ddf0a242578aaa3))
- **logging:** Restore Werkzeug console output in Debug mode ([c978c6e](https://github.com/KirilMT/mockCMMS/commit/c978c6ebce0c01a408b437ced7e1dbc9b699cccc))
- **planning:** stabilize gantt visual test and restore seeded schedule task coverage ([a2c738b](https://github.com/KirilMT/mockCMMS/commit/a2c738b16539dd11aa62a26f3ab59d6d69e44ed8))
- **planning:** stabilize seeding refs and requests dependency warning ([ef15227](https://github.com/KirilMT/mockCMMS/commit/ef15227bc49e66bc93e690be8356258f2b0187ce))
- **release:** align pyproject.toml version for release-please ([16744a1](https://github.com/KirilMT/mockCMMS/commit/16744a133f98c8b3e8b1b6e50fd6bd945d4daf42))
- Remove extra blank lines for docformatter LF compatibility ([ad076ac](https://github.com/KirilMT/mockCMMS/commit/ad076ac746671b10b6a183dc060fd1f626739c05))
- Remove unnecessary global statement in test_logging.py ([1eca5da](https://github.com/KirilMT/mockCMMS/commit/1eca5da17c7e8e5fdacbfe9bcb3486a13da13a26))
- Remove unused variables in test_planning_view.py ([b8fb859](https://github.com/KirilMT/mockCMMS/commit/b8fb859574bd9f319ff546c1be970c557f2a9b53))
- Resolve Bugs [#28](https://github.com/KirilMT/mockCMMS/issues/28) and [#29](https://github.com/KirilMT/mockCMMS/issues/29) - Assignees dropdown UX improvements ([552abc7](https://github.com/KirilMT/mockCMMS/commit/552abc7078ad7299c1eac2e094ef64c749b03cb7))
- Resolve critical bugs and improve form UX (Bug #R1, #R2, #R3) ([a046263](https://github.com/KirilMT/mockCMMS/commit/a046263cc797e1a8972ec1de00aecb28931dcb54))
- Resolve E501 and F841 flake8 linting errors ([123d48a](https://github.com/KirilMT/mockCMMS/commit/123d48a49d66c958c4914fffd2e764c743acb2fb))
- Resolve high-priority bugs - table navigation and state persistence (Bug [#4](https://github.com/KirilMT/mockCMMS/issues/4), [#14](https://github.com/KirilMT/mockCMMS/issues/14), [#25](https://github.com/KirilMT/mockCMMS/issues/25), [#26](https://github.com/KirilMT/mockCMMS/issues/26)) ([6c69dd7](https://github.com/KirilMT/mockCMMS/commit/6c69dd75c7f3d6a02aaced1fc27bb939937eaa52))
- resolve linting and coverage issues in session tests ([a2285cf](https://github.com/KirilMT/mockCMMS/commit/a2285cf0a4dfc418e67091df1e10eb96db276b19))
- resolve merge conflicts with main and fix cross-app compatibility ([5c49fca](https://github.com/KirilMT/mockCMMS/commit/5c49fcaa024cada8a00ce931c48a707a68be11dc))
- resolve ModuleNotFoundError in planning app tests ([42cc279](https://github.com/KirilMT/mockCMMS/commit/42cc2794555e3bc7a38a6248a87393d7e12ecbfd))
- Robust database isolation and E2E test infrastructure improvements ([b3fcb78](https://github.com/KirilMT/mockCMMS/commit/b3fcb78b89783d48b4997f7dd6a11e27213fe521))
- run setup check before Flask initialization ([c7b4ec0](https://github.com/KirilMT/mockCMMS/commit/c7b4ec08fffeb6b0b5415c7a40f1f15df005ca6f))
- run setup check before Flask initialization ([d318b3a](https://github.com/KirilMT/mockCMMS/commit/d318b3aa879556dabc66912df333b3cb4cacbab2))
- Shorten comment in test_planning_view.py ([c41d385](https://github.com/KirilMT/mockCMMS/commit/c41d38566337b7c89b404d3cddb4baa8aa53e71f))
- Split flake8 exclude argument across lines to satisfy yamllint ([76e26cf](https://github.com/KirilMT/mockCMMS/commit/76e26cfd12b5089f98b0957331124424fbc83cbf))
- **templates:** resolve delete button regression on detail pages ([c683f22](https://github.com/KirilMT/mockCMMS/commit/c683f22bb86822a0a3c0a29cbd043c738c507fa0))
- **templates:** resolve delete button regression on detail pages ([c7e09fc](https://github.com/KirilMT/mockCMMS/commit/c7e09fc50b0949bb6ab7a06b767387074a7e0a7b)), closes [#35](https://github.com/KirilMT/mockCMMS/issues/35)
- **templates:** resolve nested forms and update bug tracking for delete regression ([050c175](https://github.com/KirilMT/mockCMMS/commit/050c1753a64a34cc595ca71b1b4ec54f42953243))
- **test:** explicitly enable planning module and correct multiple_mos fixture ([890331f](https://github.com/KirilMT/mockCMMS/commit/890331ff01e174548812139f54027e361cc7dbae))
- **test:** patch env vars and remove duplicate linting ([126f205](https://github.com/KirilMT/mockCMMS/commit/126f205c863e5fc6771500c16d604799217c0d35))
- **tests:** Add Flask app context to planning engine unit tests ([fff43ac](https://github.com/KirilMT/mockCMMS/commit/fff43ac0923996b2789b7edc684554b859c8220d))
- **tests:** correct assertions in table-modals test and pass validation ([d770023](https://github.com/KirilMT/mockCMMS/commit/d770023c75c7d6289926f609d46a7817df63bcff)), closes [#30](https://github.com/KirilMT/mockCMMS/issues/30)
- **tests:** resolve failing tests in table-modals and improve coverage ([2632a12](https://github.com/KirilMT/mockCMMS/commit/2632a1231fc3fabae27621f2f3b840a33dc13f66)), closes [#30](https://github.com/KirilMT/mockCMMS/issues/30)
- **tooling:** remove auto-hook update noise and fix Windows env isolation ([d17adaa](https://github.com/KirilMT/mockCMMS/commit/d17adaa89ce1b02fb2dac3f34850640481e22e91))
- Update GitHub Issue Templates frontmatter and structure ([ec4fe12](https://github.com/KirilMT/mockCMMS/commit/ec4fe122efc8d39e7d271107c64ca984e5f92d6f))
- Update planning view tests to mock new dependencies ([77a3c23](https://github.com/KirilMT/mockCMMS/commit/77a3c2315b4f154cf39d1cd061c5b97c28df007e))
- update step numbering in validate_code.py for consistency ([cc60869](https://github.com/KirilMT/mockCMMS/commit/cc60869d74b04b7f3021c6409704c8690f501eec))
- Use YAML folded scalar syntax for flake8 to satisfy yamllint ([205a4e5](https://github.com/KirilMT/mockCMMS/commit/205a4e53d143815498b934917109f885d3957e87))
- **validation:** harden local tools and fix CI environment parity ([d0e167c](https://github.com/KirilMT/mockCMMS/commit/d0e167cd19c4f3c4ff9ad43aecf1bae095ec6aaa))

### Documentation

- add 'Improve README Badges' task to roadmap ([58e9540](https://github.com/KirilMT/mockCMMS/commit/58e95405ae2319d300cf296d55f17f3070719268))
- Add 3 new bugs (Assignees UX issues) to bug tracking - IN PROGRESS ([8c022f5](https://github.com/KirilMT/mockCMMS/commit/8c022f5497562db39beb12866ca16f4d1bcadb20))
- Add AI Agent Interaction Guide and Implementation Priority Guide for effective task delegation ([d87f9df](https://github.com/KirilMT/mockCMMS/commit/d87f9dfbfdf2d8aa1d0b3150ffbeab71b2f0ada0))
- Add Bug [#37](https://github.com/KirilMT/mockCMMS/issues/37) - Edit/Delete buttons for manual report items only ([f8fdda5](https://github.com/KirilMT/mockCMMS/commit/f8fdda5eed11384353c74c5a71e10de275667367))
- Add CI, Codecov, License, and Python badges to README.md ([5289375](https://github.com/KirilMT/mockCMMS/commit/5289375a3ec1363ca6e4124c400672c6ca0f9f21))
- Add CI, Codecov, License, and Python badges to README.md ([5234a40](https://github.com/KirilMT/mockCMMS/commit/5234a40c01ef16682c80c2cbd4dc4bfb6171108a))
- Add CI, Codecov, License, and Python badges to README.md ([7edb309](https://github.com/KirilMT/mockCMMS/commit/7edb30924c4c2c5032fb7b397ab40c17ef83318c))
- Add coding standards and guidelines to CONTRIBUTING.md ([580a5e6](https://github.com/KirilMT/mockCMMS/commit/580a5e618ba06087ca32dff26c0b517bda277d3f))
- Add comprehensive bug tracking document ([844a53c](https://github.com/KirilMT/mockCMMS/commit/844a53ccf686ddb8794bfc0bce4987b80d1ebb44))
- Add Core mockCMMS Code Quality & Architecture Audit Plan ([8ca9f80](https://github.com/KirilMT/mockCMMS/commit/8ca9f809d440af70c48078fc42b59f9a25a234d9))
- Add GitHub Copilot instructions and synchronize Gemini Code Assist guide. ([a3b6c99](https://github.com/KirilMT/mockCMMS/commit/a3b6c995420a77fa9ece91b74bbe25cc00ab44dd))
- Add Personal Access Token (PAT) authentication instructions to CONTRIBUTING.md ([1465a35](https://github.com/KirilMT/mockCMMS/commit/1465a3515880b27d8226bd7dfbf479a0db1ed79e))
- add project roadmap document outlining project status and future features. ([41a5b25](https://github.com/KirilMT/mockCMMS/commit/41a5b25bbf3de468375d25ebb7965962f29513ed))
- Add release_manager.py usage instructions to AI agent documentation ([13071c2](https://github.com/KirilMT/mockCMMS/commit/13071c2df4b1699cc3868e883a05997aaa759c84))
- **agents:** Create AGENTS.md and enhance GEMINI.md with 5-Step Loop ([0807065](https://github.com/KirilMT/mockCMMS/commit/080706584b3a7e0e6b7c32906732c4e66cfd91ce))
- **agents:** enhance AI agent instructions with modular apps, frontend tools, and strict testing rules ([285b52e](https://github.com/KirilMT/mockCMMS/commit/285b52e81cf94a2fadfbc9d3b9f041fad8aaab8e))
- **ai:** update AI instructions with strict Git Workflow rules ([266b231](https://github.com/KirilMT/mockCMMS/commit/266b23165b5b204fae5ad5569da2f5f1d437bf05))
- archive completed plans and reports to docs/deprecated ([ff29b14](https://github.com/KirilMT/mockCMMS/commit/ff29b1450e12511ba7e691328bfe9fdf6d002070))
- audit and improve documentation files [Phase 6.4] ([f58a94d](https://github.com/KirilMT/mockCMMS/commit/f58a94dc2932e87da7243cb6308fa1fe13ed93d9))
- clean up roadmap and bug tracking structure ([dc64739](https://github.com/KirilMT/mockCMMS/commit/dc647395fb5f1ff44079d8f61fd4810903fd8cab))
- cleanup roadmap redundancies ([87edda0](https://github.com/KirilMT/mockCMMS/commit/87edda048f5d90dbf079967d635a0ffdd119484f))
- cleanup roadmap redundancies and updated script status ([bc8041e](https://github.com/KirilMT/mockCMMS/commit/bc8041e2236de30ef7362f5daab71ec09153d87d))
- Comprehensive bug tracking cleanup and AI instructions update ([23e12ae](https://github.com/KirilMT/mockCMMS/commit/23e12ae3487b6415b1a0c29865204ef66d6d1d15))
- consolidate development tools and guides into contributing docs ([1946656](https://github.com/KirilMT/mockCMMS/commit/1946656e2b91236fe9ab8fbd14f77b79bf902186))
- Create comprehensive testing plan for mockCMMS project ([55c4702](https://github.com/KirilMT/mockCMMS/commit/55c47021b5f8ded49ec5ee9fb9967d0fc9f97878))
- deprecate priority and agent guides, update roadmap links ([b8ef4a5](https://github.com/KirilMT/mockCMMS/commit/b8ef4a5af269eb6b44a7379e62064e5e72ae2158))
- **dx:** consolidate and optimize AI instructions [release:minor] ([7243ce5](https://github.com/KirilMT/mockCMMS/commit/7243ce5e57e30d5943f6e962abdb009aa6737af9))
- Enhance code separation guidelines in documentation for HTML, CSS, and JavaScript ([2998b67](https://github.com/KirilMT/mockCMMS/commit/2998b6762018c8c554494392824485ab99296fc0))
- Enhance installation script and README for clarity and user guidance ([4ef71c1](https://github.com/KirilMT/mockCMMS/commit/4ef71c1d9f3941a952afe203aaac617b9371a074))
- finalize detailed audit and synchronization of project documentation ([cf12289](https://github.com/KirilMT/mockCMMS/commit/cf12289197a6f523adb30f5614be42b93c291934))
- **git:** improve push vs PR instructions in GIT_WORKFLOW.md ([ddb6246](https://github.com/KirilMT/mockCMMS/commit/ddb62465e4b1f8d2a96328446a3122934aca2f62))
- **git:** update workflow to enforce tracking check and 'gh pr create' ([7c0eb19](https://github.com/KirilMT/mockCMMS/commit/7c0eb195994b6cc3ae098fd95c25dced82effbe8))
- improve issue closing guidelines ([dd775ea](https://github.com/KirilMT/mockCMMS/commit/dd775ea918b37e6ff162fc4c47c12e39e1950675))
- mark Phase 8 as in progress in plan details ([dddd26d](https://github.com/KirilMT/mockCMMS/commit/dddd26dcb52bb4f6a42937f7dc0f0a9fe2d38715))
- moved some doc files to archive folder (created new) covering project issues, bug investigations, and various planning and audit reports. ([2bd2470](https://github.com/KirilMT/mockCMMS/commit/2bd2470e0e7287fe9e727e207889ba62e1b3f43e))
- **phase5:** finalize documentation verification and sync agent instructions ([68b274e](https://github.com/KirilMT/mockCMMS/commit/68b274eeab00f4bbf3629a19d119774932728173))
- **plan:** rewrite apps testing plan to reflect completed work ([c05a2b9](https://github.com/KirilMT/mockCMMS/commit/c05a2b9ed99f9aa964d3307908207f49fea258f0))
- **readme:** comprehensive refactor for clarity and developer onboarding ([f7e0b30](https://github.com/KirilMT/mockCMMS/commit/f7e0b30e3df6530c2e0f77e54ef49eeadaaccba3))
- refactor documentation to phase-based structure ([8296bbf](https://github.com/KirilMT/mockCMMS/commit/8296bbfd83cb4ee2f46384ae5a3b9d062897e19f))
- refactor documentation to phase-based structure ([fd56fa3](https://github.com/KirilMT/mockCMMS/commit/fd56fa3126bddd2f75e4b863ccb13a0a9d4a597a))
- remove Co-authored-by from commit template ([9f37586](https://github.com/KirilMT/mockCMMS/commit/9f37586cf94954b315a0762b2f6208895a6d94d6))
- Remove duplicate URL from README ([62c0e17](https://github.com/KirilMT/mockCMMS/commit/62c0e170e43f2307485990a0472449c5c0c2f2b4))
- rename PR template to lowercase standard ([add286a](https://github.com/KirilMT/mockCMMS/commit/add286affc949e453edf7c2da33c5acc011cd2d2))
- Restructure GEMINI.md documentation for improved clarity and organization ([acbb9b7](https://github.com/KirilMT/mockCMMS/commit/acbb9b79009bfd638daa0f7e2d740f7409f7ce69))
- **roadmap:** add bulk generator team labor scaling ([6dda640](https://github.com/KirilMT/mockCMMS/commit/6dda6403351d2a8a547069d1bf3b45859dec12ff))
- **roadmap:** add Monitoring app with dynamic data architecture ([6fa3ade](https://github.com/KirilMT/mockCMMS/commit/6fa3adea74a65b2bb4aa9195934cb040a2ae1f4f))
- **roadmap:** update collaborative development section with new tasks and documentation links ([dcb72d9](https://github.com/KirilMT/mockCMMS/commit/dcb72d9fb5e47f8622732d63d21159793a1ea4a5))
- Standardize and synchronize AI guidelines ([0475617](https://github.com/KirilMT/mockCMMS/commit/04756170fa00b39d337932915632b486395aee6c))
- Synchronize and enhance all planning documentation ([89a703f](https://github.com/KirilMT/mockCMMS/commit/89a703fe019a3a74bb6b15f9212212a0d530abc0))
- synchronize documentation files and fix test coverage gaps ([def43a5](https://github.com/KirilMT/mockCMMS/commit/def43a58eaf6a777d40a38a43ca190ca9fe80677))
- Synchronize documentation files with current project state ([f79deec](https://github.com/KirilMT/mockCMMS/commit/f79deec4effd5538953a56742acd41c3e9b13fee))
- **troubleshooting:** add concept and modular architecture documentation ([5df28d7](https://github.com/KirilMT/mockCMMS/commit/5df28d7f2425d7565b60a5650e86208248b40878))
- Update AI Agent Guide and comprehensive testing plan to reflect completion of all 144 tests with 100% pass rate and 75.64% coverage, marking Week 2 as complete and ready for Week 3 ([e3f49cb](https://github.com/KirilMT/mockCMMS/commit/e3f49cb47ed416678549c58e8d34484812e435fe))
- Update AI Agent Guide and comprehensive testing plan to reflect completion of error handling tests, with 116/144 tests passing and 80.6% coverage ([941de99](https://github.com/KirilMT/mockCMMS/commit/941de99807bdcacec40b7bdc827a7ebdba6a1798))
- Update AI Agent Guide and comprehensive testing plan to reflect completion of Phase 3, including 190/190 tests (100%) and coverage improvement to 78.39% ([8aedef6](https://github.com/KirilMT/mockCMMS/commit/8aedef645472f6aac6970e2d05fda62284a6f843))
- Update AI Agent Guide and comprehensive testing plan to reflect completion of Phase 3, including 210/210 tests (100%) and coverage improvement to 82.99% ([38490d5](https://github.com/KirilMT/mockCMMS/commit/38490d5ed07dd63a04e50bcad6e03785a982f80f))
- Update AI Agent Guide and comprehensive testing plan to reflect completion of test_validation.py and current test progress, including 110/144 tests passing and 76.4% coverage ([6c6f9ad](https://github.com/KirilMT/mockCMMS/commit/6c6f9adb9e957d80df38b0cf8c021ce9fcc772ea))
- Update AI Agent Guide and comprehensive testing plan to reflect Phase 1 readiness and next steps -&gt; Plan updated and corrected. ([0a84896](https://github.com/KirilMT/mockCMMS/commit/0a84896681b43e37d63aa2ad92b0ddcac4d083bc))
- Update AI Agent Guide and comprehensive testing plan to reflect progress in Phase 3, including completion of 10 enhanced tests and improved coverage to 77.68% ([50b9399](https://github.com/KirilMT/mockCMMS/commit/50b93997ec7b215f2a4f6196006f25af8e79b02c))
- Update AI Agent Guide and comprehensive testing plan to reflect progress in Phase 3, including completion of 164 tests (82%) and improved coverage metrics ([91dcbc1](https://github.com/KirilMT/mockCMMS/commit/91dcbc1be51b0779f2646a2ee6ccc3623c554e7c))
- Update AI Agent Guide and comprehensive testing plan to reflect progress in Phase 3, including completion of 174 tests (87%) and improved coverage metrics ([a65cf2a](https://github.com/KirilMT/mockCMMS/commit/a65cf2a238bed0a531eb166159a13042a40a6a65))
- Update AI Agent Guide and comprehensive testing plan to reflect progress in Phase 3, including completion of 182 tests (91%) and improved coverage to 78.39% ([63dabb1](https://github.com/KirilMT/mockCMMS/commit/63dabb16aeb33d7f37ca8463b9bb76e2f3984f89))
- Update AI Agent Guide and comprehensive testing plan to reflect progress in Week 2, including completion of test_auth.py and updated test coverage metrics ([e502b04](https://github.com/KirilMT/mockCMMS/commit/e502b04a9e35456dc7a3738df2e3b9fa9150ea6e))
- Update AI Agent Guide and comprehensive testing plan to reflect progress, including completion of advanced validation tests and updated test metrics (136/144 tests complete, 94.4% coverage) ([eb2f252](https://github.com/KirilMT/mockCMMS/commit/eb2f2520996983fa2005d824f5564039a21f75a4))
- Update AI Agent Guide and comprehensive testing plan to reflect progress, including completion of integration tests and updated test metrics (126/144 tests complete, 87.5% coverage) ([4e31e59](https://github.com/KirilMT/mockCMMS/commit/4e31e5920218a5b260f1c84f8bc510f87341beda))
- Update AI Agent Guide and comprehensive testing plan to reflect Week 2 extended status, including Phase 1 completion and Phase 2 security tests in progress ([eaa31f0](https://github.com/KirilMT/mockCMMS/commit/eaa31f0fd33908c88f3bef775e43104a1f379924))
- update AI Agent Guide and core code quality plan for Phase 6 completion ([8d64998](https://github.com/KirilMT/mockCMMS/commit/8d64998e64e58af8e962e734a97de4a6c299af85))
- Update AI Agent Guide to reflect addition of 10 new tests and coverage improvement to 77.68% ([ab16c46](https://github.com/KirilMT/mockCMMS/commit/ab16c46c5d4857567e43e618109f4d4716367cd1))
- Update AI Agent Interaction Guide and comprehensive testing plan to reflect completion of Week 2 Test Suite with 100% passing tests and 73.60% coverage ([099c504](https://github.com/KirilMT/mockCMMS/commit/099c50476a11deac585acbe5f89b61a73c8ccdc2))
- Update AI Agent Interaction Guide and comprehensive testing plan with current progress and completed tasks. test_db_utils.py creation ([d9ac256](https://github.com/KirilMT/mockCMMS/commit/d9ac256abfd05234804b57b45ed89b7546060e1f))
- Update AI Agent Interaction Guide with current status and testing progress (new 4 Pases created for Tests topic) ([2cc1324](https://github.com/KirilMT/mockCMMS/commit/2cc13243b6c9d26cfc5e565fb019eaddd7647fc7))
- update AI instructions with artifact and file management guidelines ([49bb943](https://github.com/KirilMT/mockCMMS/commit/49bb94369b30c9c629055cd73321b0ef237d1309))
- Update bug tracking - Bugs [#28](https://github.com/KirilMT/mockCMMS/issues/28), [#29](https://github.com/KirilMT/mockCMMS/issues/29) resolved, [#30](https://github.com/KirilMT/mockCMMS/issues/30) still in progress ([b35bddf](https://github.com/KirilMT/mockCMMS/commit/b35bddf171b8018b6ad65def06fe40fdfbf62528))
- Update bug tracking and roadmap documentation for clarity and improved relationships ([324eb17](https://github.com/KirilMT/mockCMMS/commit/324eb17580fc099cc9d1c8ccb55f6c274ee06d88))
- Update comment standards and cleanup guidelines in documentation ([a0cd08b](https://github.com/KirilMT/mockCMMS/commit/a0cd08b6512a7cf000aaa3fa06ede5e2252cb1a4))
- Update comprehensive testing plan and add pytest configuration files ([966a2f4](https://github.com/KirilMT/mockCMMS/commit/966a2f4894f6d1d608ba11d64076466ede83b61a))
- Update contributing guidelines and testing documentation to reflect test-driven development philosophy and coverage standards ([85cedee](https://github.com/KirilMT/mockCMMS/commit/85cedee9db14ed376b41845ed012aa54522f576b))
- Update implementation priority guide and comprehensive testing plan with completed tasks ([0d5666c](https://github.com/KirilMT/mockCMMS/commit/0d5666cb60cfefb1e71c36dc622cbc21e17bf4fa))
- update planning documents for Phase 8 progress ([af73016](https://github.com/KirilMT/mockCMMS/commit/af73016736ef9f4e6139d6e4f4001959ee252368))
- Update pull request template for clarity and structure ([a29e1ee](https://github.com/KirilMT/mockCMMS/commit/a29e1eec146d52449386eb25f4174e973f837043))
- Update roadmap and implementation priority guide for Phase 1 tasks and structure -&gt; Improved documentation plan for Audits ([4b3be77](https://github.com/KirilMT/mockCMMS/commit/4b3be7708a78a01d7c79db306ffa1a97855659b1))
- update status of Phase 8 to in progress in core code quality plan ([14b9f32](https://github.com/KirilMT/mockCMMS/commit/14b9f322d852f7f820855bb37fff4a7fd7e1ccf4))
- Update test suite organization and coverage goals, adding new tests and refining test categories for improved clarity and structure ([25de5d3](https://github.com/KirilMT/mockCMMS/commit/25de5d3a33ccb612ce5859c3cf81f1b872ca45dd))

### Code Refactoring

- rename workforceManager to planning module ([d120719](https://github.com/KirilMT/mockCMMS/commit/d1207198db7df6b8a69b7829fde1c33520e7f57e))

## [1.2.3] - Release automation improvements - 2026-03-15

### Changed

- Replace print statements with safe_print to handle UnicodeEncodeError gracefully
- Update git_commit_and_tag to use Conventional Commit message format
- Ensure consistent Unicode-safe output across release operations
- Add detailed commit message and release automation requirements to
  CONTRIBUTING.md, SKILL.md, and GIT_WORKFLOW.md
- Introduce .gitmessage template for standardized commit messages
- Update setup-dev.ps1 to configure commit template and commit-msg hook
- Refactor release_manager.py to improve changelog parsing and formatting
- Remove [Unreleased] section from CHANGELOG.md to align with automated workflow

## [1.2.0] - 2026-03-14

### Added

- **Advanced Table Enhancements:**
  - **Column Resizing Polish:** Excel-like column resizing with sub-pixel
    precision
    - Columns to the left stay fixed during resize
    - Columns to the right shift position without changing width
    - Table width adjusts dynamically to accommodate changes
    - Smooth 60fps resizing using `requestAnimationFrame`
    - Click suppression to prevent unintended sorting after resize
  - **Sidebar UI:** Modern collapsible sidebar with three sections (Filters,
    Columns, Saved Views)
  - **Filter Enhancements:** AND/OR logic, auto-apply on changes, validation
  - **Error Handling:** Loading spinners, exponential backoff retry, offline
    detection
  - **Testing Guide:** Comprehensive 200+ test cases covering all functionality
- **Planning Integration (Major Feature):**
  - **Planning Module:** Fully integrated the new Planning Module with a custom
    Gantt chart and Shift Planning capabilities
  - **Advanced Scheduling:** Added support for complex shift patterns
    (Production 3x8h, Maintenance 2x12h) and overnight shifts
  - **Team Optimization:** Implemented multi-factor team formation logic
    (skills, workload, experience)
- **Infrastructure:**
  - **Test Suite:** Restored and verified the global test suite; fixed
    cross-module import issues affecting `pytest` discovery
  - **Shared Components:** Enhanced `AdvancedTable` component with better height
    calculation and event handling, shared across all apps

### Changed

- **Advanced Table Component:**
  - Auto-fit padding reduced from 24px to 5px for tighter content fit
  - All width calculations now use float precision (`getBoundingClientRect()`)
    to eliminate jitter
  - Column resizing now updates table width synchronously:
    `New Width = Start Width + (Column Change)`
- **Documentation:**
  - **Restructuring:** Major reorganization of the `docs/` directory
    - Moved app-specific documentation to `apps/<app_name>/docs/`
    - Refactored the monolithic Planning Module action plan into phase-specific
      documents
    - Cleaned up the root `docs/` directory to focus on project-level roadmaps
    - Removed completed temporary planning document
      (`advanced-table-fixes-plan.md`)
- **Configuration:**
  - Updated `.env` handling to support new Planning Module configuration flags

### Fixed

- **Advanced Table:**
  - Fixed save/load configuration persistence across renders
  - Fixed global search breaking on input
  - Fixed filter dropdown not updating when columns change
  - Fixed empty state messages not appearing correctly
  - Fixed sidebar state persistence after page refresh
- **Stability:** Resolved startup crashes related to circular imports in the
  Planning Engine
- **UI/UX:** Fixed various issues with the Advanced Table component (modals,
  event listeners, viewport height)
- **Testing:** Fixed `pytest` discovery issues allowing full regression testing
  of the Planning module

## [1.1.0] - 2025-01-28

### Added

- **Advanced Table System**: Excel-like functionality with sorting, filtering,
  pagination, and export capabilities
- **Enhanced Database Models**:
  - Asset model with asset_code, asset_type, cost_center fields
  - MaintenanceOrder model with 16+ new fields including priority, scheduling,
    time tracking
  - SparePart model with manufacturer information and stock tracking
  - Report and TableConfiguration models for advanced reporting
- **Reporting Application**: Complete modular Flask blueprint for comprehensive
  reporting
  - Reactive production reporting with filtering capabilities
  - Weekend completion reporting with date range selection
  - PDF and Markdown export formats
  - Report management with view, download, and delete functionality
- **Advanced Table Component**: JavaScript-based table with:
  - Column management and reordering
  - Advanced filtering with multiple operators
  - Configuration saving and loading
  - Full-screen layout with internal scrolling
  - Export functionality (CSV, JSON)
- **UI Consistency**: Shared base templates across all applications
- **Template Architecture**: Modular apps use own templates extending main app
  base

### Changed

- **Database Schema**: Updated all main models with comprehensive field sets
- **Page Integration**: All main pages (Assets, MOs, Spare Parts, Users) now use
  advanced tables
- **Navigation**: Updated to include Reporting app with proper routing
- **Template Structure**: Reporting app templates moved to own directory for
  better maintainability
- **Route Handling**: Enhanced to support new database fields and dictionary
  data format

### Fixed

- **UI Consistency**: Reporting app now maintains consistent layout with main
  application
- **Template Management**: Proper separation of app templates while maintaining
  UI consistency
- **Configuration Management**: Advanced table configurations properly saved and
  loaded
- **Search Functionality**: Enhanced filtering and search across all table
  implementations

### Technical Details

- Advanced JavaScript table component with full Excel-like functionality
- Modular Flask blueprint architecture for reporting
- Enhanced SQLAlchemy models with comprehensive field coverage
- Responsive CSS design with full-screen table layouts
- Environment variable control for all modular applications

## [1.0.0] - 2025-01-27

### Added

- **Initial Release**: First stable version of the mockCMMS monorepo
- **Modular Architecture**: Main application with dynamically loadable apps
- **Planning Integration**: Skill-based technician task assignment system
- **Centralized Configuration**: Single `.env` file for all applications
- **Unified Environment**: One virtual environment and dependency management
- **Dynamic App Loading**: Enable/disable apps without code changes
- **REST API**: Complete API endpoints for data integration
- **Database Management**: SQLite-based data storage with utilities
- **Documentation**: Comprehensive project documentation and AI instructions
- **Testing Framework**: Test suite for main application functionality

### Changed

- **Project Structure**: Updated documentation to reflect actual directory
  layout
- **AI Instructions**: Enhanced AI assistant guidelines with balanced detail
  levels
- **README Documentation**: Optimized project structure for different audiences

### Technical Details

- Flask-based web application with modular design
- SQLite database with seeding capabilities
- Environment-based configuration management
- Integrated planning management capabilities
