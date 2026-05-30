"""
Trend scraper — fetches trending content from HN, Reddit, ArXiv, Papers With Code,
BioRxiv, Bluesky, Lobste.rs, and X (optional).

Each source is isolated so a single failure doesn't break the rest.
Returns normalised dicts: { title, url, score, source }.
"""

import os
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import httpx

_REDDIT_UA = {"User-Agent": "AmphoraMarketingBot/1.0 (research; contact shaunak@amphorabrain.com)"}
_TIMEOUT = 20


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
# HuggingFace Daily Papers (curated trending AI papers, sorted by upvotes)
# ---------------------------------------------------------------------------

def fetch_hf_daily_papers(n: int = 15) -> list[dict]:
    try:
        r = httpx.get(
            "https://huggingface.co/api/daily_papers",
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        papers = sorted(r.json(), key=lambda p: p.get("paper", {}).get("upvotes", 0), reverse=True)
        return [
            {
                "title":  p.get("title", ""),
                "url":    f"https://huggingface.co/papers/{p.get('paper', {}).get('id', '')}",
                "score":  p.get("paper", {}).get("upvotes", 0),
                "source": "HuggingFace Papers",
            }
            for p in papers[:n]
            if p.get("title")
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# BioRxiv (free API — neuroscience preprints from the past week)
# ---------------------------------------------------------------------------

def fetch_biorxiv_neuro(n: int = 10) -> list[dict]:
    end   = date.today()
    start = end - timedelta(days=7)
    try:
        r = httpx.get(
            f"https://api.biorxiv.org/details/biorxiv/{start}/{end}/0/json",
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        r.raise_for_status()
        papers = r.json().get("collection", [])
        neuro  = [p for p in papers if "neuro" in p.get("category", "").lower()]
        return [
            {
                "title":  p.get("title", ""),
                "url":    f"https://www.biorxiv.org/content/{p.get('doi')}",
                "score":  0,
                "source": "BioRxiv",
            }
            for p in neuro[:n]
            if p.get("title")
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Bluesky (AT Protocol public search — no auth required)
# ---------------------------------------------------------------------------

_BSKY_QUERY = "AI OR LLM OR neuroscience OR fMRI OR \"language model\" OR \"brain computer interface\""

def fetch_bluesky_ai(n: int = 20) -> list[dict]:
    try:
        r = httpx.get(
            "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",
            params={"q": _BSKY_QUERY, "limit": min(n, 25), "sort": "top"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        out = []
        for p in r.json().get("posts", []):
            text   = p.get("record", {}).get("text", "")
            handle = p.get("author", {}).get("handle", "")
            uri    = p.get("uri", "")
            rkey   = uri.split("/")[-1] if uri else ""
            if not text:
                continue
            out.append({
                "title":  text[:220],
                "url":    f"https://bsky.app/profile/{handle}/post/{rkey}" if handle and rkey else "",
                "score":  p.get("likeCount", 0),
                "source": "Bluesky",
            })
        return out
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Lobste.rs (free JSON API — curated tech community)
# ---------------------------------------------------------------------------

def fetch_lobsters_hot(n: int = 15) -> list[dict]:
    try:
        r = httpx.get(
            "https://lobste.rs/hottest.json",
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        r.raise_for_status()
        return [
            {
                "title":    s.get("title", ""),
                "url":      s.get("url") or s.get("short_id_url", ""),
                "score":    s.get("score", 0),
                "comments": s.get("comment_count", 0),
                "source":   "Lobste.rs",
            }
            for s in r.json()[:n]
            if s.get("title")
        ]
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
    Fetch from all sources. Each has its own timeout so a single slow source
    doesn't block the rest. Returns per-source lists and a sources_used list.
    """
    hn       = fetch_hn_top(25)
    ml       = fetch_reddit_hot("MachineLearning", 15)
    llm      = fetch_reddit_hot("LocalLLaMA", 12)
    ai_sub   = fetch_reddit_hot("artificial", 10)
    arxiv    = fetch_arxiv_recent(15)
    hf       = fetch_hf_daily_papers(15)
    biorxiv  = fetch_biorxiv_neuro(10)
    bluesky  = fetch_bluesky_ai(20)
    lobsters = fetch_lobsters_hot(15)
    twitter  = fetch_twitter_ai(20)

    sources_used = (
        (["HackerNews"]           if hn       else []) +
        (["r/MachineLearning"]    if ml       else []) +
        (["r/LocalLLaMA"]         if llm      else []) +
        (["r/artificial"]         if ai_sub   else []) +
        (["ArXiv"]                if arxiv    else []) +
        (["HuggingFace Papers"]   if hf       else []) +
        (["BioRxiv"]              if biorxiv  else []) +
        (["Bluesky"]              if bluesky  else []) +
        (["Lobste.rs"]            if lobsters else []) +
        (["X (Twitter)"]          if twitter  else [])
    )

    return {
        "hn":           hn,
        "reddit":       ml + llm + ai_sub,
        "arxiv":        arxiv,
        "hf":           hf,
        "biorxiv":      biorxiv,
        "bluesky":      bluesky,
        "lobsters":     lobsters,
        "twitter":      twitter,
        "sources_used": sources_used,
    }
