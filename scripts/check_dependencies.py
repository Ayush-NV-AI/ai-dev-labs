#!/usr/bin/env python
"""Cross-check declared dependencies against what the code actually imports.

For every package declared in ``requirements.txt`` and every top-level
import found under ``src/``, looks the package up on PyPI (existence,
first-publish date, owner) and flags:

  - imported but not declared in requirements.txt
  - declared but never imported anywhere in src/
  - first published on PyPI within the last 90 days

That last check is the dependency-confusion / typosquat signal: a
brand-new package with a name close to something legitimate is the
classic supply-chain attack shape, and "how long has this existed" is
one of the few automatable proxies for "should I trust this name."

Needs network access to reach pypi.org; each lookup has a short timeout
and a failed lookup is reported, not fatal to the rest of the run.
"""

from __future__ import annotations

import ast
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIREMENTS_FILES = ["requirements.txt", "requirements-dev.txt"]
SRC_DIR = REPO_ROOT / "src"
PYPI_JSON_URL = "https://pypi.org/pypi/{name}/json"
TIMEOUT_SECONDS = 5
DEPENDENCY_CONFUSION_WINDOW_DAYS = 90

# Import-name -> PyPI-distribution-name aliases for this repo's stack,
# where the two don't already match after PEP 503 normalisation. Extend
# this if a new dependency has a different import name than its
# distribution name.
IMPORT_TO_DISTRIBUTION = {
    "pydantic_settings": "pydantic-settings",
    "pytest_asyncio": "pytest-asyncio",
    "yaml": "PyYAML",
    "dotenv": "python-dotenv",
}

# A local package/module never resolves against PyPI and should not be
# looked up at all.
LOCAL_TOP_LEVEL_MODULES = {"src", "tests"}


def _normalize(name: str) -> str:
    """Normalise a package name per PEP 503 for comparison purposes."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirements(paths: list[pathlib.Path]) -> set[str]:
    """Parse declared top-level package names out of requirements files.

    Args:
        paths: Requirements files to parse. A missing file is skipped.

    Returns:
        Normalised distribution names declared across all given files.
    """
    declared: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-r "):
                continue
            match = re.match(r"^([A-Za-z0-9_.\-]+)", line)
            if match:
                declared.add(_normalize(match.group(1)))
    return declared


def find_imports(src_dir: pathlib.Path) -> set[str]:
    """Find every top-level module imported anywhere under src_dir.

    Args:
        src_dir: Directory to walk for ``.py`` files.

    Returns:
        Normalised distribution names for every non-stdlib, non-local
        top-level import found.
    """
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    top_level_imports: set[str] = set()

    for path in src_dir.rglob("*.py"):
        if "insecure_examples" in path.parts:
            # Seeded SAST training material -- deliberately never imported
            # by the running app (see src/api/app.py), and some of these
            # files intentionally import a package (e.g. requests,
            # PyYAML) that the real app has no reason to depend on. Its
            # imports would be noise here, not signal.
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level_imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                top_level_imports.add(node.module.split(".")[0])

    resolved: set[str] = set()
    for module in top_level_imports:
        if module in stdlib or module in LOCAL_TOP_LEVEL_MODULES:
            continue
        distribution = IMPORT_TO_DISTRIBUTION.get(module, module)
        resolved.add(_normalize(distribution))
    return resolved


def lookup_pypi(name: str) -> dict | None:
    """Fetch a package's PyPI metadata.

    Args:
        name: Distribution name to look up (need not be normalised).

    Returns:
        The parsed JSON response's ``info`` dict plus a computed
        ``first_published`` datetime, or ``None`` if the package does
        not exist on PyPI or the lookup failed for any reason.
    """
    url = PYPI_JSON_URL.format(name=name)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            data = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    upload_times = [
        file_info.get("upload_time_iso_8601")
        for files in data.get("releases", {}).values()
        for file_info in files
        if file_info.get("upload_time_iso_8601")
    ]
    first_published = None
    if upload_times:
        parsed = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in upload_times]
        first_published = min(parsed)

    info = data.get("info", {})
    return {
        "name": info.get("name", name),
        "owner": info.get("author") or info.get("maintainer") or "(unknown)",
        "first_published": first_published,
    }


def main() -> int:
    """Run the cross-check and print a report.

    Returns:
        0 always -- this is an advisory report, not a hard gate. Read
        the FLAG rows.
    """
    declared = parse_requirements([REPO_ROOT / f for f in REQUIREMENTS_FILES])
    imported = find_imports(SRC_DIR)

    all_names = sorted(declared | imported)
    if not all_names:
        print("No dependencies found to check.")
        return 0

    print(f"{'PACKAGE':<24}{'DECLARED':<10}{'IMPORTED':<10}{'FIRST PUBLISHED':<22}OWNER")
    print("-" * 90)

    now = datetime.now(UTC)
    flags: list[str] = []
    unreachable: list[str] = []

    for name in all_names:
        is_declared = name in declared
        is_imported = name in imported
        meta = lookup_pypi(name)

        if meta is None:
            unreachable.append(name)
            first_published_str = "(lookup failed)"
            owner = "(lookup failed)"
        else:
            published = meta["first_published"]
            first_published_str = published.date().isoformat() if published else "(unknown)"
            owner = meta["owner"]
            if meta["first_published"] and now - meta["first_published"] < timedelta(
                days=DEPENDENCY_CONFUSION_WINDOW_DAYS
            ):
                flags.append(
                    f"{name}: first published on PyPI within the last "
                    f"{DEPENDENCY_CONFUSION_WINDOW_DAYS} days ({first_published_str}) -- "
                    "verify this is the package you meant to install, not a typosquat "
                    "or dependency-confusion decoy."
                )

        print(f"{name:<24}{'yes' if is_declared else 'no':<10}{'yes' if is_imported else 'no':<10}"
              f"{first_published_str:<22}{owner}")

        if is_imported and not is_declared:
            flags.append(f"{name}: imported in src/ but not declared in requirements.txt.")
        if is_declared and not is_imported:
            flags.append(f"{name}: declared in requirements.txt but never imported under src/.")

    print()
    if flags:
        print("FLAGGED:")
        for flag in flags:
            print(f"  - {flag}")
    else:
        print("No flags: every dependency is declared, imported, and not newly published.")

    if unreachable:
        print()
        print(
            "Could not reach PyPI for: "
            + ", ".join(unreachable)
            + ". Check network access and re-run; these were not evaluated for the "
            "90-day dependency-confusion signal."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
