#!/usr/bin/env python3
"""Land queued pull requests: merge each onto the current base, verify, push what was verified.

Part of the herdr-agent-pool plugin: the lander of the GitHub Actions design (docs/lander.md),
phase 1 of the migration. It replaces integrate-pr.sh and the merge lock: a workflow runs it in
one concurrency group per base branch (template/.github/workflows/land.yml), so only one lander
ever writes the base and no lock is needed. It has no judgement: the reviewer (or you, for
`risk:high`) already decided; it only checks the gates and serialises the merges.

One run drains the queue. It lists the open pull requests against the base that carry the
queue label, oldest first (by creation time, then number), and for each one:

1. Gates, read from GitHub (`gh pr view`):
   - not a draft, and still against the base;
   - while an issue labelled `base-red` is open, only a PR labelled `fixes-base-red` lands
     (the others wait in the queue);
   - CI on the head commit: every check finished and none failed (pending: the PR waits;
     failed: it leaves the queue);
   - not from a fork (its code would run with the lander's rights);
   - approval, by `--approval`. `label` (the default): the queue label is the approval,
     because whoever added it reviewed the PR; it fits projects where every agent acts as
     one GitHub account, which cannot approve its own PRs. `review`: an approving review of
     the head commit is also needed, and a PR labelled `risk:high` needs one from a person,
     not from one of the `--bot` logins (for reviewers with their own identity, e.g. a
     GitHub App). In both modes a reviewer whose latest review requests changes blocks.
2. Land: fetch the base and `refs/pull/<N>/head` (which must still be the head the gates
   saw), check out the base detached, `git merge --no-ff` the head, run the check command on
   that merge (default `scripts/check.sh`, the full check; it must leave tracked files
   unchanged), then push the merge commit to the base, never forced. If the base moved
   meanwhile, the push is rejected and the PR is merged and verified again on the new base,
   up to `--attempts` times; after that it stays queued for the next run.
3. After a merge, the head branch is deleted (same repository only, with a lease on the
   merged head). The merge commit carries the PR body's closing lines (`Closes #12`). GitHub
   acts on closing keywords only on the default branch (checked in the sandbox, 2026-11-14:
   a pushed merge into `develop` marks the PR merged but leaves its issue open), so when the
   base is not the default branch the lander closes those issues itself.

A conflict or a red check on the candidate is a bounce: the queue label is removed, a comment
with the reason (and the end of the check's log) is posted, and the bounce is counted in that
comment. The bounce that goes over `--max-rounds` also adds `needs-human`, and the cycle stops
retrying that PR. A PR that fails a gate leaves the queue with a comment but no bounce count.

Usage:

    land.py [--base BRANCH] [--remote NAME] [--check CMD] [--check-timeout MIN]
            [--attempts N] [--max-rounds N] [--approval label|review] [--bot LOGIN]...
            [--pr N]... [--watch SECONDS] [--dry-run]

`--base` defaults to the project's `base_branch` (project-config.py). `--pr N` also
considers PR N even when GitHub's label search does not list it yet (the PR of the event that
started the run; see `queued`). `--dry-run` reads
GitHub and prints each decision without merging, commenting or labelling: shadow mode, to
compare the lander with today's integrators before switching. `--watch SECONDS` keeps
running: it drains the queue, sleeps and drains again, until interrupted (the way to run the
lander in a terminal, without GitHub Actions; a failed pass is reported and the next one
still runs).

Output: one line per pull request, `LAND #<N> <outcome> <detail>`, outcomes `merged`,
`wait`, `unqueued`, `bounced`, `needs-human`, `retry-later`, `skip` (a `--pr` that is not
open and queued). Exit codes: 0 the queue was
processed (whatever each PR's outcome); 1 usage, settings or a dirty working tree; 2 git or gh
failed in a way that leaves the run unsafe to continue.

Runs in the repository of the current directory with git and gh (authenticated with a token
that may push the base). Python 3.9 compatible, standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any

QUEUE = "queue"
BASE_RED = "base-red"
FIXES_BASE_RED = "fixes-base-red"
RISK_HIGH = "risk:high"
NEEDS_HUMAN = "needs-human"
BOUNCE_MARK = "<!-- herdr-agent-pool:lander bounce -->"
HUMAN_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
CLOSING = ("close", "closes", "closed", "fix", "fixes", "fixed", "resolve", "resolves", "resolved")
PR_FIELDS = (
    "number,state,title,body,headRefName,headRefOid,baseRefName,isDraft,isCrossRepository,"
    "labels,reviews,statusCheckRollup,comments"
)
GREEN = {"SUCCESS", "NEUTRAL", "SKIPPED"}
PENDING = {"PENDING", "QUEUED", "IN_PROGRESS", "WAITING", "REQUESTED", "EXPECTED", ""}
LOG_TAIL = 60
# A closing keyword directly followed by a same-repository reference, as GitHub reads them
# ("Fixes #3, see #4" closes #3 only; "Closes other/repo#7" is another repository's).
CLOSES_REF = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?):?\s+#(\d+)\b", re.IGNORECASE)


class Fatal(Exception):
    """git or gh failed so that continuing could land something unverified."""


@dataclass
class Settings:
    base: str
    remote: str = "origin"
    check: list[str] = field(default_factory=lambda: ["scripts/check.sh"])
    check_timeout: float = 60.0
    attempts: int = 3
    max_rounds: int = 2
    bots: set[str] = field(default_factory=set)
    dry_run: bool = False
    default_branch: str = ""
    approval: str = "label"
    watch: float = 0
    extra: list[int] = field(default_factory=list)


@dataclass
class Outcome:
    kind: str  # merged | conflict | red | moved | stale | already
    detail: str = ""


# Shell-outs ----------------------------------------------------------------------------------


def run(args: list[str], *, check: bool = True, stdin: str | None = None) -> str:
    """Run a command, return its stdout; raise Fatal when it fails and `check` is set."""
    proc = subprocess.run(args, input=stdin, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise Fatal(f"{' '.join(args[:3])} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout


def ok(args: list[str]) -> bool:
    return subprocess.run(args, capture_output=True, text=True).returncode == 0


def gh_json(args: list[str]) -> Any:
    return json.loads(run(["gh", *args]) or "null")


def git(*args: str, check: bool = True) -> str:
    return run(["git", *args], check=check).strip()


# Reading GitHub ------------------------------------------------------------------------------


def queued(s: Settings) -> list[int]:
    """Open PRs against the base with the queue label, oldest first.

    The label filter goes through GitHub's search index, which showed a label 1 to 7 s late
    in the sandbox (2026-11-14): the run a `labeled` event starts can miss its own PR. So
    the PRs given with `--pr` are added from `gh pr view`, which is consistent; `process`
    skips any of them that is not open and queued.
    """
    prs = gh_json(
        ["pr", "list", "--state", "open", "--base", s.base, "--label", QUEUE,
         "--limit", "200", "--json", "number,createdAt"]
    )  # fmt: skip
    listed = {p["number"] for p in prs}
    prs += [
        gh_json(["pr", "view", str(n), "--json", "number,createdAt"])
        for n in dict.fromkeys(s.extra) if n not in listed
    ]  # fmt: skip
    return [p["number"] for p in sorted(prs, key=lambda p: (p["createdAt"], p["number"]))]


def base_is_red() -> bool:
    issues = gh_json(["issue", "list", "--state", "open", "--label", BASE_RED, "--json", "number"])
    return bool(issues)


def view(number: int) -> dict[str, Any]:
    return gh_json(["pr", "view", str(number), "--json", PR_FIELDS])


def labels(pr: dict[str, Any]) -> set[str]:
    return {item["name"] for item in pr.get("labels") or []}


def ci_state(pr: dict[str, Any]) -> str:
    """`green`, `pending` or `red` for the checks and statuses of the head commit."""
    state = "green"
    for item in pr.get("statusCheckRollup") or []:
        if item.get("__typename") == "StatusContext":
            value = (item.get("state") or "").upper()
            done = value not in PENDING
        else:
            value = (item.get("conclusion") or "").upper()
            done = (item.get("status") or "").upper() == "COMPLETED"
        if not done:
            state = "pending"
        elif value not in GREEN:
            return "red"
    return state


def approval(pr: dict[str, Any], bots: set[str], mode: str) -> tuple[bool, str]:
    """Whether the PR is approved as `mode` (and, in `review`, its risk) requires; why not."""
    latest: dict[str, dict[str, Any]] = {}
    for review in pr.get("reviews") or []:
        if review.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[(review.get("author") or {}).get("login", "")] = review
    if any(r["state"] == "CHANGES_REQUESTED" for r in latest.values()):
        return False, "changes are requested"
    if mode == "label":
        return True, ""
    head = pr["headRefOid"]
    approvers = [
        r for r in latest.values()
        if r["state"] == "APPROVED" and (r.get("commit") or {}).get("oid") == head
    ]  # fmt: skip
    if not approvers:
        return False, "no approval of the head commit"
    if RISK_HIGH in labels(pr) and not any(is_human(r, bots) for r in approvers):
        return False, "risk:high needs a person's approval of the head commit"
    return True, ""


def is_human(review: dict[str, Any], bots: set[str]) -> bool:
    login = (review.get("author") or {}).get("login", "")
    if login in bots or login.endswith("[bot]") or login.startswith("app/"):
        return False
    return review.get("authorAssociation") in HUMAN_ASSOCIATIONS


def gate(pr: dict[str, Any], s: Settings, red: bool) -> tuple[str, str]:
    """(`land` | `wait` | `unqueue` | `skip`, reason) for one queued PR."""
    if pr.get("state", "OPEN") != "OPEN" or QUEUE not in labels(pr):
        return "skip", "not an open, queued pull request"
    if pr.get("isDraft"):
        return "unqueue", "the pull request is a draft"
    if pr.get("baseRefName") != s.base:
        return "unqueue", f"it targets {pr.get('baseRefName')}, not {s.base}"
    if pr.get("isCrossRepository"):
        return "unqueue", "it comes from a fork: land it by hand"
    if red and FIXES_BASE_RED not in labels(pr):
        return "wait", f"the base is red (an open {BASE_RED} issue); only {FIXES_BASE_RED} lands"
    ci = ci_state(pr)
    if ci == "pending":
        return "wait", "CI is still running on the head commit"
    if ci == "red":
        return "unqueue", "CI failed on the head commit"
    approved, why = approval(pr, s.bots, s.approval)
    if not approved:
        return "unqueue", why
    return "land", ""


# Landing -------------------------------------------------------------------------------------


def closing_lines(pr: dict[str, Any]) -> list[str]:
    """The PR body's lines that start with a closing keyword and name an issue."""
    return [
        line.strip() for line in (pr.get("body") or "").splitlines()
        if line.strip().split(" ", 1)[0].rstrip(":").lower() in CLOSING and "#" in line
    ]  # fmt: skip


def merge_message(pr: dict[str, Any]) -> str:
    """The merge commit's message, with the PR body's closing lines (`Closes #12`)."""
    closing = closing_lines(pr)
    parts = [f"Merge pull request #{pr['number']} from {pr['headRefName']}", pr["title"]]
    if closing:
        parts.append("\n".join(closing))
    return "\n\n".join(parts) + "\n"


def run_check(s: Settings, number: int) -> tuple[bool, str]:
    """Run the check command on the merge in the working tree; (passed, log tail)."""
    env = dict(os.environ, HERDR_AGENT_POOL_LAND="1", HERDR_AGENT_POOL_LAND_PR=str(number))
    try:
        proc = subprocess.run(
            s.check, env=env, capture_output=True, text=True, timeout=s.check_timeout * 60
        )
    except subprocess.TimeoutExpired:
        return False, f"the check timed out after {s.check_timeout:g} min"
    except OSError as exc:
        return False, f"the check could not start: {exc}"
    tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-LOG_TAIL:])
    if proc.returncode != 0:
        return False, tail
    if git("status", "--porcelain", "--untracked-files=no"):
        return False, "the check changed tracked files:\n" + git("status", "--short")
    return True, tail


def fetch(s: Settings, number: int) -> None:
    git(
        "fetch", "--quiet", s.remote,
        f"+refs/heads/{s.base}:refs/remotes/{s.remote}/{s.base}",
        f"+refs/pull/{number}/head:refs/land/pr-{number}",
    )  # fmt: skip


def reset_tree() -> None:
    git("merge", "--abort", check=False)
    git("reset", "--quiet", "--hard")


def land(pr: dict[str, Any], s: Settings) -> Outcome:
    """Merge, verify and push one PR; up to `s.attempts` tries when the base moves."""
    number, head = pr["number"], pr["headRefOid"]
    base_ref = f"refs/remotes/{s.remote}/{s.base}"
    for attempt in range(1, s.attempts + 1):
        fetch(s, number)
        if git("rev-parse", f"refs/land/pr-{number}") != head:
            return Outcome("stale", "the head moved after the gates were read")
        if ok(["git", "merge-base", "--is-ancestor", head, base_ref]):
            return Outcome("already", "the head is already in the base")
        git("checkout", "--quiet", "--detach", base_ref)
        if not ok(["git", "merge", "--quiet", "--no-ff", "-m", merge_message(pr), head]):
            reset_tree()
            return Outcome("conflict", f"it does not merge cleanly onto {s.base}")
        passed, log = run_check(s, number)
        if not passed:
            reset_tree()
            return Outcome("red", log)
        if ok(["git", "push", "--quiet", s.remote, f"HEAD:refs/heads/{s.base}"]):
            return Outcome("merged", f"{git('rev-parse', '--short', 'HEAD')} (attempt {attempt})")
    return Outcome("moved", f"the base moved {s.attempts} times during verification")


def delete_head(pr: dict[str, Any], s: Settings) -> str:
    if pr.get("isCrossRepository"):
        return "head branch kept (another repository)"
    branch, head = pr["headRefName"], pr["headRefOid"]
    lease = f"--force-with-lease=refs/heads/{branch}:{head}"
    if ok(["git", "push", "--quiet", lease, s.remote, f":refs/heads/{branch}"]):
        return f"deleted {branch}"
    return f"kept {branch} (it moved)"


# Writing GitHub ------------------------------------------------------------------------------


def comment(number: int, body: str) -> None:
    run(["gh", "pr", "comment", str(number), "--body-file", "-"], stdin=body)


def edit_labels(number: int, add: str = "", remove: str = "") -> None:
    args = ["gh", "pr", "edit", str(number)]
    if add:
        args += ["--add-label", add]
    if remove:
        args += ["--remove-label", remove]
    run(args)


def unqueue(number: int, reason: str) -> None:
    comment(number, f"Lander: removed from the queue: {reason}.")
    edit_labels(number, remove=QUEUE)


def bounce(pr: dict[str, Any], outcome: Outcome, s: Settings) -> str:
    """Count the bounce, explain it and take the PR out of the queue; returns the outcome."""
    rounds = 1 + sum(BOUNCE_MARK in (c.get("body") or "") for c in pr.get("comments") or [])
    why = {"conflict": "merge conflict", "red": "the full check failed on the merge"}
    body = [
        BOUNCE_MARK,
        f"Lander bounce {rounds} of {s.max_rounds}: {why[outcome.kind]} onto `{s.base}`.",
    ]
    if outcome.kind == "conflict":
        body.append(f"Merge `{s.base}` into the branch, resolve the conflict and push.")
    else:
        body.append("End of the check's output:\n\n```\n" + outcome.detail + "\n```")
    over = rounds > s.max_rounds
    if over:
        body.append(f"Over the limit: labelled `{NEEDS_HUMAN}`; the lander stops retrying it.")
    comment(pr["number"], "\n\n".join(body) + "\n")
    edit_labels(pr["number"], add=NEEDS_HUMAN if over else "", remove=QUEUE)
    return NEEDS_HUMAN if over else "bounced"


def close_issues(pr: dict[str, Any], s: Settings) -> str:
    """Close this repository's issues the PR names, when GitHub will not (non-default base)."""
    if not s.default_branch or s.default_branch == s.base:
        return ""
    numbers = sorted({int(n) for n in CLOSES_REF.findall(pr.get("body") or "")})
    closed = []
    for number in numbers:
        note = f"Closed by the lander: #{pr['number']} merged into `{s.base}`."
        if ok(["gh", "issue", "close", str(number), "--comment", note]):
            closed.append(f"#{number}")
    return f"; closed {' '.join(closed)}" if closed else ""


# The run -------------------------------------------------------------------------------------


def process(number: int, s: Settings, red: bool) -> tuple[str, str]:
    """Gate and land one queued PR; (outcome, detail) for the LAND line."""
    pr = view(number)
    decision, reason = gate(pr, s, red)
    if decision != "land" or s.dry_run:
        if decision == "unqueue" and not s.dry_run:
            unqueue(number, reason)
        return {"land": "would-land", "unqueue": "unqueued"}.get(decision, decision), reason
    result = land(pr, s)
    if result.kind == "merged":
        return "merged", f"{result.detail}; {delete_head(pr, s)}{close_issues(pr, s)}"
    if result.kind == "already":
        unqueue(number, result.detail)
        return "unqueued", result.detail
    if result.kind in ("stale", "moved"):
        return "retry-later", result.detail
    return bounce(pr, result, s), result.kind


def drain(s: Settings) -> int:
    """Process the queue until every queued PR was seen once in this run."""
    seen: set[int] = set()
    while True:
        red = base_is_red()
        todo = [n for n in queued(s) if n not in seen]
        if not todo:
            return len(seen)
        number = todo[0]
        seen.add(number)
        outcome, detail = process(number, s, red)
        first = detail.splitlines()[0] if detail else ""
        print(f"LAND #{number} {outcome} {first}".rstrip(), flush=True)


def default_base() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return run([sys.executable, os.path.join(here, "project-config.py"), "base_branch"]).strip()


def parse(argv: list[str]) -> Settings:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--base")
    p.add_argument("--remote", default="origin")
    p.add_argument("--check", default="scripts/check.sh", help="command, split like a shell")
    p.add_argument("--check-timeout", type=float, default=60.0, help="minutes")
    p.add_argument("--attempts", type=int, default=3)
    p.add_argument("--max-rounds", type=int, default=2)
    p.add_argument("--bot", action="append", default=[], help="a reviewer login that is a bot")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--pr", type=int, action="append", default=[], help="also consider this PR")
    p.add_argument("--approval", choices=("label", "review"), default="label")
    p.add_argument("--watch", type=float, default=0, metavar="SECONDS", help="keep running")
    a = p.parse_args(argv)
    if a.attempts < 1 or a.max_rounds < 0 or a.check_timeout <= 0:
        p.error("--attempts must be >= 1, --max-rounds >= 0, --check-timeout > 0")
    return Settings(
        base=a.base or default_base(), remote=a.remote, check=shlex.split(a.check),
        check_timeout=a.check_timeout, attempts=a.attempts, max_rounds=a.max_rounds,
        bots=set(a.bot), dry_run=a.dry_run, extra=a.pr, approval=a.approval, watch=a.watch,
    )  # fmt: skip


def main(argv: list[str]) -> int:
    try:
        s = parse(argv)
    except Fatal as exc:
        print(f"land.py: {exc}", file=sys.stderr)
        return 1
    if not s.dry_run and git("status", "--porcelain", "--untracked-files=no", check=False):
        print("land.py: the working tree has uncommitted changes", file=sys.stderr)
        return 1
    while True:
        code = one_pass(s)
        if not s.watch:
            return code
        try:
            time.sleep(s.watch)
        except KeyboardInterrupt:
            return code


def one_pass(s: Settings) -> int:
    """Drain the queue once; 0, or 2 when git or gh failed (the tree is reset)."""
    try:
        s.default_branch = (
            s.default_branch
            or run(
                ["gh", "repo", "view", "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"]
            ).strip()
        )
        count = drain(s)
    except Fatal as exc:
        print(f"land.py: {exc}", file=sys.stderr, flush=True)
        reset_tree()
        return 2
    if count or not s.watch:  # a watch stays quiet while the queue is empty
        print(f"LANDER done: {count} queued pull request(s) processed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
