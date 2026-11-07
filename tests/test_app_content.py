"""Inhalt der App: Kennzahlen der Presets, Ergebnistabelle, Modell von Hand, Tabellen der Bänder, Verdikte, Permalink (AppTest, DEMO-PLAYBOOK §5).
Zeiten der Live-Läufe schwanken: geprüft werden Struktur, Größen und Ergebnisse, nicht die Sekunden."""

import os
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

import ilm_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _run(at=None):
    if at is None:                                              # nicht `at or ...`: ein ungelaufener AppTest ist falsy
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrics(at):
    return {m.label: m.value for m in at.metric}


def _deltas(at):
    return {m.label: m.delta for m in at.metric}


def _preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(md.value for md in at.markdown)


def _bodies(at):
    return " ".join(e.value for kind in (at.success, at.info, at.warning) for e in kind)


MODEL, TIME, SEARCH, OPT = "Modell (Variablen)", "ILP-Zeit", "Suche (Zeit)", "Optimum"


def test_default_bay_runs_the_ilp_and_names_model_search_and_optimum():
    at = _run()
    m, d = _metrics(at), _deltas(at)
    assert m[MODEL] == "6 075" and d[MODEL] == "2 652 Zeilen" and re.fullmatch(r"\d+,\d\d s", m[TIME]) and d[TIME] == "Optimum bewiesen"
    assert m[SEARCH].endswith(" ms") and d[SEARCH] == "11 Knoten" and m[OPT] == "5" and d[OPT] == "Untergrenze 4, Bucht 3 × 3"
    text = _texts(at)
    assert re.search(r"\| ILP \(HiGHS, zeitindiziertes Modell\) \| 5 \| \d+,\d\d s \| 6 075 Variablen, 2 652 Zeilen; LP-Wert 5 \|", text)
    assert re.search(r"\| Suche \(IDA\* mit Untergrenze und Merken\) \| 5 \| [\d,]+ ms \| 11 Knoten in 2 Budgetstufen \|", text) and "| Untergrenze (Stück 2) | 4 |  | Zahl der Blocker |" in text
    assert any(re.match(r"Das ILP beweist das Optimum 5 in \d+,\d\d s \(Modell mit 6 075 Variablen\), die Suche in [\d,]+ ms: das [\d ]+-Fache schneller \(Untergrenze 4\)\.", s.value) for s in at.success)


def test_mini_preset_has_the_documented_model_size_and_the_move_table():
    at = _preset(_run(), "Die Mini-Bucht")
    assert _metrics(at)[MODEL] == "1 692" and _deltas(at)[MODEL] == "1 020 Zeilen" and _metrics(at)[OPT] == "2"
    text = _texts(at)
    assert "**1 692 Variablen**, **1 020 Zeilen** und 11 700 Nichtnullen; der LP-Wert ist 2." in " ".join(c.value for c in at.caption)
    assert text.count("| 4 | Stapel") == 2 and "| Periode | Container | von | nach |" in text                 # die 4 wird zweimal bewegt
    assert any("Optimum 2: Die 4 blockiert die 1" in s.value and "nachgespielt (2 Hübe)" in s.value for s in at.success)


def test_the_hand_section_shows_the_correction_of_the_lifo_constraint_for_every_setting():
    text = _texts(_run())
    assert "| Korrektur (9) | optimal | 8 |" in text and "| Originalfassung (6) | infeasible | – |" in text


def test_slow_preset_runs_the_ilp_to_a_proof():
    at = _preset(_run(), "Das ILP wird langsam (3 Stapel, 4 Lagen)")
    assert _metrics(at)[MODEL] == "15 660" and _metrics(at)[OPT] == "13" and _deltas(at)[TIME] == "Optimum bewiesen"
    assert at.sidebar.slider(key="limit_slider").value == 30


def test_giveup_preset_hits_the_time_limit_and_claims_no_optimum_from_the_ilp():
    at = _preset(_run(), "Das ILP gibt auf (4 Stapel, 3 Lagen)")
    m = _metrics(at)
    assert m[TIME] == "Limit (5 s)" and _deltas(at)[TIME] == "kein Beweis" and m[MODEL] == "21 360" and m[OPT] == "10"                     # das Optimum kommt aus der Suche
    assert any("Das ILP erreicht das Zeitlimit von 5 s ohne Optimalitätsbeweis" in w.value and "die Suche beweist das Optimum 10" in w.value for w in at.warning)
    assert re.search(r"\| ILP \(HiGHS, zeitindiziertes Modell\) \| kein Beweis[^|]*\| [\d,]+ s \(Limit 5 s\) \| 21 360 Variablen, 6 622 Zeilen \|", _texts(at))


def test_search_preset_does_not_run_the_ilp_and_says_why():
    at = _preset(_run(), "Die Suche trägt weiter (5 Stapel, 4 Lagen)")
    m = _metrics(at)
    assert m[MODEL] == "143 100" and m[TIME] == "nicht gerechnet" and _deltas(at)[TIME] == "mehr als 60 000 Variablen" and m[OPT] == "9" and _deltas(at)[SEARCH] == "31 Knoten"
    assert any("Das Modell hätte 143 100 Variablen und 26 885 Zeilen (mehr als 60 000): Das ILP wird hier nicht gerechnet." in i.value for i in at.info)
    assert "| ILP (HiGHS, zeitindiziertes Modell) | nicht gerechnet |  | 143 100 Variablen, 26 885 Zeilen |" in _texts(at)


def test_the_tables_of_the_bands_show_the_stored_numbers():
    at = _run()
    text = _texts(at)
    assert "| 3 × 2 | 6 | 1 692 | 1 020 |" in text and "| 4 × 4 | 16 | 55 104 | 13 380 |" in text
    assert "| 3 × 2 (6), 20 | 1 692 | 20 / 20 | 0,04 s / 0,10 s | 0,1 ms / 0,2 ms | 2, 2 |" in text
    assert "| 4 × 3 (12), 12 | 21 360 | 11 / 12 | 1,39 s / 60,3 s | 0,4 ms / 3,0 ms | 4, 6 |" in text and "| 4 × 4 (16), 6 | 55 104 | 5 / 6 | 33,2 s / 60,8 s | 5,0 ms / 26 ms | 7, 11,5 |" in text
    assert "| 3 × 3 (20) | 5 | 5 | 3,5 | 0, 1 | 16 von 20 |" in text and "| 3 × 4 (10) | 8,5 | 9,5 | 6 | 1, 4 | 4 von 10 |" in text
    assert "| 4 × 3 (8) | 3,58 s | 72,6 s | 5 % | 0, 1 |" in text and "| 4 × 3 (12) | 1,37 s / 81,5 s | 1,01 s / 28,5 s | 2,9-fach |" in text
    assert "| 6 × 4 (24), 10 | 9 / 10 | 11,5 | 2 228 / 72 284 | 37 ms / 1,69 s |" in text and "| 6 × 5 (30), 8 | 7 / 8 | 17 | 65 510 / 309 392 | 1,42 s / 6,26 s |" in text
    assert "| 3 × 3 (100) | 12 | 13 | 75 |" in text and "| 3 × 4 (20) | 11 | 4 | 5 |" in text
    bodies = _bodies(at)
    assert "3 × 3 (9 Container, 6 075 Variablen): Das ILP beweist 20 von 20 Buchten innerhalb von 60 s (Zeit im Median 0,21 s, Maximum 2,13 s); die Suche braucht im Median 0,3 ms, höchstens 0,9 ms." in bodies
    assert "3 × 4: LP-Wert im Median 8,5, Optimum 9,5, Untergrenze 6; Optimum minus LP-Wert im Median 1, höchstens 4 (4 von 10 Buchten mit LP-Wert gleich Optimum). Die LP-Schranke lässt hier eine Lücke." in bodies
    assert "4 × 4: Das Wurzel-LP kostet 5 % der ILP-Zeit (Summe 6,30 s von 120,2 s); der Rest ist Verzweigung." in bodies
    assert "4 × 3: HiGHS Median 1,37 s (Summe 81,5 s, 11 von 12 richtig), CP-SAT Median 1,01 s (Summe 28,5 s, 12 von 12 richtig): CP-SAT ist insgesamt das 2,9-Fache schneller." in bodies
    assert "6 × 4 (24 Container, 11,5 Blocker im Median): 9 von 10 Buchten unter 1 000 000 Knoten, Knoten im Median 2 228, höchstens 72 284; Zeit im Median 37 ms, höchstens 1,69 s." in bodies
    assert "3 × 3: Mit der Originalfassung (6) sind 12 von 100 Buchten unlösbar und 13 haben einen anderen Wert als die Suche; mit der Korrektur (9) stimmen alle." in bodies


def test_the_cell_of_the_setting_is_named_and_the_space_note_appears_for_other_space():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params.update({"stacks": "5", "layers": "4", "extra": "1", "seed": "2", "limit": "5"})
    _run(at)
    text = _texts(at)
    assert "**Zelle 5 × 4 (Ihre Einstellung)**, Tabellen gelten für Platz 2, hier ist Platz 1 eingestellt:" in text
    assert any("wurde das ILP nicht vorberechnet (zu groß)" in i.value for i in at.info)
    assert "**Zelle 3 × 3 (Ihre Einstellung)**:" in _texts(_run())


def test_permalink_is_clamped_to_the_slider_bounds():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["stacks"] = "99"
    at.query_params["layers"] = "-4"
    at.query_params["extra"] = "17"
    at.query_params["limit"] = "1000"
    at.query_params["seed"] = "5"
    _run(at)
    assert at.sidebar.slider(key="stacks_slider").value == C.STACKS_MAX
    assert at.sidebar.slider(key="layers_slider").value == C.LAYERS_MIN
    assert at.sidebar.slider(key="extra_slider").value == C.EXTRA_MAX
    assert at.sidebar.slider(key="limit_slider").value == C.LIMIT_MAX
