"""
Build Portable Windows Distribution for mockCMMS.

This script creates a zero-installation, portable distribution package
that allows non-technical users to run mockCMMS without Python, Git,
or any technical setup required.

Usage:
    python scripts/build_portable.py

Output:
    dist/mockCMMS-portable-v{VERSION}.zip

Requirements:
    - Windows OS
    - Internet connection (to download Python embeddable package)
    - 500MB free disk space
"""

import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# Configuration
PYTHON_VERSION = "3.12.1"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
APP_VERSION = "1.2.0"  # Update this with each release

# Directories
REPO_ROOT = Path(__file__).parent.parent
DIST_DIR = REPO_ROOT / "dist"
BUILD_DIR = DIST_DIR / f"mockCMMS-portable-v{APP_VERSION}"
PYTHON_DIR = BUILD_DIR / "python"
APP_DIR = BUILD_DIR / "app"


def print_step(message: str) -> None:
    """Print a formatted step message."""
    print(f"\n{'='*60}")
    print(f"🔧 {message}")
    print(f"{'='*60}\n")


def download_python_embeddable() -> None:
    """Download Python embeddable package."""
    print_step("Downloading Python Embeddable Package")

    zip_path = DIST_DIR / f"python-{PYTHON_VERSION}-embed-amd64.zip"

    if zip_path.exists():
        print(f"✅ Python embeddable already downloaded: {zip_path}")
        return

    print(f"📥 Downloading from: {PYTHON_EMBED_URL}")
    print(f"   Destination: {zip_path}")

    urllib.request.urlretrieve(PYTHON_EMBED_URL, zip_path)
    print(f"✅ Download complete ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")


def extract_python_embeddable() -> None:
    """Extract Python embeddable package."""
    print_step("Extracting Python Package")

    zip_path = DIST_DIR / f"python-{PYTHON_VERSION}-embed-amd64.zip"
    PYTHON_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📦 Extracting to: {PYTHON_DIR}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(PYTHON_DIR)

    print("✅ Python extracted successfully")


def install_pip() -> None:
    """Install pip in the embedded Python."""
    print_step("Installing pip")

    python_exe = PYTHON_DIR / "python.exe"

    # Enable site-packages in python312._pth FIRST
    pth_file = PYTHON_DIR / f"python{PYTHON_VERSION.replace('.', '')[:3]}._pth"
    if pth_file.exists():
        print(f"✏️  Modifying {pth_file.name} to enable site-packages")
        content = pth_file.read_text()

        # Remove any line with just "#import site"
        lines = content.splitlines()
        new_lines = []
        site_enabled = False

        for line in lines:
            if line.strip() == "#import site":
                new_lines.append("import site")
                site_enabled = True
            elif line.strip() == "import site":
                new_lines.append(line)
                site_enabled = True
            else:
                new_lines.append(line)

        # If "import site" wasn't found at all, add it
        if not site_enabled:
            new_lines.append("import site")

        new_content = "\n".join(new_lines) + "\n"
        pth_file.write_text(new_content)
        print("✅ site-packages enabled")
    else:
        print(f"⚠️  Warning: {pth_file.name} not found")

    # Download get-pip.py
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = PYTHON_DIR / "get-pip.py"

    print("📥 Downloading get-pip.py")
    urllib.request.urlretrieve(get_pip_url, get_pip_path)
    print(f"✅ Downloaded to: {get_pip_path}")

    # Install pip with verbose output
    print(f"⚙️  Installing pip using: {python_exe}")
    result = subprocess.run(
        [str(python_exe), str(get_pip_path), "--no-warn-script-location"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Warnings/Errors:\n{result.stderr}")
        raise RuntimeError(
            f"pip installation failed with exit code {result.returncode}"
        )

    # Verify pip is actually installed
    print("🔍 Verifying pip installation...")
    verify_result = subprocess.run(
        [str(python_exe), "-m", "pip", "--version"], capture_output=True, text=True
    )

    if verify_result.returncode != 0:
        print("❌ pip verification failed!")
        print(f"   stdout: {verify_result.stdout}")
        print(f"   stderr: {verify_result.stderr}")
        raise RuntimeError("pip is not installed correctly")

    print(f"✅ pip installed successfully: {verify_result.stdout.strip()}")


def install_dependencies() -> None:
    """Install all Python dependencies."""
    print_step("Installing Dependencies")

    # Use production requirements (no dev/test dependencies)
    requirements_file = REPO_ROOT / "requirements.txt"
    python_exe = PYTHON_DIR / "python.exe"

    print(f"📦 Installing from: {requirements_file}")
    print("   (Production only - no pytest, dev tools, type stubs)")

    # Verify pip is available first
    print("🔍 Verifying pip is available...")
    verify_result = subprocess.run(
        [str(python_exe), "-m", "pip", "--version"], capture_output=True, text=True
    )

    if verify_result.returncode != 0:
        print("❌ pip is not available!")
        print(f"   stdout: {verify_result.stdout}")
        print(f"   stderr: {verify_result.stderr}")
        raise RuntimeError("pip is not installed - cannot install dependencies")

    print(f"✅ pip is available: {verify_result.stdout.strip()}")

    # Install dependencies with progress output
    print("📦 Installing packages (this may take 2-3 minutes)...")
    result = subprocess.run(
        [
            str(python_exe),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file),
            "--no-warn-script-location",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(f"❌ Dependency installation failed with exit code {result.returncode}")
        if result.stderr:
            print(f"⚠️  Warnings:\n{result.stderr}")
        raise RuntimeError(f"Failed to install dependencies from {requirements_file}")

    print("✅ Dependencies installed successfully")


def copy_application() -> None:
    """Copy the application code and resources."""
    print_step("Copying Application Files")

    APP_DIR.mkdir(parents=True, exist_ok=True)

    # Directories to copy
    dirs_to_copy = [
        "src",
        "apps",
        "test_data",
        "config",
        "static",
        "templates",
    ]

    for dir_name in dirs_to_copy:
        src = REPO_ROOT / dir_name
        dst = APP_DIR / dir_name
        if src.exists():
            print(f"📂 Copying: {dir_name}/")
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(
                src,
                dst,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                    ".venv",
                    "node_modules",
                    "*.db",
                    "*.db-journal",
                ),
            )

    # Copy essential files
    files_to_copy = [
        "run.py",
        ".env.example",
        "LICENSE",
    ]

    for file_name in files_to_copy:
        src = REPO_ROOT / file_name
        dst = APP_DIR / file_name
        if src.exists():
            print(f"📄 Copying: {file_name}")
            shutil.copy2(src, dst)

    print("✅ Application files copied successfully")


def create_env_file() -> None:
    """Create a pre-configured .env file."""
    print_step("Creating Environment Configuration")

    env_content = f"""# mockCMMS Portable Distribution v{APP_VERSION}
# Auto-generated configuration

FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=portable-demo-key-change-in-production

# Portable Distribution Flag (disables setup checks)
PORTABLE_DISTRIBUTION=true

# Database
DATABASE_URI=sqlite:///instance/mockcmms.db

# Modular Apps
PLANNING_ENABLED=True
REPORTING_ENABLED=True

# Data Source
DATA_SOURCE=api

# Seeding
AUTO_SEED_DATABASE=True

# Server
HOST=127.0.0.1
PORT=5000
"""

    env_path = APP_DIR / ".env"
    env_path.write_text(env_content, encoding="utf-8")
    print(f"✅ Created: {env_path.name}")


def seed_databases() -> None:
    """Pre-seed all databases with test data."""
    print_step("Seeding Databases")

    python_exe = PYTHON_DIR / "python.exe"
    seed_script = APP_DIR / "src" / "services" / "db_seeding.py"

    if not seed_script.exists():
        print(f"⚠️  Seed script not found: {seed_script}")
        print("   Databases will be seeded on first run")
        return

    print("🌱 Running seed script...")

    # Set PYTHONPATH to include app directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(APP_DIR)

    try:
        subprocess.run(
            [str(python_exe), str(seed_script)], cwd=APP_DIR, env=env, check=True
        )
        print("✅ Databases seeded successfully")
    except subprocess.CalledProcessError:
        print("⚠️  Seeding failed - databases will be created on first run")


def create_launcher_scripts() -> None:
    """Create batch launcher scripts."""
    print_step("Creating Launcher Scripts")

    # START script
    start_script = BUILD_DIR / "START_mockCMMS.bat"
    start_content = f"""@echo off
chcp 65001 > nul
REM mockCMMS Portable Distribution v{APP_VERSION}
REM Auto-generated launcher script
title mockCMMS - Maintenance Management System

echo ========================================================
echo 🧰 mockCMMS - Maintenance Management System
echo 📦 Version {APP_VERSION}
echo ========================================================
echo.
echo 🔑 Login credentials:
echo    Username: admin
echo    Password: admin123
echo ========================================================
echo.

cd /d "%~dp0\\app"
set PYTHONPATH=%~dp0\\app
set PORTABLE_DISTRIBUTION=true
"%~dp0\\python\\python.exe" run.py

echo.
echo ⏹️  Server terminated.
echo 🚪 Press any key to close this window.
pause > nul
"""
    start_script.write_text(start_content, encoding="utf-8")
    print(f"✅ Created: {start_script.name}")


def create_readme() -> None:
    """Create user-facing README."""
    print_step("Creating User Documentation")

    readme_content = f"""
mockCMMS Portable Distribution v{APP_VERSION}
===========================================

QUICK START (30 seconds):
--------------------------
1. Extract this ZIP file to any location (Desktop, USB drive, etc.)
2. Double-click "START_mockCMMS.bat"
3. Your browser will open automatically to the login page
4. Login with:
   - Username: admin
   - Password: admin123

STOPPING THE APPLICATION:
--------------------------
- Press Ctrl+C in the command window, or
- Simply close the command window

SYSTEM REQUIREMENTS:
--------------------
- Windows 10 or Windows 11
- 500MB free disk space
- No Python, Git, or technical tools required
- No administrator rights required
- Works offline (no internet needed)

FEATURES:
---------
* Asset Management
* Maintenance Orders (MO)
* User & Technician Management
* Planning Module (Task Assignment)
* Reporting Module (PDF Reports)
* Simulation Tools

TROUBLESHOOTING:
----------------
Problem: Browser doesn't open automatically
Solution: Manually open browser to http://localhost:5000

Problem: Port 5000 already in use
Solution: Close other applications using port 5000, or edit
          app/.env and change PORT=5000 to PORT=5001

Problem: Application won't start
Solution: Check that you extracted the ENTIRE folder, not just
          the .bat file. All files must be in the same directory.

SUPPORT:
--------
For questions or issues, contact your IT administrator or
visit: https://github.com/yourusername/mockCMMS

VERSION: {APP_VERSION}
DATE: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
"""

    readme_path = BUILD_DIR / "README.txt"
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"✅ Created: {readme_path.name}")


def create_zip_package() -> Path:
    """Create final ZIP distribution package."""
    print_step("Creating ZIP Package")

    zip_path = DIST_DIR / f"mockCMMS-portable-v{APP_VERSION}.zip"

    if zip_path.exists():
        print(f"🗑️  Removing existing package: {zip_path.name}")
        zip_path.unlink()

    print(f"📦 Creating: {zip_path.name}")
    print(f"   Source: {BUILD_DIR}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in BUILD_DIR.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(BUILD_DIR.parent)
                zipf.write(file_path, arcname)
                # Show progress every 100 files inline
                if len(zipf.namelist()) % 100 == 0:
                    msg = f"\r   📦 Packing... {len(zipf.namelist())} files added"
                    print(msg, end="", flush=True)

    print()  # newline after the progress indicator
    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"✅ Package created: {zip_path.name} ({size_mb:.1f} MB)")

    return zip_path


def cleanup_build_directory() -> None:
    """Remove temporary build directory."""
    print_step("Cleanup")

    print(f"🗑️  Removing build directory: {BUILD_DIR}")
    shutil.rmtree(BUILD_DIR)
    print("✅ Cleanup complete")


def main():
    """Main build process."""
    print("\n" + "=" * 60)
    print("🏗️  mockCMMS Portable Distribution Builder")
    print("=" * 60)
    print(f"Version: {APP_VERSION}")
    print(f"Python: {PYTHON_VERSION}")
    print(f"Output: dist/mockCMMS-portable-v{APP_VERSION}.zip")
    print("=" * 60)

    try:
        # Create dist directory
        DIST_DIR.mkdir(exist_ok=True)

        # Build steps
        download_python_embeddable()
        extract_python_embeddable()
        install_pip()
        install_dependencies()
        copy_application()
        create_env_file()
        create_launcher_scripts()
        create_readme()
        # seed_databases()  # Optional - can seed on first run instead
        zip_path = create_zip_package()
        cleanup_build_directory()

        # Remove embeddable Python ZIP artifact
        embeddable_zip = DIST_DIR / f"python-{PYTHON_VERSION}-embed-amd64.zip"
        if embeddable_zip.exists():
            print(f"🗑️  Removing build artifact: {embeddable_zip.name}")
            embeddable_zip.unlink()
            print("✅ Embeddable Python ZIP removed.")

        # Success message
        print("\n" + "=" * 60)
        print("✅ BUILD SUCCESSFUL!")
        print("=" * 60)
        print("\n📦 Distribution package created:")
        print(f"   {zip_path}")
        print(f"\n📊 Package size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
        print("\n📤 Distribution methods:")
        print("   • Upload to OneDrive/Google Drive and share link")
        print("   • Email to stakeholders (if < 25MB)")
        print("   • Copy to USB drive for offline distribution")
        print("\n👤 End-user instructions:")
        print("   1. Extract ZIP file")
        print("   2. Double-click START_mockCMMS.bat")
        print("   3. Login: admin / admin123")
        print("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ BUILD FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
