#!/usr/bin/env python3
"""Validate a .agent-teamflow configuration file."""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

def ok(msg: str) -> None:
    print(f"  {_c('32', 'ok')}  {msg}")

def err(msg: str) -> None:
    print(f"  {_c('31', 'ERR')} {msg}")

def warn(msg: str) -> None:
    print(f"  {_c('33', 'warn')} {msg}")

def section(title: str) -> None:
    print(f"\n{_c('1', title)}")

# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

VALID_TRACKERS = {"github", "gitlab"}
REQUIRED_KEYS = {"issueTracker", "project", "branches", "owners"}
REQUIRED_BRANCH_KEYS = {"main", "staging"}
PROJECT_RE = re.compile(r"^[^/\s]+/[^/\s]+$")


class Validator:
    def __init__(self, path: Path, check_remotes: bool = False) -> None:
        self.path = path
        self.check_remotes = check_remotes
        self.errors = 0
        self.warnings = 0
        self.config: dict = {}

    # ------------------------------------------------------------------
    # Top-level runner
    # ------------------------------------------------------------------

    def run(self) -> int:
        section(f"Validating {self.path}")

        raw = self._load()
        if raw is None:
            return 1

        self._check_structure(raw)
        if self.errors:
            self._summary()
            return 1

        self._check_values(raw)
        self._check_cli(raw)
        if self.check_remotes:
            self._check_remote_branches(raw)

        self._summary()
        return 1 if self.errors else 0

    # ------------------------------------------------------------------
    # Step 1: load & parse JSON
    # ------------------------------------------------------------------

    def _load(self) -> dict | None:
        section("1. File")
        if not self.path.exists():
            err(f"{self.path} not found")
            self.errors += 1
            return None
        ok("file exists")

        try:
            with self.path.open() as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            err(f"invalid JSON — {exc}")
            self.errors += 1
            return None
        ok("valid JSON")

        if not isinstance(data, dict):
            err("top-level value must be a JSON object")
            self.errors += 1
            return None

        return data

    # ------------------------------------------------------------------
    # Step 2: required keys present
    # ------------------------------------------------------------------

    def _check_structure(self, cfg: dict) -> None:
        section("2. Required keys")
        for key in sorted(REQUIRED_KEYS):
            if key not in cfg:
                err(f'"{key}" is missing')
                self.errors += 1
            else:
                ok(f'"{key}" present')

        extra = set(cfg) - REQUIRED_KEYS
        for key in sorted(extra):
            warn(f'unknown key "{key}" — typo?')
            self.warnings += 1

    # ------------------------------------------------------------------
    # Step 3: value semantics
    # ------------------------------------------------------------------

    def _check_values(self, cfg: dict) -> None:
        section("3. Values")

        # issueTracker
        tracker = cfg.get("issueTracker")
        if not isinstance(tracker, str):
            err('"issueTracker" must be a string')
            self.errors += 1
        elif tracker not in VALID_TRACKERS:
            err(f'"issueTracker" is "{tracker}" — must be one of: {", ".join(sorted(VALID_TRACKERS))}')
            self.errors += 1
        else:
            ok(f'"issueTracker" = "{tracker}"')

        # project
        project = cfg.get("project")
        if not isinstance(project, str) or not project.strip():
            err('"project" must be a non-empty string')
            self.errors += 1
        elif not PROJECT_RE.match(project):
            err(f'"project" must be in "org/repo" format, got "{project}"')
            self.errors += 1
        else:
            ok(f'"project" = "{project}"')

        # branches
        branches = cfg.get("branches")
        if not isinstance(branches, dict):
            err('"branches" must be an object')
            self.errors += 1
        else:
            missing = REQUIRED_BRANCH_KEYS - branches.keys()
            for k in sorted(missing):
                err(f'"branches.{k}" is missing')
                self.errors += 1

            main_b = branches.get("main")
            staging_b = branches.get("staging")

            for key, val in [("main", main_b), ("staging", staging_b)]:
                if val is None:
                    pass  # already reported above
                elif not isinstance(val, str) or not val.strip():
                    err(f'"branches.{key}" must be a non-empty string')
                    self.errors += 1
                else:
                    ok(f'"branches.{key}" = "{val}"')

            if isinstance(main_b, str) and isinstance(staging_b, str) and main_b == staging_b:
                err('"branches.main" and "branches.staging" must be different')
                self.errors += 1

        # owners
        owners = cfg.get("owners")
        if not isinstance(owners, dict):
            err('"owners" must be an object')
            self.errors += 1
        elif not owners:
            warn('"owners" is empty — no personal integration branches defined')
            self.warnings += 1
        else:
            branch_vals = []
            all_ok = True
            for user, branch in owners.items():
                if not isinstance(user, str) or not user.strip():
                    err(f'"owners" key must be a non-empty string, got {user!r}')
                    self.errors += 1
                    all_ok = False
                    continue
                if not isinstance(branch, str) or not branch.strip():
                    err(f'"owners.{user}" must be a non-empty string')
                    self.errors += 1
                    all_ok = False
                    continue

                reserved = []
                if isinstance(branches, dict):
                    if branch == branches.get("main"):
                        reserved.append("branches.main")
                    if branch == branches.get("staging"):
                        reserved.append("branches.staging")
                if reserved:
                    err(f'"owners.{user}" = "{branch}" collides with {", ".join(reserved)}')
                    self.errors += 1
                    all_ok = False
                else:
                    branch_vals.append(branch)
                    ok(f'"owners.{user}" -> "{branch}"')

            # duplicate branch targets
            seen: dict[str, str] = {}
            for user, branch in owners.items():
                if not isinstance(branch, str):
                    continue
                if branch in seen:
                    warn(f'"owners.{user}" and "owners.{seen[branch]}" share branch "{branch}"')
                    self.warnings += 1
                else:
                    seen[branch] = user

    # ------------------------------------------------------------------
    # Step 4: CLI availability
    # ------------------------------------------------------------------

    def _check_cli(self, cfg: dict) -> None:
        section("4. CLI availability")
        tracker = cfg.get("issueTracker")
        cli_map = {"github": "gh", "gitlab": "glab"}
        cli = cli_map.get(tracker) if isinstance(tracker, str) else None

        if cli is None:
            warn("cannot check CLI — issueTracker value is invalid")
            self.warnings += 1
            return

        if shutil.which(cli):
            ok(f'"{cli}" is on PATH')
        else:
            warn(f'"{cli}" not found on PATH — workflows will fail until it is installed')
            self.warnings += 1

        other_cli = "glab" if cli == "gh" else "gh"
        if not shutil.which(other_cli):
            ok(f'"{other_cli}" not on PATH (not needed for {tracker})')

    # ------------------------------------------------------------------
    # Step 5 (optional): remote branch existence
    # ------------------------------------------------------------------

    def _check_remote_branches(self, cfg: dict) -> None:
        section("5. Remote branches (--check-remotes)")

        if not shutil.which("git"):
            warn('"git" not on PATH — skipping remote checks')
            self.warnings += 1
            return

        branches = cfg.get("branches", {})
        owners = cfg.get("owners", {})
        if not isinstance(branches, dict) or not isinstance(owners, dict):
            warn("skipping remote checks — branches or owners structure is invalid")
            self.warnings += 1
            return

        to_check: list[str] = []
        if isinstance(branches.get("staging"), str):
            to_check.append(branches["staging"])
        for branch in owners.values():
            if isinstance(branch, str) and branch not in to_check:
                to_check.append(branch)

        for branch in to_check:
            result = subprocess.run(
                ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
                capture_output=True,
            )
            if result.returncode == 0:
                ok(f'origin/{branch} exists')
            else:
                warn(f'origin/{branch} not found — create it before running workflows')
                self.warnings += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _summary(self) -> None:
        section("Summary")
        if self.errors == 0 and self.warnings == 0:
            print(f"  {_c('32', 'All checks passed.')} .agent-teamflow is valid.")
        elif self.errors == 0:
            print(f"  {_c('33', f'{self.warnings} warning(s), 0 errors.')} Config is usable but review the warnings above.")
        else:
            print(f"  {_c('31', f'{self.errors} error(s), {self.warnings} warning(s).')} Fix errors before running workflows.")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a .agent-teamflow configuration file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit codes: 0 = valid, 1 = errors found.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".agent-teamflow",
        help="path to the config file (default: .agent-teamflow)",
    )
    parser.add_argument(
        "--check-remotes",
        action="store_true",
        help="also verify that owner and staging branches exist on origin",
    )
    args = parser.parse_args()

    v = Validator(Path(args.path), check_remotes=args.check_remotes)
    sys.exit(v.run())


if __name__ == "__main__":
    main()
