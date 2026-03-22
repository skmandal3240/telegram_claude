def split_message(text: str, max_len: int = 4096) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


def format_task_list(tasks: list[dict]) -> str:
    if not tasks:
        return "No active scheduled tasks."
    lines = ["**Active Tasks:**\n"]
    for t in tasks:
        lines.append(f"• **#{t['id']}** - {t['name']}\n  Cron: `{t['cron']}` | Type: {t['type']}")
    return "\n".join(lines)
