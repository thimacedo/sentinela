# DuckDuckGo helper
"""Utility functions for DuckDuckGo searches used across workers.

Current implementation provides a simple Instagram handle search used by
`CandidateScannerWorker`. The function is async and returns a list of candidate
handles (max 5) after filtering generic terms.
"""
import urllib.parse
import re
import httpx
from core.constants import DEFAULT_TIMEOUT
from workers.core.base_worker import BaseWorker

# Reuse logger via a temporary BaseWorker instance (lightweight)
_logger = BaseWorker("DuckDuckGoHelper").logger

async def search_instagram(name: str, cargo: str) -> list:
    """Search DuckDuckGo HTML for Instagram handles related to a public figure.

    Args:
        name: Candidate name.
        cargo: Position (e.g., "Presidente").

    Returns:
        List of unique handles (max 5) or empty list on error.
    """
    query = f"{name} {cargo} instagram oficial"
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    _logger.info(f"🔍 DuckDuckGo search for Instagram: '{query}'")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                raw = re.findall(r"instagram\.com/([a-zA-Z0-9_\.-]+)", resp.text)
                blacklist = ["p", "developer", "explore", "about", "legal", "terms", "directory", "accounts", "reels", "stories"]
                uniq = []
                for h in raw:
                    h_clean = h.lower().strip().replace("/", "").replace("?", "").replace("&", "")
                    if h_clean and h_clean not in blacklist and len(h_clean) > 2 and h_clean not in uniq:
                        uniq.append(h_clean)
                _logger.info(f"🌐 Handles encontrados: {uniq[:5]}")
                return uniq[:5]
    except Exception as e:
        _logger.error(f"⚠️ Erro DuckDuckGo Instagram search: {e}")
    return []
