"""Fetch Met object records and Cleveland image fields."""
import json
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


IDS = [437394, 430781, 652755, 436535, 437397, 459123, 436532, 436528, 436524, 437998]


def main():
    for oid in IDS:
        try:
            obj = get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
        except Exception as e:
            print(oid, type(e).__name__, e)
            continue
        print(
            oid,
            "pd",
            obj.get("isPublicDomain"),
            "|",
            (obj.get("title") or "")[:75],
            "|",
            (obj.get("artistDisplayName") or "")[:28],
            "|",
            (obj.get("objectDate") or "")[:18],
        )
        img = obj.get("primaryImageSmall") or obj.get("primaryImage") or ""
        if img:
            print("  IMG", img[:160])
        print()

    c = get("https://openaccess-api.clevelandart.org/api/artworks/135382")
    data = c.get("data") or {}
    print("CLEVELAND KEYS", sorted(data.keys())[:40])
    for k in ("title", "creators", "images", "share_license_status", "url", "creation_date"):
        val = data.get(k)
        text = json.dumps(val, ensure_ascii=False)
        print(k, text[:400])


if __name__ == "__main__":
    main()
