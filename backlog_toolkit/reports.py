from collections import defaultdict
from datetime import date


def iso_today() -> str:
    return date.today().isoformat()


def _issue_due_date(issue: dict) -> str | None:
    due = issue.get("dueDate")
    if not due:
        return None
    return due[:10]


def today_tasks(issues: list[dict], target_date: str | None = None):
    target = target_date or iso_today()
    result = []
    for issue in issues:
        due = _issue_due_date(issue)
        if not due:
            continue
        if due <= target and issue.get("status", {}).get("name") != "完了":
            result.append(issue)
    return sorted(result, key=lambda item: (_issue_due_date(item), item["issueKey"]))


def overdue_by_assignee(issues: list[dict], target_date: str | None = None):
    target = target_date or iso_today()
    grouped = defaultdict(list)
    for issue in issues:
        due = _issue_due_date(issue)
        if not due or due >= target:
            continue
        if issue.get("status", {}).get("name") == "完了":
            continue
        assignee = (issue.get("assignee") or {}).get("name") or "未設定"
        grouped[assignee].append(issue)
    return dict(sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])))
