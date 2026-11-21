"""Targeted Commons searches for top cars that lack a matching image, with license of each hit."""
import json
import pathlib
import time

from car_candidates import fetch_files
from car_leads import commons_search

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")

QUERIES = {
    0: "Uhlenhaut Coupe 300 SLR",
    1: "W196 Stromlinienwagen",
    2: "Ferrari 3765",
    4: "Shelby Daytona CSX2300",
    8: "Ferrari 250 LM 5893",
    10: "Ferrari 412P",
    11: "Mercedes W196 00006",
    12: "Ferrari 290 MM",
    13: "Ferrari 275 GTB/4 NART Spider",
    21: "Duesenberg SSJ",
    22: "Jaguar D-Type XKD 501",
    27: "Alfa Romeo 8C 2900B Lungo",
    28: "Alfa Romeo 8C 2900B Berlinetta Touring",
    39: "Ferrari 250 Testa Rossa 0666",
    50: "Talbot-Lago T150-C SS Teardrop",
    59: "Mercedes-Benz 540K Special Roadster",
    69: "Bugatti Type 57SC Atalante",
    77: "Bugatti Royale Kellner",
    86: "Mercedes-Benz 300 SL Gullwing",
    87: "Hispano-Suiza Tulipwood",
    107: "Jaguar E-Type Lightweight",
    172: "Ferrari 330 P3",
    229: "De Dion La Marquise",
    26: "McLaren F1 LM",
    63: "Ferrari F40 LM",
    74: "LaFerrari Aperta",
}


def main():
    path = CACHE / "car_search.json"
    hits = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for row, q in QUERIES.items():
        if str(row) not in hits:
            hits[str(row)] = commons_search(q)
            path.write_text(json.dumps(hits, ensure_ascii=False, indent=1), encoding="utf-8")
            time.sleep(1.5)
    info = fetch_files(sorted({f for v in hits.values() for f in v}))
    for row, q in QUERIES.items():
        print("==", row, q)
        for f in hits[str(row)]:
            i = info.get(f, {})
            print(f"   {i.get('license', '?'):16} | {f[5:95]} | {i.get('artist', '')[:30]}")


if __name__ == "__main__":
    main()
