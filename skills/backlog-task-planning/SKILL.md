---
name: backlog-task-planning
description: Use this skill when the user wants to turn given requirements, meeting notes, and current Git repository state into a Backlog-ready markdown task plan with parent tasks, child tasks, assignees, dates, priorities, purpose, deliverables, and done conditions.
---

# Backlog Task Planning

Use this skill to create the markdown task plan before syncing to Backlog.

## Goal
Produce `task_plan.md` in the exact format used by `backlog_toolkit_cli.py sync-md`.

## Modes

### New project mode
Use this when the user is starting a new project or a new workstream and mainly wants tasks from requirements.

Required inputs:
- User-provided requirements, notes, or change requests
- Existing docs/specs if present

Do not inspect Git unless the user explicitly asks for source-based comparison.

### Existing project mode
Use this when the user already has Backlog tasks or wants to compare new work against the current repository state.

Required inputs:
- User-provided requirements, notes, or change requests
- Current repository evidence when needed
  - `git status`
  - relevant file diffs or changed file list
  - existing docs/specs if present

## Default workflow
1. Decide whether this is new project mode or existing project mode.
2. Read the given requirements and only the minimum necessary context.
3. In existing project mode, inspect Git evidence only if it is needed for task planning.
4. Separate work into parent tasks and child tasks.
5. For each task, write:
   - assignee
   - priority
   - start date
   - due date
   - purpose
   - deliverables
   - done conditions
   - issue key when updating an existing Backlog task
6. Output markdown in the exact format of `../../task_plan_template.md`.

## Safety rules
- Do not invent implementation work that is not supported by user input or repository evidence.
- If dates, assignees, or scope are missing, mark them explicitly as placeholders instead of guessing.
- When using Git state, distinguish:
  - already implemented
  - partially implemented
  - not started
- In new project mode, do not open unrelated source files just to be thorough.
- Keep child tasks reviewable and small enough for a single implementation unit.
- Prefer the lightest workflow that can still produce a correct `task_plan.md`.

## Files to load when needed
- Template: `../../task_plan_template.md`
- Backlog sync usage: `../../backlog_automation_guide.md`

## Good triggers
- `この要件からBacklog用のタスクmdを作って`
- `今のGit差分と仕様差分からタスクを洗い出して`
- `親タスク配下に追加する小タスクを整理して`
