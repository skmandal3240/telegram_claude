from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router(name="start")

HELP_TEXT = """**Telegram Claude AI Bot** - Your AI automation assistant

**Commands:**
/start - Welcome message
/help - Show this help
/clear - Clear conversation history

**AI Chat** - Just send any message to chat with Claude AI

**Web Scraping:**
/scrape <url> - Summarize a webpage
/scrape <url> <question> - Ask about a webpage

**Content Generation:**
/content <prompt> - Generate content (blog posts, descriptions, etc.)

**Task Scheduling:**
/schedule <description> - Schedule a recurring task (natural language)
/tasks - List your active scheduled tasks
/cancel <id> - Cancel a scheduled task

**Examples:**
• "What is machine learning?"
• /scrape https://example.com What is this site about?
• /content Write a blog post about AI automation
• /schedule Every day at 9am remind me to check my emails
"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"Hey {message.from_user.first_name}! I'm your AI automation assistant powered by Claude.\n\n"
        "Send me any message to chat, or use /help to see all commands."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="Markdown")
