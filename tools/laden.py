"""Lädt LibriVox-Hörbücher (64 kbit/s MP3 + Cover) aus dem Internet Archive
und schreibt den Katalog hoerbuecher.json. Läuft als GitHub Action."""
import json, os, re, sys, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISTE = os.path.join(ROOT, "tools", "hoerbuecher.txt")
ZIEL = os.path.join(ROOT, "audio")
KATALOG = os.path.join(ROOT, "hoerbuecher.json")
MAX_BYTES = 95 * 1024 * 1024  # GitHub erlaubt max. 100 MB pro Datei

def hole_json(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)

def lade(url, pfad):
    if os.path.exists(pfad) and os.path.getsize(pfad) > 0:
        return
    tmp = pfad + ".part"
    with urllib.request.urlopen(url, timeout=600) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(tmp, pfad)

def sekunden(laenge):
    if not laenge:
        return 0
    try:
        if ":" in str(laenge):
            teile = [float(x) for x in str(laenge).split(":")]
            s = 0
            for t in teile:
                s = s * 60 + t
            return round(s)
        return round(float(laenge))
    except ValueError:
        return 0

def text(v):
    if isinstance(v, list):
        v = v[0] if v else ""
    v = re.sub(r"<[^>]+>", " ", str(v or ""))
    return re.sub(r"\s+", " ", v).strip()

def kurzbeschreibung(v):
    t = text(v)
    t = re.split(r"\(Summary|Summary by|For further information", t)[0].strip()
    return t[:600]

ids = [z.strip() for z in open(LISTE, encoding="utf-8")
       if z.strip() and not z.strip().startswith("#")]
alt = {}
if os.path.exists(KATALOG):
    for b in json.load(open(KATALOG, encoding="utf-8")).get("hoerbuecher", []):
        alt[b["id"]] = b

katalog = []
for ident in ids:
    print("==>", ident, flush=True)
    meta = hole_json("https://archive.org/metadata/" + ident)
    md = meta.get("metadata", {})
    dateien = meta.get("files", [])
    basis = "https://archive.org/download/%s/" % ident
    ordner = os.path.join(ZIEL, ident)
    os.makedirs(ordner, exist_ok=True)

    mp3s = [f for f in dateien if f.get("format") == "64Kbps MP3"]
    if not mp3s:
        mp3s = [f for f in dateien if f.get("name", "").endswith(".mp3")]
    mp3s.sort(key=lambda f: (int(re.sub(r"\D", "", str(f.get("track", ""))) or 0), f["name"]))

    kapitel = []
    for i, f in enumerate(mp3s, 1):
        if int(f.get("size", 0) or 0) > MAX_BYTES:
            print("   übersprungen (zu groß):", f["name"])
            continue
        name = "%02d.mp3" % i
        lade(basis + urllib.parse.quote(f["name"]), os.path.join(ordner, name))
        titel = text(f.get("title")) or "Teil %d" % i
        kapitel.append({"titel": titel, "datei": "audio/%s/%s" % (ident, name),
                        "dauer": sekunden(f.get("length"))})
        print("   ", name, titel, flush=True)

    # Cover: größtes Original-JPG/PNG (kein Vorschaubild)
    bilder = [f for f in dateien
              if f.get("name", "").lower().endswith((".jpg", ".jpeg", ".png"))
              and "thumb" not in f["name"].lower() and f.get("source") == "original"]
    bilder.sort(key=lambda f: int(f.get("size", 0) or 0), reverse=True)
    cover = None
    if bilder:
        endung = os.path.splitext(bilder[0]["name"])[1].lower().replace(".jpeg", ".jpg")
        cover_pfad = os.path.join(ordner, "cover" + endung)
        lade(basis + urllib.parse.quote(bilder[0]["name"]), cover_pfad)
        cover = "audio/%s/cover%s" % (ident, endung)
    elif os.path.exists(os.path.join(ordner, "cover.svg")):
        cover = "audio/%s/cover.svg" % ident

    vorher = alt.get(ident, {})
    katalog.append({
        "id": ident,
        "titel": vorher.get("titel") or text(md.get("title")),
        "autor": vorher.get("autor") or text(md.get("creator")),
        "beschreibung": vorher.get("beschreibung") or kurzbeschreibung(md.get("description")),
        "sprecher": "LibriVox-Freiwillige",
        "quelle": "https://archive.org/details/" + ident,
        "cover": vorher.get("cover") if vorher.get("cover", "").endswith(".svg") and not cover else cover,
        "kapitel": kapitel,
    })

with open(KATALOG, "w", encoding="utf-8") as f:
    json.dump({"hoerbuecher": katalog}, f, ensure_ascii=False, indent=2)
print("Fertig:", len(katalog), "Hörbücher")
