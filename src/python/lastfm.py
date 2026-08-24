"""Everything that talks to the last.fm API.

Nothing in here knows about nicheness, Songsterr or Flask — it just returns
raw last.fm track dicts.
"""

import requests

from config import (
    LASTFM_API_KEY,
    LASTFM_URL,
    MAX_SEED_PAGE,
    REQUEST_TIMEOUT,
)


def lf(method: str, **params):
    """Thin last.fm GET. Raises on HTTP errors so the route can 502."""
    params.update({"method": method, "api_key": LASTFM_API_KEY, "format": "json"})
    r = requests.get(LASTFM_URL, params=params, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def fetch_lastfm_page(tag: str, plan: dict, limit: int):
    """Blocking, and cheap enough to run before the stream opens so real
    errors can still come back as a 502 instead of mid-stream."""
    params = {"tag": tag, "limit": limit}

    head = lf("tag.gettoptracks", **params)
    pages = min(int(head["tracks"]["@attr"]["totalPages"]), MAX_SEED_PAGE)
    params["page"] = 1 + round(plan["page_frac"] * (pages - 1))

    tracks = lf("tag.gettoptracks", **params)["tracks"]["track"]
    if isinstance(tracks, dict):
        tracks = [tracks]
    return tracks


def similar_tracks(artist: str, title: str, fanout: int, tail_bias: float):
    """Candidates in last.fm track shape, so build_track needs no changes.

    getsimilar is sorted by match descending, so sliding the window toward
    the tail gives looser, less obvious neighbours.
    """
    try:
        items = lf("track.getsimilar", artist=artist, track=title,
                   limit=40, autocorrect=1)["similartracks"]["track"]
    except Exception:
        return []
    if isinstance(items, dict):
        items = [items]
    if not items:
        return []

    start = int(tail_bias * max(0, len(items) - fanout))
    out = []
    for it in items[start:start + fanout]:
        try:
            out.append({
                "name": it["name"],
                "artist": {"name": it["artist"]["name"]},
                "image": it.get("image", []),
                "playcount": int(it.get("playcount") or 0),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return out
