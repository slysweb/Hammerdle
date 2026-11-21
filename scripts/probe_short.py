"""Resolve a few known CC0 object records. Short timeouts."""
import json
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def try_url(label, url, timeout=20):
    print("==", label)
    try:
        raw = fetch(url, timeout)
        print("bytes", len(raw), "head", raw[:180].decode("utf-8", "replace").replace("\n", " "))
    except Exception as e:
        print(type(e).__name__, e)
    print()


if __name__ == "__main__":
    try_url(
        "met-v11",
        "https://collectionapi.metmuseum.org/public/collection/v1.1/search?q=Aristotle&hasImages=true&limit=3",
        15,
    )
    try_url(
        "cleveland-one",
        "https://openaccess-api.clevelandart.org/api/artworks/135382",
        20,
    )
    try_url(
        "nga-page",
        "https://www.nga.gov/artworks/50724-ginevra-de-benci-obverse",
        20,
    )
