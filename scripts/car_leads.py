"""Pick one sale per car model and look for Commons photos of that exact chassis, plus the article's main image."""
import json
import pathlib
import re
import time
import urllib.parse

from check_list_images import get

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")


def amount(text):
    m = re.search(r"\$([\d,]+)", text)
    return int(m.group(1).replace(",", "")) if m else 0


def model_key(name):
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def commons_search(query):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2", "list": "search",
        "srnamespace": "6", "srlimit": "10", "srsearch": query,
    })
    return [h["title"] for h in get(url)["query"]["search"]]


def page_images(titles):
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2", "redirects": "1",
        "prop": "pageimages", "piprop": "name", "titles": "|".join(titles),
    })
    data = get(url)
    back = {}
    for n in data["query"].get("normalized", []) + data["query"].get("redirects", []):
        back[n["to"]] = back.get(n["from"], n["from"])
    out = {}
    for page in data["query"]["pages"]:
        if "pageimage" in page:
            out[back.get(page["title"], page["title"])] = "File:" + page["pageimage"]
    return out


def main():
    rows = json.loads((CACHE / "cars_tables.json").read_text(encoding="utf-8"))[1]["rows"]
    best = {}
    for i, r in enumerate(rows):
        date, my, car, sn, firm, place, price = r["cells"][:7]
        key = model_key(car)
        if key not in best or amount(price) > amount(rows[best[key]]["cells"][6]):
            best[key] = i
    picked = sorted(best.values(), key=lambda i: -amount(rows[i]["cells"][6]))
    print("rows", len(rows), "unique models", len(picked))

    articles = sorted({rows[i]["links"][2][0].split("#")[0].replace("_", " ") for i in picked if rows[i]["links"][2]})
    lead_image = {}
    for k in range(0, len(articles), 40):
        lead_image.update(page_images(articles[k : k + 40]))
        time.sleep(1)

    path = CACHE / "car_leads.json"
    leads = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for i in picked:
        date, my, car, sn, firm, place, price = rows[i]["cells"][:7]
        sn_clean = re.sub(r"\[.*?\]", "", sn).strip()
        article = rows[i]["links"][2][0].split("#")[0].replace("_", " ") if rows[i]["links"][2] else None
        entry = leads.get(str(i)) or {}
        if "chassis_hits" not in entry:
            hits = []
            if len(re.sub(r"\W", "", sn_clean)) >= 4:
                hits = commons_search(f'"{sn_clean}"')
                time.sleep(1.5)
            entry["chassis_hits"] = hits
        entry.update({"row": i, "car": car, "year": my, "sn": sn_clean, "price": price, "date": date,
                      "firm": firm, "place": place, "article": article, "lead_image": lead_image.get(article)})
        leads[str(i)] = entry
        path.write_text(json.dumps(leads, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{i:3} {price:18} {my} {car[:45]:45} sn={sn_clean[:18]:18} hits={len(entry['chassis_hits'])} lead={bool(entry['lead_image'])}")


if __name__ == "__main__":
    main()
