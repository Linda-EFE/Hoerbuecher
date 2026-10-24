"""Einmalige Suche: russischsprachige LibriVox-Hörbücher auflisten."""
import json, re, urllib.request, urllib.parse
def hole(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Hoerbuecher/1.0"}), timeout=90) as r:
        return json.load(r)
q = "collection:librivoxaudio AND language:(Russian OR rus OR russian)"
p = urllib.parse.urlencode([("q", q), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "creator"),
    ("fl[]", "runtime"), ("fl[]", "downloads"), ("fl[]", "description"), ("sort[]", "downloads desc"),
    ("rows", 1000), ("output", "json")])
docs = hole("https://archive.org/advancedsearch.php?" + p)["response"]["docs"]
print("ANZAHL", len(docs))
for d in docs:
    desc = d.get("description", "")
    if isinstance(desc, list): desc = " ".join(desc)
    desc = re.sub(r"<[^>]+>", " ", desc); desc = re.sub(r"\s+", " ", desc)[:260]
    cr = d.get("creator", ""); cr = ", ".join(cr) if isinstance(cr, list) else cr
    print(" | ".join([d["identifier"], str(d.get("title", "")), cr, str(d.get("runtime", "")), str(d.get("downloads", "")), desc]))
