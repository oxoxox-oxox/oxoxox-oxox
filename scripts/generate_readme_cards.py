import json
import os
import time
from urllib.request import Request, urlopen

USERNAME = os.environ.get("GITHUB_USERNAME", "oxoxox-oxox")
TOKEN = os.environ.get("GITHUB_TOKEN")

API_BASE = "https://api.github.com"
OUT_STATS = os.path.join("assets", "readme-stats.svg")
OUT_LANGS = os.path.join("assets", "readme-langs.svg")


def request_json(url):
    headers = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_repos(username):
    repos = []
    page = 1
    while True:
        url = f"{API_BASE}/users/{username}/repos?per_page=100&page={page}"
        batch = request_json(url)
        if not batch:
            break
        repos.extend(batch)
        page += 1
        time.sleep(0.2)
    return repos


def aggregate_stats(username):
    user = request_json(f"{API_BASE}/users/{username}")
    repos = fetch_repos(username)

    total_stars = 0
    language_bytes = {}

    for repo in repos:
        if repo.get("fork"):
            continue
        total_stars += int(repo.get("stargazers_count", 0))
        languages_url = repo.get("languages_url")
        if not languages_url:
            continue
        languages = request_json(languages_url)
        for lang, size in languages.items():
            language_bytes[lang] = language_bytes.get(lang, 0) + int(size)
        time.sleep(0.2)

    stats = {
        "name": user.get("login", username),
        "public_repos": int(user.get("public_repos", 0)),
        "followers": int(user.get("followers", 0)),
        "following": int(user.get("following", 0)),
        "stars": total_stars,
    }

    return stats, language_bytes


def format_number(value):
    return f"{value:,}"


def write_stats_svg(stats, path):
    width = 520
    height = 190
    padding = 22

    lines = [
        ("Total Stars", stats["stars"]),
        ("Public Repos", stats["public_repos"]),
        ("Followers", stats["followers"]),
        ("Following", stats["following"]),
    ]

    title = f"{stats['name']} - Stats"

    y_start = padding + 40
    line_gap = 28

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "<defs>",
        "<style>",
        ".title{font:600 18px 'Segoe UI', Arial, sans-serif;fill:#1f2a44}",
        ".label{font:500 14px 'Segoe UI', Arial, sans-serif;fill:#334155}",
        ".value{font:600 14px 'Segoe UI', Arial, sans-serif;fill:#0f172a}",
        "</style>",
        "</defs>",
        f"<rect x='0' y='0' width='{width}' height='{height}' rx='14' fill='#f7f9fc' stroke='#d8dee9'/>",
        f"<text x='{padding}' y='{padding + 18}' class='title'>{title}</text>",
    ]

    for i, (label, value) in enumerate(lines):
        y = y_start + i * line_gap
        parts.append(f"<text x='{padding}' y='{y}' class='label'>{label}</text>")
        parts.append(
            f"<text x='{width - padding}' y='{y}' text-anchor='end' class='value'>{format_number(value)}</text>"
        )

    parts.append("</svg>")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def write_langs_svg(language_bytes, path):
    width = 520
    padding = 22
    bar_width = 260
    top_n = 6

    items = sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)[:top_n]
    total = sum(size for _, size in items) or 1

    height = 40 + padding * 2 + len(items) * 26
    title = "Top Languages"

    colors = [
        "#ef4444",
        "#f59e0b",
        "#10b981",
        "#3b82f6",
        "#8b5cf6",
        "#ec4899",
    ]

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "<defs>",
        "<style>",
        ".title{font:600 18px 'Segoe UI', Arial, sans-serif;fill:#1f2a44}",
        ".label{font:500 13px 'Segoe UI', Arial, sans-serif;fill:#334155}",
        ".percent{font:600 12px 'Segoe UI', Arial, sans-serif;fill:#0f172a}",
        "</style>",
        "</defs>",
        f"<rect x='0' y='0' width='{width}' height='{height}' rx='14' fill='#f7f9fc' stroke='#d8dee9'/>",
        f"<text x='{padding}' y='{padding + 18}' class='title'>{title}</text>",
    ]

    y = padding + 40
    for idx, (lang, size) in enumerate(items):
        percent = size / total
        bar_len = int(bar_width * percent)
        color = colors[idx % len(colors)]

        parts.append(f"<text x='{padding}' y='{y}' class='label'>{lang}</text>")
        parts.append(
            f"<rect x='{padding + 150}' y='{y - 12}' width='{bar_width}' height='10' rx='5' fill='#e5e7eb'/>"
        )
        parts.append(
            f"<rect x='{padding + 150}' y='{y - 12}' width='{bar_len}' height='10' rx='5' fill='{color}'/>"
        )
        parts.append(
            f"<text x='{padding + 150 + bar_width + 8}' y='{y - 3}' class='percent'>{percent * 100:.1f}%</text>"
        )
        y += 26

    parts.append("</svg>")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def main():
    stats, language_bytes = aggregate_stats(USERNAME)
    write_stats_svg(stats, OUT_STATS)
    write_langs_svg(language_bytes, OUT_LANGS)


if __name__ == "__main__":
    main()
