"""Collect CC0 museum records for a short list of titled works."""
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def met_search(q):
    url = (
        "https://collectionapi.metmuseum.org/public/collection/v1.1/search?"
        + urllib.parse.urlencode({"q": q, "hasImages": "true", "limit": "5"})
    )
    data = get(url)
    ids = data.get("objectIDs") or []
    print("SEARCH", q, "total", data.get("total"), "ids", ids[:5])
    for oid in ids[:3]:
        obj = get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
        title = obj.get("title") or ""
        if q.split()[0].lower() not in title.lower() and q.split()[-1].lower() not in title.lower():
            continue
        print(
            " ",
            oid,
            "pd",
            obj.get("isPublicDomain"),
            "year",
            obj.get("accessionYear"),
            "|",
            title[:80],
            "|",
            (obj.get("artistDisplayName") or "")[:32],
            "|",
            (obj.get("objectDate") or "")[:16],
        )
        img = obj.get("primaryImageSmall") or ""
        if img:
            print("   ", img)
    print(flush=True)


def nga_manifest():
    url = "https://www.nga.gov/api/v1/iiif/presentation/manifest.json?cultObj:id=50724"
    try:
        data = get(url, 25)
    except Exception as e:
        print("NGA", type(e).__name__, e)
        return
    text = json.dumps(data)
    print("NGA manifest bytes", len(text))
    # print any jpg/iiif urls
    for token in ("iiif", "jpg", "service", "id"):
        pass
    # walk for image ids
    def walk(node, depth=0):
        if depth > 8:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("id", "@id") and isinstance(v, str) and ("iiif" in v or v.endswith(".jpg")):
                    print(" ", v[:200])
                else:
                    walk(v, depth + 1)
        elif isinstance(node, list):
            for item in node[:30]:
                walk(item, depth + 1)
    walk(data)
    print(flush=True)


if __name__ == "__main__":
    for q in [
        "Juan de Pareja",
        "Wheat Field with Cypresses",
        "Madonna and Child Duccio",
        "The Death of Socrates",
        "Washington Crossing the Delaware",
    ]:
        try:
            met_search(q)
        except Exception as e:
            print("ERR", q, type(e).__name__, e, flush=True)
    nga_manifest()
