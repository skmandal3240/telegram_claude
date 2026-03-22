import json
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import db
from services import claude_service, scraper_service

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_bot = None


def set_bot(bot):
    global _bot
    _bot = bot


async def start_scheduler():
    scheduler.start()
    await _restore_tasks()


async def _restore_tasks():
    tasks = await db.get_all_active_tasks()
    for task in tasks:
        try:
            _register_job(task)
            logger.info(f"Restored task #{task['id']}: {task['name']}")
        except Exception as e:
            logger.warning(f"Failed to restore task #{task['id']}: {e}")


def _register_job(task: dict):
    job_id = f"task_{task['id']}"
    trigger = CronTrigger.from_crontab(task["cron"])
    scheduler.add_job(
        _execute_task,
        trigger=trigger,
        id=job_id,
        args=[task],
        replace_existing=True,
    )


async def _execute_task(task: dict):
    if not _bot:
        return
    user_id = task["user_id"]
    task_type = task["type"]
    data = task.get("data", {})

    try:
        if task_type == "remind":
            text = data.get("message", task["name"])
            await _bot.send_message(user_id, f"Reminder: {text}")

        elif task_type == "scrape":
            url = data.get("url", "")
            result = await scraper_service.scrape_and_summarize(url)
            await _bot.send_message(user_id, f"Scheduled scrape of {url}:\n\n{result[:4000]}")

        elif task_type == "content":
            prompt = data.get("prompt", "")
            result = await claude_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="Generate fresh content based on this recurring prompt.",
            )
            await _bot.send_message(user_id, f"Scheduled content:\n\n{result[:4000]}")

    except Exception as e:
        logger.error(f"Task #{task['id']} failed: {e}")
        await _bot.send_message(user_id, f"Task #{task['id']} ({task['name']}) failed: {e}")


async def add_task(user_id: int, name: str, cron_expr: str, task_type: str, task_data: dict) -> int:
    task_id = await db.save_task(user_id, name, cron_expr, task_type, task_data)
    task = {
        "id": task_id,
        "user_id": user_id,
        "name": name,
        "cron": cron_expr,
        "type": task_type,
        "data": task_data,
    }
    _register_job(task)
    return task_id


async def remove_task(task_id: int, user_id: int) -> bool:
    success = await db.delete_task(task_id, user_id)
    if success:
        job_id = f"task_{task_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass
    return success


async def list_tasks(user_id: int) -> list[dict]:
    return await db.get_tasks(user_id)
