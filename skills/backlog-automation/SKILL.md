---
name: backlog-automation
description: Use this skill when the user wants a markdown-first Backlog workflow: write parent and child tasks in md, sync them to Backlog, add child tasks or comments, report today's or delayed work, or compare repository evidence against Backlog safely with an explicit manifest before updating status.
---

# Backlog Automation

Use this skill for Backlog operations in this repository when `.env` contains `BACKLOG_SPACE_ID`, `BACKLOG_API_KEY`, and `BACKLOG_PROJECT_KEY`.

## Entry point
- Run `python3 backlog_toolkit_cli.py ...` in `backlog_automation_kit/`

## Supported workflows
- Export markdown task plans to Backlog: `sync-md`
- Convert markdown task plans to JSON: `convert-md`
- Export structured JSON to Backlog: `sync-json`
- Add a comment to an issue: `add-comment`
- Add a child task under a parent issue: `add-child-task`
- Report tasks due today or overdue: `report-today`
- Report overdue work grouped by assignee: `report-delayed`
- Generate review drafts from Git diff and tests: `draft-progress-review`
- Apply only approved reviewed manifests: `apply-reviewed-manifest`
- Compare repository evidence to Backlog and optionally post comments or update status: `compare-progress`

## Safety rules
- `sync-md` and `sync-json` default to preview mode before any write.
- Only use `--apply` when the user clearly asked to write to Backlog.
- Only use `--allow-update-existing` when the user clearly approved updating existing issues.
- For progress reflection, prefer `draft-progress-review` then `apply-reviewed-manifest`.
- Do not apply a reviewed manifest unless `approved=true` was set by a human reviewer.
- Do not update task status from guesswork.
- For task sync, only use fields explicitly written in the markdown task plan.
- For source-code comparison, require an explicit manifest file that lists evidence checks.
- Only write Backlog comments that describe verified evidence or direct user instructions.
- When multiple duplicate issues exist, prefer the latest parent-child set and say which set you touched.

## Files to load when needed
- Usage and command examples: `../../backlog_automation_guide.md`
- Compare manifest example: `../../compare_manifest.example.json`
- CLI implementation: `../../backlog_toolkit/cli.py`
- Markdown parser: `../../backlog_toolkit/markdown_tasks.py`

## Default flow
1. Confirm `.env` target project.
2. Default to markdown-first: create or edit the md task plan, then run `sync-md`.
3. Run the preview first and show what would change.
4. Only if the user wants writeback, rerun with `--apply`.
5. If the request involves source-code progress, require or generate a manifest from explicit evidence.
6. Summarize what changed in Backlog and mention any skipped or ambiguous items.
