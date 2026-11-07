"""JEDE Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über die vorberechneten Tabellen (ilm_bands.json; die kleinen Zellen werden in test_presets.py frisch
gerechnet, soweit es nicht von der Zeit abhängt) und die Auswertungsfunktionen der App. **Zeiten sind gespeicherte Einzelmessungen**, keine Eigenschaft, die der Test erneut belegt."""

import pytest

import ilm_constants as C
import ilm_evaluation as ev

BANDS = ev.load_bands()

# Tabelle A: Zelle -> (Buchten, Container, Variablen, Zeilen, bewiesen, ILP-Zeit Median, Maximum (alle Läufe, Sekunden), Suche Median, Maximum (Millisekunden), Untergrenze, Optimum (Median))
ZEIT = {
    (3, 2): (20, 6, 1692, 1020, 20, 0.040, 0.103, 0.096, 0.236, 2.0, 2.0),
    (4, 2): (20, 8, 5952, 2576, 20, 0.147, 0.642, 0.107, 0.263, 2.0, 2.0),
    (3, 3): (20, 9, 6075, 2652, 20, 0.213, 2.126, 0.270, 0.943, 3.5, 5.0),
    (5, 2): (12, 10, 15500, 5220, 12, 0.433, 0.635, 0.178, 0.395, 2.5, 3.0),
    (4, 3): (12, 12, 21360, 6622, 11, 1.389, 60.333, 0.354, 2.969, 4.0, 6.0),
    (3, 4): (10, 12, 15660, 5379, 10, 2.526, 25.111, 1.521, 8.406, 6.0, 9.5),
    (5, 3): (8, 15, 55500, 13335, 7, 11.428, 60.885, 0.418, 1.689, 5.5, 6.5),
    (4, 4): (6, 16, 55104, 13380, 5, 33.156, 60.774, 4.986, 25.84, 7.0, 11.5),
}
# Tabelle B: LP-Wert, Optimum, Untergrenze (Median), Optimum minus LP-Wert (Median, Maximum), Buchten mit LP-Wert gleich Optimum
LP = {(3, 2): (20, 2.0, 2.0, 2.0, 0.0, 0.0, 20), (4, 2): (20, 2.0, 2.0, 2.0, 0.0, 0.0, 20), (3, 3): (20, 5.0, 5.0, 3.5, 0.0, 1.0, 16), (5, 2): (12, 3.0, 3.0, 2.5, 0.0, 0.0, 12),
      (4, 3): (12, 5.5, 6.0, 4.0, 0.0, 1.0, 9), (3, 4): (10, 8.5, 9.5, 6.0, 1.0, 4.0, 4)}
LPZEIT = {(3, 3): (8, 0.928, 3.336, 0.278, 0.0, 1.0), (4, 3): (8, 3.583, 72.627, 0.049, 0.0, 1.0), (3, 4): (8, 3.246, 51.686, 0.063, 0.5, 4.0),
          (5, 3): (6, 7.088, 130.03, 0.055, 0.0, 0.0), (4, 4): (4, 6.299, 120.235, 0.052, 1.0, 1.0)}
# Tabelle C: Zelle -> (Buchten, HiGHS Median, Summe, richtig, CP-SAT Median, Summe, richtig, Faktor der Summen)
LOESER = {(3, 3): (10, 0.215, 4.411, 10, 0.190, 2.390, 10, 1.846), (4, 3): (12, 1.372, 81.522, 11, 1.013, 28.491, 12, 2.861),
          (3, 4): (10, 3.140, 57.755, 10, 0.928, 15.565, 10, 3.711), (5, 3): (6, 4.502, 115.505, 5, 2.655, 57.252, 6, 2.017)}
# Tabelle D: Zelle -> (Buchten, Container, fertig, Blocker (Median), Knoten Median, Maximum, Zeit Median, Maximum (Sekunden))
SUCHE = {(4, 4): (20, 16, 20, 7.0, 251.0, 2299, 0.004, 0.034), (5, 4): (20, 20, 20, 10.5, 415.0, 56710, 0.008, 1.013), (6, 3): (10, 18, 10, 6.0, 46.0, 206, 0.001, 0.003),
         (6, 4): (10, 24, 9, 11.5, 2228, 72284, 0.037, 1.69), (5, 5): (10, 25, 10, 14.0, 13260.0, 283134, 0.366, 6.692), (7, 4): (8, 28, 8, 14.5, 1483.5, 167214, 0.038, 3.934),
         (6, 5): (8, 30, 7, 17.0, 65510, 309392, 1.417, 6.264), (8, 4): (8, 32, 8, 16.0, 658.0, 151730, 0.013, 3.991)}
KORREKTUR = {(3, 2): (100, 0, 0, 100), (4, 2): (60, 0, 0, 60), (3, 3): (100, 12, 13, 75), (3, 4): (20, 11, 4, 5)}


@pytest.mark.parametrize("cell", list(ZEIT))
def test_readme_time_cell(cell):
    n, containers, variables, rows, solved, tmed, tmax, smed, smax, lb, opt = ZEIT[cell]
    c = BANDS["zeit"][ev.cell_key(*cell)]
    assert (c["n"], c["containers"], c["variables"], c["rows"], c["solved"], c["wrong"]) == (n, containers, variables, rows, solved, 0)
    assert (round(c["time"]["median"], 3), round(c["time"]["max"], 3)) == (tmed, tmax) and (round(c["search_ms"]["median"], 3), round(c["search_ms"]["max"], 3)) == (smed, smax)
    assert (c["lb"], c["opt"]) == (lb, opt)


@pytest.mark.parametrize("cell", list(LP))
def test_readme_lp_cell(cell):
    n, lp, opt, lb, gmed, gmax, equal = LP[cell]
    c = BANDS["lp"][ev.cell_key(*cell)]
    assert c["n"] == n and (round(c["lp"], 3), c["opt"], c["lb"], c["equal"]) == (lp, opt, lb, equal)
    assert (round(c["gap"]["median"], 3), round(c["gap"]["max"], 3)) == (gmed, gmax)


@pytest.mark.parametrize("cell", list(LPZEIT))
def test_readme_lp_time_cell(cell):
    n, lps, ilps, share, gmed, gmax = LPZEIT[cell]
    c = BANDS["lpzeit"][ev.cell_key(*cell)]
    assert c["n"] == n and (round(c["lp_s"]["sum"], 3), round(c["ilp_s"]["sum"], 3), round(c["share"], 3)) == (lps, ilps, share) and (round(c["gap"]["median"], 3), round(c["gap"]["max"], 3)) == (gmed, gmax)


@pytest.mark.parametrize("cell", list(LOESER))
def test_readme_solver_cell(cell):
    n, hmed, hsum, hok, cmed, csum, cok, speed = LOESER[cell]
    c = BANDS["loeser"][ev.cell_key(*cell)]
    assert c["n"] == n and (round(c["highs"]["median"], 3), round(c["highs"]["sum"], 3), c["highs"]["solved"]) == (hmed, hsum, hok)
    assert (round(c["cpsat"]["median"], 3), round(c["cpsat"]["sum"], 3), c["cpsat"]["solved"]) == (cmed, csum, cok) and round(c["speed"], 3) == speed


@pytest.mark.parametrize("cell", list(SUCHE))
def test_readme_search_cell(cell):
    n, containers, done, blockers, nmed, nmax, tmed, tmax = SUCHE[cell]
    c = BANDS["suche"][ev.cell_key(*cell)]
    assert (c["n"], c["containers"], c["done"], c["blockers"]) == (n, containers, done, blockers) and (c["nodes"]["median"], c["nodes"]["max"]) == (nmed, nmax)
    assert (round(c["time"]["median"], 3), round(c["time"]["max"], 3)) == (tmed, tmax)


@pytest.mark.parametrize("cell", list(KORREKTUR))
def test_readme_fix_cell(cell):
    n, infeasible, different, ok = KORREKTUR[cell]
    assert BANDS["korrektur"][ev.cell_key(*cell)] == {"n": n, "infeasible": infeasible, "different": different, "ok": ok}


def test_the_ilp_never_returns_a_wrong_value_and_is_correct_in_every_proved_run():
    assert sum(ZEIT[c][4] for c in ZEIT) == 20 + 20 + 20 + 12 + 11 + 10 + 7 + 5 == 105
    assert all(BANDS["zeit"][ev.cell_key(*c)]["wrong"] == 0 for c in ZEIT)


def test_the_model_grows_with_the_containers_and_the_search_is_far_faster_in_every_cell():
    by_n = sorted(ZEIT.items(), key=lambda kv: (kv[1][1], kv[1][2]))
    assert [v[2] for _, v in by_n][-2:] == [55104, 55500] or [v[2] for _, v in by_n][-2:] == [55500, 55104]
    for cell, v in ZEIT.items():
        assert v[7] / 1000 < v[5] / 10, cell                                      # das Maximum der Suche liegt unter einem Zehntel der mittleren ILP-Zeit
    assert 1692 < 6075 < 21360 < 55500 and ZEIT[(3, 2)][2] == 1692 and ZEIT[(5, 3)][2] == 55500


def test_the_ilp_median_time_grows_with_the_containers_and_the_tail_is_heavy():
    med = {c: v[5] for c, v in ZEIT.items()}
    assert med[(3, 2)] < med[(3, 3)] < med[(4, 3)] < med[(5, 3)] < med[(4, 4)]
    assert ZEIT[(4, 3)][6] > 40 * ZEIT[(4, 3)][5] and ZEIT[(5, 3)][6] > 5 * ZEIT[(5, 3)][5]            # das Maximum liegt weit über dem Median (Schwanz)
    assert [c for c, v in ZEIT.items() if v[4] < v[0]] == [(4, 3), (5, 3), (4, 4)]                       # nur diese Zellen haben Buchten ohne Beweis in 60 s
    assert [v[0] - v[4] for c, v in ZEIT.items() if v[4] < v[0]] == [1, 1, 1]


def test_the_lp_bound_is_good_in_the_median_and_the_root_lp_is_a_small_part_of_the_time():
    assert all(v[4] <= C.LP_TIGHT for c, v in LP.items() if c != (3, 4)) and LP[(3, 4)][4] == 1.0
    assert all(v[2] >= v[1] - 1.0 for v in LP.values())                           # LP-Wert im Median höchstens 1 unter dem Optimum
    assert [f"{v[1] / v[2] * 100:.0f}" for v in LPZEIT.values()] == ["28", "5", "6", "5", "5"] and min(v[3] for v in LPZEIT.values()) >= 0.04 and max(v[3] for v in LPZEIT.values()) <= 0.28


def test_cpsat_is_faster_than_highs_on_the_same_model_in_every_cell():
    assert all(v[7] > 1.0 for v in LOESER.values()) and round(min(v[7] for v in LOESER.values()), 1) == 1.8 and round(max(v[7] for v in LOESER.values()), 1) == 3.7
    assert [v[3] for v in LOESER.values()] == [10, 11, 10, 5] and [v[6] for v in LOESER.values()] == [10, 12, 10, 6]         # CP-SAT beweist alle, HiGHS in zwei Zellen eine Bucht nicht


def test_the_search_carries_to_32_containers_with_two_slow_cells():
    assert max(v[1] for v in SUCHE.values()) == 32 and max(v[4] for v in SUCHE.values()) == 65510
    assert [(c, v[0] - v[2]) for c, v in SUCHE.items() if v[2] < v[0]] == [((6, 4), 1), ((6, 5), 1)]
    assert max(v[7] for v in SUCHE.values()) <= 6.7 and max(v[3] for v in SUCHE.values()) == 17.0


def test_the_original_lifo_constraint_is_wrong_in_many_bays_but_not_in_the_small_cells():
    assert KORREKTUR[(3, 2)][1:3] == KORREKTUR[(4, 2)][1:3] == (0, 0) and KORREKTUR[(3, 3)][1] + KORREKTUR[(3, 3)][2] == 25 and KORREKTUR[(3, 4)][1] + KORREKTUR[(3, 4)][2] == 15


def test_the_cells_and_the_documented_cells_agree():
    assert [(s, l, n) for s, l, n in C.TIME_CELLS] == [(s, l, ZEIT[(s, l)][0]) for s, l, _ in C.TIME_CELLS]
    assert {(s, l) for s, l, _ in C.LP_CELLS} == set(LP) and {(s, l) for s, l, _ in C.LPTIME_CELLS} == set(LPZEIT) and {(s, l) for s, l, _ in C.SOLVER_CELLS} == set(LOESER)
    assert {(s, l) for s, l, _ in C.SEARCH_CELLS} == set(SUCHE) and {(s, l) for s, l, _ in C.FIX_CELLS} == set(KORREKTUR)
