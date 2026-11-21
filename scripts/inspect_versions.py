"""Print collection/owner/price details for Wikidata items behind each image."""
import json
import pathlib
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (local dataset research)"}
CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")
PROPS = {"P195": "collection", "P127": "owner", "P2284": "price", "P571": "inception", "P528": "catalog", "P217": "inventory", "P276": "location"}


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


def entities(ids, props="labels|claims"):
    out = {}
    ids = list(ids)
    for i in range(0, len(ids), 45):
        url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "format": "json", "ids": "|".join(ids[i : i + 45]), "props": props, "languages": "en"}
        )
        out.update(get(url)["entities"])
        time.sleep(2)
    return out


def value_of(snak):
    dv = (snak.get("datavalue") or {}).get("value")
    if isinstance(dv, dict):
        if "id" in dv:
            return dv["id"]
        if "amount" in dv:
            return dv["amount"] + " " + dv.get("unit", "").rsplit("/", 1)[-1]
        if "time" in dv:
            return dv["time"][1:11]
    return str(dv)


def main():
    matches = json.loads((CACHE / "en_matches.json").read_text(encoding="utf-8"))
    qs = sorted({q for m in matches for q in (m["fileQ"] or [])})
    ents = entities(qs)
    refs = set()
    summary = {}
    for q in qs:
        claims = ents[q].get("claims", {})
        rec = {}
        for pid, name in PROPS.items():
            vals = []
            for st in claims.get(pid, []):
                v = value_of(st["mainsnak"])
                quals = st.get("qualifiers", {})
                when = [value_of(s) for s in quals.get("P585", []) + quals.get("P580", [])]
                vals.append(v + (f" @{when[0]}" if when else ""))
                if v.startswith("Q"):
                    refs.add(v)
            if vals:
                rec[name] = vals
        summary[q] = {"label": ents[q].get("labels", {}).get("en", {}).get("value"), **rec}
    labels = entities(sorted(refs), props="labels")
    def lab(v):
        q = v.split(" ")[0]
        l = labels.get(q, {}).get("labels", {}).get("en", {}).get("value")
        return v.replace(q, l) if l else v
    for m in matches:
        for q in m["fileQ"] or []:
            s = summary[q]
            print(m["row"], m["status"], q, "|", s.get("label"))
            for k in ("collection", "owner", "location", "price", "catalog", "inception"):
                if k in s:
                    print("    ", k, ":", "; ".join(lab(v) for v in s[k])[:220])
    (CACHE / "file_q_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
