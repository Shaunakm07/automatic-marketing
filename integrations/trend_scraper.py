"""
Trend scraper — fetches trending content from HN, Reddit, ArXiv, and X (optional).

Each source is isolated so a single failure doesn't break the rest.
Returns normalised dicts: { title, url, score, source }.
"""

import os
import xml.etree.ElementTree as ET
from typing import Optional

import httpx

_REDDIT_UA = {"User-Agent": "AmphoraMarketingBot/1.0 (research; contact shaunak@amphorabrain.com)"}
_TIMEOUT = 12


# ---------------------------------------------------------------------------
# Hacker News (Algolia API — free, no auth)
# ---------------------------------------------------------------------------

def fetch_hn_top(n: int = 25) -> list[dict]:
    try:
        r = httpx.get(
            "https://hn.algolia.com/api/v1/search",
            params={"tags": "front_page", "hitsPerPage": n},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        return [
            {
                "title":    h.get("title", ""),
                "url":      h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                "score":    h.get("points", 0),
                "comments": h.get("num_comments", 0),
                "source":   "HackerNews",
            }
            for h in r.json().get("hits", [])
            if h.get("title")
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Reddit public JSON API (no auth needed for read-only hot/top)
# ---------------------------------------------------------------------------

def fetch_reddit_hot(subreddit: str, n: int = 15) -> list[dict]:
    try:
        r = httpx.get(
            f"https://www.reddit.com/r/{subreddit}/hot.json",
            params={"limit": n},
            headers=_REDDIT_UA,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        r.raise_for_status()
        return [
            {
                "title":    p["data"]["title"],
                "url":      p["data"].get("url", ""),
                "score":    p["data"]["score"],
                "comments": p["data"]["num_comments"],
                "source":   f"r/{subreddit}",
            }
            for p in r.json().get("data", {}).get("children", [])
            if not p["data"].get("stickied") and p["data"].get("title")
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# ArXiv Atom API (free, no auth)
# ---------------------------------------------------------------------------

_ARXIV_QUERY = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:q-bio.NC"

def fetch_arxiv_recent(n: int = 15) -> list[dict]:
    try:
        r = httpx.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": _ARXIV_QUERY,
                "sortBy":       "submittedDate",
                "sortOrder":    "descending",
                "max_results":  n,
            },
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        r.raise_for_status()
        ns   = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(r.text)
        out  = []
        for entry in root.findall("atom:entry", ns):
            title   = entry.find("atom:title",   ns)
            summary = entry.find("atom:summary", ns)
            link    = entry.find("atom:id",      ns)
            out.append({
                "title":   title.text.strip().replace("\n", " ") if title   is not None else "",
                "url":     link.text.strip()                     if link    is not None else "",
                "summary": (summary.text or "").strip()[:280]    if summary is not None else "",
                "source":  "ArXiv",
                "score":   0,
            })
        return [o for o in out if o["title"]]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# X / Twitter API v2 (optional — requires X_BEARER_TOKEN in env)
# ---------------------------------------------------------------------------

_X_QUERY = (
    "(AI OR LLM OR 'language model' OR neuroscience OR fMRI OR 'brain AI') "
    "lang:en -is:retweet -is:reply"
)

def fetch_twitter_ai(n: int = 20) -> list[dict]:
    bearer = os.getenv("X_BEARER_TOKEN", "")
    if not bearer:
        return []
    try:
        r = httpx.get(
            "https://api.twitter.com/2/tweets/search/recent",
            params={
                "query":        _X_QUERY,
                "max_results":  min(n, 100),
                "tweet.fields": "public_metrics,created_at",
                "sort_order":   "relevancy",
            },
            headers={"Authorization": f"Bearer {bearer}"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        return [
            {
                "title":  t["text"][:220],
                "url":    f"https://x.com/i/web/status/{t['id']}",
                "score":  t.get("public_metrics", {}).get("like_count", 0),
                "source": "X (Twitter)",
            }
            for t in r.json().get("data", [])
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

def fetch_all() -> dict:
    """
    Fetch from all sources in parallel (sequential for simplicity; each has its
    own timeout so total wall time is bounded to ~4× _TIMEOUT in the worst case).
    Returns a dict with per-source lists and a sources_used list.
    """
    hn      = fetch_hn_top(25)
    ml      = fetch_reddit_hot("MachineLearning", 15)
    llm     = fetch_reddit_hot("LocalLLaMA", 12)
    ai_sub  = fetch_reddit_hot("artificial", 10)
    arxiv   = fetch_arxiv_recent(15)
    twitter = fetch_twitter_ai(20)

    sources_used = (
        (["HackerNews"]         if hn      else []) +
        (["r/MachineLearning"]  if ml      else []) +
        (["r/LocalLLaMA"]       if llm     else []) +
        (["r/artificial"]       if ai_sub  else []) +
        (["ArXiv"]              if arxiv   else []) +
        (["X (Twitter)"]        if twitter else [])
    )

    return {
        "hn":           hn,
        "reddit":       ml + llm + ai_sub,
        "arxiv":        arxiv,
        "twitter":      twitter,
        "sources_used": sources_used,
    }
