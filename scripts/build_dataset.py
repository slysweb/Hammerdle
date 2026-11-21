"""Build data/items.json from the parsed Wikipedia painting lists and download images."""
import json
import pathlib
import re
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = pathlib.Path(r"d:\work\Hammerdle")
CACHE = ROOT / "scripts" / "cache"
DATA = ROOT / "data"
IMAGES = DATA / "images"
UA = {"User-Agent": "HammerdleDataBot/0.1 (local dataset; contact via project owner)"}
LIST_URL = "https://en.wikipedia.org/wiki/List_of_most_expensive_paintings"

# Rows of the main table whose image was verified to show the painting that was sold.
MAIN_IMAGE_OK = {
    0, 2, 3, 5, 7, 9, 10, 11, 15, 18, 19, 20, 26, 27, 28, 29, 30, 33, 35, 43, 44, 45, 46,
    52, 55, 57, 61, 65, 67, 70, 76, 78, 80, 81, 82, 84, 86, 91, 94, 98, 101, 109, 112,
    113, 118, 121, 124, 125,
}
MAIN_IMAGE_REJECTED = {
    22: "Image shows the Musée d'Orsay version, not the smaller version that was sold.",
    23: "Qi Baishi died in 1957; still under copyright in the EU until the end of 2027.",
    47: "Image is a copy after Rubens in Brussels, not the painting that was sold.",
    63: "Could not confirm which 1919 water-lily painting the image shows.",
    79: "Image shows a different grainstack painting (Wildenstein 1290).",
    107: "Qi Baishi died in 1957; still under copyright in the EU until the end of 2027.",
    116: "Could not confirm the image shows the scroll that was sold.",
}
# Progression-table rows to add (others repeat main-table rows or existing items).
PROGRESSION_ROWS = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16}
PROGRESSION_IMAGE_OK = {0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 16}
PROGRESSION_IMAGE_REJECTED = {
    2: "Only the wing panels were sold in 1821; the image shows the whole altarpiece.",
}
# The list's table and its own prose disagree; the prose names the London sale room.
VENUE_FIXES = {"Adoration of the Magi": "Christie's, London"}
# Main-table row already covered by a hand-checked item with a museum CC0 image.
SKIP_MAIN = {53}

# Death years of artists whose works are out of copyright in both the US and the EU.
PUBLIC_DOMAIN_ARTISTS = (
    "Leonardo", "Cézanne", "Gauguin", "Klimt", "Rembrandt", "Modigliani", "van Gogh",
    "Renoir", "Seurat", "Munch", "Monet", "Rubens", "Titian", "Malevich", "Botticelli",
    "Holbein", "Eakins", "Wu Bin", "Léger", "Pontormo", "Wang Meng", "Manet", "Correggio",
    "Raphael", "van Eyck", "Murillo", "van Dyck", "Vermeer", "Turner", "Mantegna",
)

AUCTION_WORDS = ("Christie", "Sotheby", "Phillips", "Philips", "Poly", "Guardian", "Binoche", "Parke-Bernet")

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}


def clean(text):
    text = re.sub(r"\[[^\]]*\]", "", text or "")
    text = re.sub(r"\s+", " ", text).strip(" .,")
    return text


def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def parse_date(text):
    text = clean(text)
    m = re.match(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", text)
    if m and m.group(1) in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"
    m = re.match(r"([A-Z][a-z]+) (\d{4})", text)
    if m and m.group(1) in MONTHS:
        return f"{m.group(2)}-{MONTHS[m.group(1)]:02d}"
    m = re.search(r"\d{4}", text)
    return m.group(0) if m else None


def parse_year(text):
    m = re.search(r"\d{4}", text)
    return int(m.group(0)) if m else None


def parse_main_price(text):
    approx = bool(re.search(r"~|\+|plus", text))
    m = re.search(r"\$\s*([\d.,]+)", text)
    amount = round(float(m.group(1).replace(",", "")) * 1_000_000)
    note = None
    if "plus exchange" in text:
        note = "Plus an exchange of other works."
    return amount, approx, note


def parse_progression_price(text):
    note = original_currency(text)
    approx = "~" in text or note is not None
    exact = re.search(r"\(\s*~?\$([\d,]+)\)", text)
    if exact:
        return int(exact.group(1).replace(",", "")), True, note
    m = re.search(r"\$([\d.]+) million", text)
    return round(float(m.group(1)) * 1_000_000), approx, note


def original_currency(text):
    m = re.search(r"\(([^()$]*(?:francs|£)[^()]*)\)", text)
    return f"Paid as {m.group(1).strip()}." if m else None


def price_type(venue):
    return "auction" if any(w in venue for w in AUCTION_WORDS) else "private_sale"


def public_domain_artist(artist):
    return any(name in artist for name in PUBLIC_DOMAIN_ARTISTS)


def get_json(url):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(url)


def image_urls(files):
    out = {}
    files = list(files)
    for i in range(0, len(files), 40):
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2", "prop": "imageinfo",
            "titles": "|".join(files[i:i + 40]), "iiprop": "url", "iiurlwidth": "1280",
        })
        data = get_json(url)
        norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        for page in data["query"]["pages"]:
            ii = page["imageinfo"][0]
            out[norm.get(page["title"], page["title"])] = (ii.get("thumburl") or ii["url"], ii["descriptionurl"])
        time.sleep(2)
    return out


def download(url, dest):
    if dest.exists() and dest.stat().st_size > 10_000:
        return True
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                data = r.read()
            if not data.startswith(b"\xff\xd8") and not data.startswith(b"\x89PNG"):
                raise ValueError("not an image")
            dest.write_bytes(data)
            return True
        except urllib.error.HTTPError as e:
            if e.code != 429:
                print("FAIL", dest.name, e)
                return False
            time.sleep(20 * (attempt + 1))
    print("FAIL rate limited", dest.name)
    return False


def build_rows():
    main = json.loads((CACHE / "en_rows.json").read_text(encoding="utf-8"))
    progression = json.loads((CACHE / "progression_rows.json").read_text(encoding="utf-8"))
    rows = []
    for i, r in enumerate(main):
        if i in SKIP_MAIN:
            continue
        amount, approx, note = parse_main_price(r["original"])
        ok = i in MAIN_IMAGE_OK
        reason = MAIN_IMAGE_REJECTED.get(i)
        rows.append((r, amount, approx, note, ok, reason))
    for i, r in enumerate(progression):
        if i not in PROGRESSION_ROWS:
            continue
        amount, approx, note = parse_progression_price(r["price"])
        r = dict(r, venue=r["venue"])
        ok = i in PROGRESSION_IMAGE_OK
        reason = PROGRESSION_IMAGE_REJECTED.get(i)
        rows.append((r, amount, approx, note, ok, reason))
    return rows


def main():
    IMAGES.mkdir(parents=True, exist_ok=True)
    existing = json.loads((DATA / "items.json").read_text(encoding="utf-8"))
    hand_checked = [it for it in existing["items"] if it.get("imageRights") == "cc0"]
    other_categories = [it for it in existing["items"] if it.get("category") != "painting"]

    rows = build_rows()
    wanted = {r["files"][0] for r, *_rest, ok, _ in rows if ok and r["files"]}
    urls = image_urls(sorted(wanted))

    items = []
    seen = {it["id"] for it in hand_checked}
    for r, amount, approx, note, ok, reason in rows:
        name = clean(r["name"])
        artist = clean(r["artist"])
        year = parse_year(r["year"])
        venue = VENUE_FIXES.get(name, clean(r["venue"]) or "Private sale")
        sale_date = parse_date(r["date"])
        base = f"{slug(artist.split('(')[0])}-{slug(name)}"
        item_id = base
        n = 2
        while item_id in seen:
            item_id = f"{base}-{n}"
            n += 1
        seen.add(item_id)

        image = None
        image_page = None
        image_rights = None
        if ok and r["files"] and public_domain_artist(artist):
            src, image_page = urls[r["files"][0]]
            ext = ".png" if src.lower().endswith(".png") else ".jpg"
            dest = IMAGES / f"{item_id}{ext}"
            if download(src, dest):
                image = f"images/{dest.name}"
                image_rights = "public_domain"
            time.sleep(1.5)
        if not image and not reason:
            if not public_domain_artist(artist):
                reason = "Artwork is still under copyright."
            else:
                reason = "No verified public-domain image yet."

        kind = price_type(venue)
        context = f"{'Auction' if kind == 'auction' else 'Private-sale'} price"
        if sale_date:
            context += f", {sale_date[:4]}"
        context += "."
        if note:
            context = f"{context[:-1]}. {note}"

        item = {
            "id": item_id,
            "name": name,
            "creator": artist,
            "year": year,
            "yearLabel": clean(r["year"]),
            "category": "painting",
            "priceType": kind,
            "price": {"amount": amount, "currency": "USD", "approximate": approx},
            "priceDate": sale_date,
            "venue": venue,
            "seller": clean(r.get("seller")) or None,
            "buyer": clean(r.get("buyer")) or None,
            "context": context,
            "sourceUrl": LIST_URL,
            "image": image,
            "imageRights": image_rights,
            "imagePage": image_page if image else None,
        }
        if reason and not image:
            item["imageNote"] = reason
        items.append(item)

    all_items = hand_checked + items + other_categories
    existing["meta"]["imageRule"] = (
        "Images are only used when the artwork is out of copyright in both the US and the EU "
        "(artist died 70+ years ago) and the image file is a public-domain or CC0 reproduction "
        "verified to show the exact painting that was sold. Items with image null still need an image."
    )
    existing["meta"]["priceRule"] = (
        "price.amount is the nominal price in US dollars at the time of sale, including buyer's premium "
        "where the source includes it. approximate=true means the source only gives an estimate."
    )
    existing["items"] = all_items
    (DATA / "items.json").write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with_image = sum(1 for it in all_items if it["image"])
    print("items", len(all_items), "with image", with_image)


if __name__ == "__main__":
    main()
