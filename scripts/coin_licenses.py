"""Print license templates and sources for candidate coin images."""
import json
import pathlib
import re
import urllib.parse

from check_list_images import get

CACHE = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")
FILES = [
    "Specimen1Obv.jpg",
    "Flowing hair dollar.jpeg",
    "1787 Brasher Doubloon.jpg",
    "1804 dollar type I obverse.jpeg",
    "1861 $20 Paquet Double Eagle (rev).jpg",
    "1870-S three dollar edit.jpg",
    "1804 eagle plain 4 edit.jpg",
    "NNC-US-1913-5C-Liberty Nickel (cents).jpg",
    "1907 Ultra High Relief $20 Double Eagle (Inverted Edge Letters).jpg",
    "NNC-US-1795-G$10-Turban Head (small eagle).jpg",
    "Const.jpg",
    "NNC-US-1880-G$4-Stella Pattern (Coiled Hair).jpg",
    "NNC-US-1808-G$2½-Capped Bust (left).jpg",
    "NNC-US-1793-1C-Flowing Hair Cent (chain) (obverse).jpg",
    "1893-S Morgan dollar obverse.jpg",
    "NNC-US-1796-G$2½-Turban Head (no stars).jpg",
    "NNC-US-1879-G$20-Quintuple Stella Pattern.jpg",
    "1792 silver center cent.png",
    "1855-S Three Dollar Proof.jpg",
    "1894-S Barber dime.jpg",
    "1792 Half Disme pattern (Judd-7).jpg",
]


def main():
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query", "format": "json", "formatversion": "2", "prop": "revisions",
            "rvprop": "content", "rvslots": "main", "titles": "|".join("File:" + f for f in FILES),
        }
    )
    data = get(url)
    texts = {}
    for page in data["query"]["pages"]:
        revs = page.get("revisions") or []
        text = revs[0]["slots"]["main"]["content"] if revs else "(missing)"
        texts[page["title"]] = text
        templates = re.findall(r"\{\{\s*([^{}|\n]+)", text)
        keep = [t.strip() for t in templates if re.search(r"PD|CC|cc-|Smithsonian|NNC|GFDL|self|license|permission|Heritage|PCGS", t, re.I)]
        src = re.search(r"\|\s*source\s*=\s*([^\n]*)", text, re.I)
        desc = re.search(r"\|\s*description\s*=\s*([^\n]*)", text, re.I)
        print("==", page["title"])
        print("   templates:", sorted(set(keep))[:10])
        print("   source:", (src.group(1) if src else "")[:150])
        print("   desc:", (desc.group(1) if desc else "")[:150])
    (CACHE / "coin_file_wikitext.json").write_text(json.dumps(texts, ensure_ascii=False, indent=1), encoding="utf-8")

    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "format": "json", "list": "search", "srnamespace": "6", "srlimit": "10",
         "srsearch": "NNC-US-1822"}
    )
    print("SEARCH 1822:", [r["title"] for r in get(url)["query"]["search"]])


if __name__ == "__main__":
    main()
