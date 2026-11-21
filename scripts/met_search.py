"""Search the Met's current API for specific works and report CC0 status."""
import json
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


QUERIES = [
    "Aristotle with a Bust of Homer",
    "Juan de Pareja",
    "Wheat Field with Cypresses",
    "Washington Crossing the Delaware",
    "Madame X",
    "The Death of Socrates",
    "Bridge over a Pond of Water Lilies",
    "Self-Portrait with a Straw Hat",
    "Portrait of a Young Woman Vermeer",
    "The Dance Class Degas",
]


def main():
    for i, q in enumerate(QUERIES):
        if i:
            time.sleep(0.4)
        url = (
            "https://collectionapi.metmuseum.org/public/collection/v1.1/search?"
            + urllib.parse.urlencode({"q": q, "hasImages": "true", "limit": "5"})
        )
        try:
            data = get(url)
        except Exception as e:
            print("SEARCH ERR", q, type(e).__name__, e)
            continue
        ids = data.get("objectIDs") or []
        print("Q", q, "total", data.get("total"), "ids", ids[:5])
        for oid in ids[:2]:
            time.sleep(0.3)
            obj = get(
                f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}"
            )
            print(
                " ",
                oid,
                "pd",
                obj.get("isPublicDomain"),
                "cc0img",
                obj.get("hasCC0Image") or obj.get("isPublicDomain"),
                "|",
                (obj.get("title") or "")[:70],
                "|",
                (obj.get("artistDisplayName") or "")[:30],
                "|",
                (obj.get("objectDate") or "")[:16],
                "|",
                "IMG" if obj.get("primaryImage") else "noimg",
            )
        print()


if __name__ == "__main__":
    main()
