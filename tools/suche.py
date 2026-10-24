"""Listet deutsche LibriVox-Hörbücher im Internet Archive auf."""
import json, urllib.request, urllib.parse

def suche(q, rows=150):
    params = urllib.parse.urlencode([
        ("q", q), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "creator"),
        ("fl[]", "runtime"), ("fl[]", "item_size"), ("fl[]", "downloads"),
        ("sort[]", "downloads desc"), ("rows", rows), ("output", "json")])
    url = "https://archive.org/advancedsearch.php?" + params
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)["response"]["docs"]

for q in ['collection:librivoxaudio AND language:(German OR deu OR ger)',
          'collection:librivoxaudio AND (Hörbuch OR deutsch)']:
    print("### Abfrage:", q)
    for d in suche(q):
        print(" | ".join(str(d.get(k, "")) for k in
              ("identifier", "title", "creator", "runtime", "item_size", "downloads")))
