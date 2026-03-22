import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Claude Code OAuth: read token from file descriptor if available
_oauth_fd = os.getenv("CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR")
AUTH_TOKEN = ""
if _oauth_fd:
    try:
        with os.fdopen(int(_oauth_fd), "r", closefd=False) as f:
            AUTH_TOKEN = f.read().strip()
    except (OSError, ValueError):
        pass
if not AUTH_TOKEN:
    AUTH_TOKEN = os.getenv("ANTHROPIC_API_KEY", "")

BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))

_allowed = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: list[int] = [int(x.strip()) for x in _allowed.split(",") if x.strip()]

DB_PATH = os.getenv("DB_PATH", "bot_data.db")
