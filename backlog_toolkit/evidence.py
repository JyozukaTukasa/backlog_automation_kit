import json
import shlex
import subprocess
from pathlib import Path


DISALLOWED_SHELL_TOKENS = {"|", "||", "&", "&&", ";", ">", ">>", "<", "$(", "`"}


def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _check_paths_exist(repo_root: Path, paths: list[str]):
    results = []
    for rel_path in paths:
        path = repo_root / rel_path
        results.append((rel_path, path.exists()))
    return results


def _check_grep(repo_root: Path, items: list[dict]):
    results = []
    for item in items:
        path = repo_root / item["path"]
        pattern = item["pattern"]
        matched = path.exists() and pattern in path.read_text(encoding="utf-8", errors="replace")
        results.append((item["path"], pattern, matched))
    return results


def _check_commands(repo_root: Path, commands: list[dict]):
    results = []
    for item in commands:
        workdir = repo_root / item.get("workdir", ".")
        command = item["cmd"]
        if any(token in command for token in DISALLOWED_SHELL_TOKENS):
            results.append(
                {
                    "cmd": command,
                    "workdir": str(workdir),
                    "ok": False,
                    "stdout": "",
                    "stderr": "blocked: shell operators are not allowed",
                }
            )
            continue
        completed = subprocess.run(
            shlex.split(command),
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        results.append(
            {
                "cmd": command,
                "workdir": str(workdir),
                "ok": completed.returncode == item.get("expect_exit", 0),
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
    return results


def evaluate_manifest(manifest: dict, repo_root: str):
    root = Path(repo_root).resolve()
    checks = []
    for item in manifest.get("checks", []):
        has_evidence = bool(item.get("paths_exist") or item.get("grep") or item.get("commands"))
        path_results = _check_paths_exist(root, item.get("paths_exist", []))
        grep_results = _check_grep(root, item.get("grep", []))
        command_results = _check_commands(root, item.get("commands", []))
        passed = (
            has_evidence
            and
            all(result[1] for result in path_results)
            and all(result[2] for result in grep_results)
            and all(result["ok"] for result in command_results)
        )
        checks.append(
            {
                "issue_key": item["issue_key"],
                "approved": item.get("approved", False),
                "has_evidence": has_evidence,
                "passed": passed,
                "path_results": path_results,
                "grep_results": grep_results,
                "command_results": command_results,
                "pass_status_id": item.get("pass_status_id"),
                "fail_status_id": item.get("fail_status_id"),
                "comment_header": item.get("comment_header", "証拠ベース確認結果"),
                "repo_name": item.get("repo_name"),
                "branch": item.get("branch"),
                "pr_url": item.get("pr_url"),
                "implemented": item.get("implemented", []),
                "fixed": item.get("fixed", []),
                "pm_confirmed": item.get("pm_confirmed", False),
            }
        )
    return checks


def render_evidence_comment(result: dict) -> str:
    lines = [result["comment_header"], f"- 判定: {'PASS' if result['passed'] else 'FAIL'}"]
    if result.get("repo_name"):
        lines.append(f"- リポジトリ: {result['repo_name']}")
    if result.get("branch"):
        lines.append(f"- ブランチ: {result['branch']}")
    if result.get("pr_url"):
        lines.append(f"- PR/URL: {result['pr_url']}")
    if result.get("implemented"):
        lines.append("- 実装内容:")
        lines.extend(f"  - {item}" for item in result["implemented"])
    if result.get("fixed"):
        lines.append("- 修正内容:")
        lines.extend(f"  - {item}" for item in result["fixed"])
    if result["path_results"]:
        lines.append("- 存在確認:")
        lines.extend(
            f"  - {path}: {'OK' if ok else 'NG'}" for path, ok in result["path_results"]
        )
    if result["grep_results"]:
        lines.append("- 文字列確認:")
        lines.extend(
            f"  - {path} / {pattern}: {'OK' if ok else 'NG'}"
            for path, pattern, ok in result["grep_results"]
        )
    if result["command_results"]:
        lines.append("- コマンド確認:")
        for command in result["command_results"]:
            status = "OK" if command["ok"] else "NG"
            lines.append(f"  - {command['cmd']}: {status}")
            if command["stdout"]:
                lines.append(f"    - stdout: {command['stdout'][:200]}")
            if command["stderr"]:
                lines.append(f"    - stderr: {command['stderr'][:200]}")
    if result["passed"]:
        lines.append(f"- Backlog反映候補: {'完了' if result.get('pm_confirmed') else '処理済み'}")
    else:
        lines.append("- Backlog反映候補: 処理中")
    if not result.get("has_evidence", True):
        lines.append("- 注意: 判定に使う証拠が未設定")
    return "\n".join(lines)
