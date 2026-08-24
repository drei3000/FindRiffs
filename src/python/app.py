"""Flask entrypoint. Parses the request, hands off, streams the result.

Run locally with `python app.py`; in prod this module exposes `app` for
Gunicorn.
"""

import requests
from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS
from discovery import nicheness_plan
from lastfm import fetch_lastfm_page
from tracks import stream_tracks

app = Flask(__name__)
CORS(app, origins=["https://findriffs.andreicalota0305.workers.dev"])

@app.route("/api/tracks")
def search():
    tag = request.args.get("tag")
    if not tag:
        return jsonify({"error": "tag is required"}), 400

    nicheness = request.args.get("nicheness", default=0.0, type=float)
    limit = request.args.get("limit", default=50, type=int)
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
