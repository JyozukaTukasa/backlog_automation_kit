import json
import ssl
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def request_json(url: str, method: str = "GET", data: dict | None = None):
    encoded_data = None
    headers = {}
    if data is not None:
        encoded_data = urlencode(data, doseq=True).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request = Request(url, data=encoded_data, method=method, headers=headers)
    verify_ssl = os.environ.get("BACKLOG_ALLOW_INSECURE_SSL", "").lower() not in {"1", "true", "yes"}
    ssl_context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    try:
        with urlopen(request, context=ssl_context) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc
