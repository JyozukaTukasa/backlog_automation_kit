from backlog_toolkit.client import BacklogClient
from backlog_toolkit.http import request_json


if __name__ == "__main__":
    print("Testing connection...")
    try:
        client = BacklogClient()
        issues = client.get_issues()
        print(f"Connection Successful! Found {len(issues)} active issues in project {client.project_key}.")
    except Exception as exc:
        print(f"Error during connection: {exc}")
