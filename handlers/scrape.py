from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services import scraper_service
from utils.helpers import split_message

router = Router(name="scrape")


@router.message(Command("scrape"))
async def cmd_scrape(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer("Usage: /scrape <url> [question]\n\nExample: /scrape https://example.com What is this about?")
        return

    url = args[1]
    question = args[2] if len(args) > 2 else None

    status = await message.answer(f"Scraping {url}...")

    try:
        result = await scraper_service.scrape_and_summarize(url, question)
    except Exception as e:
        await status.edit_text(f"Failed to scrape: {e}")
        return

    chunks = split_message(result)
    await status.edit_text(chunks[0], parse_mode="Markdown")
    for chunk in chunks[1:]:
        await message.answer(chunk, parse_mode="Markdown")
