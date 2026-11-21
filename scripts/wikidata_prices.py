"""Pull Wikidata items that have a recorded price and an image."""
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "HammerdleDataBot/0.1 (dataset research; local project)"}

QUERY = """
SELECT ?item ?itemLabel ?amount ?date ?image ?collectionLabel ?creatorLabel ?inception WHERE {
  ?item p:P2284 ?stmt .
  ?stmt ps:P2284 ?amount .
  OPTIONAL { ?stmt pq:P585 ?date . }
  ?item wdt:P18 ?image .
  OPTIONAL { ?item wdt:P195 ?collection . }
  OPTIONAL { ?item wdt:P170 ?creator . }
  OPTIONAL { ?item wdt:P571 ?inception . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 300
"""


def main():
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode(
        {"query": QUERY, "format": "json"}
    )
    req = urllib.request.Request(url, headers={**UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.load(r)
    rows = data["results"]["bindings"]
    print("rows", len(rows))
    for row in rows:
        def g(k):
            return (row.get(k) or {}).get("value", "")
        amount = g("amount")
        label = g("itemLabel")
        coll = g("collectionLabel")
        creator = g("creatorLabel")
        date = g("date")[:10]
        inception = g("inception")[:4]
        print(f"{amount:>14} | {date:10} | {inception:4} | {coll[:28]:28} | {creator[:22]:22} | {label[:48]}")


if __name__ == "__main__":
    main()
