"""Turns raw last.fm dicts into the payloads the frontend consumes, and
yields them as NDJSON.

This is the only module that knows the wire format, so if the client
contract changes it changes here.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

from config import MAX_WORKERS
from discovery import harvest, select_by_playcount
from songsterr import get_songsterr_data


def normalise_tuning(value) -> str:
    """'E A D G B E' or ['E','A','D','G','B','E'] -> 'EADGBE'."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = "".join(str(v) for v in value)
    return "".join(str(value).split()).upper()


def build_track(t: dict) -> dict:
    artist, title = t["artist"]["name"], t["name"]

    tuning = None
    try:
        data = get_songsterr_data(f"{artist} - {title}")
        if data:
            tuning = data.get("tuning")
    except Exception:
        # No tab on Songsterr, or the lookup failed. Track still streams,
        # it just won't survive a tuning filter.
        tuning = None

    q = quote_plus(f"{artist} {title}")
    images = {i["size"]: i["#text"] for i in t.get("image", [])}

    return {
        "type": "track",
        "artist": artist,
        "title": title,
        "youtube": "https://www.youtube.com/results?search_query=" + q,
        "spotify": "https://open.spotify.com/search/" + q,
        "songsterr": ("https://www.songsterr.com/a/wa/bestMatchForQueryString"
                      f"?s={quote_plus(title)}&a={quote_plus(artist)}"),
        "cover": images.get("extralarge") or images.get("large") or None,
        "tuning": normalise_tuning(tuning) or None,
    }


def stream_tracks(raw_tracks, plan, limit):
    """Yields one JSON object per line (NDJSON).

    Branching happens inside the generator, not before it, so the client
    isn't staring at a blank page while getsimilar runs. Songsterr lookups
    then run 8 at a time, yielded in submission order to keep the ranking.
    """
    if plan["hops"]:
        pool = harvest(raw_tracks, plan)
        yield json.dumps({"type": "status", "stage": "branching",
                          "pool": len(pool)}) + "\n"
        selected = select_by_playcount(pool, plan, limit)
        if selected:
            raw_tracks = selected

    sent = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(build_track, t) for t in raw_tracks]

        for future in futures:
            try:
                track = future.result()
            except Exception:
                continue

            sent += 1
            yield json.dumps(track) + "\n"

    yield json.dumps({"type": "done", "sent": sent}) + "\n"
