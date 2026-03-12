#!/usr/bin/env python3
"""Generate test stubs for new Python code.

Analyzes source files using AST and generates pytest test templates that follow
repository standards. Generated tests include proper fixtures, docstrings, and
the Arrange-Act-Assert pattern.

Usage:
    python scripts/generate_tests.py src/services/new_module.py
    python scripts/generate_tests.py src/routes/api.py --dry-run
    python scripts/generate_tests.py --scan src/
"""

import argparse
import ast
import os
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]


class CodeAnalyzer:
    """Analyzes Python source files to extract testable entities."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.module_name = Path(filepath).stem
        self.entities: List[Tuple[str, str]] = []  # (name, type)

    def analyze(self) -> List[Tuple[str, str]]:
        """Extract module-level public (non-private) classes and functions."""
        with open(self.filepath, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {self.filepath}: {e}")
            return []

        # Only inspect top-level statements to avoid nested/helper functions.
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                self.entities.append((node.name, "class"))
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                self.entities.append((node.name, "function"))

        return self.entities


class TestGenerator:
    """Generates pytest test templates following repo standards."""

    CATEGORY_PATTERNS = {
        "api.py": "functional",
        "routes.py": "functional",
        "services/": "unit",
        "utils.py": "unit",
        "models.py": "unit",
    }

    def __init__(self, source_file: str, category: Optional[str] = None):
        self.source_file = source_file
        self.module_name = Path(source_file).stem
        self.category = category or self._detect_category()

    def _detect_category(self) -> str:
        """Auto-detect test category based on file path."""
        filepath_lower = self.source_file.lower()
        for pattern, cat in self.CATEGORY_PATTERNS.items():
            if pattern in filepath_lower:
                return cat
        return "unit"

    def generate(self, entities: List[Tuple[str, str]]) -> str:
        """Generate test file content."""
        if not entities:
            return ""

        lines = [
            f'"""Tests for {self.module_name} module."""',
            "",
            "import pytest",
            "",
        ]

        # Add imports
        classes = [e[0] for e in entities if e[1] == "class"]
        functions = [e[0] for e in entities if e[1] == "function"]

        if classes or functions:
            lines.append("from src." + self._get_import_path() + " import (")
            for name in sorted(set(classes + functions)):
                lines.append(f"    {name},")
            lines[-1] = lines[-1].rstrip(",")
            lines.append(")")
            lines.append("")

        # Generate test classes
        for class_name, _ in entities:
            if class_name in classes:
                lines.extend(self._generate_class_tests(class_name))
                lines.append("")

        # Generate function tests
        function_entities = [e[0] for e in entities if e[1] == "function"]
        if function_entities:
            lines.extend(self._generate_function_tests(function_entities))

        return "\n".join(lines)

    def _get_import_path(self) -> str:
        """Convert file path to import path."""
        path = self.source_file.replace("\\", "/")
        if "src/" in path:
            return path.split("src/")[1].replace("/", ".").replace(".py", "")
        return self.module_name

    def _generate_class_tests(self, class_name: str) -> List[str]:
        """Generate test class for a source class."""
        lines = [
            f"class Test{class_name}:",
            f'    """Test suite for {class_name}."""',
            "",
            "    # Add fixtures as needed (app, client, db, etc.)",
            "",
            "    def test_class_is_importable(self):",
            f'        """Ensure {class_name} is importable and usable by tests."""',
            f"        assert {class_name} is not None",
            "",
        ]
        return lines

    def _generate_function_tests(self, functions: List[str]) -> List[str]:
        """Generate tests for module-level functions."""
        lines = [
            "class TestModuleFunctions:",
            '    """Test suite for module functions."""',
            "",
        ]

        for func_name in sorted(functions):
            lines.extend(
                [
                    f"    def test_{func_name}_is_callable(self):",
                    f'        """Smoke test: {func_name} is callable."""',
                    f"        assert callable({func_name})",
                    "",
                    f"    def test_{func_name}(self):",
                    f'        """TODO: implement behavior test for {func_name}."""',
                    "        # Arrange",
                    "        # (set up test data)",
                    "",
                    "        # Act",
                    f"        # result = {func_name}(...)",
                    "",
                    "        # Assert",
                    "        pytest.skip(\"TODO: add assertions for this generated test\")",
                    "",
                ]
            )

        return lines


class TestDiscovery:
    """Find modules without test coverage."""

    def __init__(self):
        self.test_dir = "tests/backend"

    def find_untested(self, src_dir: str) -> List[str]:
        """Find Python modules without corresponding tests."""
        tested = self._get_tested_modules()
        untested = []

        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if not d.startswith(("_", "."))]

            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    module = file.replace(".py", "")
                    if module not in tested:
                        untested.append(os.path.join(root, file))

        return sorted(untested)

    def _get_tested_modules(self) -> Set[str]:
        """Get set of modules that have tests."""
        tested = set()
        for root, dirs, files in os.walk(self.test_dir):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    module = file.replace("test_", "").replace(".py", "")
                    tested.add(module)
        return tested


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate pytest test stubs for Python code"
    )
    parser.add_argument("source_file", nargs="?", help="Path to source Python file")
    parser.add_argument(
        "--category",
        choices=["unit", "functional", "integration"],
        help="Test category (auto-detected if not specified)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print output without creating file"
    )
    parser.add_argument("--scan", action="store_true", help="Scan for untested modules")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing test files"
    )

    args = parser.parse_args()

    # Scan mode
    if args.scan:
        print("\n📊 Untested modules in src/:\n")
        discovery = TestDiscovery()
        untested = discovery.find_untested("src")

        if untested:
            for module in untested:
                print(f"  • {module}")
            print("\nRun: python scripts/generate_tests.py <module_path>\n")
        else:
            print("✅ All modules have tests!\n")
        return

    # Generate tests for specific file
    if not args.source_file:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.source_file):
        print(f"❌ File not found: {args.source_file}\n")
        sys.exit(1)

    # Analyze
    analyzer = CodeAnalyzer(args.source_file)
    entities = analyzer.analyze()

    if not entities:
        print(f"⚠️  No testable entities found in {args.source_file}\n")
        return

    print(f"🔍 Found {len(entities)} testable entities\n")

    # Generate
    generator = TestGenerator(args.source_file, category=args.category)
    test_code = generator.generate(entities)

    # Determine output path
    test_dir = Path("tests") / "backend" / generator.category
    test_file = test_dir / f"test_{generator.module_name}.py"

    # Handle existing files
    if test_file.exists() and not args.force and not args.dry_run:
        print(f"⚠️  File exists: {test_file}")
        print("   Use --force to overwrite or --dry-run to preview\n")
        return

    # Dry-run mode
    if args.dry_run:
        print("📋 Generated test template:\n")
        print("=" * 80)
        print(test_code)
        print("=" * 80)
        print("\n✅ Preview mode - no files created\n")
        return

    # Create file
    test_dir.mkdir(parents=True, exist_ok=True)
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_code)

    print(f"✅ Created: {test_file}")
    print(f"📝 Next: Fill in test logic and run: pytest {test_file}\n")


if __name__ == "__main__":
    main()
