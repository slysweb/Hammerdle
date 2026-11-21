"""Classify licenses of every image on the coin articles, from the file wikitext."""
import json
import pathlib
import re
import time
import urllib.parse

from check_list_images import get, strip

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


def classify(text):
    t = text.lower()
    if re.search(r"\{\{\s*(cc-zero|cc0)", t):
        return "CC0"
    m = re.search(r"cc-by-sa-(\d\.\d)", t)
    if m:
        return f"CC BY-SA {m.group(1)}"
    m = re.search(r"cc-by-(\d\.\d)", t)
    if m:
        return f"CC BY {m.group(1)}"
    if "pd-usgov-si" in t or "national numismatic collection" in t:
        return "PD (Smithsonian)"
    if "pd-self" in t:
        return "PD (released by author)"
    if "gfdl" in t:
        return "GFDL only"
    return "unclear"


def main():
    leads = json.loads((CACHE / "coin_leads.json").read_text(encoding="utf-8"))
    files = sorted({f for v in leads.values() for f in v["images"]})
    files = [f for f in files if not re.search(r"penny, obverse, 2002|portrait|Flag|\.svg", f, re.I)]
    out = {}
    for i in range(0, len(files), 45):
        batch = files[i : i + 45]
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "prop": "revisions|imageinfo", "rvprop": "content", "rvslots": "main",
            "iiprop": "extmetadata|size", "titles": "|".join(batch),
        })
        data = get(url)
        norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        for page in data["query"]["pages"]:
            key = norm.get(page["title"], page["title"])
            revs = page.get("revisions") or []
            text = revs[0]["slots"]["main"]["content"] if revs else ""
            meta = ((page.get("imageinfo") or [{}])[0].get("extmetadata")) or {}
            src = re.search(r"\|\s*source\s*=\s*([^\n]*)", text, re.I)
            out[key] = {
                "onCommons": bool(revs),
                "license": classify(text) if revs else "not on Commons",
                "artist": strip((meta.get("Artist") or {}).get("value"))[:120],
                "source": (src.group(1).strip() if src else "")[:160],
            }
        time.sleep(3)
    (CACHE / "coin_candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for article, v in sorted(leads.items()):
        print("==", article)
        for f in v["images"]:
            info = out.get(f)
            if info:
                print(f"   {info['license']:22} | {f[5:95]} | {info['artist'][:40]}")


if __name__ == "__main__":
    main()
