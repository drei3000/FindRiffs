"""The nicheness algorithm: how far from the tag chart we wander, and which
of the results survive.

Pure logic over track dicts — no Flask, no streaming, no Songsterr.
"""

import random
from concurrent.futures import ThreadPoolExecutor

from config import BRANCH_SEEDS, MAX_WORKERS, SEED_ANCHORS
from lastfm import similar_tracks


def key(artist: str, title: str):
    return (artist.strip().lower(), title.strip().lower())


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

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
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
