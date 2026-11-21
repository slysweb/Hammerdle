"""Parse the 'Progression of highest prices paid' table and check its images."""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

from parse_zh_list import TableParser
from check_list_images import get, strip

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


def main():
    p = TableParser()
    p.feed((CACHE / "en_list.html").read_text(encoding="utf-8"))
    rows = []
    for table in p.tables:
        header = [c["text"] for c in table[0]]
        if header[:2] != ["Price", "Painting"]:
            continue
        for row in table[1:]:
            rows.append(
                {
                    "price": row[0]["text"],
                    "name": row[1]["text"],
                    "nameLinks": row[1]["links"],
                    "files": [f for c in row for f in c["files"]],
                    "artist": row[3]["text"],
                    "year": row[4]["text"],
                    "date": row[5]["text"],
                    "seller": row[6]["text"],
                    "buyer": row[7]["text"],
                    "venue": row[8]["text"],
                }
            )
    (CACHE / "progression_rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    files = [r["files"][0] for r in rows if r["files"]] + ["File:Modigliani_-_Nu_couché.jpg"]
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo|revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": "|".join(files),
            "iiprop": "url|extmetadata|size",
            "iiurlwidth": "1280",
        }
    )
    data = get(url)
    norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
    info = {}
    for page in data["query"]["pages"]:
        key = norm.get(page["title"], page["title"])
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        revs = page.get("revisions") or []
        text = revs[0]["slots"]["main"]["content"] if revs else ""
        qs = sorted(set(re.findall(r"\|\s*wikidata\s*=\s*(Q\d+)", text, re.I)))
        info[key] = {
            "missing": "missing" in page,
            "license": ((meta.get("LicenseShortName") or {}).get("value") or ""),
            "objectName": strip((meta.get("ObjectName") or {}).get("value"))[:120],
            "description": strip((meta.get("ImageDescription") or {}).get("value"))[:240],
            "fileQ": qs,
            "width": ii.get("width"),
            "height": ii.get("height"),
            "thumb": ii.get("thumburl"),
        }
    (CACHE / "progression_image_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    for i, r in enumerate(rows):
        f = r["files"][0] if r["files"] else None
        inf = info.get(f, {}) if f else {}
        print(i, "|", r["price"][:40], "|", r["name"][:40], "|", r["artist"][:24], "|", r["date"], "|", inf.get("license"), inf.get("missing"), inf.get("fileQ"), "|", (f or "")[5:70])
    m = info.get("File:Modigliani_-_Nu_couché.jpg")
    print("MODIGLIANI", m)


if __name__ == "__main__":
    main()
