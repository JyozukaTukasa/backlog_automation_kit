import argparse
import json
from pathlib import Path

from .client import BacklogClient, PRIORITY_NAME_TO_ID
from .description import build_description
from .evidence import evaluate_manifest, load_manifest, render_evidence_comment
from .markdown_tasks import dump_json_from_markdown, dump_markdown_template, parse_markdown_tasks
from .review import build_review_draft, render_review_markdown
from .reports import overdue_by_assignee, today_tasks
from .sync import load_json, sync_tasks


def _add_common_env_arg(parser):
    parser.add_argument("--env-file", default=None, help="Path to .env file")


def cmd_sync_json(args):
    client = BacklogClient(env_path=args.env_file)
    sync_tasks(
        client,
        load_json(args.json_file),
        apply=args.apply,
        allow_update=args.allow_update_existing,
        require_issue_key_for_updates=args.require_issue_key_for_updates,
    )


def cmd_sync_md(args):
    client = BacklogClient(env_path=args.env_file)
    sync_tasks(
        client,
        parse_markdown_tasks(args.markdown_file),
        apply=args.apply,
        allow_update=args.allow_update_existing,
        require_issue_key_for_updates=args.require_issue_key_for_updates,
    )


def cmd_add_comment(args):
    client = BacklogClient(env_path=args.env_file)
    result = client.add_comment(args.issue_key, args.content)
    print(result["id"])


def cmd_add_child_task(args):
    client = BacklogClient(env_path=args.env_file)
    parent = client.get_issue(args.parent_key)
    description = build_description(
        purpose=args.purpose,
        deliverables=args.deliverables,
        done_conditions=args.done_conditions,
    )
    priority_id = PRIORITY_NAME_TO_ID[args.priority]
    issue = client.create_issue(
        summary=args.summary,
        description=description,
        priority_id=priority_id,
        start_date=args.start_date,
        due_date=args.due_date,
        parent_issue_id=parent["id"],
        assignee_id=client.find_user_id_by_name(args.assignee) if args.assignee else None,
    )
    print(issue["issueKey"])


def cmd_report_today(args):
    client = BacklogClient(env_path=args.env_file)
    issues = today_tasks(client.get_issues(include_closed=False), args.date)
    if not issues:
        print("No tasks due today or overdue.")
        return
    for issue in issues:
        assignee = (issue.get("assignee") or {}).get("name") or "未設定"
        due = (issue.get("dueDate") or "")[:10]
        print(f"{issue['issueKey']}\t{due}\t{assignee}\t{issue['summary']}")


def cmd_report_delayed(args):
    client = BacklogClient(env_path=args.env_file)
    grouped = overdue_by_assignee(client.get_issues(include_closed=False), args.date)
    if not grouped:
        print("No overdue tasks.")
        return
    for assignee, issues in grouped.items():
        print(f"{assignee}\t{len(issues)}")
        for issue in issues:
            due = (issue.get("dueDate") or "")[:10]
            print(f"  {issue['issueKey']} {due} {issue['summary']}")


def cmd_report_rate_limit(args):
    client = BacklogClient(env_path=args.env_file)
    rate_limit = client.get_rate_limit()["rateLimit"]
    for key in ["read", "update", "search", "icon"]:
        if key not in rate_limit:
            continue
        item = rate_limit[key]
        print(f"{key}\tlimit={item['limit']}\tremaining={item['remaining']}\treset={item['reset']}")


def cmd_compare_progress(args):
    client = BacklogClient(env_path=args.env_file)
    manifest = load_manifest(args.manifest)
    results = evaluate_manifest(manifest, args.repo_root)
    for result in results:
        print(f"{result['issue_key']}\t{'PASS' if result['passed'] else 'FAIL'}")
        if args.write_comments:
            client.add_comment(result["issue_key"], render_evidence_comment(result))
        if args.apply_status:
            if result["passed"] and result.get("pm_confirmed"):
                status_id = 4
            else:
                status_id = result["pass_status_id"] if result["passed"] else result["fail_status_id"]
            if status_id:
                client.update_issue(result["issue_key"], {"statusId": status_id})


def cmd_draft_progress_review(args):
    client = BacklogClient(env_path=args.env_file)
    issue_keys = list(args.issue_key or [])
    if args.parent_key:
        parent = client.get_issue(args.parent_key)
        for issue in client.get_issues(include_closed=True):
            if issue.get("parentIssueId") == parent["id"]:
                issue_keys.append(issue["issueKey"])
    issue_keys = sorted(set(issue_keys))
    if not issue_keys:
        raise RuntimeError("issue_key か parent_key のどちらかが必要です。")
    output = build_review_draft(client, args.repo_root, issue_keys, args.test_cmd or [], args.output)
    draft = load_manifest(output)
    if args.markdown_summary:
        Path(args.markdown_summary).write_text(render_review_markdown(draft), encoding="utf-8")
        print(args.markdown_summary)
    print(output)


def cmd_apply_reviewed_manifest(args):
    client = BacklogClient(env_path=args.env_file)
    manifest = load_manifest(args.manifest)
    results = evaluate_manifest(manifest, args.repo_root)
    for result in results:
        if not result.get("approved"):
            print(f"[SKIP_UNAPPROVED] {result['issue_key']}")
            continue
        print(f"{result['issue_key']}\t{'PASS' if result['passed'] else 'FAIL'}")
        if not args.apply:
            continue
        if args.write_comments:
            client.add_comment(result["issue_key"], render_evidence_comment(result))
        if args.apply_status:
            if result["passed"] and result.get("pm_confirmed"):
                status_id = 4
            else:
                status_id = result["pass_status_id"] if result["passed"] else result["fail_status_id"]
            if status_id:
                client.update_issue(result["issue_key"], {"statusId": status_id})


def cmd_dump_template(args):
    template = {
        "checks": [
            {
                "issue_key": "AITEST-123",
                "paths_exist": ["src/app.py"],
                "grep": [{"path": "src/app.py", "pattern": "def main("}],
                "commands": [{"cmd": "python3 -m py_compile src/app.py", "workdir": "."}],
                "pass_status_id": 3,
                "fail_status_id": 2,
                "pm_confirmed": False,
                "comment_header": "証拠ベース確認結果",
            }
        ]
    }
    Path(args.output).write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


def cmd_dump_md_template(args):
    print(dump_markdown_template(args.output))


def cmd_convert_md(args):
    print(dump_json_from_markdown(args.markdown_file, args.output))


def build_parser():
    parser = argparse.ArgumentParser(description="Reusable Backlog automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync-json", help="Create or update issues from structured JSON")
    _add_common_env_arg(sync_parser)
    sync_parser.add_argument("json_file")
    sync_parser.add_argument("--apply", action="store_true", help="Actually write to Backlog")
    sync_parser.add_argument(
        "--allow-update-existing",
        action="store_true",
        help="Allow updating existing issues that match by summary",
    )
    sync_parser.add_argument(
        "--require-issue-key-for-updates",
        action="store_true",
        help="Block updates unless the task explicitly includes Issue Key",
    )
    sync_parser.set_defaults(func=cmd_sync_json)

    sync_md_parser = subparsers.add_parser("sync-md", help="Create or update issues from markdown task plan")
    _add_common_env_arg(sync_md_parser)
    sync_md_parser.add_argument("markdown_file")
    sync_md_parser.add_argument("--apply", action="store_true", help="Actually write to Backlog")
    sync_md_parser.add_argument(
        "--allow-update-existing",
        action="store_true",
        help="Allow updating existing issues that match by summary",
    )
    sync_md_parser.add_argument(
        "--require-issue-key-for-updates",
        action="store_true",
        help="Block updates unless the task explicitly includes Issue Key",
    )
    sync_md_parser.set_defaults(func=cmd_sync_md)

    comment_parser = subparsers.add_parser("add-comment", help="Add comment to issue")
    _add_common_env_arg(comment_parser)
    comment_parser.add_argument("issue_key")
    comment_parser.add_argument("content")
    comment_parser.set_defaults(func=cmd_add_comment)

    child_parser = subparsers.add_parser("add-child-task", help="Create child task under parent issue")
    _add_common_env_arg(child_parser)
    child_parser.add_argument("--parent-key", required=True)
    child_parser.add_argument("--summary", required=True)
    child_parser.add_argument("--purpose", required=True)
    child_parser.add_argument("--deliverables", nargs="+", required=True)
    child_parser.add_argument("--done-conditions", nargs="+", required=True)
    child_parser.add_argument("--assignee")
    child_parser.add_argument("--start-date")
    child_parser.add_argument("--due-date")
    child_parser.add_argument("--priority", choices=sorted(PRIORITY_NAME_TO_ID), default="medium")
    child_parser.set_defaults(func=cmd_add_child_task)

    today_parser = subparsers.add_parser("report-today", help="List tasks due today or overdue")
    _add_common_env_arg(today_parser)
    today_parser.add_argument("--date", default=None, help="YYYY-MM-DD")
    today_parser.set_defaults(func=cmd_report_today)

    delayed_parser = subparsers.add_parser("report-delayed", help="Group overdue tasks by assignee")
    _add_common_env_arg(delayed_parser)
    delayed_parser.add_argument("--date", default=None, help="YYYY-MM-DD")
    delayed_parser.set_defaults(func=cmd_report_delayed)

    rate_parser = subparsers.add_parser("report-rate-limit", help="Show current Backlog API rate limits")
    _add_common_env_arg(rate_parser)
    rate_parser.set_defaults(func=cmd_report_rate_limit)

    compare_parser = subparsers.add_parser("compare-progress", help="Evaluate source evidence and optionally update Backlog")
    _add_common_env_arg(compare_parser)
    compare_parser.add_argument("--manifest", required=True)
    compare_parser.add_argument("--repo-root", required=True)
    compare_parser.add_argument("--write-comments", action="store_true")
    compare_parser.add_argument("--apply-status", action="store_true")
    compare_parser.set_defaults(func=cmd_compare_progress)

    draft_review_parser = subparsers.add_parser(
        "draft-progress-review",
        help="Generate a review draft from Git diff and test commands before any Backlog update",
    )
    _add_common_env_arg(draft_review_parser)
    draft_review_parser.add_argument("--repo-root", required=True)
    draft_review_parser.add_argument("--parent-key")
    draft_review_parser.add_argument("--issue-key", action="append")
    draft_review_parser.add_argument("--test-cmd", action="append")
    draft_review_parser.add_argument("--output", required=True)
    draft_review_parser.add_argument("--markdown-summary")
    draft_review_parser.set_defaults(func=cmd_draft_progress_review)

    apply_review_parser = subparsers.add_parser(
        "apply-reviewed-manifest",
        help="Apply only approved entries from a reviewed manifest",
    )
    _add_common_env_arg(apply_review_parser)
    apply_review_parser.add_argument("--manifest", required=True)
    apply_review_parser.add_argument("--repo-root", required=True)
    apply_review_parser.add_argument("--write-comments", action="store_true")
    apply_review_parser.add_argument("--apply-status", action="store_true")
    apply_review_parser.add_argument("--apply", action="store_true", help="Actually write to Backlog")
    apply_review_parser.set_defaults(func=cmd_apply_reviewed_manifest)

    template_parser = subparsers.add_parser("dump-compare-template", help="Write a compare manifest template")
    template_parser.add_argument("output")
    template_parser.set_defaults(func=cmd_dump_template)

    md_template_parser = subparsers.add_parser("dump-md-template", help="Write a markdown task template")
    md_template_parser.add_argument("output")
    md_template_parser.set_defaults(func=cmd_dump_md_template)

    convert_parser = subparsers.add_parser("convert-md", help="Convert markdown task plan to structured JSON")
    convert_parser.add_argument("markdown_file")
    convert_parser.add_argument("output")
    convert_parser.set_defaults(func=cmd_convert_md)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
