from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services import claude_service
from utils.helpers import split_message

router = Router(name="content")

CONTENT_SYSTEM = (
    "You are an expert content creator. Generate high-quality, engaging content "
    "based on the user's request. Support blog posts, product descriptions, "
    "SEO-optimized articles, social media posts, email copy, and more. "
    "Use markdown formatting. Make it professional and ready to publish."
)


@router.message(Command("content"))
async def cmd_content(message: Message):
    prompt = message.text.removeprefix("/content").strip()
    if not prompt:
        await message.answer(
            "Usage: /content <prompt>\n\n"
            "Examples:\n"
            "• /content Write a blog post about AI automation\n"
            "• /content Product description for a smart water bottle\n"
            "• /content SEO article about remote work productivity"
        )
        return

    status = await message.answer("Generating content...")

    try:
        result = await claude_service.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=CONTENT_SYSTEM,
        )
    except Exception as e:
        await status.edit_text(f"Error generating content: {e}")
        return

    chunks = split_message(result)
    await status.edit_text(chunks[0], parse_mode="Markdown")
    for chunk in chunks[1:]:
        await message.answer(chunk, parse_mode="Markdown")
