import json
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services import claude_service, scheduler_service
from utils.helpers import format_task_list

router = Router(name="automation")

PARSE_SCHEDULE_SYSTEM = """You are a scheduling assistant. Parse the user's natural language scheduling request into a JSON object with these fields:
- "cron": a 5-field cron expression (minute hour day_of_month month day_of_week)
- "name": a short description of the task
- "type": one of "remind", "scrape", or "content"
- "data": an object with relevant data:
  - For "remind": {"message": "the reminder text"}
  - For "scrape": {"url": "the url to scrape"}
  - For "content": {"prompt": "the content generation prompt"}

Respond with ONLY the JSON object, no other text.

Examples:
- "every day at 9am remind me to check emails" -> {"cron": "0 9 * * *", "name": "Check emails reminder", "type": "remind", "data": {"message": "Check your emails"}}
- "every monday at 8am scrape https://news.com" -> {"cron": "0 8 * * 1", "name": "Weekly news scrape", "type": "scrape", "data": {"url": "https://news.com"}}
- "every friday generate a weekly blog post about AI" -> {"cron": "0 9 * * 5", "name": "Weekly AI blog post", "type": "content", "data": {"prompt": "Write a weekly blog post about the latest in AI"}}
"""


@router.message(Command("schedule"))
async def cmd_schedule(message: Message):
    description = message.text.removeprefix("/schedule").strip()
    if not description:
        await message.answer(
            "Usage: /schedule <natural language description>\n\n"
            "Examples:\n"
            "• /schedule every day at 9am remind me to check emails\n"
            "• /schedule every monday scrape https://news.com\n"
            "• /schedule every friday write a blog post about AI trends"
        )
        return

    status = await message.answer("Parsing your schedule request...")

    try:
        result = await claude_service.chat(
            messages=[{"role": "user", "content": description}],
            system_prompt=PARSE_SCHEDULE_SYSTEM,
        )
        parsed = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
    except (json.JSONDecodeError, Exception) as e:
        await status.edit_text(f"Could not parse schedule: {e}\n\nTry being more specific, e.g. 'every day at 9am remind me to check stocks'")
        return

    try:
        task_id = await scheduler_service.add_task(
            user_id=message.from_user.id,
            name=parsed["name"],
            cron_expr=parsed["cron"],
            task_type=parsed["type"],
            task_data=parsed.get("data", {}),
        )
    except Exception as e:
        await status.edit_text(f"Failed to create task: {e}")
        return

    await status.edit_text(
        f"Task #{task_id} created!\n\n"
        f"**Name:** {parsed['name']}\n"
        f"**Schedule:** `{parsed['cron']}`\n"
        f"**Type:** {parsed['type']}\n\n"
        "Use /tasks to see all tasks, /cancel <id> to remove.",
        parse_mode="Markdown",
    )


@router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    tasks = await scheduler_service.list_tasks(message.from_user.id)
    await message.answer(format_task_list(tasks), parse_mode="Markdown")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /cancel <task_id>")
        return

    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("Task ID must be a number.")
        return

    success = await scheduler_service.remove_task(task_id, message.from_user.id)
    if success:
        await message.answer(f"Task #{task_id} cancelled.")
    else:
        await message.answer(f"Task #{task_id} not found or not yours.")
