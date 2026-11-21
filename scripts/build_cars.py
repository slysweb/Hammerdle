"""Add cars from the en Wikipedia list of most expensive cars sold at auction to data/items.json."""
import json
import pathlib
import re
import time
import urllib.parse

from build_dataset import DATA, IMAGES, download, get_json, parse_date, slug
from car_candidates import fetch_files

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")
LIST_URL = "https://en.wikipedia.org/wiki/List_of_most_expensive_cars_sold_at_auction"
REPRESENTATIVE = "Image shows another car of the same model, not the car that was sold."

# row index in cars_tables.json -> (Commons file, image shows the car that was sold)
CARS = {
    0: ("Mercedes-Benz 300 SLR Coupé, (Uhlenhaut Coupé) (51566311415).jpg", False),
    3: ("1962 Ferrari 250 GTO 3413GT, Series II update, front left.jpg", True),
    4: ("Shelby Daytona, 1964.JPG", False),
    5: ("2027 Ferrari Luce, front left.jpg", False),
    8: ("Ferrari 250 LM 5893 at PB 2022.jpg", True),
    9: ("1957 Ferrari 335 Sport Spider Scaglietti no 0674, Greenwich 2018.jpg", True),
    10: ("Ferrari 412P 0850 at CF 2023.jpg", False),
    12: ("Ferrari 1956 290 MM Scaglietti Spyder.jpg", False),
    13: ("Ferrari 275 GTB 4 NART Spider (54961699981).jpg", False),
    15: ("Ferrari Daytona SP3 front side at CF 2022.jpg", False),
    18: ("1956 Aston Martin DBR1-1 at Pebble Beach 2007 fvl.jpg", True),
    19: ("1955 Ferrari 410 Sport front.jpg", True),
    22: ("Paris - Retromobile 2013 - Jaguar D Type - 1955 - 106.jpg", False),
    23: ("Aston Martin DP215 frontt.JPG", True),
    25: ("1996 McLaren F1 Chassis No 63 6.1 Front.jpg", False),
    28: ("Alfa Romeo 8C 2900B Touring Berlinetta (avant).jpg", False),
    29: ("Lewis Hamilton 2013 Malaysia FP2 2.jpg", False),
    30: ("アランドロンが乗っていたフェラーリ.jpg", True),
    34: ("Orange Enzo Ferrari (7191948164).jpg", False),
    38: ("Ferrari 250 GT Bertone sn3269GT Retromobile 2018 (cropped).jpg", True),
    39: ("Ferrari250TestaRossa-Pebble2006.jpeg", False),
    45: ("1960 Aston Martin DB4 GT Zagato HCC24.jpg", False),
    46: ("1969 Porsche 917K Red.jpg", False),
    50: ("Talbot-Lago T150-C-SS Coupé Goutte d'Eau (1938) (55082149327).jpg", False),
    51: ("Jaguar 1956 XKSS (5678420041).jpg", False),
    53: ("Jaguar C-Type 1953.jpg", False),
    54: ("Paris - Retromobile 2013 - Ferrari 312 PB - 1972 - 101.jpg", False),
    56: ("1997-05-01 Mille Ferrari 340 0320AM.jpg", True),
    59: ("1937 Mercedes Benz 540K Special Roadster.jpg", False),
    61: ("2019-07-26 Silverstone Ferrari 250 SWB 1995GT.jpg", True),
    63: ("1993 Ferrari F40 LM.jpg", False),
    64: ("GT40 at Goodwood.jpg", False),
    68: ("Bugatti Type 55 3.jpg", False),
    69: ("Bugatti Type-57SC Atalante.jpg", False),
    72: ("Porsche 956 Rothmans.jpg", False),
    74: ("2017 Ferrari Laferrari Aperta.jpg", False),
    85: ("Ferrari 330 TR.jpg", False),
    86: ("Mercedes-Benz W198 300 SL Gullwing Genf 2019 1Y7A4987.jpg", False),
    87: ("1924 Hispano Suiza H6C Tulipwood Torpedo front.jpg", True),
    88: ("1999 Ferrari F50.jpg", False),
    94: ("Bugatti Divo, GIMS 2019, Le Grand-Saconnex (GIMS0029).jpg", False),
    95: ("1959 Ferrari 250 GT 1519GT (20576362612).jpg", True),
    107: ("Jaguar E-Type Lightweight, Bj. 1963, Eingang Mercedes-Arena (2009-08-07 Sp b).JPG", False),
    110: ("Birkin Bentley 4½ Litre Blower.jpg", False),
    112: ("1957 Ferrari 500 TRC 0706 MDTR.jpg", True),
    116: ("Ferrari 400 Superamerica Pininfarina Cabriolet.jpg", True),
    118: ("1954 Ferrari 375 America Vignale Cabriolet.jpg", True),
    120: ("Schumacher Ferrari F2001 at Laguna Seca.jpg", False),
    121: ("1953 Ferrari 375 MM Spider front.jpg", True),
    123: ("Paris - Retromobile 2012 - Mercedes-Benz SSK - 1928 - 017.jpg", False),
    124: ("Rétromobile 2015 - Ferrari 212 Touring Barchetta - 1952 - 003.jpg", True),
    128: ("Ferrari 250 MM Berlinetta - MM 2014 - (14241703734).jpg", False),
    131: ("1997-05-01 Mille Miglia Ferrari 250 0415GT.jpg", True),
    135: ("1964 Ford GT40 proto GT.104.jpg", True),
    138: ("1965 Ford GT40 Roadster Prototype.jpg", True),
    155: ("Aston Martin DB5 (Skyfall).jpg", False),
    158: ("Ferrari F300 front-right1 2019 Michael Schumacher Private Collection.jpg", False),
    172: ('" 07 FERRARI 412P (0844).jpg', True),
    173: ("Porsche RS Spyder 2006 frontright 2009-03-14 A.JPG", False),
    177: ("1955 Aston Martin DB3S-111.png", True),
    185: ("1959 Ferrari 250 GT TdF 1161 front.jpg", True),
    188: ("Porsche 550 Spyder from 1957 in the Porsche-Museum (2009) 1X7A0325.jpg", False),
    192: ("Ferrari 750 Monza (1955) (55081629525).jpg", True),
    193: ("MC12. (5234528513).jpg", False),
    198: ("1930 Bentley Speed Six - Old Number 2 fvr 4669178762.jpg", True),
    203: ("BMW 507.jpg", False),
    207: ("Ayrton Senna - Mclaren MP4-8 during practice for the 1993 British Grand Prix (32873580103).jpg", False),
    215: ("1957 Maserati 450S - fvl (edit).jpg", False),
    229: ("De Dion-Bouton, W 92, London to Brighton Veteran Car Run 1996, Steam car La Marquise 1884, 5 CV.jpg", True),
    243: ("Nationale Sportwagenraces Zandvoort, Bestanddeelnr 906-5080 (cropped).jpg", True),
    246: ("Ferrari 288 GTO (1).JPG", False),
    252: ("GM FuturLiner at Flint 2011.jpg", False),
    253: ("Porsche 718RSK Spyder, front right, Stratford.jpg", False),
    254: ("1930 Duesenberg J Murphy Disappearing Top Torpedo Convertible Coupe - fvl (4609844035).jpg", False),
    259: ("Duesenberg SJ Mormon Meteor.jpg", True),
    266: ("Bugatti Chiron 1.jpg", False),
    275: ("Bugatti 51 (1932) Solitude Revival 2019 IMG 1584.jpg", False),
}


def image_urls(files):
    out = {}
    for i in range(0, len(files), 40):
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2", "prop": "imageinfo",
            "titles": "|".join("File:" + f for f in files[i : i + 40]), "iiprop": "url", "iiurlwidth": "1280",
        })
        data = get_json(url)
        norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        for page in data["query"]["pages"]:
            ii = page["imageinfo"][0]
            out[norm.get(page["title"], page["title"])[5:]] = (ii.get("thumburl") or ii["url"], ii["descriptionurl"])
        time.sleep(1)
    return out


def rights(license_name, artist):
    credit = re.sub(r"^\W+", "", artist).strip()
    if license_name == "CC0":
        return {"imageRights": "cc0", "imageLicense": "CC0 1.0",
                "imageLicenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/", "imageCredit": credit}
    if license_name == "PD (released by author)":
        return {"imageRights": "public_domain", "imageLicense": "Public domain (released by the photographer)",
                "imageLicenseUrl": None, "imageCredit": credit}
    m = re.fullmatch(r"CC (BY(?:-SA)?) (\d\.\d)", license_name)
    assert m, license_name
    kind, version = m.groups()
    return {"imageRights": "cc_by_sa" if kind == "BY-SA" else "cc_by", "imageLicense": license_name,
            "imageLicenseUrl": f"https://creativecommons.org/licenses/{kind.lower()}/{version}/", "imageCredit": credit}


def main():
    rows = json.loads((CACHE / "cars_tables.json").read_text(encoding="utf-8"))[1]["rows"]
    files = sorted({f for f, _ in CARS.values()})
    info = fetch_files(["File:" + f for f in files])
    urls = image_urls(files)

    doc = json.loads((DATA / "items.json").read_text(encoding="utf-8"))
    items = [it for it in doc["items"] if it.get("category") != "car"]
    seen = {it["id"] for it in items}

    for idx, (file, exact) in CARS.items():
        date, model_year, car, sn, firm, place, price = rows[idx]["cells"][:7]
        sn = re.sub(r"\[.*?\]", "", sn).strip()
        name = f"{model_year} {car}"
        item_id = f"car-{slug(name)}"
        assert item_id not in seen, item_id
        seen.add(item_id)

        meta = info["File:" + file]
        src, image_page = urls[file]
        suffix = ".png" if file.lower().endswith(".png") else ".jpg"
        dest = IMAGES / f"{item_id}{suffix}"
        image = f"images/{dest.name}" if download(src, dest) else None
        time.sleep(2)

        sale_date = parse_date(date)
        context = f"Auction price, {sale_date[:4]}." if sale_date else "Auction price."
        if sn and sn.upper() != "N/A":
            context += f" Chassis {sn}."

        item = {
            "id": item_id,
            "name": name,
            "creator": car.split()[0],
            "year": int(re.search(r"\d{4}", model_year).group(0)),
            "yearLabel": model_year,
            "category": "car",
            "priceType": "auction",
            "price": {"amount": int(re.sub(r"\D", "", price.split(".")[0])), "currency": "USD", "approximate": False},
            "priceDate": sale_date,
            "venue": f"{firm}, {place}",
            "seller": None,
            "buyer": None,
            "context": context,
            "sourceUrl": LIST_URL,
            "image": image,
            **(rights(meta["license"], meta["artist"]) if image else {"imageRights": None}),
            "imagePage": image_page if image else None,
        }
        if not exact:
            item["imageNote"] = REPRESENTATIVE
        items.append(item)

    doc["items"] = items
    (DATA / "items.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cars = [it for it in items if it["category"] == "car"]
    print("cars", len(cars), "with image", sum(1 for c in cars if c["image"]),
          "exact", sum(1 for c in cars if c["image"] and "imageNote" not in c), "total items", len(items))


if __name__ == "__main__":
    main()
