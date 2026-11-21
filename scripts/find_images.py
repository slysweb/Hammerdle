"""Find Wikimedia Commons files that are CC0 or public domain."""
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def commons(q, n=8):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "generator": "search",
            "gsrsearch": q,
            "gsrnamespace": "6",
            "gsrlimit": str(n),
            "iiprop": "url|extmetadata|size",
            "iiurlwidth": "10",
        }
    )
    data = get(url)
    pages = (data.get("query") or {}).get("pages") or {}
    print("QUERY", q)
    rows = []
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}

        def g(k):
            v = meta.get(k) or {}
            return (v.get("value") if isinstance(v, dict) else "") or ""

        lic = g("LicenseShortName")
        title = p.get("title") or ""
        ok = ("CC0" in lic) or (lic.strip().lower() == "public domain")
        mark = "*" if ok else " "
        print(f" {mark} {lic} | {title[:150]}")
        if ok:
            rows.append({"title": title, "license": lic, "usage": g("UsageTerms")})
    print()
    return rows


QUERIES = [
    'incategory:CC0 Apple computer',
    'incategory:CC0 Brownie camera',
    'incategory:CC0 Stratocaster',
    'incategory:CC0 Model T',
    'incategory:CC0 Walkman',
    'incategory:CC0 iPhone',
    'incategory:CC0 Mustang',
    'incategory:CC0 Barbie doll',
    'incategory:CC0 Monopoly',
    'incategory:CC0 Rubik',
    'incategory:CC0 Polaroid',
    'incategory:CC0 Zippo',
    'incategory:CC0 Coca-Cola',
    'incategory:CC0 Les Paul',
    'incategory:CC0 calculator',
    'incategory:CC0 typewriter',
    'incategory:CC0 telephone',
    'incategory:CC0 sewing machine',
    'incategory:CC0 sneaker',
    'incategory:CC0 Game Boy',
    'incategory:CC0 Atari',
    'incategory:CC0 Macintosh',
    'incategory:CC0 Commodore',
    'incategory:CC0 violin',
    'incategory:CC0 Rolex',
    'incategory:CC0 Leica',
    'incategory:CC0 Hamilton watch',
    'incategory:CC0 Ford',
    'incategory:CC0 bicycle',
    'incategory:CC0 radio',
]

if __name__ == "__main__":
    for q in QUERIES:
        try:
            commons(q)
        except Exception as e:
            print("ERR", q, type(e).__name__, e)
