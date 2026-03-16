import json
from pathlib import Path

from .description import build_description


FIELD_MAP = {
    "issue key": "issue_key",
    "assignee": "assignee_name",
    "priority": "priority",
    "start date": "start_date",
    "due date": "due_date",
    "purpose": "purpose",
}

LIST_FIELD_MAP = {
    "deliverables": "deliverables",
    "done conditions": "done_conditions",
}


def _new_task(task_type: str, summary: str, parent_summary: str | None = None):
    return {
        "task_type": task_type,
        "summary": summary,
        "issue_key": None,
        "parent_summary": parent_summary,
        "assignee_name": None,
        "priority": "medium",
        "start_date": None,
        "due_date": None,
        "purpose": "",
        "deliverables": [],
        "done_conditions": [],
    }


def parse_markdown_tasks(path: str):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    tasks = []
    current_parent = None
    current_task = None
    current_list = None

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            current_list = None
            continue
        if stripped.startswith("# "):
            continue
        if stripped.startswith("## Parent: "):
            if current_task:
                tasks.append(finalize_task(current_task))
            summary = stripped.removeprefix("## Parent: ").strip()
            current_parent = summary
            current_task = _new_task("parent", summary)
            current_list = None
            continue
        if stripped.startswith("### Child: "):
            if current_task:
                tasks.append(finalize_task(current_task))
            if not current_parent:
                raise ValueError("Child task appears before any parent task.")
            summary = stripped.removeprefix("### Child: ").strip()
            current_task = _new_task("child", summary, current_parent)
            current_list = None
            continue
        if stripped.startswith("- ") and ":" in stripped:
            key, value = stripped[2:].split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key in FIELD_MAP:
                current_task[FIELD_MAP[key]] = value
                current_list = None
                continue
            if key in LIST_FIELD_MAP:
                current_list = LIST_FIELD_MAP[key]
                if value:
                    current_task[current_list].append(value)
                continue
        if stripped.startswith("- ") and current_list:
            current_task[current_list].append(stripped[2:].strip())
            continue
        raise ValueError(f"Unsupported markdown format: {line}")

    if current_task:
        tasks.append(finalize_task(current_task))
    return tasks


def finalize_task(task: dict):
    result = {
        "task_type": task["task_type"],
        "summary": task["summary"],
        "description": build_description(
            purpose=task["purpose"],
            deliverables=task["deliverables"],
            done_conditions=task["done_conditions"],
        ),
        "start_date": task["start_date"],
        "due_date": task["due_date"],
        "priority_name": task["priority"].lower(),
    }
    if task["issue_key"]:
        result["issue_key"] = task["issue_key"]
    if task["parent_summary"]:
        result["parent_summary"] = task["parent_summary"]
    if task["assignee_name"]:
        result["assignee_name"] = task["assignee_name"]
    return result


def dump_markdown_template(path: str):
    template = """# Backlog Task Plan

## Parent: 第一研修の要件定義を固める
- Issue Key:
- Assignee: 定塚 司
- Priority: high
- Start Date: 2026-03-16
- Due Date: 2026-03-19
- Purpose: 第一研修の前提、到達目標、判断基準を確定する。
- Deliverables:
  - 要件定義書
  - 判断基準表
- Done Conditions:
  - 要件定義書が確定している
  - 関係者合意が取れている

### Child: 1-1 議事録から前提情報を抜き出す
- Issue Key:
- Assignee: 定塚 司
- Priority: high
- Start Date: 2026-03-16
- Due Date: 2026-03-16
- Purpose: 議事録から研修の目的、対象者、期間、期待レベルを抽出する。
- Deliverables:
  - 前提整理メモ
- Done Conditions:
  - 目的、対象者、期間、期待レベルが整理されている
"""
    Path(path).write_text(template, encoding="utf-8")
    return path


def dump_json_from_markdown(md_path: str, json_path: str):
    tasks = parse_markdown_tasks(md_path)
    Path(json_path).write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return json_path
