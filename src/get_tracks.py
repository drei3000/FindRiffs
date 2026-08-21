import os
import json
import random
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, stream_with_context

from songsterr import get_songsterr_data

load_dotenv()

API_KEY = os.getenv("LAST_FM_API_KEY")
API_SECRET = os.getenv("LAST_FM_SECRET")
LASTFM = "https://ws.audioscrobbler.com/2.0/"

SEED_ANCHORS = 15      # how many tag-page tracks we branch from
BRANCH_SEEDS = 12      # how many hop-1 results we branch from again
MAX_SEED_PAGE = 20     # deep tag pages come back thin/empty, so cap it


def normalise_tuning(value) -> str:
    """'E A D G B E' or ['E','A','D','G','B','E'] -> 'EADGBE'."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = "".join(str(v) for v in value)
    return "".join(str(value).split()).upper()


def lf(method: str, **params):
    """Thin last.fm GET. Raises on HTTP errors so the route can 502."""
    params.update({"method": method, "api_key": API_KEY, "format": "json"})
    r = requests.get(LASTFM, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def key(artist: str, title: str):
    return (artist.strip().lower(), title.strip().lower())


# ---------------------------------------------------------------- nicheness

def nicheness_plan(n: float) -> dict:
    """One 0-100 dial, several levers.

    page_frac   how deep into the tag chart the seeds come from
    hops        how many getsimilar expansions to run (0 = today's behaviour)
    fanout      how many similar tracks to take per seed
    tail_bias   0 = closest matches, 1 = loosest adjacency
    per_artist  cap on tracks from any one artist, kills repetition
    """
    n = max(0.0, min(100.0, n))
    return {
        "n": n,
        "page_frac": min(n / 100, 0.5),
        "hops": 0 if n < 25 else (1 if n < 65 else 2),
        "fanout": 3 + round(n / 100 * 7),
        "tail_bias": n / 100,
        "per_artist": max(1, 3 - round(n / 50)),
    }


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


def harvest(seeds, plan):
    """Expand seeds outward via getsimilar.

    Seeds are anchors only, they never make it into the pool themselves.
    That matters because tag.gettoptracks has no playcount field, while
    getsimilar does, so everything here can be ranked by popularity.
    """
    pool, seen = {}, set()
    frontier = []

    for s in seeds:
        try:
            a, t = s["artist"]["name"], s["name"]
        except (KeyError, TypeError):
            continue
        seen.add(key(a, t))
        frontier.append((a, t))

    random.shuffle(frontier)
    frontier = frontier[:SEED_ANCHORS]

    for hop in range(plan["hops"]):
        if not frontier:
            break
        fanout = plan["fanout"] if hop == 0 else max(2, plan["fanout"] // 2)

        with ThreadPoolExecutor(max_workers=8) as ex:
            batches = list(ex.map(
                lambda p: similar_tracks(p[0], p[1], fanout, plan["tail_bias"]),
                frontier))

        nxt = []
        for batch in batches:
            for c in batch:
                k = key(c["artist"]["name"], c["name"])
                if k in seen:
                    continue
                seen.add(k)
                pool[k] = c
                nxt.append((c["artist"]["name"], c["name"]))

        random.shuffle(nxt)
        frontier = nxt[:BRANCH_SEEDS]

    return list(pool.values())


def select_by_playcount(pool, plan, limit):
    """Slide a window down the popularity distribution, then cap per artist.

    Relative position beats an absolute playcount ceiling, since what counts
    as niche is completely different between, say, deathcore and emo.
    """
    if not pool:
        return []

    pool = sorted(pool, key=lambda c: c["playcount"], reverse=True)

    if len(pool) > limit:
        span = max(limit, int(len(pool) * 0.4))
        start = int((plan["n"] / 100) * (len(pool) - span))
        pool = pool[start:start + span]

    counts, out = {}, []
    for c in pool:
        a = c["artist"]["name"].strip().lower()
        if counts.get(a, 0) >= plan["per_artist"]:
            continue
        counts[a] = counts.get(a, 0) + 1
        out.append(c)
        if len(out) >= limit:
            break
    return out


# ------------------------------------------------------------------ streaming

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

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(build_track, t) for t in raw_tracks]

        for future in futures:
            try:
                track = future.result()
            except Exception:
                continue

            sent += 1
            yield json.dumps(track) + "\n"

    yield json.dumps({"type": "done", "sent": sent}) + "\n"


app = Flask(__name__)


@app.route("/api/tracks")
def search():
    tag = request.args.get("tag")
    if not tag:
        return jsonify({"error": "tag is required"}), 400

    nicheness = request.args.get("nicheness", default=0.0, type=float)
    limit = request.args.get("limit", default=100, type=int)
    plan = nicheness_plan(nicheness)

    try:
        raw = fetch_lastfm_page(tag, plan, limit)
    except (KeyError, ValueError, requests.RequestException) as e:
        return jsonify({"error": f"last.fm request failed: {e}"}), 502

    return Response(
        stream_with_context(stream_tracks(raw, plan, limit)),
        mimetype="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # stops nginx buffering in prod
        },
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)