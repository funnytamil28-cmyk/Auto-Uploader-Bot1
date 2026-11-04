import os
import re
import uuid

import httpx

ANILIST_URL = "https://graphql.anilist.co"

QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    title { romaji english }
    description(asHtml: false)
    coverImage { extraLarge large }
    siteUrl
  }
}
"""


def _clean_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


async def fetch_anime_info(title: str) -> dict | None:
    async with httpx.AsyncClient(timeout=15) as http:
        resp = await http.post(
            ANILIST_URL,
            json={"query": QUERY, "variables": {"search": title}},
        )

    if resp.status_code != 200:
        return None

    media = (resp.json().get("data") or {}).get("Media")
    if not media:
        return None

    synopsis = _clean_html(media.get("description"))
    if len(synopsis) > 600:
        synopsis = synopsis[:600].rsplit(" ", 1)[0] + "..."

    return {
        "title": media["title"]["english"] or media["title"]["romaji"],
        "synopsis": synopsis,
        "poster": (media.get("coverImage") or {}).get("extraLarge"),
        "url": media.get("siteUrl"),
    }


async def download_poster(url: str | None) -> str | None:
    if not url:
        return None
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.get(url)
    if resp.status_code != 200:
        return None
    path = f"/tmp/poster_{uuid.uuid4().hex}.jpg"
    with open(path, "wb") as f:
        f.write(resp.content)
    return path
