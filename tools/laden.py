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

UMLAUTE = [("ae", "ä"), ("oe", "ö"), ("ue", "ü"), ("Ae", "Ä"), ("Oe", "Ö"), ("Ue", "Ü")]

def schoener_titel(t):
    """'180_frau_holle' -> 'Frau holle', '01 - Kapitel' -> 'Kapitel'."""
    t = re.sub(r"^\d+\s*[-_.:]\s*", "", t).replace("_", " ").strip()
    return t[:1].upper() + t[1:]

FARBEN = [("#7a2e2e", "#f3d9a4"), ("#24485f", "#f1e4c8"), ("#3d5a3a", "#f4e7c5"),
          ("#5b3a6b", "#f2dcc2"), ("#8a5a1f", "#fbefd6"), ("#2f3b4c", "#e8c37e")]

def erstelle_cover(titel, autor, pfad):
    """Erstellt ein eigenes Cover (SVG) aus Titel und Autor."""
    from html import escape
    bg, fg = FARBEN[sum(map(ord, titel)) % len(FARBEN)]
    woerter, zeilen, z = titel.split(), [], ""
    for w in woerter:
        if len(z) + len(w) + 1 > 14 and z:
            zeilen.append(z); z = w
        else:
            z = (z + " " + w).strip()
    if z:
        zeilen.append(z)
    zeilen = zeilen[:4]
    groesse = 52 if max(len(x) for x in zeilen) <= 10 else 42
    y0 = 300 - (len(zeilen) - 1) * groesse * 0.6
    tsp = "".join('<tspan x="300" y="%d">%s</tspan>' % (y0 + i * groesse * 1.2, escape(x))
                  for i, x in enumerate(zeilen))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600">
<rect width="600" height="600" fill="{bg}"/>
<rect x="30" y="30" width="540" height="540" fill="none" stroke="{fg}" stroke-width="3" opacity=".7"/>
<rect x="44" y="44" width="512" height="512" fill="none" stroke="{fg}" stroke-width="1" opacity=".5"/>
<g fill="none" stroke="{fg}" stroke-width="6" stroke-linecap="round" opacity=".9">
<path d="M255 150a45 45 0 0 1 90 0"/></g>
<g fill="{fg}" opacity=".9"><rect x="243" y="146" width="18" height="34" rx="8"/><rect x="339" y="146" width="18" height="34" rx="8"/></g>
<text font-family="Georgia, 'Times New Roman', serif" font-size="{groesse}" font-weight="bold" fill="{fg}" text-anchor="middle">{tsp}</text>
<line x1="230" y1="{y0 + len(zeilen) * groesse * 1.2 - 10:.0f}" x2="370" y2="{y0 + len(zeilen) * groesse * 1.2 - 10:.0f}" stroke="{fg}" stroke-width="2" opacity=".6"/>
<text x="300" y="{y0 + len(zeilen) * groesse * 1.2 + 34:.0f}" font-family="Georgia, serif" font-size="28" font-style="italic" fill="{fg}" text-anchor="middle" opacity=".85">{escape(autor)}</text>
<text x="300" y="530" font-family="Arial, sans-serif" font-size="16" letter-spacing="4" fill="{fg}" text-anchor="middle" opacity=".6">HÖRBUCH</text>
</svg>'''
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(svg)

ids = [z.strip() for z in open(LISTE, encoding="utf-8")
       if z.strip() and not z.strip().startswith("#")]
ANPASSUNGEN = {}
_ap = os.path.join(ROOT, "tools", "anpassungen.json")
if os.path.exists(_ap):
    ANPASSUNGEN = json.load(open(_ap, encoding="utf-8"))

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
        titel = schoener_titel(text(f.get("title"))) or "Teil %d" % i
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

    if not cover:
        cover_pfad = os.path.join(ordner, "cover.svg")
        if not os.path.exists(cover_pfad):
            a = ANPASSUNGEN.get(ident, {})
            erstelle_cover(a.get("titel") or text(md.get("title")),
                           a.get("autor") or text(md.get("creator")), cover_pfad)
        cover = "audio/%s/cover.svg" % ident

    a = ANPASSUNGEN.get(ident, {})
    if a.get("kapitel"):
        nach_nr = {int(k["datei"][-6:-4]): k for k in kapitel}
        kapitel = [dict(nach_nr[nr], titel=t) for nr, t in a["kapitel"] if nr in nach_nr]
    katalog.append({
        "id": ident,
        "titel": a.get("titel") or text(md.get("title")),
        "autor": a.get("autor") or text(md.get("creator")),
        "beschreibung": a.get("beschreibung") or kurzbeschreibung(md.get("description")),
        "kategorie": a.get("kategorie", "Romane & Erzählungen"),
        "quelle": "https://archive.org/details/" + ident,
        "cover": cover,
        "kapitel": kapitel,
    })

with open(KATALOG, "w", encoding="utf-8") as f:
    json.dump({"hoerbuecher": katalog}, f, ensure_ascii=False, indent=2)
print("Fertig:", len(katalog), "Hörbücher")
