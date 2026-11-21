import collections
import json
import pathlib

doc = json.loads(pathlib.Path(r"d:\work\Hammerdle\data\items.json").read_text(encoding="utf-8"))
items = doc["items"]
print("total", len(items), "with image", sum(1 for it in items if it["image"]))
print(collections.Counter(it["imageRights"] for it in items if it["image"]))
for it in items:
    if it["category"] == "coin" and it["image"]:
        print(it["id"], "|", it["imageRights"], "|", it.get("imageLicense"), "|", it.get("imageCredit"), "|", "rep" if it.get("imageNote") else "exact")
