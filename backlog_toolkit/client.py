import time
from urllib.parse import urlencode

from .config import BacklogConfig
from .http import request_json


PRIORITY_NAME_TO_ID = {"high": 2, "medium": 3, "low": 4}
STATUS_NAME_TO_ID = {"open": 1, "working": 2, "resolved": 3, "done": 4}


class BacklogClient:
    def __init__(self, env_path: str | None = None):
        self.config = BacklogConfig.from_env(env_path)
        self.base_url = self.config.base_url
        self.api_key = self.config.api_key
        self.project_key = self.config.project_key
        self._project_id = None
        self._default_issue_type_id = None
        self._project_users = None
        self._issues_by_key = {}
        self._last_update_request_at = 0.0
        self._update_interval_seconds = 1.0

    def _with_api_key(self, path: str) -> str:
        separator = "&" if "?" in path else "?"
        return f"{self.base_url}{path}{separator}apiKey={self.api_key}"

    def get_project(self):
        return request_json(self._with_api_key(f"/projects/{self.project_key}"))

    def get_project_id(self):
        if self._project_id is None:
            self._project_id = self.get_project().get("id")
        return self._project_id

    def get_issue_types(self):
        return request_json(self._with_api_key(f"/projects/{self.project_key}/issueTypes"))

    def get_default_issue_type_id(self):
        if self._default_issue_type_id is None:
            types = self.get_issue_types()
            if not types:
                raise RuntimeError("プロジェクトに課題種別が設定されていません。")
            default_type = next((item for item in types if item["name"] == "タスク"), types[0])
            self._default_issue_type_id = default_type["id"]
        return self._default_issue_type_id

    def get_users(self):
        return request_json(self._with_api_key("/users"))

    def get_project_users(self):
        if self._project_users is None:
            self._project_users = request_json(self._with_api_key(f"/projects/{self.project_key}/users"))
        return self._project_users

    def find_user_id_by_name(self, name: str) -> int:
        users = self.get_project_users()
        matches = [user for user in users if user.get("name") == name]
        if len(matches) == 1:
            return matches[0]["id"]
        if not matches:
            raise RuntimeError(f"担当者が見つかりません: {name}")
        raise RuntimeError(f"担当者名が重複しています: {name}")

    def get_statuses(self):
        return request_json(self._with_api_key(f"/projects/{self.project_key}/statuses"))

    def get_priorities(self):
        return request_json(self._with_api_key("/priorities"))

    def get_rate_limit(self):
        return request_json(self._with_api_key("/rateLimit"))

    def get_issue(self, issue_key: str):
        if issue_key not in self._issues_by_key:
            self._issues_by_key[issue_key] = request_json(self._with_api_key(f"/issues/{issue_key}"))
        return self._issues_by_key[issue_key]

    def get_issues(self, include_closed: bool = False):
        all_issues = []
        offset = 0
        count = 100
        while True:
            params = {
                "apiKey": self.api_key,
                "projectId[]": [self.get_project_id()],
                "count": count,
                "offset": offset,
            }
            if not include_closed:
                params["statusId[]"] = [1, 2, 3]
            url = f"{self.base_url}/issues?{urlencode(params, doseq=True)}"
            issues = request_json(url)
            all_issues.extend(issues)
            if len(issues) < count:
                break
            offset += count
        return all_issues

    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type_id: int | None = None,
        priority_id: int = 3,
        start_date: str | None = None,
        due_date: str | None = None,
        parent_issue_id: int | None = None,
        assignee_id: int | None = None,
    ):
        data = {
            "projectId": self.get_project_id(),
            "summary": summary,
            "description": description,
            "issueTypeId": issue_type_id or self.get_default_issue_type_id(),
            "priorityId": priority_id,
        }
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
        if parent_issue_id:
            data["parentIssueId"] = parent_issue_id
        if assignee_id:
            data["assigneeId"] = assignee_id
        self._throttle_update()
        return request_json(self._with_api_key("/issues"), method="POST", data=data)

    def update_issue(self, issue_key: str, data: dict):
        self._throttle_update()
        return request_json(self._with_api_key(f"/issues/{issue_key}"), method="PATCH", data=data)

    def add_comment(self, issue_key: str, content: str):
        self._throttle_update()
        return request_json(
            self._with_api_key(f"/issues/{issue_key}/comments"),
            method="POST",
            data={"content": content},
        )

    def _throttle_update(self):
        now = time.time()
        wait = self._update_interval_seconds - (now - self._last_update_request_at)
        if wait > 0:
            time.sleep(wait)
        self._last_update_request_at = time.time()
