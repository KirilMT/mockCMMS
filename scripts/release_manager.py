#!/usr/bin/env python3
"""Release Manager Script.

Automates version bumping, changelog updates, and git tagging for releases.
Follows Semantic Versioning and Keep a Changelog conventions.

Usage:
    python scripts/release_manager.py patch      # Bug fixes (1.0.0 -> 1.0.1)
    python scripts/release_manager.py minor      # New features (1.0.0 -> 1.1.0)
    python scripts/release_manager.py major      # Breaking changes (1.0.0 -> 2.0.0)
    python scripts/release_manager.py --dry-run  # Preview changes without applying
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ReleaseManager:
    """Manages version bumping and release process."""

    def __init__(self, dry_run: bool = False):
        """Initialize the release manager.

        Args:
            dry_run: If True, preview changes without applying them
        """
        self.dry_run = dry_run
        self.root_dir = Path(__file__).parent.parent
        self.changelog_path = self.root_dir / "CHANGELOG.md"
        self.readme_path = self.root_dir / "README.md"

    def get_current_version(self) -> Optional[str]:
        """Extract current version from CHANGELOG.md.

        Returns:
            Current version string (e.g., "1.2.3") or None if not found
        """
        if not self.changelog_path.exists():
            print("❌ CHANGELOG.md not found")
            return None

        content = self.changelog_path.read_text(encoding="utf-8")

        # Match version pattern: ## [1.2.3] - 2024-12-29
        match = re.search(r"## \[(\d+\.\d+\.\d+)\]", content)
        if match:
            return match.group(1)

        print("❌ Could not find version in CHANGELOG.md")
        return None

    def bump_version(self, current: str, bump_type: str) -> str:
        """Bump version according to semantic versioning.

        Args:
            current: Current version (e.g., "1.2.3")
            bump_type: Type of bump ("major", "minor", or "patch")

        Returns:
            New version string
        """
        major, minor, patch = map(int, current.split("."))

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

    def update_changelog(self, new_version: str) -> bool:
        """Update CHANGELOG.md with new version, auto-populating sections from commits."""
        if not self.changelog_path.exists():
            print("❌ CHANGELOG.md not found")
            return False

        content = self.changelog_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")

        # Get categorized commit messages
        commits = self.get_commits_since_last_tag()
        sections = self.parse_commits_for_changelog(commits)

        def format_section(name):
            items = sections.get(name, [])
            if not items:
                return ""
            return "\n" + "\n".join(f"- {msg}" for msg in items) + "\n"

        # Build new version section
        new_version_section = f"## [{new_version}] - {today}\n"
        for sec in ["Added", "Changed", "Fixed", "Removed"]:
            new_version_section += f"\n### {sec}\n"
            new_version_section += format_section(sec)

        # Find the [Unreleased] section and move its content down
        unreleased_pattern = r"## \[Unreleased\](.*?)(?=^## |\Z)"
        unreleased_match = re.search(unreleased_pattern, content, re.DOTALL | re.MULTILINE)
        if not unreleased_match:
            print("❌ Could not find [Unreleased] section in CHANGELOG.md")
            return False

        # Insert new [Unreleased] section at the top
        new_unreleased = "## [Unreleased]\n\n### Added\n\n### Changed\n\n### Fixed\n\n### Removed\n\n"
        # Place new version section after new [Unreleased]
        updated_content = re.sub(unreleased_pattern, new_unreleased + new_version_section, content, count=1)

        if self.dry_run:
            print("\n[DRY RUN] Would update CHANGELOG.md:")
            print(f"  - Add new version: {new_version}")
            print(f"  - Date: {today}")
            print(f"  - Commits: {commits}")
        else:
            self.changelog_path.write_text(updated_content, encoding="utf-8")
            print(f"✅ Updated CHANGELOG.md with version {new_version} and auto-populated sections")

        return True

    def update_readme(self, new_version: str) -> bool:
        """Update README.md with new version.

        Args:
            new_version: New version string

        Returns:
            True if successful, False otherwise
        """
        if not self.readme_path.exists():
            print("⚠️  README.md not found - skipping")
            return True

        content = self.readme_path.read_text(encoding="utf-8")

        # Update version badge or version mention
        # Pattern: **Version:** 1.2.3 or Version: 1.2.3
        version_pattern = r"(\*\*Version:\*\*|Version:)\s+\d+\.\d+\.\d+"

        if not re.search(version_pattern, content):
            print("⚠️  Version line not found in README.md - skipping")
            return True

        updated_content = re.sub(version_pattern, rf"\1 {new_version}", content)

        if self.dry_run:
            print(f"\n[DRY RUN] Would update README.md version to {new_version}")
        else:
            self.readme_path.write_text(updated_content, encoding="utf-8")
            print(f"✅ Updated README.md with version {new_version}")

        return True

    def git_commit_and_tag(self, version: str) -> bool:
        """Create git commit and tag for the release.

        Args:
            version: Version string for the tag

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print("\n[DRY RUN] Would create git commit and tag:")
            print(f"  - Commit: 'chore: Release version {version}'")
            print(f"  - Tag: v{version}")
            return True

        try:
            # Stage changes
            subprocess.run(
                ["git", "add", "CHANGELOG.md", "README.md"],
                cwd=self.root_dir,
                check=True,
            )

            # Commit
            subprocess.run(
                ["git", "commit", "-m", f"chore: Release version {version}"],
                cwd=self.root_dir,
                check=True,
            )

            # Create tag
            subprocess.run(
                ["git", "tag", "-a", f"v{version}", "-m", f"Release version {version}"],
                cwd=self.root_dir,
                check=True,
            )

            print(f"\n✅ Created git commit and tag v{version}")
            print("\nℹ️  To push to remote:")
            print(f"    git push origin main v{version}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Git operation failed: {e}")
            return False

    def get_commits_since_last_tag(self) -> list:
        """Get commit messages since the last version tag."""
        # Find the last version tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=self.root_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        last_tag = result.stdout.strip() if result.returncode == 0 else None
        if not last_tag:
            # No tags found, get all commits
            range_ref = "HEAD"
        else:
            range_ref = f"{last_tag}..HEAD"
        # Get commit messages in range
        log_result = subprocess.run(
            ["git", "log", range_ref, "--pretty=%s"],
            cwd=self.root_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [msg.strip() for msg in log_result.stdout.splitlines() if msg.strip()]
        return commits

    def parse_commits_for_changelog(self, commits: list) -> dict:
        """Categorize commit messages into changelog sections using conventional commits."""
        sections = {"Added": [], "Changed": [], "Fixed": [], "Removed": []}
        for msg in commits:
            lowered = msg.lower()
            if lowered.startswith("feat"):
                sections["Added"].append(msg)
            elif lowered.startswith("fix"):
                sections["Fixed"].append(msg)
            elif lowered.startswith("chore") or lowered.startswith("refactor") or lowered.startswith("perf"):
                sections["Changed"].append(msg)
            elif lowered.startswith("remove") or lowered.startswith("revert"):
                sections["Removed"].append(msg)
            else:
                # Default to Changed if not matched
                sections["Changed"].append(msg)
        return sections

    def release(self, bump_type: str) -> int:
        """Execute the release process.

        Args:
            bump_type: Type of version bump ("major", "minor", or "patch")

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("=" * 80)
        print("RELEASE MANAGER")
        print("=" * 80)

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be applied\n")

        # Get current version
        current_version = self.get_current_version()
        if not current_version:
            return 1

        # Calculate new version
        new_version = self.bump_version(current_version, bump_type)

        print(f"\nCurrent version: {current_version}")
        print(f"New version: {new_version}")
        print(f"Bump type: {bump_type}")

        # Update files
        if not self.update_changelog(new_version):
            return 1

        if not self.update_readme(new_version):
            return 1

        # Format files after update to satisfy pre-commit hooks
        print("\n" + "-" * 40)
        print("Formatting files...")
        formatter_path = self.root_dir / "scripts" / "format_code.py"
        subprocess.run(
            [sys.executable, str(formatter_path), "--docs"],
            cwd=self.root_dir,
            check=False,
        )
        print("-" * 40 + "\n")

        # Git operations
        if not self.git_commit_and_tag(new_version):
            return 1

        # Summary
        print("\n" + "=" * 80)
        print("RELEASE COMPLETE")
        print("=" * 80)

        if self.dry_run:
            print("\n✅ Dry run completed - no changes were applied")
            print("\nTo apply changes, run without --dry-run:")
            print(f"    python scripts/release_manager.py {bump_type}")
        else:
            print(f"\n✅ Successfully released version {new_version}")
            print("\nNext steps:")
            print(f"  1. Review the changes: git show v{new_version}")
            print(f"  2. Push to remote: git push origin main v{new_version}")
            print("  3. Create GitHub release from tag")

        return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage releases with version bumping and tagging"
    )
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        nargs="?",
        help="Type of version bump",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )

    args = parser.parse_args()

    if not args.bump_type and not args.dry_run:
        parser.print_help()
        return 1

    bump_type = args.bump_type or "patch"

    manager = ReleaseManager(dry_run=args.dry_run)
    return manager.release(bump_type)


if __name__ == "__main__":
    sys.exit(main())
