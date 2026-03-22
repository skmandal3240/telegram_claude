import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Claude Code cloud: read session token for Bearer auth
_SESSION_TOKEN_FILE = "/home/claude/.claude/remote/.session_ingress_token"
AUTH_TOKEN = ""
USE_BEARER_AUTH = False

try:
    with open(_SESSION_TOKEN_FILE) as f:
        AUTH_TOKEN = f.read().strip()
    USE_BEARER_AUTH = True
except FileNotFoundError:
    pass

if not AUTH_TOKEN:
    AUTH_TOKEN = os.getenv("ANTHROPIC_API_KEY", "")
    USE_BEARER_AUTH = False

BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))

_allowed = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: list[int] = [int(x.strip()) for x in _allowed.split(",") if x.strip()]

DB_PATH = os.getenv("DB_PATH", "bot_data.db")
