import json
import re
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


html = get("https://www.nga.gov/artworks/1231-marchesa-elena-grimaldi-cattaneo").decode("utf-8", "replace")
urls = sorted(set(re.findall(r"https://[^\s\"']+\.(?:jpg|jpeg|png)", html, re.I)))
print("page urls", len(urls))
for u in urls[:40]:
    print(u)

candidates = [
    "https://media.nga.gov/public/objects/1/2/3/1/1231-primary-0-nativeres.ptif/full/800,/0/default.jpg",
    "https://media.nga.gov/public/objects/1/2/3/1/1231-primary-0-nativeres.jpg",
    "https://api.nga.gov/v1/artworks/1231",
]
for u in candidates:
    try:
        d = get(u)
        print("OK", u[:100], len(d), d[:30])
    except Exception as e:
        print("FAIL", u[:100], e)
