"""Inspect license wikitext and a few open-access endpoints."""
import json
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def commons_wikitext(title):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "format": "json", "page": title, "prop": "wikitext"}
    )
    data = json.loads(fetch(url))
    text = data["parse"]["wikitext"]["*"]
    print("=" * 70)
    print(title)
    # print license-related lines only
    for line in text.splitlines():
        low = line.lower()
        if any(
            k in low
            for k in (
                "license",
                "pd-",
                "cc0",
                "cc-",
                "permission",
                "copyright",
                "{{pd",
                "{{cc",
                "source",
                "date",
                "author",
            )
        ):
            print(line[:300])
    print()


FILES = [
    "File:Apple 1 computer.jpg",
    "File:1985 Air Jordan 1s.jpg",
    "File:Fender Stratocaster 004-2.jpg",
    "File:Fender Stratocaster 004.JPG",
    "File:2014-365-233 The Basic Brownie Camera (14809795240).jpg",
    "File:Steve Jobs and Macintosh computer, January 1984, by Bernard Gotfryd - edited.jpg",
]

if __name__ == "__main__":
    for i, title in enumerate(FILES):
        if i:
            time.sleep(1.5)
        try:
            commons_wikitext(title)
        except Exception as e:
            print("ERR", title, type(e).__name__, e)
