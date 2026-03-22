import aiohttp
from bs4 import BeautifulSoup

from services import claude_service

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TelegramBot/1.0)"
}
_MAX_TEXT_LENGTH = 8000


async def scrape_url(url: str) -> str:
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    if len(text) > _MAX_TEXT_LENGTH:
        text = text[:_MAX_TEXT_LENGTH] + "\n...[truncated]"
    return text


async def scrape_and_summarize(url: str, question: str | None = None) -> str:
    text = await scrape_url(url)
    if not text.strip():
        return "Could not extract meaningful text from that URL."

    if question:
        prompt = f"Based on this webpage content, answer: {question}\n\nContent:\n{text}"
    else:
        prompt = f"Summarize the key information from this webpage:\n\n{text}"

    return await claude_service.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are a web content analyst. Provide clear, concise summaries and answers based on webpage content.",
    )
