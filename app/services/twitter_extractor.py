"""
Extract Twitter/X threads using twscrape.

Supports twitter.com and x.com URLs. Returns (title, text) matching
the same contract as article_extractor.extract_article().
"""
import asyncio
import re
from typing import Optional

# Module-level singletons — initialized lazily inside the running event loop
_api = None
_lock: Optional[asyncio.Lock] = None


def is_twitter_url(url: str) -> bool:
    """Return True if url is a twitter.com or x.com tweet URL."""
    return bool(re.match(r"https?://(www\.)?(twitter\.com|x\.com)/", url))


def _extract_tweet_id(url: str) -> str:
    """
    Parse the numeric tweet ID from a twitter.com or x.com URL.

    Handles URLs with trailing query strings or fragments, e.g.:
      https://twitter.com/user/status/1234567890
      https://x.com/user/status/1234567890?s=20
    """
    match = re.search(r"/status/(\d+)", url)
    if not match:
        raise ValueError(f"Cannot extract tweet ID from URL: {url}")
    return match.group(1)


async def _get_api():
    """
    Lazily initialize and cache the twscrape API singleton.

    The asyncio.Lock is created on first call (always inside the running
    event loop), which is safe on uvicorn's single-loop model and Python 3.12+.
    """
    global _api, _lock

    # Create the lock on first call, inside the running event loop
    if _lock is None:
        _lock = asyncio.Lock()

    async with _lock:
        if _api is not None:
            return _api

        from app.config import settings

        if not settings.twitter_username or not settings.twitter_password:
            raise ValueError(
                "Twitter credentials not configured. "
                "Set TWITTER_USERNAME, TWITTER_PASSWORD, and TWITTER_EMAIL in .env."
            )

        from twscrape import API

        api = API(settings.twitter_db_path)

        # add_account is idempotent: a no-op if the account already exists in the DB
        await api.pool.add_account(
            username=settings.twitter_username,
            password=settings.twitter_password,
            email=settings.twitter_email,
            email_password=settings.twitter_email_password or "",
        )

        # login_all is a no-op for accounts that already have a valid session
        await api.pool.login_all()

        _api = api
        return _api


async def extract_thread(url: str) -> tuple[str, str]:
    """
    Extract a Twitter/X thread and return (title, text).

    Title: "Thread by @username: {first 80 chars of first tweet}..."
    Text:  tweets joined with "\\n\\n---\\n\\n", each prefixed "Tweet N:"

    For a single tweet (no thread), returns the same format with N=1.
    Raises ValueError if credentials are not configured.
    """
    api = await _get_api()

    tweet_id = _extract_tweet_id(url)
    tweet = await api.tweet_detail(int(tweet_id))

    if tweet is None:
        raise ValueError(f"Tweet not found or account is protected: {url}")

    conversation_id = tweet.conversationId
    author_username = tweet.user.username

    # Collect all tweets from the author in this conversation
    query = f"conversation_id:{conversation_id} from:{author_username}"
    thread_tweets = []
    async for t in api.search(query):
        thread_tweets.append(t)

    # Fall back to just the seed tweet when search returns nothing
    # (single tweet, very recent post not yet indexed, or rate limit)
    if not thread_tweets:
        thread_tweets = [tweet]

    # Sort chronologically
    thread_tweets.sort(key=lambda t: t.date)

    # Build title from first tweet
    first_text = thread_tweets[0].rawContent or ""
    snippet = first_text[:80] + ("..." if len(first_text) > 80 else "")
    title = f"Thread by @{author_username}: {snippet}"

    # Build body
    parts = [
        f"Tweet {i}:\n{t.rawContent or ''}"
        for i, t in enumerate(thread_tweets, start=1)
    ]
    text = "\n\n---\n\n".join(parts)

    return title, text
