"""Probe museum open-access APIs for CC0 / public-domain object images."""
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def met(q):
    search = "https://collectionapi.metmuseum.org/public/collection/v1/search?" + urllib.parse.urlencode(
        {"q": q, "hasImages": "true", "isPublicDomain": "true"}
    )
    data = get(search)
    ids = (data.get("objectIDs") or [])[:3]
    print("MET", q, "hits", data.get("total"))
    for i in ids:
        obj = get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}")
        print(
            " ",
            obj.get("objectID"),
            "|",
            obj.get("isPublicDomain"),
            "|",
            (obj.get("title") or "")[:80],
            "|",
            (obj.get("artistDisplayName") or "")[:40],
            "|",
            (obj.get("objectDate") or "")[:20],
        )
    print()


def aic(q):
    url = "https://api.artic.edu/api/v1/artworks/search?" + urllib.parse.urlencode(
        {
            "q": q,
            "limit": "3",
            "fields": "id,title,artist_title,date_display,is_public_domain,image_id",
        }
    )
    data = get(url)
    print("AIC", q, "hits", (data.get("pagination") or {}).get("total"))
    for item in data.get("data") or []:
        if not item.get("is_public_domain") or not item.get("image_id"):
            continue
        print(
            " ",
            item.get("id"),
            "|",
            (item.get("title") or "")[:80],
            "|",
            (item.get("artist_title") or "")[:40],
            "|",
            item.get("date_display"),
        )
    print()


QUERIES = [
    "Aristotle with a Bust of Homer",
    "Juan de Pareja",
    "Salvator Mundi",
    "Irises van Gogh",
    "The Scream",
    "Sunflowers",
    "Water Lilies Monet",
    "Girl with a Pearl Earring",
    "American Gothic",
    "The Gross Clinic",
    "Adele Bloch-Bauer",
    "Starry Night",
    "The Kiss Klimt",
    "Birth of Venus",
    "Mona Lisa",
    "Night Watch",
    "Apple computer",
    "Kodak Brownie",
    "Model T",
]

if __name__ == "__main__":
    import sys

    which = sys.argv[1] if len(sys.argv) > 1 else "met"
    fn = met if which == "met" else aic
    for q in QUERIES:
        try:
            fn(q)
        except Exception as e:
            print("ERR", q, type(e).__name__, e)
