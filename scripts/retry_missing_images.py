"""Fill remaining rate-limited images. Rembrandt from Rijksmuseum; others from Commons with long cooldown."""
import json
import pathlib
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from build_cars import rights as car_rights
from build_coins import rights as coin_rights
from build_dataset import DATA, IMAGES, UA
from check_list_images import strip

COMMONS = [
    ("paul-cezanne-rideau-cruchon-et-compotier", "Rideau,_Cruchon_et_Compotier,_par_Paul_Cézanne.jpg", "paul-cezanne-rideau-cruchon-et-compotier.jpg", "painting"),
    ("anthony-van-dyck-portrait-of-elena-grimaldi-cattaneo", "Marchesa_Elena_Grimaldi_c1623_Anthony_van_Dyck.jpg", "anthony-van-dyck-portrait-of-elena-grimaldi-cattaneo.jpg", "painting"),
    ("coin-1893-s-morgan-dollar", "1893-S Morgan dollar obverse.jpg", "coin-1893-s-morgan-dollar.jpg", "coin"),
    ("car-1956-aston-martin-dbr1", "1956 Aston Martin DBR1-1 at Pebble Beach 2007 fvl.jpg", "car-1956-aston-martin-dbr1.jpg", "car"),
    ("car-1966-ferrari-330-p3", '" 07 FERRARI 412P (0844).jpg', "car-1966-ferrari-330-p3.jpg", "car"),
    ("car-1930-bentley-speed-six-tourer", "1930 Bentley Speed Six - Old Number 2 fvr 4669178762.jpg", "car-1930-bentley-speed-six-tourer.jpg", "car"),
    ("car-1884-de-dion-bouton-et-trepardoux-dos-a-dos-steam-runabout-l", "De Dion-Bouton, W 92, London to Brighton Veteran Car Run 1996, Steam car La Marquise 1884, 5 CV.jpg", "car-1884-de-dion-bouton-et-trepardoux-dos-a-dos-steam-runabout-l.jpg", "car"),
    ("car-1935-duesenberg-sj-speedster-mormon-meteor", "Duesenberg SJ Mormon Meteor.jpg", "car-1935-duesenberg-sj-speedster-mormon-meteor.jpg", "car"),
]


def get(url, timeout=120):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def get_json(url):
    return json.loads(get(url).decode("utf-8"))


def save(data, dest):
    if not (data.startswith(b"\xff\xd8") or data.startswith(b"\x89PNG")):
        raise ValueError(f"not an image: {data[:40]!r}")
    dest.write_bytes(data)
    print(f"  saved {dest.name} ({len(data)} bytes)")


def patch(item, dest_name, **fields):
    item["image"] = f"images/{dest_name}"
    for k, v in fields.items():
        if v is None:
            item.pop(k, None)
        else:
            item[k] = v
    note = item.get("imageNote", "")
    if note and "another" not in note.lower() and "representative" not in note.lower() and "specimen" not in note.lower():
        item.pop("imageNote", None)


def upgrade_rembrandt(item):
    dest = IMAGES / "rembrandt-the-standard-bearer.jpg"
    url = "https://iiif.micr.io/wceCO/full/1280,/0/default.jpg"
    print("\n== rembrandt-the-standard-bearer (Rijksmuseum IIIF)")
    save(get(url), dest)
    patch(
        item, dest.name,
        imagePage="https://www.rijksmuseum.nl/en/collection/SK-A-5092",
        imageRights="public_domain",
        imageCredit="Rijksmuseum, Amsterdam",
        imageLicense="Public domain",
        imageLicenseUrl=None,
    )


def commons_meta(filename, width=1024):
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2",
        "prop": "imageinfo|revisions", "rvprop": "content", "rvslots": "main",
        "titles": "File:" + filename, "iiprop": "url|extmetadata", "iiurlwidth": str(width),
    })
    for attempt in range(8):
        try:
            page = get_json(api)["query"]["pages"][0]
            break
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            wait = 90 * (attempt + 1)
            print(f"  API 429 sleep {wait}s")
            time.sleep(wait)
    else:
        raise RuntimeError("API rate limited")
    ii = page["imageinfo"][0]
    text = page["revisions"][0]["slots"]["main"]["content"]
    artist = strip(((ii.get("extmetadata") or {}).get("Artist") or {}).get("value", ""))
    return ii.get("thumburl") or ii["url"], ii["descriptionurl"], artist, text


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
    if "pd-self" in t or "pd-author" in t:
        return "PD (released by author)"
    if "pd-art" in t or "pd-old" in t or "pd-usgov" in t:
        return "public_domain"
    return "unclear"


def curl_download(url, dest):
    """Use curl.exe — sometimes clears a stuck urllib rate-limit session."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    cmd = [
        "curl.exe", "-L", "--fail", "--retry", "5", "--retry-delay", "60",
        "-A", UA["User-Agent"], "-o", str(tmp), url,
    ]
    print("  curl", url[:110])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 10_000:
        if tmp.exists():
            tmp.unlink()
        print("  curl fail", proc.returncode, (proc.stderr or "")[-200:])
        return False
    data = tmp.read_bytes()
    if not (data.startswith(b"\xff\xd8") or data.startswith(b"\x89PNG")):
        tmp.unlink()
        print("  curl got non-image")
        return False
    tmp.replace(dest)
    print(f"  saved {dest.name} ({dest.stat().st_size} bytes)")
    return True


def main():
    IMAGES.mkdir(parents=True, exist_ok=True)
    doc = json.loads((DATA / "items.json").read_text(encoding="utf-8"))
    by_id = {it["id"]: it for it in doc["items"]}
    ok = fail = 0

    try:
        upgrade_rembrandt(by_id["rembrandt-the-standard-bearer"])
        ok += 1
    except Exception as e:
        # keep existing smaller file if present
        if (IMAGES / "rembrandt-the-standard-bearer.jpg").exists():
            patch(
                by_id["rembrandt-the-standard-bearer"], "rembrandt-the-standard-bearer.jpg",
                imagePage="https://www.rijksmuseum.nl/en/collection/SK-A-5092",
                imageRights="public_domain", imageCredit="Rijksmuseum, Amsterdam",
                imageLicense="Public domain", imageLicenseUrl=None,
            )
            print("  kept existing rembrandt file")
            ok += 1
        else:
            print("  FAIL rembrandt", e)
            fail += 1

    for item_id, commons, dest_name, category in COMMONS:
        print(f"\n== {item_id}")
        dest = IMAGES / dest_name
        if dest.exists() and dest.stat().st_size > 10_000:
            print("  already on disk")
        else:
            try:
                src, page, artist, wikitext = commons_meta(commons)
                print("  license", classify(wikitext))
                time.sleep(5)
                if not curl_download(src, dest):
                    # one more urllib attempt after a long wait
                    print("  waiting 5 minutes before urllib retry...")
                    time.sleep(300)
                    try:
                        save(get(src), dest)
                    except Exception as e:
                        print("  FAIL", e)
                        fail += 1
                        time.sleep(120)
                        continue
            except Exception as e:
                print("  FAIL meta/download", e)
                fail += 1
                time.sleep(120)
                continue

        # refresh meta for rights if needed
        try:
            src, page, artist, wikitext = commons_meta(commons)
        except Exception:
            page = f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(commons)}"
            artist, wikitext = "", ""

        item = by_id[item_id]
        if category == "painting":
            patch(item, dest_name, imagePage=page, imageRights="public_domain")
        elif category == "coin":
            patch(item, dest_name, imagePage=page, **coin_rights(commons, artist))
        else:
            license_name = classify(wikitext) if wikitext else "CC BY 2.0"
            fields = (
                {"imageRights": "public_domain", "imageLicense": "Public domain",
                 "imageLicenseUrl": None, "imageCredit": artist}
                if license_name == "public_domain"
                else car_rights(license_name, artist)
            )
            patch(item, dest_name, imagePage=page, **fields)
        ok += 1
        print("  resting 3 minutes...")
        time.sleep(180)

    (DATA / "items.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with_image = sum(1 for it in doc["items"] if it.get("image"))
    print(f"\ndone ok={ok} fail={fail} with_image={with_image}/{len(doc['items'])}")


if __name__ == "__main__":
    main()
