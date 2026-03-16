from dataclasses import dataclass
import os
from pathlib import Path


def load_env_file(env_path: str | None = None) -> Path | None:
    path = Path(env_path) if env_path else Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
    return path


@dataclass(frozen=True)
class BacklogConfig:
    space_id: str
    api_key: str
    project_key: str

    @property
    def host(self) -> str:
        if ".backlog." in self.space_id:
            return self.space_id
        return f"{self.space_id}.backlog.com"

    @property
    def base_url(self) -> str:
        return f"https://{self.host}/api/v2"

    @classmethod
    def from_env(cls, env_path: str | None = None) -> "BacklogConfig":
        load_env_file(env_path)
        space_id = os.environ.get("BACKLOG_SPACE_ID")
        api_key = os.environ.get("BACKLOG_API_KEY")
        project_key = os.environ.get("BACKLOG_PROJECT_KEY")
        if not all([space_id, api_key, project_key]):
            raise ValueError("必要な環境変数が設定されていません (.env を確認してください)。")
        return cls(space_id=space_id, api_key=api_key, project_key=project_key)
