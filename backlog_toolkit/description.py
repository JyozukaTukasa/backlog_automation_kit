def build_description(purpose: str, deliverables: list[str], done_conditions: list[str]) -> str:
    lines = ["目的:", purpose.strip(), "成果物:"]
    lines.extend(f"- {item}" for item in deliverables if item)
    lines.append("完了条件:")
    lines.extend(f"- {item}" for item in done_conditions if item)
    return "\n".join(lines)
