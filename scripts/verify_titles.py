"""Verify titles and download museum images that are CC0 or public domain."""
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(r"d:\work\Hammerdle\data")
IMG = ROOT / "images"
IMG.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "HammerdleDataBot/0.1 (local dataset; museum open access)"}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def download(url, dest: pathlib.Path):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        mime = r.headers.get("Content-Type", "")
    dest.write_bytes(data)
    print(f"saved {dest.name} {len(data)} {mime}")


def commons_license(title):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "titles": title,
            "iiprop": "url|extmetadata",
            "iiurlwidth": "1600",
        }
    )
    data = get_json(url)
    page = next(iter(data["query"]["pages"].values()))
    ii = page["imageinfo"][0]
    meta = ii.get("extmetadata") or {}

    def g(k):
        v = meta.get(k) or {}
        return (v.get("value") if isinstance(v, dict) else "") or ""

    print("COMMONS", title)
    print(" license", g("LicenseShortName"), "|", g("UsageTerms"))
    print(" credit", g("Credit")[:300].replace("\n", " "))
    print(" thumb", ii.get("thumburl"))
    return ii.get("thumburl")


import urllib.parse

IDS = {
    437394: "expect Aristotle",
    437869: "expect Juan de Pareja",
    436535: "expect Wheat Field",
}

for oid, note in IDS.items():
    obj = get_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
    print(
        oid,
        note,
        "|",
        obj.get("title"),
        "|",
        obj.get("artistDisplayName"),
        "|",
        obj.get("objectDate"),
        "| pd",
        obj.get("isPublicDomain"),
        "| acc",
        obj.get("accessionNumber"),
        obj.get("accessionYear"),
    )

commons_license("File:Ginevra de' Benci - National Gallery of Art.jpg")
