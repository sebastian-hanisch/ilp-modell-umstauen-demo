"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import ilm_algorithm as A
import ilm_constants as C
import ilm_evaluation as ev
import ilm_model as M


def _ilp(status="optimal", seconds=0.5, optimum=5, best=None, variables=6075, rows=2652, lp=5.0):
    return M.IlpResult(optimum if status == "optimal" else None, status, optimum if status == "optimal" else best, 0.1, seconds, variables, rows, 52404, lp, 0.1, ())


def _a(ilp=None, ms=1.0, nodes=11, opt=5, capped=False, limit=15, size=(6075, 2652), lower=4):
    return ev.Analysis(((1,),), 5, 9, lower, size, limit, A.SearchResult(None if capped else opt, nodes, capped, 2), ms, ilp)


def test_bay_verdict_success_names_times_factor_and_model():
    kind, text = ev.verdict_bay(_a(_ilp(seconds=0.5), ms=1.0))
    assert kind == "success"                                           # Faktor 500
    assert ("Das ILP beweist das Optimum 5 in 0,50 s (Modell mit 6 075 Variablen), die Suche in 1,0 ms: das 500-Fache schneller (Untergrenze 4).") in text


def test_bay_verdict_thresholds_at_ten_and_one_hundred():
    assert ev.verdict_bay(_a(_ilp(seconds=0.1), ms=1.0))[0] == "success"          # genau das Hundertfache zählt
    kind, text = ev.verdict_bay(_a(_ilp(seconds=0.0999), ms=1.0))
    assert kind == "info" and not text.startswith("Die Bucht ist so klein")      # knapp unter 100: mäßig
    assert ev.verdict_bay(_a(_ilp(seconds=0.01), ms=1.0))[0] == "info" and not ev.verdict_bay(_a(_ilp(seconds=0.01), ms=1.0))[1].startswith("Die Bucht ist so klein")   # genau das Zehnfache
    kind, text = ev.verdict_bay(_a(_ilp(seconds=0.0099), ms=1.0))
    assert kind == "info" and text.startswith("Die Bucht ist so klein, dass beide schnell sind.")
    assert C.SPEED_STRONG == 100.0 and C.SPEED_WEAK == 10.0


def test_bay_verdict_when_the_ilp_hits_the_time_limit():
    kind, text = ev.verdict_bay(_a(_ilp("time_limit", seconds=7.07, best=None), ms=0.9, opt=10, nodes=100, limit=5, lower=7))
    assert kind == "warning" and text == ("Das ILP erreicht das Zeitlimit von 5 s ohne Optimalitätsbeweis (keine Lösung gefunden); die Suche beweist das Optimum 10 in 0,9 ms (Untergrenze 7).")
    kind, text = ev.verdict_bay(_a(_ilp("time_limit", best=12), opt=10))
    assert "(beste gefundene Lösung: 12 Hübe)" in text


def test_bay_verdict_when_the_model_is_too_big_and_when_everything_gives_up():
    kind, text = ev.verdict_bay(_a(None, ms=0.5, nodes=31, opt=9, size=(143100, 26885), lower=8))
    assert kind == "info" and text == ("Das Modell hätte 143 100 Variablen und 26 885 Zeilen (mehr als 60 000): Das ILP wird hier nicht gerechnet. "
                                       "Die Suche löst die Bucht mit 31 Knoten in 0,5 ms (Optimum 9, Untergrenze 8).")
    kind, text = ev.verdict_bay(_a(None, capped=True, nodes=1_000_000))
    assert kind == "warning" and "Auch die Suche gibt bei 1 000 000 Knoten auf" in text and "nicht gerechnet" in text
    kind, text = ev.verdict_bay(_a(_ilp("error"), opt=5))
    assert kind == "warning" and "Status „error“" in text


def test_result_rows_by_hand():
    rows = ev.result_rows(_a(_ilp(seconds=0.5), ms=1.0))
    assert rows[0] == {"name": "ILP (HiGHS, zeitindiziertes Modell)", "result": "5", "time": "0,50 s", "size": "6 075 Variablen, 2 652 Zeilen; LP-Wert 5"}
    assert rows[1] == {"name": "Suche (IDA* mit Untergrenze und Merken)", "result": "5", "time": "1,0 ms", "size": "11 Knoten in 2 Budgetstufen"}
    assert rows[2]["result"] == "4"
    assert ev.result_rows(_a(None))[0]["result"] == "nicht gerechnet"
    limited = ev.result_rows(_a(_ilp("time_limit", seconds=7.07, best=12), limit=5))[0]
    assert limited["result"] == "kein Beweis (beste Lösung 12)" and limited["time"] == "7,07 s (Limit 5 s)"
    assert ev.result_rows(_a(_ilp("time_limit", best=None)))[0]["result"] == "kein Beweis"
    assert ev.result_rows(_a(None, capped=True, nodes=1_000_000))[1]["result"] == "nicht bewiesen"


def test_move_rows_by_hand():
    r = M.IlpResult(2, "optimal", 2, 0, 0, 1692, 1020, 0, None, None, ((1, 4, 0, 1, 1, 2), (2, 4, 1, 2, 0, 0)))
    assert ev.move_rows(r) == [{"period": 1, "container": 4, "from": "Stapel 1, Lage 2", "to": "Stapel 2, Lage 3"}, {"period": 2, "container": 4, "from": "Stapel 2, Lage 3", "to": "Stapel 1, Lage 1"}]
    assert ev.move_rows(M.IlpResult(None, "time_limit", None, 0, 0, 0, 0, 0, None, None, None)) == []


def _tstats(solved=20, n=20, wrong=0, tmed=0.5, tmax=2.6, smed=0.3, smax=1.0, containers=9, variables=6075):
    st = lambda med, mx: {"n": n, "median": med, "mean": med, "min": med, "max": mx}
    return {"n": n, "containers": containers, "variables": variables, "rows": 2652, "solved": solved, "wrong": wrong, "time": st(tmed, tmax), "solved_time": st(tmed, tmax),
            "search_ms": st(smed, smax), "build": st(0.1, 0.1), "lb": 3.5, "opt": 5}


def test_break_verdict_three_states_and_numbers():
    kind, text = ev.verdict_break(_tstats(), "3 × 3")
    assert kind == "info"
    assert ("3 × 3 (9 Container, 6 075 Variablen): Das ILP beweist 20 von 20 Buchten innerhalb von 60 s (Zeit im Median 0,50 s, Maximum 2,60 s); "
            "die Suche braucht im Median 0,3 ms, höchstens 1,0 ms.") == text
    kind, text = ev.verdict_break(_tstats(solved=11, n=12, containers=12, variables=21360, tmed=1.33, tmax=61.91), "4 × 3")
    assert kind == "warning" and "beweist 11 von 12 Buchten" in text and text.endswith("1 Buchten sind nicht fertig.")
    kind, text = ev.verdict_break(_tstats(wrong=2), "x")
    assert kind == "warning" and "2 bewiesene Werte weichen von der Suche ab." in text


def _lp(lp=5.0, opt=5.0, lb=3.5, gap=0.0, gmax=1.0, equal=18, n=20):
    return {"n": n, "lp": lp, "opt": opt, "lb": lb, "lp_opt": 1.0, "gap": {"median": gap, "max": gmax}, "equal": equal}


def test_lp_verdict_two_states_and_numbers():
    kind, text = ev.verdict_lp(_lp(), "3 × 3")
    assert kind == "info" and text == ("3 × 3: LP-Wert im Median 5, Optimum 5, Untergrenze 3,5; Optimum minus LP-Wert im Median 0, höchstens 1 (18 von 20 Buchten mit LP-Wert gleich Optimum). "
                                       "Die LP-Schranke ist hier gut: Das Problem des ILP ist nicht die Schranke.")
    assert "gut" in ev.verdict_lp(_lp(gap=0.5), "x")[1] and "lässt hier eine Lücke" in ev.verdict_lp(_lp(gap=0.51), "x")[1]
    assert C.LP_TIGHT == 0.5


def test_lptime_solvers_search_and_fix_verdicts():
    lt = {"n": 8, "lp_s": {"median": 0.4, "sum": 3.3}, "ilp_s": {"median": 1.6, "sum": 66.3}, "share": 3.3 / 66.3, "gap": {"median": 0.0, "max": 1.0}}
    assert ev.verdict_lptime(lt, "4 × 3")[1] == "4 × 3: Das Wurzel-LP kostet 5 % der ILP-Zeit (Summe 3,30 s von 66,3 s); der Rest ist Verzweigung."
    sv = {"n": 12, "highs": {"median": 1.05, "sum": 69.0, "solved": 12}, "cpsat": {"median": 0.59, "sum": 23.0, "solved": 12}, "speed": 3.0}
    assert ev.verdict_solvers(sv, "4 × 3")[1] == ("4 × 3: HiGHS Median 1,05 s (Summe 69,0 s, 12 von 12 richtig), CP-SAT Median 0,59 s (Summe 23,0 s, 12 von 12 richtig): CP-SAT ist insgesamt das 3,0-Fache schneller.")
    se = {"n": 10, "containers": 24, "done": 9, "blockers": 11.5, "nodes": {"median": 2228, "max": 72284}, "time": {"median": 0.07, "max": 26.2}}
    kind, text = ev.verdict_search(se, "6 × 4")
    assert kind == "warning" and text == ("6 × 4 (24 Container, 11,5 Blocker im Median): 9 von 10 Buchten unter 1 000 000 Knoten, Knoten im Median 2 228, höchstens 72 284; "
                                          "Zeit im Median 70 ms, höchstens 26,2 s.")
    assert ev.verdict_search({**se, "done": 10}, "x")[0] == "info"
    kind, text = ev.verdict_fix({"n": 60, "infeasible": 6, "different": 7, "ok": 47}, "3 × 3")
    assert kind == "warning" and text == ("3 × 3: Mit der Originalfassung (6) sind 6 von 60 Buchten unlösbar und 7 haben einen anderen Wert als die Suche; mit der Korrektur (9) stimmen alle.")
    kind, text = ev.verdict_fix({"n": 100, "infeasible": 0, "different": 0, "ok": 100}, "3 × 2")
    assert kind == "info" and text == "3 × 2: Hier macht die Korrektur (9) keinen Unterschied: In allen 100 Buchten stimmt auch die Originalfassung (6)."


def test_lp_gap_search_and_fix_stats_by_hand():
    rows = [{"seed": 0, "lb": 4, "opt": 5, "lp": 5.0}, {"seed": 1, "lb": 3, "opt": 6, "lp": 4.5}, {"seed": 2, "lb": 6, "opt": 8, "lp": 7.0}]
    st = ev.lp_stats(rows)
    assert st["lp"] == 5.0 and st["opt"] == 6 and st["lb"] == 4 and st["equal"] == 1 and st["gap"] == {"median": 1.0, "max": 1.5} and round(st["lp_opt"], 3) == 0.875
    f = ev.fix_stats([{"seed": 0, "status": "infeasible", "same": False}, {"seed": 1, "status": "optimal", "same": False}, {"seed": 2, "status": "optimal", "same": True}])
    assert f == {"n": 3, "infeasible": 1, "different": 1, "ok": 1}
    s = ev.solver_stats([{"seed": 0, "highs_s": 2.0, "highs_ok": True, "cp_s": 1.0, "cp_ok": True}, {"seed": 1, "highs_s": 4.0, "highs_ok": True, "cp_s": 1.0, "cp_ok": False}])
    assert s["speed"] == 3.0 and s["highs"]["solved"] == 2 and s["cpsat"]["solved"] == 1 and s["highs"]["median"] == 3.0
    t = ev.lptime_stats([{"seed": 0, "lp_s": 1.0, "ilp_s": 4.0, "gap": 0.0}, {"seed": 1, "lp_s": 1.0, "ilp_s": 6.0, "gap": None}])
    assert t["share"] == 0.2 and t["gap"] == {"median": 0.0, "max": 0.0}
