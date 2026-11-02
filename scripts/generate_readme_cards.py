"""Generate the SVG cards embedded in README.md."""

from __future__ import annotations

import html
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
BAR_WIDTH = 260
LANGUAGE_COLORS = (
    "#ef4444",
    "#f59e0b",
    "#10b981",
    "#3b82f6",
    "#8b5cf6",
    "#ec4899",
)


def github_get(url: str, token: str) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "readme-card-generator",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"GitHub API request failed for {url}: {error}") from error


def get_repositories(username: str, token: str) -> list[dict[str, Any]]:
    repositories: list[dict[str, Any]] = []
    page = 1
    while True:
        result = github_get(
            f"{API_URL}/users/{username}/repos?per_page=100&page={page}", token
        )
        if not isinstance(result, list):
            raise RuntimeError("GitHub API returned an invalid repository list")
        repositories.extend(result)
        if len(result) < 100:
            return repositories
        page += 1


def language_totals(
    repositories: list[dict[str, Any]], token: str
) -> Counter[str]:
    totals: Counter[str] = Counter()
    for repository in repositories:
        if repository.get("fork") or repository.get("archived"):
            continue
        languages_url = repository.get("languages_url")
        if not isinstance(languages_url, str):
            continue
        languages = github_get(languages_url, token)
        if not isinstance(languages, dict):
            raise RuntimeError("GitHub API returned invalid language data")
        for language, bytes_count in languages.items():
            if isinstance(language, str) and isinstance(bytes_count, int):
                totals[language] += bytes_count
    return totals


def xml_text(value: object) -> str:
    return html.escape(str(value), quote=True)


def stats_svg(username: str, user: dict[str, Any], repositories: list[dict[str, Any]]) -> str:
    stars = sum(
        repository.get("stargazers_count", 0)
        for repository in repositories
        if isinstance(repository.get("stargazers_count"), int)
    )
    values = (
        ("Total Stars", stars),
        ("Public Repos", user.get("public_repos", 0)),
        ("Followers", user.get("followers", 0)),
        ("Following", user.get("following", 0)),
    )
    lines = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='520' height='190'>",
        "<defs>",
        "<style>",
        ".title{font:600 18px 'Segoe UI', Arial, sans-serif;fill:#1f2a44}",
        ".label{font:500 14px 'Segoe UI', Arial, sans-serif;fill:#334155}",
        ".value{font:600 14px 'Segoe UI', Arial, sans-serif;fill:#0f172a}",
        "</style>",
        "</defs>",
        "<rect x='0' y='0' width='520' height='190' rx='14' fill='#f7f9fc' stroke='#d8dee9'/>",
        f"<text x='22' y='40' class='title'>{xml_text(username)} - Stats</text>",
    ]
    for index, (label, value) in enumerate(values):
        y = 62 + index * 28
        lines.extend(
            (
                f"<text x='22' y='{y}' class='label'>{label}</text>",
                f"<text x='498' y='{y}' text-anchor='end' class='value'>{xml_text(value)}</text>",
            )
        )
    lines.extend(("</svg>", ""))
    return "\n".join(lines)


def languages_svg(totals: Counter[str]) -> str:
    top_languages = totals.most_common(6)
    total_bytes = sum(totals.values()) or 1
    lines = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='520' height='240'>",
        "<defs>",
        "<style>",
        ".title{font:600 18px 'Segoe UI', Arial, sans-serif;fill:#1f2a44}",
        ".label{font:500 13px 'Segoe UI', Arial, sans-serif;fill:#334155}",
        ".percent{font:600 12px 'Segoe UI', Arial, sans-serif;fill:#0f172a}",
        "</style>",
        "</defs>",
        "<rect x='0' y='0' width='520' height='240' rx='14' fill='#f7f9fc' stroke='#d8dee9'/>",
        "<text x='22' y='40' class='title'>Top Languages</text>",
    ]
    for index, (language, bytes_count) in enumerate(top_languages):
        percentage = bytes_count / total_bytes * 100
        y = 62 + index * 26
        bar_width = round(BAR_WIDTH * percentage / 100)
        lines.extend(
            (
                f"<text x='22' y='{y}' class='label'>{xml_text(language)}</text>",
                f"<rect x='172' y='{y - 12}' width='260' height='10' rx='5' fill='#e5e7eb'/>",
                f"<rect x='172' y='{y - 12}' width='{bar_width}' height='10' rx='5' fill='{LANGUAGE_COLORS[index]}'/>",
                f"<text x='440' y='{y - 3}' class='percent'>{percentage:.1f}%</text>",
            )
        )
    lines.extend(("</svg>", ""))
    return "\n".join(lines)


def main() -> None:
    username = os.environ.get("GITHUB_USERNAME")
    token = os.environ.get("GITHUB_TOKEN")
    if not username:
        raise RuntimeError("GITHUB_USERNAME is required")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")

    user = github_get(f"{API_URL}/users/{username}", token)
    if not isinstance(user, dict):
        raise RuntimeError("GitHub API returned invalid user data")
    repositories = get_repositories(username, token)
    totals = language_totals(repositories, token)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "readme-stats.svg").write_text(
        stats_svg(username, user, repositories), encoding="utf-8"
    )
    (ASSETS_DIR / "readme-langs.svg").write_text(
        languages_svg(totals), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
