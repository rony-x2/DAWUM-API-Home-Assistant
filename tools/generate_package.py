#!/usr/bin/env python3
"""Erzeugt packages/dawum_umfragen.yaml.

Die 238 Sensoren unterscheiden sich nur in Parlament und Partei. Statt sie
von Hand zu pflegen, werden sie aus den Tabellen unten generiert:

    python3 tools/generate_package.py

Namen und unique_ids bleiben dabei stabil, damit bestehende Entitäten und
ihre Langzeitstatistiken erhalten bleiben.
"""
from __future__ import annotations

from pathlib import Path

TREND_DAYS = 14
SCAN_INTERVAL = 3600

# (DAWUM-Parliament_ID, Anzeigename, Teil der unique_id)
PARLIAMENTS = [
    ("0", "Bundestag", "bundestag"),
    ("1", "Baden-Württemberg", "baden_wuerttemberg"),
    ("2", "Bayern", "bayern"),
    ("3", "Berlin", "berlin"),
    ("4", "Brandenburg", "brandenburg"),
    ("5", "Bremen", "bremen"),
    ("6", "Hamburg", "hamburg"),
    ("7", "Hessen", "hessen"),
    ("8", "Mecklenburg-Vorpommern", "mecklenburg_vorpommern"),
    ("9", "Niedersachsen", "niedersachsen"),
    ("10", "Nordrhein-Westfalen", "nordrhein_westfalen"),
    ("11", "Rheinland-Pfalz", "rheinland_pfalz"),
    ("12", "Saarland", "saarland"),
    ("13", "Sachsen", "sachsen"),
    ("14", "Sachsen-Anhalt", "sachsen_anhalt"),
    ("15", "Schleswig-Holstein", "schleswig_holstein"),
    ("16", "Thüringen", "thueringen"),
]

# (Anzeigename, Teil der unique_id, Icon, DAWUM-Kürzel)
# Mehrere Kürzel werden je Umfrage addiert (z. B. CDU + CSU, falls ein
# Institut die Union im Bund getrennt ausweist).
PARTIES = [
    ("CDU/CSU", "cdu_csu", "mdi:alpha-c-circle", ["CDU/CSU", "CDU", "CSU"]),
    ("SPD", "spd", "mdi:alpha-s-circle", ["SPD"]),
    ("Grüne", "gruene", "mdi:leaf", ["Grüne", "GRÜNE", "Grune"]),
    ("FDP", "fdp", "mdi:alpha-f-circle", ["FDP"]),
    ("AfD", "afd", "mdi:alpha-a-circle", ["AfD"]),
    ("Linke", "linke", "mdi:alpha-l-circle", ["Linke", "LINKE", "PDS"]),
    ("BSW", "bsw", "mdi:alpha-b-circle", ["BSW"]),
]

HEADER = f"""\
# =============================================================================
# DAWUM Wahlumfragen für Home Assistant (v5)
# =============================================================================
# DIESE DATEI WIRD GENERIERT – Änderungen bitte in tools/generate_package.py
# vornehmen und das Skript erneut ausführen.
#
# 17 Parlamente x 7 Parteien x 2 = 238 Sensoren aus EINEM REST-Aufruf:
#
#   sensor.umfrage_<parlament>_<partei>   - jeweils neueste Einzelumfrage
#                                           (Wert kommt vom zuletzt
#                                            veröffentlichenden Institut)
#
#   sensor.trend_<parlament>_<partei>     - Mittelwert aller Institute der
#                                           letzten {TREND_DAYS} Tage
#
# Sensoren ohne aktuelle Daten (Partei nicht in der Umfrage / kein Institut
# hat in den letzten {TREND_DAYS} Tagen befragt) sind "nicht verfügbar"
# (unavailable) - das ist gewollt.
#
# Installation:
#   1. Diese Datei nach <config>/packages/dawum_umfragen.yaml ablegen.
#   2. In configuration.yaml sicherstellen:
#        homeassistant:
#          packages: !include_dir_named packages
#   3. Konfiguration prüfen und Home Assistant neu starten.
#
# Datenquelle: https://dawum.de/ (Lizenz: ODC-ODbL)
# =============================================================================

rest:
  - resource: https://api.dawum.de/newest_surveys.json
    scan_interval: {SCAN_INTERVAL}
    timeout: 30
    sensor:
"""

# Gemeinsamer Anfang aller Templates. Die Prüfung auf "mapping" fängt
# fehlgeschlagene Abrufe ab (dann ist value_json nicht gesetzt).
_IDS = (
    "{{% set d = value_json if value_json is defined and value_json is mapping else {{}} %}}\n"
    "{{% set ids = (d.Parties | default({{}})).items() | selectattr('1.Shortcut', 'in', {targets}) | map(attribute='0') | list %}}\n"
)

LATEST_SURVEY = (
    _IDS
    + "{{% set s = (d.Surveys | default({{}})).values() | selectattr('Parliament_ID', 'eq', '{pid}') | sort(attribute='Date', reverse=true) | first %}}\n"
    + "{{% set vals = (s.Results.items() | selectattr('0', 'in', ids) | map(attribute='1') | list) if s is defined else [] %}}\n"
)

TREND_SURVEYS = (
    _IDS
    + "{{% set cutoff = (now() - timedelta(days=" + str(TREND_DAYS) + ")).strftime('%Y-%m-%d') %}}\n"
    + "{{% set ns = namespace(vals=[]) %}}\n"
    + "{{% for s in (d.Surveys | default({{}})).values() | selectattr('Parliament_ID', 'eq', '{pid}') | selectattr('Date', 'ge', cutoff) %}}\n"
    + "{{% set v = s.Results.items() | selectattr('0', 'in', ids) | map(attribute='1') | list %}}\n"
    + "{{% if v %}}{{% set ns.vals = ns.vals + [v | sum] %}}{{% endif %}}\n"
    + "{{% endfor %}}\n"
    + "{{% set vals = ns.vals %}}\n"
)

LATEST_VALUE = "{{ vals | sum }}"
TREND_VALUE = "{{ (vals | sum / vals | count) | round(1) }}"
AVAILABLE = "{{ vals | count > 0 }}"


def _block(text: str, indent: int) -> str:
    pad = " " * indent
    return "\n".join(pad + line if line else line for line in text.splitlines())


def _sensor(name: str, unique_id: str, icon: str, body: str, value: str) -> str:
    return (
        f'      - name: "{name}"\n'
        f"        unique_id: {unique_id}\n"
        f'        unit_of_measurement: "%"\n'
        f"        state_class: measurement\n"
        f"        icon: {icon}\n"
        f"        availability: >-\n"
        f"{_block(body + AVAILABLE, 10)}\n"
        f"        value_template: >-\n"
        f"{_block(body + value, 10)}\n"
    )


def build() -> str:
    out = [HEADER]
    out.append(
        "\n      # =====================================================\n"
        "      # GRUPPE 1: Jeweils neueste Einzelumfrage je Parlament\n"
        "      # =====================================================\n"
    )
    for pid, land, land_uid in PARLIAMENTS:
        out.append(f"\n      # ----- {land} (ID {pid}) -----\n")
        for party, party_uid, icon, targets in PARTIES:
            body = LATEST_SURVEY.format(targets=targets, pid=pid)
            out.append(
                _sensor(
                    f"Umfrage {land} {party}",
                    f"dawum_{land_uid}_{party_uid}",
                    icon,
                    body,
                    LATEST_VALUE,
                )
            )
    out.append(
        "\n      # =====================================================\n"
        f"      # GRUPPE 2: {TREND_DAYS}-Tage-Trend (Mittelwert aller Institute)\n"
        "      # =====================================================\n"
    )
    for pid, land, land_uid in PARLIAMENTS:
        out.append(f"\n      # ----- {land} Trend (ID {pid}) -----\n")
        for party, party_uid, icon, targets in PARTIES:
            body = TREND_SURVEYS.format(targets=targets, pid=pid)
            out.append(
                _sensor(
                    f"Trend {land} {party}",
                    f"dawum_trend_{land_uid}_{party_uid}",
                    icon,
                    body,
                    TREND_VALUE,
                )
            )
    return "".join(out)


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "packages" / "dawum_umfragen.yaml"
    target.parent.mkdir(exist_ok=True)
    target.write_text(build(), encoding="utf-8")
    print(f"geschrieben: {target}")
