import os

from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------ last.fm

LASTFM_API_KEY = os.getenv("LAST_FM_API_KEY")
LASTFM_API_SECRET = os.getenv("LAST_FM_SECRET")
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"

# ------------------------------------------------------------------ tunables

SEED_ANCHORS = 15      # how many tag-page tracks we branch from
BRANCH_SEEDS = 12      # how many hop-1 results we branch from again
MAX_SEED_PAGE = 20     # deep tag pages come back thin/empty, so cap it

MAX_WORKERS = 8        # shared by the getsimilar and Songsterr pools
REQUEST_TIMEOUT = 10   # seconds, per outbound HTTP call
