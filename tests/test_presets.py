"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Eigenschaften der Sonderbuchten und der vorberechneten Tabellen."""

import ilm_algorithm as A
import ilm_constants as C
import ilm_evaluation as ev
import ilm_presets as P
from ilm_scenario import canonical, make_bay, max_height


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.STACKS_MIN <= preset["stacks"] <= C.STACKS_MAX and C.LAYERS_MIN <= preset["layers"] <= C.LAYERS_MAX
        assert C.EXTRA_MIN <= preset["extra"] <= C.EXTRA_MAX and 0 <= preset["seed"] <= C.SEED_MAX and C.LIMIT_MIN <= preset["limit"] <= C.LIMIT_MAX


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS[next(iter(C.PRESETS))]
    assert ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"], p["limit"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def _analysis(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"], p["limit"]))


def test_everyday_preset():
    a = _analysis("Alltag (3 Stapel, 3 Lagen)")
    assert a.size == (6075, 2652) and a.lower == 4 and a.optimum == 5 and a.search.nodes == 11
    assert a.ilp.status == "optimal" and a.ilp.optimum == 5 and abs(a.ilp.lp_value - 5.0) < 1e-6 and a.ilp.seconds_solve < 5


def test_mini_preset_is_the_stage_two_bay_with_1692_variables():
    p = C.PRESETS["Die Mini-Bucht"]
    assert canonical(make_bay(p["stacks"], p["layers"], p["seed"])) == canonical(C.MINI_BAY)
    a = _analysis("Die Mini-Bucht")
    assert a.size == (1692, 1020) and (a.lower, a.optimum, a.search.nodes) == (1, 2, 6) and a.ilp.optimum == 2


def test_slow_preset_the_ilp_needs_seconds_and_the_search_milliseconds():
    a = _analysis("Das ILP wird langsam (3 Stapel, 4 Lagen)")
    assert a.limit == 30 and a.size == (15660, 5379) and (a.lower, a.optimum) == (6, 13)
    assert a.ilp.status == "optimal" and a.ilp.optimum == 13 and a.ilp.seconds_solve > 0.5 and a.search_ms < 100                 # Sekunden gegen Millisekunden (grob, ohne feste Zeiten)


def test_giveup_preset_the_ilp_finds_no_proof_within_five_seconds():
    a = _analysis("Das ILP gibt auf (4 Stapel, 3 Lagen)")
    assert a.limit == 5 and a.size == (21360, 6622) and a.ilp.status == "time_limit" and a.ilp.optimum is None
    assert (a.lower, a.optimum, a.search.nodes) == (7, 10, 100) and a.ilp.best is None or a.ilp.best >= 10


def test_search_preset_does_not_build_the_model():
    a = _analysis("Die Suche trägt weiter (5 Stapel, 4 Lagen)")
    assert a.ilp is None and a.size == (143100, 26885) and (a.lower, a.optimum, a.search.nodes) == (8, 9, 31) and a.size[0] > C.LIVE_MAX_VARS


def test_the_named_seeds_are_the_documented_bays():
    assert (C.MINI_SEED, C.EVERYDAY_SEED, C.SLOW_SEED, C.GIVEUP_SEED, C.SEARCH_SEED) == (223, 12, 4, 0, 2)
    assert C.MINI_HEIGHT == C.FIX_HEIGHT == 4 and A.search(C.FIX_BAY, C.FIX_HEIGHT).optimum == 8


def test_stored_cells_equal_a_fresh_computation_where_the_time_does_not_matter():
    bands = ev.load_bands()
    for stacks, layers, n in ((3, 2, 20), (4, 2, 20)):
        key = ev.cell_key(stacks, layers)
        fresh = ev.time_stats(ev.time_rows(stacks, layers, C.DEFAULT_EXTRA, range(n), limit=30))
        stored = bands["zeit"][key]
        for field in ("n", "containers", "variables", "rows", "solved", "wrong", "lb", "opt"):
            assert fresh[field] == stored[field], (key, field)
    assert bands["lp"][ev.cell_key(3, 2)] == ev.lp_stats(ev.lp_rows(3, 2, C.DEFAULT_EXTRA, range(20)))
    assert bands["lp"][ev.cell_key(4, 2)] == ev.lp_stats(ev.lp_rows(4, 2, C.DEFAULT_EXTRA, range(20)))
    assert bands["suche"][ev.cell_key(6, 3)]["nodes"] == ev.search_stats(ev.search_rows(6, 3, C.DEFAULT_EXTRA, range(10)), 18)["nodes"]
    assert bands["suche"][ev.cell_key(6, 3)]["blockers"] == 6.0
    assert bands["korrektur"][ev.cell_key(3, 2)] == ev.fix_stats(ev.fix_rows(3, 2, C.DEFAULT_EXTRA, range(100)))
    assert bands["korrektur"][ev.cell_key(3, 3)] == ev.fix_stats(ev.fix_rows(3, 3, C.DEFAULT_EXTRA, range(100)))


def test_every_band_cell_exists_and_has_the_documented_bay_count():
    bands = ev.load_bands()
    for kind, cells in (("zeit", C.TIME_CELLS), ("lp", C.LP_CELLS), ("lpzeit", C.LPTIME_CELLS), ("loeser", C.SOLVER_CELLS), ("suche", C.SEARCH_CELLS), ("korrektur", C.FIX_CELLS)):
        assert set(bands[kind]) == {ev.cell_key(s, l) for s, l, _ in cells}, kind
        assert all(bands[kind][ev.cell_key(s, l)]["n"] == n for s, l, n in cells), kind


def test_the_model_sizes_in_the_bands_equal_the_formula():
    from ilm_model import model_size
    bands = ev.load_bands()
    for s, l, _ in C.TIME_CELLS:
        c = bands["zeit"][ev.cell_key(s, l)]
        assert (c["variables"], c["rows"]) == model_size(s, max_height(l, C.DEFAULT_EXTRA), s * l) and c["containers"] == s * l


def test_cell_rows_use_the_fixed_seeds():
    rows = ev.time_rows(3, 2, 2, range(6), limit=30)
    assert [r["seed"] for r in rows] == list(range(6))
    for r in rows:
        bay = make_bay(3, 2, r["seed"])
        assert r["lb"] == A.blocker_count(bay) and r["opt"] == A.search(bay, 4).optimum == r["ilp_opt"] and r["status"] == "optimal" and r["vars"] == 1692
    fixed = ev.fix_rows(3, 3, 2, [0, 1])
    assert [r["seed"] for r in fixed] == [0, 1]
    lp = ev.lp_rows(3, 2, 2, [0])[0]
    assert lp["lp"] <= lp["opt"] + 1e-6 and lp["lb"] == A.blocker_count(make_bay(3, 2, 0))
    s = ev.search_rows(3, 2, 2, [C.MINI_SEED], cap=1)[0]
    assert s["done"] is False and s["nodes"] == 1
    solver = ev.solver_rows(3, 2, 2, [0, 1], lambda bay, h, limit: (A.search(bay, h).optimum, 0.5))
    assert [(r["highs_ok"], r["cp_ok"], r["cp_s"]) for r in solver] == [(True, True, 0.5)] * 2
    lt = ev.lptime_rows(3, 2, 2, [0, 1])
    assert all(r["gap"] is not None and abs(r["gap"]) < 1e-6 and r["lp_s"] >= 0 for r in lt)
