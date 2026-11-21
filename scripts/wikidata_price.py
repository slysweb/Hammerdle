"""Find the Wikidata price property on Ginevra and sample other priced paintings."""
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}


def get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main():
    data = get(
        "https://www.wikidata.org/w/api.php?"
        + urllib.parse.urlencode(
            {
                "action": "wbgetentities",
                "ids": "Q1267893",
                "props": "claims",
                "format": "json",
            }
        )
    )
    claims = data["entities"]["Q1267893"]["claims"]
    print("properties", ", ".join(sorted(claims)))
    for pid, stmts in claims.items():
        blob = json.dumps(stmts)
        if "5000000" in blob or "amount" in blob and "USD" in blob:
            print("MAYBE", pid, blob[:500])
            print("---")


if __name__ == "__main__":
    main()
