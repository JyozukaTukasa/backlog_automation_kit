import argparse

from backlog_toolkit.client import BacklogClient
from backlog_toolkit.sync import load_json, sync_tasks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync tasks from JSON to Backlog.")
    parser.add_argument("json_file", help="Path to target tasks JSON file")
    parser.add_argument("--env-file", default=None, help="Path to .env file")
    args = parser.parse_args()

    try:
        client = BacklogClient(env_path=args.env_file)
        sync_tasks(client, load_json(args.json_file))
        print("Sync completed!")
    except Exception as exc:
        print(f"Error during script execution: {exc}")
