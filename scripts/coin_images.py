"""Find lead images for each coin article and check their licenses."""
import json
import pathlib
import re
import time
import urllib.parse

from check_list_images import get, strip

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


def batched(items, n):
    for i in range(0, len(items), n):
        yield items[i : i + n]


def lead_images(titles):
    out = {}
    for batch in batched(titles, 40):
        url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query", "format": "json", "formatversion": "2",
                "prop": "pageimages|images", "piprop": "name", "imlimit": "max",
                "redirects": "1", "titles": "|".join(batch),
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
            imgs = [i["title"] for i in page.get("images", []) if re.search(r"\.(jpe?g|png)$", i["title"], re.I)]
            out[key] = {"article": page["title"], "lead": page.get("pageimage"), "images": imgs}
        time.sleep(2)
    return out


def file_info(files):
    out = {}
    for batch in batched(files, 40):
        url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query", "format": "json", "formatversion": "2", "prop": "imageinfo",
                "titles": "|".join(batch), "iiprop": "url|extmetadata|size", "iiurlwidth": "1280",
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

            out[norm.get(page["title"], page["title"])] = {
                "repository": page.get("imagerepository"),
                "license": g("LicenseShortName"),
                "credit": strip(g("Credit"))[:160],
                "artist": strip(g("Artist"))[:100],
                "description": strip(g("ImageDescription"))[:200],
                "width": ii.get("width"),
                "thumb": ii.get("thumburl"),
                "page": ii.get("descriptionurl"),
            }
        time.sleep(2)
    return out


def free(info):
    lic = (info or {}).get("license", "")
    return info and info.get("repository") == "shared" and (lic == "Public domain" or "CC0" in lic)


def main():
    tables = json.loads((CACHE / "coins_tables.json").read_text(encoding="utf-8"))
    rows = tables[0]["rows"]
    titles = sorted({r["links"][2][0].replace("_", " ") for r in rows if r["links"][2]})
    print("unique articles", len(titles), "rows without link", sum(1 for r in rows if not r["links"][2]))
    leads = lead_images(titles)
    files = sorted({f for v in leads.values() for f in v["images"]})
    info = file_info(files)
    (CACHE / "coin_leads.json").write_text(json.dumps(leads, ensure_ascii=False, indent=1), encoding="utf-8")
    (CACHE / "coin_file_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    for t in titles:
        v = leads.get(t) or {}
        lead = f"File:{v['lead']}" if v.get("lead") else None
        lead_info = info.get(lead) if lead else None
        free_files = [f for f in v.get("images", []) if free(info.get(f))]
        print("==", t, "->", v.get("article"))
        print("   lead:", (lead or "")[5:80], "|", (lead_info or {}).get("license"), (lead_info or {}).get("repository"))
        for f in free_files[:6]:
            print("   free:", f[5:90], "|", info[f]["license"], "|", info[f]["credit"][:70])


if __name__ == "__main__":
    main()
