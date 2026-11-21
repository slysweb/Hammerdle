"""Assemble the static site and the server-only puzzle list.

Prices are written to src/puzzles.json, which the Worker imports.
They are not copied into site/.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WEB = ROOT / "web"
SITE = ROOT / "site"
IMAGES = SITE / "images"


def main():
    doc = json.loads((DATA / "items.json").read_text(encoding="utf-8"))
    puzzles = []
    if IMAGES.exists():
        shutil.rmtree(IMAGES)
    IMAGES.mkdir(parents=True)
    if SITE.exists():
        for child in SITE.iterdir():
            if child.name != "images":
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
    for src in WEB.iterdir():
        dest = SITE / src.name
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)

    for item in doc["items"]:
        rel = item.get("image")
        if not rel:
            continue
        src = DATA / rel
        if not src.is_file() or src.stat().st_size < 10_000:
            print("skip missing", item["id"])
            continue
        shutil.copy2(src, IMAGES / src.name)
        price = item["price"]
        puzzles.append({
            "id": item["id"],
            "name": item["name"],
            "creator": item.get("creator"),
            "year": item.get("year"),
            "yearLabel": item.get("yearLabel") or (str(item["year"]) if item.get("year") is not None else None),
            "category": item.get("category"),
            "priceType": item.get("priceType") or "auction",
            "priceDate": item.get("priceDate"),
            "approximate": bool(price.get("approximate")),
            "amount": price["amount"],
            "venue": item.get("venue"),
            "context": item.get("context"),
            "sourceUrl": item.get("sourceUrl"),
            "image": rel.replace("\\", "/"),
            "imageRights": item.get("imageRights"),
            "imageLicense": item.get("imageLicense"),
            "imageLicenseUrl": item.get("imageLicenseUrl"),
            "imageCredit": item.get("imageCredit"),
            "imagePage": item.get("imagePage"),
            "imageNote": item.get("imageNote"),
        })

    puzzles.sort(key=lambda p: p["id"])
    (ROOT / "src" / "puzzles.json").write_text(json.dumps(puzzles, ensure_ascii=False), encoding="utf-8")
    print(f"puzzles {len(puzzles)} images {len(list(IMAGES.iterdir()))}")


if __name__ == "__main__":
    main()
