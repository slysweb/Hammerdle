"""Look up CC0 / public-domain images and verify a few museum endpoints."""
import json
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def commons_file(title):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "titles": title,
            "iiprop": "url|extmetadata|mime|size",
            "iiurlwidth": "1200",
        }
    )
    data = get(url)
    page = next(iter((data.get("query") or {}).get("pages", {}).values()))
    if "missing" in page:
        print("MISSING", title)
        return
    ii = (page.get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata") or {}

    def g(k):
        v = meta.get(k) or {}
        return (v.get("value") if isinstance(v, dict) else "") or ""

    print("FILE", title)
    print("  license:", g("LicenseShortName"), "|", g("UsageTerms"), "| copyrighted:", g("Copyrighted"))
    print("  mime:", ii.get("mime"), "size:", ii.get("size"), "thumb:", (ii.get("thumburl") or "")[:140])
    credit = g("Credit").replace("\n", " ")
    print("  credit:", credit[:240])
    print()


FILES = [
    "File:Apple 1 computer.jpg",
    "File:1985 Air Jordan 1s.jpg",
    "File:2014-365-233 The Basic Brownie Camera (14809795240).jpg",
    "File:Fender Stratocaster 004-2.jpg",
    "File:Macintosh 128K - CPU only.svg",
    "File:Steve Jobs and Macintosh computer, January 1984, by Bernard Gotfryd - edited.jpg",
]

if __name__ == "__main__":
    for i, title in enumerate(FILES):
        if i:
            time.sleep(2)
        try:
            commons_file(title)
        except Exception as e:
            print("ERR", title, type(e).__name__, e)
