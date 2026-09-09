#!/usr/bin/env python
"""Environment sanity check for lab participants.

Runs standalone with ZERO third-party imports — only the standard
library — so it works before ``pip install`` has ever been run. Prints a
PASS/FAIL table and exits non-zero if anything fails.

Scope note: this scaffold build intentionally does not perform the
external-host HTTPS-reachability checks (api.anthropic.com, github.com,
pypi.org, etc.) or the pip-index-reachability check described in the full
course spec, since those need real calls to third-party services that
aren't the point of this scaffold. See SCOPE_NOTES.md at the repo root.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

MIN_PYTHON = (3, 11)


class CheckResult:
    """Outcome of a single check.

    Attributes:
        name: Short label for the check.
        passed: Whether the check succeeded.
        detail: Human-readable detail. For a failure, this must state the
            fix, not just what went wrong.
    """

    def __init__(self, name: str, passed: bool, detail: str) -> None:
        self.name = name
        self.passed = passed
        self.detail = detail


def check_python_version() -> CheckResult:
    """Check that the running interpreter is Python 3.11 or newer."""
    current = sys.version_info[:2]
    if current >= MIN_PYTHON:
        return CheckResult(
            "python version",
            True,
            f"Python {current[0]}.{current[1]} (>= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})",
        )
    return CheckResult(
        "python version",
        False,
        f"Found Python {current[0]}.{current[1]}, need >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}. "
        "Install a supported Python from python.org and re-run this script with it.",
    )


def check_git_on_path() -> CheckResult:
    """Check that a ``git`` executable is on PATH."""
    git_path = shutil.which("git")
    if git_path:
        return CheckResult("git on PATH", True, git_path)
    return CheckResult(
        "git on PATH",
        False,
        "git was not found on PATH. Install Git from git-scm.com and restart your terminal.",
    )


def _git_config(key: str) -> str | None:
    """Read a single git config value, or ``None`` if unset or git is missing."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value or None


def check_git_identity() -> CheckResult:
    """Check that ``user.name`` and ``user.email`` are both configured."""
    name = _git_config("user.name")
    email = _git_config("user.email")
    if name and email:
        return CheckResult("git identity", True, f"{name} <{email}>")
    missing = []
    if not name:
        missing.append('git config --global user.name "Your Name"')
    if not email:
        missing.append('git config --global user.email "you@example.com"')
    return CheckResult(
        "git identity",
        False,
        "user.name and/or user.email not configured. Run: " + " && ".join(missing),
    )


def check_inside_git_repo() -> CheckResult:
    """Check that the current directory is inside a git working tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return CheckResult(
            "inside a git repo",
            False,
            "Could not run git. Install Git and run this script from inside the cloned repo.",
        )
    if result.returncode == 0 and result.stdout.strip() == "true":
        return CheckResult("inside a git repo", True, "confirmed via git rev-parse")
    return CheckResult(
        "inside a git repo",
        False,
        "Not inside a git working tree. cd into the ai-dev-labs clone and re-run this script.",
    )


def check_virtualenv_active() -> CheckResult:
    """Check that a virtualenv (or equivalent) is active."""
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    venv_env_var = bool(os.environ.get("VIRTUAL_ENV"))
    if in_venv or venv_env_var:
        return CheckResult("virtualenv active", True, sys.prefix)
    return CheckResult(
        "virtualenv active",
        False,
        "No active virtualenv detected. Create and activate one, e.g.: "
        "python -m venv .venv && "
        "(macOS/Linux: source .venv/bin/activate | Windows: .venv\\Scripts\\activate)",
    )


def run_all_checks() -> list[CheckResult]:
    """Run every automated check in a fixed order.

    Returns:
        One :class:`CheckResult` per check.
    """
    return [
        check_python_version(),
        check_git_on_path(),
        check_git_identity(),
        check_inside_git_repo(),
        check_virtualenv_active(),
    ]


def print_table(results: list[CheckResult]) -> None:
    """Print a PASS/FAIL table for the given results.

    Args:
        results: Checks to render, in display order.
    """
    name_width = max((len(r.name) for r in results), default=4)
    print()
    print(f"{'CHECK'.ljust(name_width)}  RESULT  DETAIL")
    print("-" * (name_width + 60))
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"{r.name.ljust(name_width)}  {status:<6}  {r.detail}")
    print()


def print_manual_checks() -> None:
    """Print the section listing checks this script cannot automate."""
    print("MANUAL CHECK - this script cannot verify these, confirm yourself:")
    print("  - Each AI coding assistant you plan to use is installed and signed in.")
    print("  - Your terminal is not restricted by a corporate proxy/allowlist that")
    print("    would block the assistant's own network calls.")
    print("  - You have permission to open a pull request on the training org's repo.")
    print()


def main() -> int:
    """Run all checks, print the report, and return a process exit code.

    Returns:
        0 if every automated check passed, 1 otherwise.
    """
    results = run_all_checks()
    print_table(results)
    print_manual_checks()

    if all(r.passed for r in results):
        print("All automated checks passed.")
        return 0

    failed = [r.name for r in results if not r.passed]
    print(f"FAILED: {', '.join(failed)}. See the fixes above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
