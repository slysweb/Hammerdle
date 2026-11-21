"""Add coins from the Wikipedia list of most expensive coins to data/items.json."""
import json
import pathlib
import re
import time
import urllib.parse

from build_dataset import DATA, IMAGES, download, get_json, parse_date, slug
from check_list_images import strip

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")
CREDIT_FIXES = {"1804 eagle plain 4 edit.jpg": "Photo by Wehwalt, derivative work by Crisco 1492"}
LICENSES = json.loads((CACHE / "coin_candidates.json").read_text(encoding="utf-8"))
LIST_URL = "https://en.wikipedia.org/wiki/List_of_most_expensive_coins"
REPRESENTATIVE = "Image shows another specimen of the same coin type, not the coin that was sold."

# One row per coin type: the highest sale in the list. Value: (display name, image file or None, exact).
# exact=True means the image shows the same date and variety as the coin sold.
COINS = {
    0: ("1933 Double Eagle", "NNC-US-1933-G$20-Saint Gaudens.jpg", True),
    1: ("1794 Flowing Hair Dollar", "Flowing hair dollar.jpeg", False),
    2: ("1787 Brasher Doubloon", "1787 Brasher Doubloon.jpg", True),
    3: ("1822 Half Eagle", "NNC-US-1822-G$5-Capped Head (large diameter).jpg", True),
    4: ("1804 Silver Dollar", "1804 dollar type I obverse.jpeg", True),
    5: ("1894 Double Dragon Longevity Tael", None, None),
    7: ("1861 Paquet Double Eagle", "1861 $20 Paquet Double Eagle (rev).jpg", True),
    8: ("1903 Fengtien Tael", None, None),
    10: ("Gold Dinar of Yazid II", None, None),
    12: ("1870-S Three-Dollar Gold Piece", "NNC-US-1854-G$3-Indian Princess Head.jpg", False),
    14: ("1804 Proof $10 Gold Eagle", "1804 eagle plain 4 edit.jpg", True),
    15: ("1913 Liberty Head Nickel", "NNC-US-1913-5C-Liberty Nickel (cents).jpg", True),
    16: ("1911 Short Whisker Dragon Dollar Pattern", None, None),
    18: ("1907 Ultra High Relief Double Eagle", "NNC-US-1907-G$20-Saint Gaudens (Roman, ultra high relief, wire edge).jpg", True),
    20: ("Gold Aureus of Brutus", None, None),
    21: ("$1 Million Canadian Gold Maple Leaf", None, None),
    22: ("1898 \"Single 9\" Gold Pond", None, None),
    23: ("1885 Trade Dollar", None, None),
    25: ("1873 No Arrows Seated Liberty Dime", "NNC-US-1860-10C-Seated Liberty (legend).jpg", False),
    27: ("1795 Turban Head Gold Eagle", "NNC-US-1795-G$10-Turban Head (small eagle).jpg", False),
    31: ("1927-D Saint-Gaudens Double Eagle", "NNC-US-1908-D-G$20-Saint Gaudens (Arabic & motto).jpg", False),
    32: ("1911 Long Whisker Dragon Dollar Pattern", None, None),
    35: ("Silver Decadrachm of Akragas", None, None),
    38: ("1825 Constantine Ruble", None, None),
    39: ("1792 Birch Cent", None, None),
    41: ("1880 Coiled Hair $4 Stella", "NNC-US-1880-G$4-Stella Pattern (Coiled Hair).jpg", True),
    43: ("1854-S Half Eagle", "NNC-US-1840-G$5-Liberty Head (no motto).jpg", False),
    44: ("1808 Quarter Eagle", "NNC-US-1808-G$2½-Capped Bust (left).jpg", True),
    45: ("1793 Chain Cent", "NNC-US-1793-1C-Flowing Hair Cent (chain) (obverse).jpg", False),
    48: ("100 Ducats of Sigismund III Vasa", None, None),
    49: ("1937 Edward VIII £5 Pattern", None, None),
    50: ("1792 Pattern Quarter Dollar", None, None),
    51: ("1907 Rolled Edge $10 Gold Eagle", "NNC-US-1907-G$10-Indian Head (no motto).jpg", False),
    53: ("1796 No Stars Quarter Eagle", "NNC-US-1796-G$2½-Turban Head (no stars).jpg", True),
    56: ("1928 \"Mukden Tiger\" Dollar Pattern", None, None),
    58: ("1893-S Morgan Dollar", "1893-S Morgan dollar obverse.jpg", True),
    59: ("1921 Proof Saint-Gaudens Double Eagle", None, None),
    60: ("1894-S Barber Dime", "NNC-US-1892-10C-Barber Dime.jpg", False),
    62: ("1792 Silver Center Cent", None, None),
    63: ("1874 Bickford $10 Pattern", None, None),
    64: ("Hishi Oban (10 Ryō)", None, None),
    67: ("1879 Quintuple Stella ($20 Pattern)", "NNC-US-1879-G$20-Quintuple Stella Pattern.jpg", True),
    72: ("1792 Washington $10 Gold Pattern", None, None),
    73: ("1796 Draped Bust Quarter", None, None),
    76: ("Sestertius of Hadrian", None, None),
    78: ("1870-CC Double Eagle", "NNC-US-1866-G$20-Liberty Head (motto).jpg", False),
    80: ("1839/8 Liberty Head Gold Eagle", "NNC-US-1839-G$10-Liberty Head (old style).jpg", False),
    81: ("1991 Chinese 10,000 Yuan Gold Coin", None, None),
    83: ("1776 Continental Dollar (Silver)", None, None),
    84: ("1797 Draped Bust Half Dollar", None, None),
    92: ("1839 \"Una and the Lion\" £5", None, None),
    96: ("1792 Half Disme", None, None),
    99: ("1829 Large Date Half Eagle", None, None),
    113: ("1795 Reeded Edge Cent", None, None),
    117: ("1866 No Motto Seated Liberty Dollar", None, None),
    119: ("1911 Hsüan-t'ung Dollar Pattern", None, None),
    121: ("1783 Nova Constellatio Quint", None, None),
    122: ("1798 Small Eagle Half Eagle", "NNC-US-1795-G$5-Turban Head (small eagle).jpg", False),
    124: ("1792 Disme", "NNC-US-1792-10C-Pattern Disme Copper (J-10).jpg", False),
    128: ("1884 Trade Dollar", "1884 T$1 Trade Dollar (Judd-1732).jpg", True),
    136: ("1852 Humbert $10 Territorial Gold", None, None),
}
NO_IMAGE_NOTE = "No image released without restrictions was found for this coin."
CANADA_NOTE = "Modern Royal Canadian Mint design; still under Crown copyright."


def parse_year(text):
    m = re.search(r"(\d{1,4})", text)
    if not m:
        return None
    year = int(m.group(1))
    return -year if "BC" in text else year


def image_urls(files):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2", "prop": "imageinfo",
        "titles": "|".join("File:" + f for f in files), "iiprop": "url|extmetadata", "iiurlwidth": "1280",
    })
    data = get_json(url)
    norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
    out = {}
    for page in data["query"]["pages"]:
        ii = page["imageinfo"][0]
        artist = ((ii.get("extmetadata") or {}).get("Artist") or {}).get("value", "")
        key = norm.get(page["title"], page["title"])[5:]
        out[key] = (ii.get("thumburl") or ii["url"], ii["descriptionurl"], strip(artist))
    return out


def rights(file, artist):
    """Map the license read from the file's wikitext to fields the site shows next to the image."""
    license_name = LICENSES[f"File:{file}"]["license"]
    if license_name == "PD (Smithsonian)":
        return {
            "imageRights": "public_domain",
            "imageLicense": "Public domain",
            "imageLicenseUrl": None,
            "imageCredit": "National Numismatic Collection, National Museum of American History",
        }
    m = re.fullmatch(r"CC (BY(?:-SA)?) (\d\.\d)", license_name)
    assert m, (file, license_name)
    kind, version = m.groups()
    return {
        "imageRights": "cc_by_sa" if kind == "BY-SA" else "cc_by",
        "imageLicense": license_name,
        "imageLicenseUrl": f"https://creativecommons.org/licenses/{kind.lower()}/{version}/",
        "imageCredit": CREDIT_FIXES.get(file, artist),
    }


def main():
    rows = json.loads((CACHE / "coins_tables.json").read_text(encoding="utf-8"))[0]["rows"]
    doc = json.loads((DATA / "items.json").read_text(encoding="utf-8"))
    items = [it for it in doc["items"] if it.get("category") != "coin"]
    seen = {it["id"] for it in items}
    urls = image_urls(sorted({v[1] for v in COINS.values() if v[1]}))

    for idx, (name, file, exact) in COINS.items():
        price, year, kind_text, grade, country, provenance, firm, date = rows[idx]["cells"][:8]
        amount = int(re.search(r"\$([\d,]+)", price).group(1).replace(",", ""))
        firm = re.sub(r"\[[^\]]*\]", "", firm).strip()
        private = "private" in firm.lower()
        item_id = f"coin-{slug(name)}"
        assert item_id not in seen, item_id
        seen.add(item_id)

        image = image_page = None
        image_rights = {"imageRights": None}
        note = None
        if file:
            src, image_page, artist = urls[file]
            image_rights = rights(file, artist)
            dest = IMAGES / f"{item_id}.jpg"
            if download(src, dest):
                image = f"images/{dest.name}"
            time.sleep(2)
            if not exact:
                note = REPRESENTATIVE
        else:
            note = CANADA_NOTE if "Maple Leaf" in name else NO_IMAGE_NOTE

        sale_date = parse_date(date) if date else None
        context = f"{'Private-sale' if private else 'Auction'} price"
        if sale_date:
            context += f", {sale_date[:4]}"
        context += "."
        if grade:
            context += f" Grade {grade}."
        if "ZAR" in price:
            context += " Paid as 20 million South African rand."

        item = {
            "id": item_id,
            "name": name,
            "creator": country,
            "year": parse_year(year),
            "yearLabel": year,
            "category": "coin",
            "priceType": "private_sale" if private else "auction",
            "price": {"amount": amount, "currency": "USD", "approximate": False},
            "priceDate": sale_date,
            "venue": firm,
            "seller": None,
            "buyer": None,
            "context": context,
            "sourceUrl": LIST_URL,
            "image": image,
            **(image_rights if image else {"imageRights": None}),
            "imagePage": image_page if image else None,
        }
        if note:
            item["imageNote"] = note
        items.append(item)

    doc["meta"]["attributionRule"] = (
        "When imageRights is cc_by or cc_by_sa, show imageCredit, imageLicense (linked to imageLicenseUrl) "
        "and a link to imagePage next to the image. cc_by_sa images that are edited must be shared under the same license."
    )
    doc["items"] = items
    (DATA / "items.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    coins = [it for it in items if it["category"] == "coin"]
    print("coins", len(coins), "with image", sum(1 for c in coins if c["image"]), "total items", len(items))


if __name__ == "__main__":
    main()
