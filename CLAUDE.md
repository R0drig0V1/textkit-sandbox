# CLAUDE.md

<!-- Project rules for Claude Code agents, installed by multi-agent-herdr's install.sh. -->

`textkit` is a small Python package of text helpers: standard library only, Python 3.9+,
tests with `unittest`. Every public function has a docstring, type hints, tests, one row in
the README function table and a line in `CHANGELOG.md`.

## Layout

```
textkit/     the package, one module per topic
tests/       unittest tests, one file per module
docs/        architecture, phases/ (the plan), decisions/ (ADRs), plan-reviews/
scripts/     check.sh (all checks), integrator.sh; optional worktree-setup.sh, verify-reset.sh
.claude/     settings.json (enables the multi-agent-herdr plugin), multi-agent-herdr.json
             (base branch, integrator name), multi-agent-herdr-workflow.md (managed by the
             plugin), prompts/integrator.md
```

The workflow itself (skills, agents, guard hooks, notifications, `new-worktree.sh`,
`verify-merge.sh`) comes from the `multi-agent-herdr` plugin
(https://github.com/R0drig0V1/claude-code-herdr), enabled in `.claude/settings.json`. It runs
inside herdr (https://herdr.dev).

## Commands (run from the repo root)

```bash
scripts/check.sh                   # lint + types + tests; must stay green (edit it per project)
scripts/integrator.sh              # launch the integrator agent (inside herdr, main worktree)
/multi-agent-herdr:dispatch <type>/<name> <task>   # integrator: start a development agent
python3 -m unittest discover -s tests -t . -q     # only the unit tests
```

## Workflow

The multi-agent-herdr workflow rules (documentation, ADRs, `scripts/check.sh`, the plan, the
integrator and the development agents) are managed by the plugin and imported here; do not edit
the imported file, `/multi-agent-herdr:setup` updates it:

@.claude/multi-agent-herdr-workflow.md

## Rules

- **Language:** code, identifiers, comments, docs and commits in **English**.
- No dependencies outside the standard library.
- Every PR that adds or changes a public function adds one line under `## Unreleased` in
  `CHANGELOG.md` and keeps the README function table in sync (`scripts/check.sh` checks
  both, and the ADR numbering).
