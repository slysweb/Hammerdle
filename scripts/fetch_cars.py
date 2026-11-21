"""Fetch and parse the en Wikipedia list of most expensive cars sold at auction."""
import json
import pathlib
import urllib.parse
import urllib.request

from parse_zh_list import TableParser

UA = {"User-Agent": "HammerdleDataBot/0.1 (local dataset research)"}
CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


def fetch():
    path = CACHE / "cars.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "format": "json", "page": "List of most expensive cars sold at auction", "prop": "text", "formatversion": "2"}
    )
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        text = json.load(r)["parse"]["text"]
    path.write_text(text, encoding="utf-8")
    return text


def main():
    p = TableParser()
    p.feed(fetch())
    tables = []
    for ti, table in enumerate(p.tables):
        header = [c["text"] for c in table[0]]
        print("TABLE", ti, "rows", len(table) - 1, "header", header)
        rows = []
        for row in table[1:]:
            rows.append({"cells": [c["text"] for c in row], "links": [c["links"] for c in row], "files": [c["files"] for c in row]})
        tables.append({"header": header, "rows": rows})
        for r in rows[:3]:
            print("   ", r["cells"])
            print("   ", r["links"], r["files"])
    (CACHE / "cars_tables.json").write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
