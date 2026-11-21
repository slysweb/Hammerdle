"""Fetch and parse the en Wikipedia list of most expensive paintings (main table)."""
import json
import pathlib
import re
import urllib.parse
import urllib.request

from parse_zh_list import TableParser

UA = {"User-Agent": "HammerdleDataBot/0.1 (local dataset research)"}
CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


def fetch():
    path = CACHE / "en_list.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "parse",
            "format": "json",
            "page": "List of most expensive paintings",
            "prop": "text",
            "formatversion": "2",
        }
    )
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        text = json.load(r)["parse"]["text"]
    path.write_text(text, encoding="utf-8")
    return text


def main():
    p = TableParser()
    p.feed(fetch())
    rows = []
    for table in p.tables:
        header = [c["text"] for c in table[0]]
        if not header or not header[0].startswith("Adjusted"):
            continue
        for row in table[1:]:
            if len(row) < 11:
                continue
            rows.append(
                {
                    "adjusted": row[0]["text"],
                    "original": row[1]["text"],
                    "name": row[2]["text"],
                    "nameLinks": row[2]["links"],
                    "files": [f for c in row for f in c["files"]],
                    "artist": row[4]["text"],
                    "year": row[5]["text"],
                    "date": row[6]["text"],
                    "seller": row[8]["text"],
                    "buyer": row[9]["text"],
                    "venue": row[10]["text"],
                }
            )
        break
    (CACHE / "en_rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("rows", len(rows), "with image", sum(1 for r in rows if r["files"]))
    for i, r in enumerate(rows):
        print(i, "|", r["original"], "|", r["name"][:45], "|", r["artist"][:28], "|", r["year"], "|", r["date"], "|", (r["files"] or [""])[0][:70])


if __name__ == "__main__":
    main()
