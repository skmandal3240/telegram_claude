from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from services import claude_service, memory_service
from utils.helpers import split_message

router = Router(name="chat")


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await memory_service.clear_conversation(message.from_user.id)
    await message.answer("Conversation history cleared.")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_chat(message: Message):
    user_id = message.from_user.id
    user_text = message.text

    thinking = await message.answer("Thinking...")

    await memory_service.add_message(user_id, "user", user_text)
    history = await memory_service.get_conversation(user_id)

    try:
        response = await claude_service.chat(messages=history)
    except Exception as e:
        await thinking.edit_text(f"Error: {e}")
        return

    await memory_service.add_message(user_id, "assistant", response)

    chunks = split_message(response)
    await thinking.edit_text(chunks[0], parse_mode="Markdown")
    for chunk in chunks[1:]:
        await message.answer(chunk, parse_mode="Markdown")
