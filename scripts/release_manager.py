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


def safe_print(msg: str, fallback: Optional[str] = None):
    """Print with emoji if possible, fallback to plain text if UnicodeEncodeError
    occurs."""
    try:
        print(msg)
    except UnicodeEncodeError:
        if fallback is not None:
            print(fallback)
        else:
            print(msg.encode("ascii", errors="ignore").decode())


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
            safe_print("❌ CHANGELOG.md not found", "CHANGELOG.md not found")
            return None

        content = self.changelog_path.read_text(encoding="utf-8")

        # Match version pattern: ## [1.2.3] - 2024-12-29
        match = re.search(r"## \[(\d+\.\d+\.\d+)\]", content)
        if match:
            return match.group(1)

        safe_print(
            "❌ Could not find version in CHANGELOG.md",
            "Could not find version in CHANGELOG.md",
        )
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
        """Update CHANGELOG.md with new version, auto-populating sections from
        commits."""
        if not self.changelog_path.exists():
            safe_print("❌ CHANGELOG.md not found", "CHANGELOG.md not found")
            return False

        content = self.changelog_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")

        # Get categorized commit messages
        commits = self.get_commits_since_last_tag()
        sections = self.parse_commits_for_changelog(commits)
        version_title = self.get_version_title(commits)

        def format_section(name):
            items = sections.get(name, [])
            if not items:
                return ""
            # Render each item as a raw Markdown block (no bullet)
            return f"\n### {name}\n" + "\n\n".join(items)

        # Build new version section with only non-empty sections and title
        new_version_section = f"## [{new_version}] - {version_title} - {today}\n"
        for sec in ["Added", "Changed", "Fixed", "Removed"]:
            sec_block = format_section(sec)
            if sec_block:
                new_version_section += sec_block + "\n"

        # Remove [Unreleased] section entirely after release
        unreleased_pattern = r"## \[Unreleased\](.*?)(?=^## |\Z)"
        updated_content = re.sub(
            unreleased_pattern,
            "",
            content,
            count=1,
            flags=re.DOTALL | re.MULTILINE,
        )

        # Insert new version section at the top after the header
        header_pattern = r"(#[^\n]*Changelog[^\n]*\n.*?\n)(?=## |\Z)"
        match = re.search(header_pattern, updated_content, re.DOTALL | re.IGNORECASE)
        if match:
            insert_at = match.end(1)
            updated_content = (
                updated_content[:insert_at]
                + new_version_section
                + "\n"
                + updated_content[insert_at:]
            )
        else:
            updated_content = new_version_section + "\n" + updated_content

        if self.dry_run:
            print("\n[DRY RUN] Would update CHANGELOG.md:")
            print(f"  - Add new version: {new_version}")
            print(f"  - Date: {today}")
            print(f"  - Commits: {commits}")
            print("\n--- Changelog Preview ---\n")
            print(new_version_section)
            print("\n------------------------\n")
        else:
            self.changelog_path.write_text(updated_content, encoding="utf-8")
            safe_print(
                f"✅ Updated CHANGELOG.md with version {new_version}\n"
                f"and auto-populated sections"
            )

        return True

    def update_readme(self, new_version: str) -> bool:
        """Update README.md with new version, and show preview in dry-run."""
        if not self.readme_path.exists():
            print("\u26a0\ufe0f  README.md not found - skipping")
            return True

        content = self.readme_path.read_text(encoding="utf-8")

        # Update version badge or version mention
        # Pattern: **Version:** 1.2.3 or Version: 1.2.3
        version_pattern = r"(\*\*Version:\*\*|Version:)\s+\d+\.\d+\.\d+"

        if not re.search(version_pattern, content):
            print("\u26a0\ufe0f  Version line not found in README.md - skipping")
            return True

        updated_content = re.sub(version_pattern, rf"\1 {new_version}", content)

        if self.dry_run:
            print("\n--- README Preview ---\n")
            # Show only the changed line(s)
            for old, new in zip(content.splitlines(), updated_content.splitlines()):
                if old != new:
                    print(f"- {old}")
                    print(f"+ {new}")
            print("\n------------------------\n")
        else:
            self.readme_path.write_text(updated_content, encoding="utf-8")
            safe_print(
                f"\u2705 Updated README.md with version {new_version}",
                f"Updated README.md with version {new_version}",
            )

        return True

    def git_commit_and_tag(self, version: str, bump_type: str) -> bool:
        """Create git commit and tag for the release.

        Args:
            version: Version string for the tag
            bump_type: Type of version bump ("major", "minor", or "patch")

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print("\n[DRY RUN] Would create git commit and tag:")
            commit_msg = (
                f"chore(release): release version {version} " f"[release:{bump_type}]"
            )
            print(f"  - Commit: '{commit_msg}'")
            print(f"  - Tag: v{version}")
            return True

        try:
            # Stage changes
            subprocess.run(
                ["git", "add", "CHANGELOG.md", "README.md"],
                cwd=self.root_dir,
                check=True,
            )

            # Commit (Conventional Commits + release tag)
            commit_msg = (
                f"chore(release): release version {version} [release:{bump_type}]"
            )
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.root_dir,
                check=True,
            )

            # Create tag
            subprocess.run(
                ["git", "tag", "-a", f"v{version}", "-m", f"Release version {version}"],
                cwd=self.root_dir,
                check=True,
            )

            safe_print(
                f"\n✅ Created git commit and tag v{version}",
                f"Created git commit and tag v{version}",
            )
            print("\nℹ️  To push to remote:")
            print(f"    git push origin main v{version}")

            return True

        except subprocess.CalledProcessError as e:
            safe_print(f"\n❌ Git operation failed: {e}", f"Git operation failed: {e}")
            return False

    def get_commits_since_last_tag(self) -> list:
        """Get full commit messages (subject + body) since the last version tag."""
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=self.root_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        last_tag = result.stdout.strip() if result.returncode == 0 else None
        if not last_tag:
            range_ref = "HEAD"
        else:
            range_ref = f"{last_tag}..HEAD"
        # Get full commit messages (subject + body, separated by \x1e)
        log_result = subprocess.run(
            ["git", "log", range_ref, "--pretty=%B%x1e"],
            cwd=self.root_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        # Split on \x1e (record separator)
        commits = [
            msg.strip() for msg in log_result.stdout.split("\x1e") if msg.strip()
        ]
        return commits

    def parse_commits_for_changelog(self, commits: list) -> dict[str, list[str]]:
        """Categorize commit messages into changelog sections using conventional
        commits.

        Use only the full body as section content (no extra bullet).
        """
        sections: dict[str, list[str]] = {
            "Added": [],
            "Changed": [],
            "Fixed": [],
            "Removed": [],
        }
        # Explicit mapping of commit types to changelog sections
        type_to_section = {
            "feat": "Added",
            "fix": "Fixed",
            "chore": "Changed",
            "refactor": "Changed",
            "perf": "Changed",
            "build": "Changed",
            "ci": "Changed",
            "remove": "Removed",
            "revert": "Removed",
            # The following types are mapped to 'Changed' for now, but can be split out
            # if changelog sections are expanded in the future.
            "docs": "Changed",
            "test": "Changed",
            "style": "Changed",
        }
        for msg in commits:
            # Remove [release:...] and [release] tags
            msg = re.sub(r"\[release(:\w+)?]", "", msg, flags=re.IGNORECASE).strip()
            # Split into lines: first line is type/title, rest is body
            lines = msg.splitlines()
            if not lines:
                continue
            # Parse type from first line (support optional scope: feat(scope): ...)
            match = re.match(
                r"(feat|fix|chore|refactor|perf|remove|revert|docs|test|style|build|ci)"
                r"(\([^)]*\))?:?\s*(.*)",
                lines[0],
                re.IGNORECASE,
            )
            if match:
                type_ = match.group(1).lower()
            else:
                type_ = None
            # Body is everything after the first line, joined and stripped
            body = "\n".join(lines[1:]).strip()
            # Section content: use body only (skip if empty)
            if not body:
                continue
            if type_ in type_to_section:
                section = type_to_section[type_]
                sections[section].append(body)
            else:
                # Unknown type: log a warning and skip (could also map to 'Changed')
                print(
                    f"[release_manager] WARNING: Unknown commit type '{type_}' "
                    f"in message: {lines[0]}"
                )
                continue
        return sections

    def get_version_title(self, commits: list) -> str:
        """Return the first commit message's first line (without tags/prefixes) as the
        version title."""
        if not commits:
            return ""
        # Remove [release:...] and [release] tags, and type prefix (with optional scope)
        lines = commits[0].splitlines()
        if not lines:
            return ""
        first_line = re.sub(
            r"\[release(:\w+)?]", "", lines[0], flags=re.IGNORECASE
        ).strip()
        # Remove type and optional scope (e.g., feat(test): ...)
        first_line = re.sub(
            r"^(feat|fix|chore|refactor|perf|remove|revert|docs|test|style|build|ci)"
            r"(\([^)]*\))?:?\s*",
            "",
            first_line,
            flags=re.IGNORECASE,
        )
        return first_line.strip()

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
        if not self.git_commit_and_tag(new_version, bump_type):
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
