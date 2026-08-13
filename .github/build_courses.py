#!/usr/bin/env python3
"""Write courses.json: every public repo in the org that publishes a Pages site.

Run by .github/workflows/courses.yml on push, on a daily schedule, and on
demand. The schedule is the important one — a new course lives in its *own*
repo, so pushing there cannot trigger a build here. The cron picks it up
within a day; hit "Run workflow" if you want it sooner.
"""
import datetime
import json
import os
import urllib.request

ORG = os.environ.get("ORG", "iitm-da")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
SELF = f"{ORG}.github.io"


def api(path):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "course-hub"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def all_repos():
    out, page = [], 1
    while True:
        batch = api(f"/orgs/{ORG}/repos?per_page=100&page={page}&type=public")
        out.extend(batch)
        if len(batch) < 100:
            return out
        page += 1


def main():
    courses = []
    for r in all_repos():
        if r["name"] == SELF or r.get("archived") or r.get("fork"):
            continue
        if not r.get("has_pages"):
            continue          # no site published yet — nothing to link to
        courses.append({
            "name": r["name"],
            "code": r["name"].upper(),
            "description": r.get("description") or "",
            "url": f"/{r['name']}/",
            "repo": r["html_url"],
            "updated": (r.get("pushed_at") or "")[:10],
        })
    courses.sort(key=lambda c: c["name"])

    payload = {
        "org": ORG,
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "courses": courses,
    }
    with open("courses.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    print(f"courses.json: {len(courses)} course sites")
    for c in courses:
        print(f"  {c['name']:<20} {c['description'][:50]}")


if __name__ == "__main__":
    main()
