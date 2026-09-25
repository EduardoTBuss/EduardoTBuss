"""Talk to the GitHub REST API and write the refreshed snapshot to data/github.json.

Isolated from rendering on purpose: swapping the data source (a different
API, GraphQL, a cache) means editing only this file.

Security note: requests are sent with `Authorization: Bearer <GITHUB_TOKEN>`
when the token is available in the environment, raising the rate limit from
60 to 5000 requests/hour. The workflow already has GITHUB_TOKEN for free
(no new secret); locally, without a token, the client degrades to
unauthenticated calls and prints a warning instead of failing silently.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone

from . import datastore

GITHUB_USERNAME = "EduardoTBuss"
API_BASE = "https://api.github.com"
USER_AGENT = "EduardoTBuss-profile-generator"
REQUEST_TIMEOUT_SECONDS = 20
TOP_LANGUAGES_LIMIT = 6
REPOS_PER_PAGE = 100


def _headers() -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        print(
            "warning: GITHUB_TOKEN not set; calling the GitHub API unauthenticated "
            "(60 requests/hour instead of 5000). Fine locally, risky in CI.",
            file=sys.stderr,
        )
    return headers


def request_json(url: str):
    """GET a URL and parse the JSON body. Raises urllib.error.HTTPError on 4xx/5xx."""
    request = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.load(response)


def refresh_github() -> dict:
    """Fetch the public profile snapshot and persist it to data/github.json."""
    user = request_json(f"{API_BASE}/users/{GITHUB_USERNAME}")
    repos = request_json(
        f"{API_BASE}/users/{GITHUB_USERNAME}/repos?per_page={REPOS_PER_PAGE}&sort=updated"
    )
    owned = [repo for repo in repos if not repo.get("fork")]
    language_counts = Counter(repo.get("language") for repo in owned if repo.get("language"))
    created_at = str(user.get("created_at") or "")
    value = {
        "username": user["login"],
        "public_repos": user["public_repos"],
        "followers": user["followers"],
        "following": user["following"],
        "stars_received": sum(repo.get("stargazers_count", 0) for repo in owned),
        "forks_received": sum(repo.get("forks_count", 0) for repo in owned),
        "top_languages": [
            {"name": name, "repositories": count}
            for name, count in language_counts.most_common(TOP_LANGUAGES_LIMIT)
        ],
        # Free field: /users/<login> already carries created_at, so "Active
        # since <year>" costs nothing extra (see spec 7.3). Commits/contributions
        # would require GraphQL + a mandatory token + a new failure mode in the
        # daily cron -- deliberately not done.
        "account_created_year": int(created_at[:4]) if created_at[:4].isdigit() else None,
        "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    datastore.save_json("github.json", value)
    return value
