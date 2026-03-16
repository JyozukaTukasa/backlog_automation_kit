import json


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_create_payload(task: dict) -> dict:
    return {
        "issue_key": task.get("issue_key"),
        "summary": task["summary"],
        "description": task.get("description", ""),
        "priority_id": task.get("priority_id", 3),
        "priority_name": task.get("priority_name"),
        "start_date": task.get("start_date"),
        "due_date": task.get("due_date"),
        "assignee_id": task.get("assignee_id"),
        "assignee_name": task.get("assignee_name"),
    }


def build_update_payload(payload: dict) -> dict:
    data = {
        "summary": payload["summary"],
        "description": payload["description"],
        "priorityId": payload["priority_id"],
    }
    if payload.get("start_date"):
        data["startDate"] = payload["start_date"]
    if payload.get("due_date"):
        data["dueDate"] = payload["due_date"]
    if payload.get("parent_issue_id"):
        data["parentIssueId"] = payload["parent_issue_id"]
    if payload.get("assignee_id"):
        data["assigneeId"] = payload["assignee_id"]
    return data


def _log_result(results: list[dict], action: str, task: dict, issue=None, reason: str | None = None):
    results.append(
        {
            "action": action,
            "summary": task["summary"],
            "issue_key": (issue or {}).get("issueKey") if issue else task.get("issue_key"),
            "reason": reason,
        }
    )


def _print_summary(stdout, results: list[dict]):
    counts = {}
    for item in results:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
    stdout(
        "[SUMMARY] "
        + ", ".join(f"{key}={counts[key]}" for key in sorted(counts))
    )
    for item in results:
        parts = [f"[{item['action']}]", item.get("issue_key") or "-", item["summary"]]
        if item.get("reason"):
            parts.append(item["reason"])
        stdout(" ".join(parts))


def _find_existing_issue(task: dict, existing_by_summary: dict, client):
    if task.get("issue_key"):
        return client.get_issue(task["issue_key"])
    return existing_by_summary.get(task["summary"])


def sync_tasks(
    client,
    tasks: list[dict],
    stdout=print,
    apply: bool = False,
    allow_update: bool = False,
    require_issue_key_for_updates: bool = False,
):
    existing_issues = client.get_issues(include_closed=True)
    target_summaries = {
        task["summary"] for task in tasks
    } | {
        task["parent_summary"] for task in tasks if task.get("parent_summary")
    }
    existing_by_summary = {}
    duplicates = set()
    for issue in existing_issues:
        summary = issue["summary"]
        if summary not in target_summaries:
            continue
        if summary in existing_by_summary:
            duplicates.add(summary)
            continue
        existing_by_summary[summary] = issue
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise RuntimeError(f"同名課題が複数あるため同期を停止しました: {duplicate_list}")

    parents = [task for task in tasks if task.get("task_type") == "parent"]
    children = [task for task in tasks if task.get("task_type") != "parent"]
    results = []

    for task in parents:
        payload = build_create_payload(task)
        resolve_payload_refs(client, payload)
        summary = task["summary"]
        issue = _find_existing_issue(task, existing_by_summary, client)
        if issue:
            if require_issue_key_for_updates and not task.get("issue_key"):
                stdout(f"[BLOCKED_UPDATE_NO_ISSUE_KEY] {issue['issueKey']} {summary}")
                _log_result(results, "BLOCKED_UPDATE_NO_ISSUE_KEY", task, issue, "issue key is required for updates in existing-project mode")
                continue
            if not allow_update:
                stdout(f"[BLOCKED_UPDATE] {issue['issueKey']} {summary}")
                _log_result(results, "BLOCKED_UPDATE", task, issue, "allow_update_existing is required")
                continue
            if not apply:
                stdout(f"[DRY_RUN_UPDATE] {issue['issueKey']} {summary}")
                _log_result(results, "DRY_RUN_UPDATE", task, issue)
                continue
            stdout(f"[UPDATE] {issue['issueKey']} {summary}")
            client.update_issue(issue["issueKey"], build_update_payload(payload))
            _log_result(results, "UPDATE", task, issue)
        else:
            if not apply:
                stdout(f"[DRY_RUN_CREATE] {summary}")
                _log_result(results, "DRY_RUN_CREATE", task)
                continue
            stdout(f"[CREATE] {summary}")
            issue = client.create_issue(**payload)
            stdout(f"  -> {issue['issueKey']}")
            existing_by_summary[summary] = issue
            _log_result(results, "CREATE", task, issue)

    for task in children:
        payload = build_create_payload(task)
        resolve_payload_refs(client, payload)
        summary = task["summary"]
        parent_summary = task.get("parent_summary")
        if parent_summary:
            parent_issue = existing_by_summary.get(parent_summary)
            if not parent_issue:
                raise RuntimeError(f"親課題が見つかりません: {parent_summary}")
            payload["parent_issue_id"] = parent_issue["id"]
        issue = _find_existing_issue(task, existing_by_summary, client)
        if issue:
            if require_issue_key_for_updates and not task.get("issue_key"):
                stdout(f"[BLOCKED_UPDATE_NO_ISSUE_KEY] {issue['issueKey']} {summary}")
                _log_result(results, "BLOCKED_UPDATE_NO_ISSUE_KEY", task, issue, "issue key is required for updates in existing-project mode")
                continue
            if not allow_update:
                stdout(f"[BLOCKED_UPDATE] {issue['issueKey']} {summary}")
                _log_result(results, "BLOCKED_UPDATE", task, issue, "allow_update_existing is required")
                continue
            if not apply:
                stdout(f"[DRY_RUN_UPDATE] {issue['issueKey']} {summary}")
                _log_result(results, "DRY_RUN_UPDATE", task, issue)
                continue
            stdout(f"[UPDATE] {issue['issueKey']} {summary}")
            client.update_issue(issue["issueKey"], build_update_payload(payload))
            _log_result(results, "UPDATE", task, issue)
        else:
            if not apply:
                stdout(f"[DRY_RUN_CREATE] {summary}")
                _log_result(results, "DRY_RUN_CREATE", task)
                continue
            stdout(f"[CREATE] {summary}")
            issue = client.create_issue(**payload)
            stdout(f"  -> {issue['issueKey']}")
            existing_by_summary[summary] = issue
            _log_result(results, "CREATE", task, issue)
    _print_summary(stdout, results)


def resolve_payload_refs(client, payload: dict):
    priority_name = payload.pop("priority_name", None)
    payload.pop("issue_key", None)
    if priority_name:
        mapping = {"high": 2, "medium": 3, "low": 4}
        if priority_name not in mapping:
            raise RuntimeError(f"未対応の優先度です: {priority_name}")
        payload["priority_id"] = mapping[priority_name]
    assignee_name = payload.pop("assignee_name", None)
    if assignee_name:
        payload["assignee_id"] = client.find_user_id_by_name(assignee_name)
