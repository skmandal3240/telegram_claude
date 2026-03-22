from database import db
import config


async def get_conversation(user_id: int) -> list[dict]:
    return await db.get_history(user_id, config.MAX_CONVERSATION_HISTORY)


async def add_message(user_id: int, role: str, content: str):
    await db.save_message(user_id, role, content)


async def clear_conversation(user_id: int):
    await db.clear_history(user_id)
