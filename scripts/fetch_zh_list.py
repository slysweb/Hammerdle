"""Download the parsed HTML of the zh Wikipedia list of most expensive paintings."""
import json
import pathlib
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (local dataset research)"}
OUT = pathlib.Path(r"d:\work\Hammerdle\scripts\cache")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    url = "https://zh.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "parse",
            "format": "json",
            "page": "最昂贵画作列表",
            "prop": "text|images",
            "variant": "zh-cn",
            "formatversion": "2",
        }
    )
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    parse = data["parse"]
    (OUT / "zh_list.html").write_text(parse["text"], encoding="utf-8")
    (OUT / "zh_list_images.json").write_text(
        json.dumps(parse["images"], ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print("title", parse["title"], "html chars", len(parse["text"]), "images", len(parse["images"]))


if __name__ == "__main__":
    main()
