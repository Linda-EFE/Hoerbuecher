# Hörbücher

Private Web-App zum Anhören gemeinfreier **Hörbücher für Kinder bis 10 Jahre** – optimiert fürs iPhone.

**Seite:** https://linda-efe.github.io/Hoerbuecher/

- **Gespeichert:** 4 Hörbücher liegen als MP3 direkt in diesem Repository (`audio/`).
- **Online:** weitere kindgerechte deutsche LibriVox-Hörbücher sind nur verlinkt und werden
  direkt vom Internet Archive gestreamt (`katalog-online.json`).
- **Nur kindgerechte Titel:** Welche Online-Hörbücher erscheinen, steht in `tools/kinder.txt`
  (von Hand geprüft, für Kinder bis 10 Jahre). Neue Titel kommen nur dazu, wenn sie dort
  eingetragen werden – eine Zeile `bezeichner | Kategorie` genügt (Kategorien: Märchen,
  Kindergeschichten, Bildergeschichten & Reime, Weihnachten).

## Funktionen
- Übersicht aller Hörbücher mit Cover und Knopf
- Suche (Titel, Autor, Sprecher, Kapitel), Kategorien, Filter Gespeichert/Online, Sortierung
- Titelauswahl je Hörbuch, Zurück zur Übersicht
- Vorheriger / nächster Titel, 15 s und 1 min spulen, gedrückt halten zum schnellen Spulen
- Geschwindigkeit 0,75× bis 2×, Steuerung über Sperrbildschirm und Kopfhörer
- Merkt sich pro Hörbuch, wo du aufgehört hast

## Hörbuch fest im Repository speichern
Jedes Online-Hörbuch lässt sich auch fest speichern (dann unabhängig vom Internet Archive):
1. Auf [LibriVox](https://librivox.org) bzw. im [Internet Archive](https://archive.org/details/librivoxaudio) ein Hörbuch suchen
   und den Bezeichner aus der Adresse kopieren (z. B. `schimmelreiter_storm_librivox`).
2. Den Bezeichner als neue Zeile in `tools/hoerbuecher.txt` eintragen und speichern (auch direkt auf github.com möglich).
3. Die GitHub Action „Hörbücher laden“ lädt MP3s und Cover automatisch und trägt das Hörbuch ein.
   Gibt es kein Cover, wird automatisch eines aus Titel und Autor erstellt.
4. Schönere Titel, Autor und Beschreibung lassen sich optional in `tools/anpassungen.json` festlegen.

## Rechtliches
Alle Aufnahmen stammen von [LibriVox](https://librivox.org) und sind gemeinfrei (Public Domain).
Die 4 gespeicherten Titel sind auch in Deutschland gemeinfrei, weil die Autoren seit über 70 Jahren verstorben sind.
Die Online-Titel werden nicht kopiert, sondern nur von ihrer legalen Quelle (archive.org) abgespielt.
