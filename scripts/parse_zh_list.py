"""Parse the zh list tables into rows: cells as text, plus image file and links."""
import html
import json
import pathlib
import re
from html.parser import HTMLParser

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.depth = 0
        self.row = None
        self.cell = None
        self.in_sup = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table" and "wikitable" in (a.get("class") or ""):
            self.depth += 1
            if self.depth == 1:
                self.tables.append([])
        elif self.depth != 1:
            return
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = {"text": "", "files": [], "links": [], "th": tag == "th"}
        elif tag == "sup":
            self.in_sup += 1
        elif self.cell is not None and tag == "a":
            href = a.get("href") or ""
            if "/wiki/File:" in href or "/wiki/File%3A" in href:
                self.cell["files"].append(urllib_unquote(href.split("/wiki/")[1]))
            elif href.startswith("/wiki/") and ":" not in href[6:]:
                self.cell["links"].append(urllib_unquote(href[6:]))
        elif self.cell is not None and tag == "img":
            src = a.get("src") or ""
            self.cell.setdefault("imgsrc", []).append(src)
        elif self.cell is not None and tag == "br":
            self.cell["text"] += " "

    def handle_endtag(self, tag):
        if tag == "table" and self.depth:
            self.depth -= 1 if self.depth else 0
            return
        if self.depth != 1:
            return
        if tag == "sup" and self.in_sup:
            self.in_sup -= 1
        elif tag in ("td", "th") and self.cell is not None:
            self.cell["text"] = re.sub(r"\s+", " ", self.cell["text"]).strip()
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.tables[-1].append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None and not self.in_sup:
            self.cell["text"] += data


def urllib_unquote(s):
    import urllib.parse

    return urllib.parse.unquote(s)


def main():
    text = (CACHE / "zh_list.html").read_text(encoding="utf-8")
    p = TableParser()
    p.feed(text)
    out = []
    for ti, table in enumerate(p.tables):
        print("TABLE", ti, "rows", len(table))
        for ri, row in enumerate(table[:3]):
            print("  ", [c["text"][:30] for c in row])
        out.append(table)
    (CACHE / "zh_tables.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
