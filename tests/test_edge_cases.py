"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12)."""

import ilm_algorithm as A
import ilm_constants as C
import ilm_evaluation as ev
import ilm_model as M


def test_two_stacks_one_hub():
    r = M.solve(((1, 2), ()), 3, 30)
    assert (r.optimum, r.status, len(r.moves)) == (1, "optimal", 1) and A.search(((1, 2), ()), 3).optimum == 1
    assert M.replay_moves(((1, 2), ()), 3, r) == 1


def test_exactly_two_containers_in_each_order():
    assert M.solve(((2,), (1,)), 2, 30).optimum == 0
    assert M.solve(((2, 1),), 2, 30).optimum == 0                       # ein Stapel: die 2 liegt unten, die 1 oben: sortiert
    assert M.solve(((1, 2), ()), 2, 30).optimum == 1


def test_a_stack_without_containers_and_unequal_heights():
    bay = ((1, 5, 4), (2,), (3, 6), ())                                   # teilgefüllte Bucht mit einem leeren Stapel
    r = M.solve(bay, 4, 30)
    assert r.status == "optimal" and M.replay_moves(bay, 4, r) == r.optimum == A.search(bay, 4).optimum


def test_only_one_free_slot_per_stack():
    bay = ((1, 5), (2, 3), (4, 6))                                        # Höchsthöhe 3: jeder Blocker findet höchstens einen freien Platz
    r = M.solve(bay, 3, 30)
    assert r.optimum == A.search(bay, 3).optimum and M.replay_moves(bay, 3, r) == r.optimum


def test_time_limit_budget_is_respected_loosely_and_never_claims_an_optimum():
    r = M.solve(((1, 6, 7, 8), (2, 3), (4, 5)), 4, 0.001)
    assert r.status in ("time_limit", "optimal")
    assert (r.status == "time_limit") == (r.optimum is None)


def test_analysis_without_the_ilp_when_the_model_is_too_big():
    a = ev.analyse(ev.Settings(5, 4, 2, 2, 5))
    assert a.ilp is None and a.size == (143100, 26885) and a.search.optimum == 9 and a.containers == 20 and a.optimum == 9


def test_analysis_with_the_ilp_checks_both_optima():
    a = ev.analyse(ev.Settings(3, 2, 2, C.MINI_SEED, 5))
    assert a.ilp.status == "optimal" and a.ilp.optimum == a.search.optimum == a.optimum == 2 and a.size == (1692, 1020)
    assert ev.analyse(ev.Settings(3, 3, 2, 12, 5), max_vars=1000).ilp is None                 # eigenes Limit der Live-Rechnung


def test_number_formats():
    assert ev.num(5) == "5" and ev.num(1234) == "1 234" and ev.num(143100) == "143 100"
    assert ev.sec_text(0.03) == "0,03" and ev.sec_text(9.994) == "9,99" and ev.sec_text(10.04) == "10,0" and ev.sec_text(55.56) == "55,6"
    assert ev.ms_text(0.25) == "0,2" and ev.ms_text(9.94) == "9,9" and ev.ms_text(12.4) == "12" and ev.ms_text(1234.5) == "1 234"
    assert ev.factor_text(1.0) == "1,0" and ev.factor_text(9.94) == "9,9" and ev.factor_text(10.0) == "10" and ev.factor_text(1234.0) == "1 234" and ev.ratio_text(0.714) == "0,71"
    assert ev.num_f(5.0) == "5" and ev.num_f(71.5) == "71,5" and ev.num_f(1234.0) == "1 234" and ev.num_f(0.9999999999999987) == "1" and ev.num_f(5.499999999999999) == "5,5"
    assert ev.dur_text(0.0007) == "0,7 ms" and ev.dur_text(0.07) == "70 ms" and ev.dur_text(0.999) == "999 ms" and ev.dur_text(1.0) == "1,00 s" and ev.dur_text(26.2) == "26,2 s"


def test_stats_with_nothing_solved_or_finished():
    rows = [{"seed": 0, "lb": 5, "opt": 8, "nodes": 10, "search_ms": 2.0, "status": "time_limit", "ilp_s": 60.0, "build_s": 0.5, "ilp_opt": None, "vars": 100, "nrows": 50, "containers": 12}]
    st = ev.time_stats(rows)
    assert st["solved"] == 0 and st["wrong"] == 0 and st["solved_time"]["median"] is None and st["time"]["median"] == 60.0 and st["variables"] == 100
    assert ev.search_stats([{"seed": 0, "lb": 9, "nodes": 1_000_000, "seconds": 20.0, "done": False}], 30)["nodes"]["median"] is None
    assert ev.verdict_search(ev.search_stats([{"seed": 0, "lb": 9, "nodes": 1_000_000, "seconds": 20.0, "done": False}], 30), "x")[0] == "warning"
