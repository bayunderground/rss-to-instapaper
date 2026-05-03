from __future__ import annotations

import logging
import os

from flask import Flask, abort, jsonify, request

from job import run_job

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

_ON_APP_ENGINE = bool(os.environ.get("GAE_APPLICATION"))


@app.get("/tasks/fetch")
@app.post("/tasks/fetch")
def tasks_fetch():
    if _ON_APP_ENGINE and request.headers.get("X-Appengine-Cron") != "true":
        abort(403)

    result = run_job()
    return jsonify(result), 200


@app.get("/")
def healthcheck():
    return {"ok": True}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)