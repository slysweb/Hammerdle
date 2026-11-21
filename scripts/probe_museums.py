"""Probe museum open-access search for a few known works."""
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def show(label, url, limit=500):
    print("==", label)
    try:
        raw = get(url)
        print(raw[:limit].decode("utf-8", "replace"))
    except Exception as e:
        print(type(e).__name__, e)
    print()


if __name__ == "__main__":
    show(
        "met",
        "https://collectionapi.metmuseum.org/public/collection/v1/search?"
        + urllib.parse.urlencode(
            {"q": "Aristotle with a Bust of Homer", "hasImages": "true", "isPublicDomain": "true"}
        ),
    )
    show(
        "aic",
        "https://api.artic.edu/api/v1/artworks/search?"
        + urllib.parse.urlencode(
            {
                "q": "American Gothic",
                "limit": "2",
                "fields": "id,title,artist_title,date_display,is_public_domain,image_id",
            }
        ),
    )
    show(
        "cleveland",
        "https://openaccess-api.clevelandart.org/api/artworks/?"
        + urllib.parse.urlencode({"q": "Monet", "cc0": "1", "has_image": "1", "limit": "1"}),
    )
    show(
        "nga",
        "https://api.nga.gov/artworks?" + urllib.parse.urlencode({"q": "Ginevra", "limit": "1"}),
    )
