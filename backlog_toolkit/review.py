import json
import shlex
import subprocess
from pathlib import Path


DISALLOWED_SHELL_TOKENS = {"|", "||", "&", "&&", ";", ">", ">>", "<", "$(", "`"}


def _run(cmd: str, cwd: Path):
    if any(token in cmd for token in DISALLOWED_SHELL_TOKENS):
        return {
            "cmd": cmd,
            "cwd": str(cwd),
            "returncode": 1,
            "stdout": "",
            "stderr": "blocked: shell operators are not allowed",
        }
    completed = subprocess.run(
        shlex.split(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return {
        "cmd": cmd,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def collect_git_snapshot(repo_root: str):
    root = Path(repo_root).resolve()
    status = _run("git status --short", root)
    diff_names = _run("git diff --name-only", root)
    cached_names = _run("git diff --cached --name-only", root)
    untracked = _run("git ls-files --others --exclude-standard", root)
    diff_stat = _run("git diff --stat", root)
    cached_stat = _run("git diff --cached --stat", root)
    branch = _run("git rev-parse --abbrev-ref HEAD", root)
    changed_files = set()
    for item in [diff_names, cached_names, untracked]:
        if item["returncode"] == 0 and item["stdout"]:
            changed_files.update(line.strip() for line in item["stdout"].splitlines() if line.strip())
    changed_files = {
        path for path in changed_files
        if "__pycache__" not in path and not path.endswith(".pyc")
    }
    return {
        "repo_root": str(root),
        "branch": branch["stdout"] if branch["returncode"] == 0 else "",
        "git_status": status,
        "diff_stat": diff_stat,
        "cached_diff_stat": cached_stat,
        "changed_files": sorted(changed_files),
        "git_ok": all(item["returncode"] == 0 for item in [status, diff_names, cached_names, untracked, diff_stat, cached_stat, branch]),
    }


def run_test_commands(repo_root: str, commands: list[str]):
    root = Path(repo_root).resolve()
    return [_run(command, root) for command in commands]


def build_review_draft(client, repo_root: str, issue_keys: list[str], test_commands: list[str], output_path: str):
    snapshot = collect_git_snapshot(repo_root)
    tests = run_test_commands(repo_root, test_commands)
    repo_name = Path(repo_root).resolve().name
    draft = {
        "meta": {
            "repo_root": snapshot["repo_root"],
                "repo_name": repo_name,
                "branch": snapshot["branch"],
                "git_ok": snapshot["git_ok"],
                "changed_files": snapshot["changed_files"],
            "git_status": snapshot["git_status"],
            "diff_stat": snapshot["diff_stat"],
            "cached_diff_stat": snapshot["cached_diff_stat"],
            "test_results": tests,
        },
        "checks": [],
    }

    for issue_key in issue_keys:
        issue = client.get_issue(issue_key)
        draft["checks"].append(
            {
                "issue_key": issue_key,
                "summary": issue["summary"],
                "approved": False,
                "review_notes": "Review required. Select relevant changed files and fill implemented/fixed before apply.",
                "paths_exist": [],
                "candidate_paths": snapshot["changed_files"],
                "grep": [],
                "commands": [
                    {"cmd": command, "workdir": ".", "expect_exit": 0}
                    for command in test_commands
                ],
                "pass_status_id": 3,
                "fail_status_id": 2,
                "repo_name": repo_name,
                "branch": snapshot["branch"],
                "pr_url": "",
                "implemented": [],
                "fixed": [],
                "pm_confirmed": False,
                "comment_header": "証拠ベース確認結果",
            }
        )

    path = Path(output_path)
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


def render_review_markdown(draft: dict) -> str:
    lines = ["# Progress Review Draft", ""]
    meta = draft["meta"]
    lines.append(f"- Repo: {meta['repo_name']}")
    lines.append(f"- Branch: {meta['branch']}")
    lines.append(f"- Git available: {'yes' if meta.get('git_ok') else 'no'}")
    lines.append("- Changed files:")
    for path in meta["changed_files"]:
        lines.append(f"  - {path}")
    lines.append("- Test results:")
    for item in meta["test_results"]:
        status = "OK" if item["returncode"] == 0 else "NG"
        lines.append(f"  - {item['cmd']}: {status}")
    lines.append("")
    for entry in draft["checks"]:
        lines.append(f"## {entry['issue_key']} {entry['summary']}")
        lines.append(f"- approved: {entry['approved']}")
        lines.append(f"- pm_confirmed: {entry['pm_confirmed']}")
        lines.append("- candidate_paths:")
        for path in entry["candidate_paths"]:
            lines.append(f"  - {path}")
        lines.append("- implemented: []")
        lines.append("- fixed: []")
        lines.append("")
    return "\n".join(lines)
