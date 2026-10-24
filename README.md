# Hörbücher

Private Web-App zum Anhören gemeinfreier Hörbücher – optimiert fürs iPhone.

## Funktionen
- Übersicht aller Hörbücher mit Cover und Knopf
- Titelauswahl je Hörbuch, Zurück zur Übersicht
- Vorheriger / nächster Titel, 15 s und 1 min spulen, gedrückt halten zum schnellen Spulen
- Geschwindigkeit 0,75× bis 2×, Steuerung über Sperrbildschirm und Kopfhörer
- Merkt sich pro Hörbuch, wo du aufgehört hast

## Neues Hörbuch hinzufügen
1. Auf [LibriVox](https://librivox.org) bzw. im [Internet Archive](https://archive.org/details/librivoxaudio) ein Hörbuch suchen
   und den Bezeichner aus der Adresse kopieren (z. B. `schimmelreiter_storm_librivox`).
2. Den Bezeichner als neue Zeile in `tools/hoerbuecher.txt` eintragen und speichern (auch direkt auf github.com möglich).
3. Die GitHub Action „Hörbücher laden“ lädt MP3s und Cover automatisch und trägt das Hörbuch ein.
   Gibt es kein Cover, wird automatisch eines aus Titel und Autor erstellt.
4. Schönere Titel, Autor und Beschreibung lassen sich optional in `tools/anpassungen.json` festlegen.

## Rechtliches
Alle Aufnahmen stammen von [LibriVox](https://librivox.org) und sind gemeinfrei (Public Domain).
Die Texte sind auch in Deutschland gemeinfrei, weil die Autoren seit über 70 Jahren verstorben sind.
