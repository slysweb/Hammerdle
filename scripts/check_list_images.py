"""Batch-check license, repository and description of the list's image files."""
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


def strip(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def main():
    rows = json.loads((CACHE / "en_rows.json").read_text(encoding="utf-8"))
    files = sorted({r["files"][0] for r in rows if r["files"]})
    out = {}
    for i in range(0, len(files), 40):
        batch = files[i : i + 40]
        url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "imageinfo",
                "titles": "|".join(batch),
                "iiprop": "url|extmetadata|size",
                "iiurlwidth": "1280",
            }
        )
        data = get(url)
        norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        for page in data["query"]["pages"]:
            ii = (page.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}

            def g(k):
                v = meta.get(k) or {}
                return (v.get("value") if isinstance(v, dict) else "") or ""

            key = norm.get(page["title"], page["title"])
            out[key] = {
                "title": page["title"],
                "repository": page.get("imagerepository"),
                "license": g("LicenseShortName"),
                "usage": g("UsageTerms"),
                "nonFree": g("NonFree"),
                "objectName": strip(g("ObjectName"))[:160],
                "description": strip(g("ImageDescription"))[:300],
                "credit": strip(g("Credit"))[:200],
                "width": ii.get("width"),
                "height": ii.get("height"),
                "thumb": ii.get("thumburl"),
                "original": ii.get("url"),
                "descriptionUrl": ii.get("descriptionurl"),
            }
        time.sleep(3)
    (CACHE / "en_image_info.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in files:
        info = out.get(f) or out.get(f.replace("_", " ")) or {}
        print(
            f"{info.get('repository')!s:7} | {info.get('license')[:18] if info.get('license') else '':18} | nf={info.get('nonFree')!s:4} | {info.get('width')}x{info.get('height')} | {f[5:60]} | {info.get('objectName', '')[:70]}"
        )


if __name__ == "__main__":
    main()
