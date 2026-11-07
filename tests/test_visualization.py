"""Abbildungen: Farben je Rolle des Containers, feste Achsen, logarithmische Achsen, Zahlen der Kurven."""

import ilm_algorithm as A
import ilm_constants as C
import ilm_visualization as V


def _cell_colors(fig):
    out = {}
    for tr in fig.data:
        for txt, color in zip(tr.text, tr.marker.color):
            if txt:
                out[int(txt)] = color
    return out


def test_bay_colours_by_role(mini):
    bay, h = mini
    cols = _cell_colors(V.build_bay(bay, h, target=1))
    assert cols[1] == C.COLOR_TARGET and cols[4] == C.COLOR_BLOCK and cols[5] == cols[2] == cols[6] == cols[3] == C.COLOR_CELL
    assert sorted(_cell_colors(V.build_bay(bay, h))) == [1, 2, 3, 4, 5, 6] and len(V.build_bay(bay, h).data) == h


def test_blocker_cells_agree_with_the_kernel():
    from ilm_scenario import make_bay
    assert V.blocker_cells(((1, 4), (5, 2), (6, 3))) == {(0, 1)}
    for sd in range(20):
        bay = make_bay(4, 3, sd)
        assert len(V.blocker_cells(bay)) == A.blocker_count(bay)


def _t(containers, variables, med=1.0, mx=2.0, smed=0.5):
    return {"containers": containers, "variables": variables, "rows": variables // 3, "time": {"median": med, "max": mx}, "search_ms": {"median": smed}}


def test_times_figure_marks_the_limit_and_uses_a_log_axis():
    rows = [{"name": "ILP (HiGHS)", "ms": 7070.0, "limit": True, "color": C.COLOR_ILP, "text": "7,07 s (Limit)"},
            {"name": "Suche (IDA* + Merken)", "ms": 0.9, "limit": False, "color": C.COLOR_SEARCH, "text": "0,9 ms"}]
    fig = V.build_times(rows)
    assert fig.layout.yaxis.type == "log" and list(fig.data[0].y) == [7070.0, 0.9] and list(fig.data[0].text) == ["7,07 s (Limit)", "0,9 ms"]
    assert list(fig.data[0].marker.color) == [C.COLOR_LIMIT, C.COLOR_SEARCH]
    assert list(V.build_times([{"name": "x", "ms": 0.0, "limit": False, "color": "#000", "text": "0"}]).data[0].y) == [0.01]           # null Millisekunden würden auf der Log-Achse fehlen


def test_size_figure_orders_cells_by_containers_and_has_two_series():
    cells = {"4 × 3": _t(12, 21360), "3 × 2": _t(6, 1692), "3 × 4": _t(12, 15660)}
    fig = V.build_size(cells)
    assert [t.name for t in fig.data] == ["Variablen", "Zeilen"] and fig.layout.yaxis.type == "log"
    assert list(fig.data[0].x) == ["3 × 2 (6)", "3 × 4 (12)", "4 × 3 (12)"] and list(fig.data[0].y) == [1692, 15660, 21360]


def test_break_figure_has_three_curves_and_the_limit_curve():
    cells = {"3 × 2": _t(6, 1692, 0.05, 0.11, 0.2), "4 × 4": _t(16, 55104, 56.0, 63.8, 16.2)}
    fig = V.build_break(cells, 60.0)
    assert [t.name for t in fig.data] == ["ILP, Median", "ILP, Maximum", "Suche, Median", "Zeitlimit"] and fig.layout.yaxis.type == "log"
    assert list(fig.data[2].y) == [0.0002, 0.0162]                                              # Millisekunden in Sekunden umgerechnet
    assert list(fig.data[3].y) == [60.0, 60.0] and list(fig.data[3].x) == ["3 × 2 (6)", "4 × 4 (16)"] and fig.data[3].line.dash == "dash"
    assert len(fig.layout.shapes) == 0                                                           # keine Form: auf einer Log-Achse würde Plotly y als Exponenten lesen


def test_lp_figure_has_three_series():
    cells = {"3 × 3": {"lb": 3.5, "lp": 5.0, "opt": 5.0}, "3 × 4": {"lb": 6.0, "lp": 8.5, "opt": 9.5}}
    fig = V.build_lp(cells)
    assert [t.name for t in fig.data] == ["Untergrenze (Stück 2)", "LP-Relaxation des ILP", "Optimum"] and list(fig.data[1].y) == [5.0, 8.5]


def test_solver_figure_uses_the_sums_on_a_log_axis():
    cells = {"4 × 3": {"highs": {"sum": 69.0}, "cpsat": {"sum": 23.0}}}
    fig = V.build_solvers(cells)
    assert [t.name for t in fig.data] == ["HiGHS", "CP-SAT"] and list(fig.data[0].y) == [69.0] and list(fig.data[1].y) == [23.0] and fig.layout.yaxis.type == "log"


def test_search_figure_skips_cells_without_a_finished_run_and_sorts_by_containers():
    cells = {"8 × 4": {"containers": 32, "nodes": {"median": 658, "max": 151730}}, "4 × 4": {"containers": 16, "nodes": {"median": 251, "max": 2299}},
             "x": {"containers": 40, "nodes": {"median": None, "max": None}}}
    fig = V.build_search(cells)
    assert list(fig.data[0].x) == ["4 × 4 (16)", "8 × 4 (32)"] and list(fig.data[1].y) == [2299, 151730] and fig.layout.yaxis.type == "log"


def test_axes_are_locked_in_every_figure(mini):
    bay, h = mini
    figs = [V.build_bay(bay, h), V.build_times([{"name": "x", "ms": 1.0, "limit": False, "color": "#000", "text": "1"}]), V.build_size({"a": _t(6, 100)}), V.build_break({"a": _t(6, 100)}, 60.0),
            V.build_lp({"a": {"lb": 1, "lp": 1, "opt": 1}}), V.build_solvers({"a": {"highs": {"sum": 1.0}, "cpsat": {"sum": 1.0}}}),
            V.build_search({"a": {"containers": 6, "nodes": {"median": 3, "max": 4}}})]
    for fig in figs:
        assert fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True
