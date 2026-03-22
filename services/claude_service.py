import httpx
from anthropic import AsyncAnthropic

import config

if config.USE_BEARER_AUTH:
    # Claude Code cloud: use Bearer token auth instead of x-api-key
    _http_client = httpx.AsyncClient(
        headers={"Authorization": f"Bearer {config.AUTH_TOKEN}"},
    )
    _client = AsyncAnthropic(
        api_key="bearer-auth",  # placeholder, overridden by header
        base_url=config.BASE_URL,
        http_client=_http_client,
    )
else:
    _client = AsyncAnthropic(api_key=config.AUTH_TOKEN, base_url=config.BASE_URL)

DEFAULT_SYSTEM = (
    "You are an AI automation assistant on Telegram. "
    "You help users with scheduling tasks, analyzing web content, "
    "generating content, writing code, and general AI assistance. "
    "Keep responses concise and actionable. Use markdown formatting."
)


async def chat(messages: list[dict], system_prompt: str | None = None) -> str:
    response = await _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt or DEFAULT_SYSTEM,
        messages=messages,
    )
    return response.content[0].text


async def chat_stream(messages: list[dict], system_prompt: str | None = None):
    async with _client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt or DEFAULT_SYSTEM,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
