"""Read license and description of every candidate car photo; keep chassis hits whose text names the chassis and make."""
import json
import pathlib
import re
import time
import urllib.parse

from check_list_images import get, strip
from coin_candidates import classify

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


def squash(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def fetch_files(files):
    path = CACHE / "car_file_info.json"
    info = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    todo = [f for f in files if f not in info]
    for i in range(0, len(todo), 40):
        batch = todo[i : i + 40]
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "prop": "revisions|imageinfo", "rvprop": "content", "rvslots": "main",
            "iiprop": "extmetadata|size|mime", "titles": "|".join(batch),
        })
        data = get(url)
        norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        for page in data["query"]["pages"]:
            key = norm.get(page["title"], page["title"])
            revs = page.get("revisions") or []
            text = revs[0]["slots"]["main"]["content"] if revs else ""
            ii = (page.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}
            info[key] = {
                "onCommons": bool(revs),
                "license": classify(text) if revs else "not on Commons",
                "artist": strip((meta.get("Artist") or {}).get("value")),
                "description": strip((meta.get("ImageDescription") or {}).get("value"))[:400],
                "width": ii.get("width"),
                "mime": ii.get("mime"),
            }
        path.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(3)
    return info


def main():
    leads = json.loads((CACHE / "car_leads.json").read_text(encoding="utf-8"))
    files = sorted({f for v in leads.values() for f in v["chassis_hits"] + [v["lead_image"]] if f})
    info = fetch_files(files)

    out = {}
    lines = []
    for key, v in sorted(leads.items(), key=lambda kv: -int(re.sub(r"\D", "", kv[1]["price"].split(".")[0]) or 0)):
        sn = squash(v["sn"])
        make = squash(v["car"].split()[0])
        exact = []
        for f in v["chassis_hits"]:
            if f not in info:
                continue
            meta = info[f]
            text = squash(f + " " + meta.get("description", ""))
            if len(sn) >= 4 and sn in text and make in text:
                exact.append({"file": f, **meta})
        lead = v["lead_image"] if v["lead_image"] in info else None
        out[key] = {**v, "exact": exact, "lead": {"file": lead, **info[lead]} if lead else None}
        lines.append(f"== {key} {v['price']} {v['year']} {v['car']} sn={v['sn']}")
        for e in exact:
            lines.append(f"   EXACT {e['license']:16} | {e['file'][5:100]} | {e['artist'][:40]}")
        if lead:
            lines.append(f"   LEAD  {info[lead]['license']:16} | {lead[5:100]} | {info[lead]['artist'][:40]}")
    (CACHE / "car_candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (CACHE / "car_candidates.txt").write_text("\n".join(lines), encoding="utf-8")
    print("models", len(out), "with exact", sum(1 for v in out.values() if v["exact"]),
          "with usable lead", sum(1 for v in out.values() if v["lead"] and v["lead"]["license"] not in ("unclear", "not on Commons", "GFDL only")))


if __name__ == "__main__":
    main()
