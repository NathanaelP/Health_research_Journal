"""
Extract Twitter/X threads using twscrape (primary) with ThreadReaderApp fallback.

Primary: twscrape with cookie-based auth — bypasses Cloudflare login blocks.
Fallback: ThreadReaderApp — no auth required, works for popular/pre-unrolled threads.

Supports twitter.com and x.com URLs. Returns (title, text) matching
the same contract as article_extractor.extract_article().
"""
import asyncio
import re
import requests
from typing import Optional

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HealthResearchBot/1.0)"}

# twscrape API singleton — initialized lazily inside the running event loop
_api = None
_lock: Optional[asyncio.Lock] = None


def is_twitter_url(url: str) -> bool:
    """Return True if url is a twitter.com or x.com tweet URL."""
    return bool(re.match(r"https?://(www\.)?(twitter\.com|x\.com)/", url))


def _extract_tweet_id(url: str) -> str:
    """Parse the numeric tweet ID from a twitter.com or x.com URL."""
    match = re.search(r"/status/(\d+)", url)
    if not match:
        raise ValueError(f"Cannot extract tweet ID from URL: {url}")
    return match.group(1)


async def _get_api():
    """
    Lazily initialize and cache the twscrape API singleton.

    Prefers cookie-based auth (TWITTER_COOKIES) which bypasses Cloudflare.
    Falls back to password login if no cookies are set.
    """
    global _api, _lock

    if _lock is None:
        _lock = asyncio.Lock()

    async with _lock:
        if _api is not None:
            return _api

        from app.config import settings

        if not settings.twitter_username:
            raise ValueError(
                "TWITTER_USERNAME not set in .env. "
                "Set TWITTER_USERNAME and TWITTER_COOKIES (recommended) or TWITTER_PASSWORD."
            )

        from twscrape import API

        api = API(settings.twitter_db_path)

        await api.pool.add_account(
            username=settings.twitter_username,
            password=settings.twitter_password,
            email=settings.twitter_email,
            email_password=settings.twitter_email_password or "",
            cookies=settings.twitter_cookies or None,
        )

        # When cookies are provided, the account is already active — login_all is a no-op.
        # When only password is set, login_all performs the login flow (may be Cloudflare-blocked).
        await api.pool.login_all()

        _api = api
        return _api


async def _extract_via_twscrape(tweet_id: str, url: str) -> tuple[str, str]:
    """Fetch thread using twscrape (requires credentials in .env)."""
    api = await _get_api()

    tweet = await api.tweet_detail(int(tweet_id))
    if tweet is None:
        raise ValueError(f"Tweet not found or account is protected: {url}")

    conversation_id = tweet.conversationId
    author_username = tweet.user.username

    query = f"conversation_id:{conversation_id} from:{author_username}"
    thread_tweets = []
    async for t in api.search(query):
        thread_tweets.append(t)

    if not thread_tweets:
        thread_tweets = [tweet]

    thread_tweets.sort(key=lambda t: t.date)

    first_text = thread_tweets[0].rawContent or ""
    snippet = first_text[:80] + ("..." if len(first_text) > 80 else "")
    title = f"Thread by @{author_username}: {snippet}"

    parts = [
        f"Tweet {i}:\n{t.rawContent or ''}"
        for i, t in enumerate(thread_tweets, start=1)
    ]
    text = "\n\n---\n\n".join(parts)

    return title, text


def _extract_via_threadreaderapp(tweet_id: str) -> tuple[str, str]:
    """
    Fallback: fetch an unrolled thread from ThreadReaderApp (no auth needed).
    Raises if the thread hasn't been unrolled yet.
    """
    url = f"https://threadreaderapp.com/thread/{tweet_id}"
    response = requests.get(url, headers=_HEADERS, timeout=15)
    response.raise_for_status()

    from readability import Document
    doc = Document(response.text)
    title = doc.title() or f"Twitter Thread {tweet_id}"
    html = doc.summary()
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) < 100:
        raise ValueError(
            f"Thread {tweet_id} not found on ThreadReaderApp. "
            "The thread may not have been unrolled yet — try submitting the URL "
            "to threadreaderapp.com first, or configure TWITTER_COOKIES in .env."
        )

    return title, text


async def extract_thread(url: str) -> tuple[str, str]:
    """
    Extract a Twitter/X thread. Tries twscrape first, falls back to ThreadReaderApp.

    Returns (title, text). Raises only if both methods fail.
    """
    from app.config import settings

    tweet_id = _extract_tweet_id(url)

    if settings.twitter_username:
        try:
            return await _extract_via_twscrape(tweet_id, url)
        except Exception as e:
            print(f"[INFO] twscrape failed for tweet {tweet_id}: {e} — trying ThreadReaderApp")

    return _extract_via_threadreaderapp(tweet_id)
