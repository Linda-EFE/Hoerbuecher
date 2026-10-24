"""Erstellt katalog-online.json: alle deutschsprachigen LibriVox-Hörbücher im
Internet Archive, die NICHT im Repository liegen. Es werden nur Links gespeichert,
die Audiodateien werden direkt vom Internet Archive gestreamt.
Läuft als GitHub Action (tools/katalog.yml)."""
import json, os, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOKAL = os.path.join(ROOT, "tools", "hoerbuecher.txt")
AUSGABE = os.path.join(ROOT, "katalog-online.json")

def hole_json(url, versuche=4):
    for v in range(versuche):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Hoerbuecher-Katalog/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:
            if v == versuche - 1:
                raise
            time.sleep(3 * (v + 1))

def text(v):
    if isinstance(v, list):
        v = " ".join(str(x) for x in v)
    v = re.sub(r"<br\s*/?>", "\n", str(v or ""), flags=re.I)
    v = re.sub(r"<[^>]+>", " ", v)
    v = (v.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
          .replace("&nbsp;", " ").replace("&uuml;", "ü").replace("&ouml;", "ö")
          .replace("&auml;", "ä").replace("&szlig;", "ß").replace("&Uuml;", "Ü")
          .replace("&Ouml;", "Ö").replace("&Auml;", "Ä"))
    return re.sub(r"\s+", " ", v).strip()

def sekunden(laenge):
    try:
        s = 0
        for t in str(laenge).split(":"):
            s = s * 60 + float(t)
        return round(s)
    except ValueError:
        return 0

def schoener_titel(t):
    t = re.sub(r"^\s*(?:\d+\s*[-_:–]\s*|\d{2,3}\s+)(?=\D)", "", t)
    if "_" in t and " " not in t:
        t = t.replace("_", " ")
    t = t.strip(" -–")
    return t[:1].upper() + t[1:]

def natuerlich(name):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", name)]

SPRECHER_MUSTER = re.compile(
    r"^\s*(?:Read (?:in (?:the original )?German |in German )?by|"
    r"(?:Auf Deutsch )?[Gg]elesen (?:auf |in )?(?:[Dd]eutsch )?(?:für LibriVox )?von|"
    r"Auf Deutsch gelesen von)\s+(.{1,600}?)(?:\.(?=\s|$)|\s*¶)", re.S)

def sprecher_und_text(beschreibung, autor):
    """Trennt den LibriVox-Vorspann ('LibriVox recording of ... Read by X.') von der Beschreibung."""
    roh = beschreibung if not isinstance(beschreibung, list) else " ".join(map(str, beschreibung))
    roh = re.sub(r"<br\s*/?>|</p>|</div>|\n", " ¶ ", str(roh or ""), flags=re.I)
    t = text(roh)
    t = re.sub(r"For (?:more )?free audio ?books.*?librivox\.?\s*org\s*\.?", " ", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    if re.match(r"\s*libri\s*vox", t, re.I):
        pos = t.find(autor, 0, 400) if autor else -1
        if pos >= 0:
            kandidaten = [i for i in (t.find(".", pos + len(autor)), t.find("¶", pos + len(autor))) if i >= 0]
            punkt = min(kandidaten) if kandidaten else -1
            t = t[punkt + 1:] if punkt >= 0 else t[pos + len(autor):]
        else:
            t = re.sub(r"^\s*Libri\s*[Vv]ox[^.]{0,250}\.", "", t)
    sprecher = ""
    t = re.sub(r"^[\s¶.,;:–-]+", "", t)
    m = re.match(r"\s*(?:Read|Gelesen|Auf Deutsch gelesen)[^.]{0,40}?(?:volunteers|Freiwillige\w*)\s*\.?", t, re.I)
    if not m:
        m = re.match(r"\s*(?:Read in German|(?:Auf Deutsch )?[Gg]elesen(?: auf| in)? [Dd]eutsch)( mit verteilten Rollen)?\s*(?:\.|¶)", t)
    if m:
        sprecher = "mehrere LibriVox-Sprecher" if "Rollen" in m.group(0) else "LibriVox-Freiwillige"
        t = t[m.end():]
        m = None
    else:
        m = SPRECHER_MUSTER.match(t)
    if m:
        sprecher = m.group(1).strip(" ,;")
        t = t[m.end():]
    if re.search(r"freiwillig|volunteer", sprecher, re.I):
        sprecher = "LibriVox-Freiwillige"
    namen = [n.strip() for n in re.split(r"[;,]| und ", sprecher) if n.strip()]
    if len(namen) > 3:
        sprecher = ", ".join(namen[:3]) + " u. a."
    elif len(sprecher) > 80:
        sprecher = sprecher[:80].rsplit(" ", 1)[0] + " …"
    t = re.split(r"\(Summary|Summary by|\(Zusammenfassung|Zusammenfassung (?:von|aus|nach)|\(Text aus|For further information", t)[0]
    t = re.sub(r"\s*¶\s*", " ", t)
    t = re.sub(r"^[\s\-–.;,]+", "", t).strip()
    if len(t) > 700:
        t = t[:700].rsplit(" ", 1)[0] + " …"
    return sprecher, t

KATEGORIEN = [
    ("Gedichte", r"poetry|poem|gedicht|lyrik|ballade|hymne|sonett"),
    ("Kinder & Märchen", r"child|kinder|märchen|maerchen|fairy|fabel|juvenile|sage"),
    ("Krimi", r"mystery|detective|crime|krimi|detektiv|mord|sherlock|holmes"),
    ("Abenteuer", r"adventure|abenteuer|reise|travel|winnetou|western|science fiction|meer"),
    ("Drama", r"drama|play|theater|tragödie|komödie|trauerspiel|lustspiel|schauspiel"),
    ("Sachbuch", r"philosoph|history|geschichte des|essay|science|politi|religio|biograph|brief|letters|non-?fiction|psycholog|ratgeber|abhandlung"),
]

def kategorie(titel, subjekt):
    blob = (titel + " " + subjekt).lower()
    for name, muster in KATEGORIEN:
        if re.search(muster, blob):
            return name
    return "Romane & Erzählungen"

def suche():
    ergebnis, seite = [], 1
    q = "collection:librivoxaudio AND language:(German OR deu OR ger OR Deutsch)"
    while True:
        params = urllib.parse.urlencode([
            ("q", q), ("fl[]", "identifier"), ("fl[]", "downloads"),
            ("sort[]", "downloads desc"), ("rows", 500), ("page", seite), ("output", "json")])
        docs = hole_json("https://archive.org/advancedsearch.php?" + params)["response"]["docs"]
        ergebnis += docs
        if len(docs) < 500:
            return ergebnis
        seite += 1

def buch(doc):
    ident = doc["identifier"]
    try:
        meta = hole_json("https://archive.org/metadata/" + ident)
    except Exception as e:
        print("   Fehler", ident, e, flush=True)
        return None
    md = meta.get("metadata", {})
    dateien = meta.get("files", [])
    sprache = text(md.get("language")).lower()
    if sprache and not re.search(r"german|deu|ger|deutsch", sprache):
        return None
    mp3s = [f for f in dateien if f.get("format") == "64Kbps MP3"]
    if not mp3s:
        mp3s = [f for f in dateien if f.get("name", "").lower().endswith(".mp3")]
    if not mp3s:
        return None
    mp3s.sort(key=lambda f: natuerlich(f["name"]))
    kapitel = []
    for i, f in enumerate(mp3s, 1):
        kapitel.append({"t": schoener_titel(text(f.get("title"))) or "Teil %d" % i,
                        "d": f["name"], "s": sekunden(f.get("length"))})
    bilder = [f for f in dateien
              if f.get("name", "").lower().endswith((".jpg", ".jpeg", ".png"))
              and "thumb" not in f["name"].lower() and f.get("source") == "original"]
    bilder.sort(key=lambda f: int(f.get("size", 0) or 0), reverse=True)
    titel = text(md.get("title"))
    autor = text(md.get("creator")) or "Verschiedene"
    if autor.lower() in ("various", "unknown"):
        autor = {"various": "Verschiedene", "unknown": "Unbekannt"}[autor.lower()]
    sprecher, beschreibung = sprecher_und_text(md.get("description"), text(md.get("creator")))
    return {
        "id": ident,
        "titel": titel,
        "autor": autor,
        "sprecher": sprecher,
        "beschreibung": beschreibung,
        "kategorie": kategorie(titel, text(md.get("subject"))),
        "beliebt": int(doc.get("downloads") or 0),
        "cover": bilder[0]["name"] if bilder else None,
        "kapitel": kapitel,
    }

def main():
    lokal = {z.strip() for z in open(LOKAL, encoding="utf-8")
             if z.strip() and not z.strip().startswith("#")}
    treffer = [d for d in suche() if d["identifier"] not in lokal]
    print("Gefunden:", len(treffer), flush=True)
    with ThreadPoolExecutor(8) as ex:
        buecher = [b for b in ex.map(buch, treffer) if b]
    buecher.sort(key=lambda b: -b["beliebt"])
    daten = {
        "hinweis": "Nur Links. Die Audiodateien werden direkt vom Internet Archive (archive.org) gestreamt.",
        "basis": "https://archive.org/download/",
        "stand": time.strftime("%Y-%m-%d"),
        "hoerbuecher": buecher,
    }
    with open(AUSGABE, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, separators=(",", ":"))
    print("Fertig:", len(buecher), "Hörbücher,", os.path.getsize(AUSGABE) // 1024, "KB")

if __name__ == "__main__":
    main()
