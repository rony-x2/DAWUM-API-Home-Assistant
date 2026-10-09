# Changelog

Alle nennenswerten Änderungen an diesem Projekt. Das Format folgt
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/), die Versionen
[Semantic Versioning](https://semver.org/lang/de/).

## [5.0.0] – 2026-10-09

### Behoben
- Sensoren ohne Wert (Partei nicht abgefragt, keine Umfrage in den letzten
  14 Tagen) lieferten den Text „unknown“. Home Assistant lehnt das bei
  Sensoren mit Einheit ab: Die betroffenen Entitäten wurden gar nicht erst
  angelegt bzw. blieben auf einem veralteten Wert stehen, und das Log füllte
  sich mit „non-numeric value“-Fehlern. Mit den Daten vom 9. Oktober 2026
  betraf das 108 von 238 Sensoren.
- Schlägt der Abruf der DAWUM-API fehl, werden alle Sensoren sauber
  „nicht verfügbar“ statt Fehler zu protokollieren.
- Die Dateien liegen jetzt dort, wo das README sie beschreibt
  (`packages/dawum_umfragen.yaml`, `lovelace/examples.yaml`).
- Beispiel „Sprung-Alarm“: löst nicht mehr fälschlich beim Wechsel von oder
  zu „nicht verfügbar“ aus.

### Geändert
- **Sensoren ohne Daten sind jetzt `unavailable` statt `unknown`.**
  Automationen, die auf `unknown` prüfen, bitte anpassen.
- Weist ein Institut CDU und CSU getrennt aus, werden die Werte je Umfrage
  addiert.
- Namen, `unique_id`s und damit Entitäts-IDs und Langzeitstatistiken bleiben
  unverändert.
- Mindestversion: Home Assistant 2023.9 (`availability` bei REST-Sensoren).
- README: Automations-Beispiele in der aktuellen Schreibweise
  (`triggers:`/`actions:`, `tts.speak`).

### Hinzugefügt
- `tools/generate_package.py`: erzeugt das Paket aus zwei Tabellen
  (Parlamente, Parteien). Trend-Zeitraum und weitere Parteien lassen sich
  dort an einer Stelle ändern.
- `lovelace/examples.yaml` mit den sieben im README beschriebenen Karten.

### Entfernt
- Leere Platzhalterdatei `docs/test`.

## [4.0.0] – 2026-05-10

- Erste Veröffentlichung (Paketversion „v4 – mit Trend-Sensoren“).

[5.0.0]: https://github.com/rony-x2/DAWUM-API-Home-Assistant/compare/4.0.0...5.0.0
[4.0.0]: https://github.com/rony-x2/DAWUM-API-Home-Assistant/releases/tag/4.0.0
