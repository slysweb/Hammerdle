"""Match each list row's image to the painting via Wikidata IDs."""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (local dataset research)"}
CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


def get(url):
    for attempt in range(5):
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(20 * (attempt + 1))
    raise RuntimeError("rate limited")


def batched(items, n):
    for i in range(0, len(items), n):
        yield items[i : i + n]


def file_wikidata(files):
    out = {}
    for batch in batched(files, 40):
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "revisions",
                "rvprop": "content",
                "rvslots": "main",
                "titles": "|".join(batch),
            }
        )
        data = get(url)
        norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        for page in data["query"]["pages"]:
            key = norm.get(page["title"], page["title"])
            revs = page.get("revisions") or []
            text = revs[0]["slots"]["main"]["content"] if revs else ""
            qs = re.findall(r"\|\s*wikidata\s*=\s*(Q\d+)", text, re.I)
            qs += re.findall(r"\{\{\s*Artwork\s*\|\s*(?:wikidata\s*=\s*)?(Q\d+)", text, re.I)
            out[key] = {"q": sorted(set(qs)), "text": text}
        time.sleep(3)
    return out


def article_wikidata(titles):
    out = {}
    for batch in batched(titles, 40):
        url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "pageprops",
                "ppprop": "wikibase_item",
                "redirects": "1",
                "titles": "|".join(batch),
            }
        )
        data = get(url)
        q = data["query"]
        mapping = {}
        for n in q.get("normalized", []):
            mapping[n["to"]] = n["from"]
        for r in q.get("redirects", []):
            mapping[r["to"]] = mapping.get(r["from"], r["from"])
        for page in q["pages"]:
            key = mapping.get(page["title"], page["title"])
            out[key] = (page.get("pageprops") or {}).get("wikibase_item")
        time.sleep(3)
    return out


def main():
    rows = json.loads((CACHE / "en_rows.json").read_text(encoding="utf-8"))
    info = json.loads((CACHE / "en_image_info.json").read_text(encoding="utf-8"))
    shared = [f for f, v in info.items() if v["repository"] == "shared"]
    fq = file_wikidata(shared)
    names = sorted({r["nameLinks"][0].replace("_", " ") for r in rows if r["nameLinks"]})
    aq = article_wikidata(names)
    result = []
    for i, r in enumerate(rows):
        f = r["files"][0] if r["files"] else None
        art = r["nameLinks"][0].replace("_", " ") if r["nameLinks"] else None
        a_q = aq.get(art) if art else None
        f_q = (fq.get(f) or {}).get("q") if f else None
        status = "no-image"
        if f:
            if info.get(f, {}).get("repository") != "shared":
                status = "local-file"
            elif a_q and f_q:
                status = "match" if a_q in f_q else "MISMATCH"
            else:
                status = "unverified"
        result.append({"row": i, "file": f, "article": art, "articleQ": a_q, "fileQ": f_q, "status": status})
        print(i, status, "|", r["name"][:40], "|", art, a_q, "|", f_q, "|", (f or "")[5:60])
    (CACHE / "en_matches.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    texts = {k: v["text"] for k, v in fq.items()}
    (CACHE / "file_wikitext.json").write_text(json.dumps(texts, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
