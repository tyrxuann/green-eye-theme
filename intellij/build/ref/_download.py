#!/usr/bin/env python3
"""Download reference files from two public GitHub repos into build/ref/."""
import base64
import json
import os
import urllib.request

REF = os.path.dirname(os.path.abspath(__file__))

REPO_A = ("francma", "everforest-jetbrains", "everforest")
REPO_B = ("sergeymakinen", "jetbrains-github-theme", "github")

PATHS_A = [
    "src/pallete_light_soft.env",
    "src/pallete_light_medium.env",
    "src/pallete_light_hard.env",
    "src/pallete_dark_soft.env",
    "src/pallete_dark_medium.env",
    "src/pallete_dark_hard.env",
    "src/theme.xml",
    "src/plugin.xml",
    "src/everforest.theme.json",
    "src/includes/general.xml",
    "src/includes/default.xml",
    "src/includes/console.xml",
    "src/includes/diff.xml",
    "src/includes/python.xml",
    "src/includes/javascript.xml",
    "src/includes/json.xml",
    "src/includes/xml.xml",
    "src/includes/markdown.xml",
]

PATHS_B = ["GitHub 3.icls"]

UA = {"User-Agent": "ref-collector"}


def http_get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def via_api(owner, repo, path):
    """GitHub contents API -> base64 decoded bytes."""
    url = "https://api.github.com/repos/%s/%s/contents/%s" % (
        owner,
        repo,
        urllib.parse.quote(path),
    )
    raw = http_get(url)
    obj = json.loads(raw.decode("utf-8"))
    if obj.get("content") and obj.get("encoding") == "base64":
        return base64.b64decode(obj["content"])
    # Too large for contents API: fall back to git blobs endpoint
    blob = http_get(obj["git_url"])
    bobj = json.loads(blob.decode("utf-8"))
    return base64.b64decode(bobj["content"])


def via_jsdelivr(owner, repo, path):
    return http_get(
        "https://cdn.jsdelivr.net/gh/%s/%s@master/%s"
        % (owner, repo, urllib.parse.quote(path))
    )


def via_raw(owner, repo, path):
    return http_get(
        "https://raw.githubusercontent.com/%s/%s/master/%s"
        % (owner, repo, urllib.parse.quote(path))
    )


import urllib.parse  # noqa: E402  (used above)

saved = []
failed = []

for owner, repo, sub in (REPO_A, REPO_B):
    paths = PATHS_A if sub == "everforest" else PATHS_B
    for p in paths:
        dest = os.path.join(REF, sub, p)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        data = None
        errs = []
        for label, fn in (
            ("api", via_api),
            ("jsdelivr", via_jsdelivr),
            ("raw", via_raw),
        ):
            try:
                data = fn(owner, repo, p)
                if data:
                    break
            except Exception as e:  # noqa: BLE001
                errs.append("%s:%s" % (label, type(e).__name__))
                data = None
        if data is None:
            failed.append((sub + "/" + p, ";".join(errs)))
            print("FAIL %-50s %s" % (sub + "/" + p, ";".join(errs)))
            continue
        with open(dest, "wb") as f:
            f.write(data)
        saved.append((sub + "/" + p, len(data)))
        print("OK   %-50s %7d bytes" % (sub + "/" + p, len(data)))

print("\nSaved %d, failed %d" % (len(saved), len(failed)))
