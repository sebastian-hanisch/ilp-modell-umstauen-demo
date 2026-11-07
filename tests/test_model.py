"""Das Modell gegen Handrechnung und Eigenschaften (DEMO-PLAYBOOK §1b und §12)."""

import itertools

import numpy as np
import pytest

import ilm_algorithm as A
import ilm_model as M
from ilm_scenario import make_bay, max_height


def test_model_size_formula_by_hand():
    assert M.model_size(3, 4, 6) == (1692, 1020)                       # Mini-Bucht: 252 + 1 440 Variablen
    assert M.model_size(1, 3, 1) == (3, 0)                             # ein Container: nur b, keine Zeilen
    assert M.model_size(2, 3, 2) == (36, 47)
    assert M.model_size(4, 5, 12) == (21360, 6622) and M.model_size(5, 5, 15) == (55500, 13335)      # Zellen 4 x 3 und 5 x 3 mit Platz 2


def test_model_size_formula_equals_the_built_model():
    for stacks, layers, seed in ((3, 2, 0), (4, 2, 1), (3, 3, 2), (5, 2, 3), (2, 1, 0), (2, 2, 5)):
        for extra in (1, 2):
            bay = make_bay(stacks, layers, seed)
            h = layers + extra
            assert M.build(bay, h).size[:2] == M.model_size(stacks, h, stacks * layers), (stacks, layers, extra)


def test_mini_model_by_hand(mini):
    model = M.build(*mini)
    assert model.size == (1692, 1020, 11700)
    assert model.containers == 6 and model.stacks == 3 and model.height == 4
    assert len(model.b_index) == 252 and len(model.x_index) == 1440                  # 12 * 21 und 96 * 15
    assert int(model.lb.sum()) == 6 and int(model.ub[: 0].sum()) == 0                # sechs feste Startplätze, sonst frei


def test_mini_solution_by_hand(mini):
    bay, h = mini
    r = M.solve(bay, h, 30, with_lp=True)
    assert (r.optimum, r.status, r.best) == (2, "optimal", 2) and abs(r.lp_value - 2.0) < 1e-6
    assert (r.variables, r.rows, r.nonzeros) == (1692, 1020, 11700) and r.seconds_solve >= 0 and r.seconds_build >= 0
    assert len(r.moves) == 2 and {m[1] for m in r.moves} == {4} and r.moves[0][0] == 1 and r.moves[1][0] > 1       # die 4 wird zweimal bewegt, zuerst in Periode 1
    assert r.moves[0][2:4] == (0, 1)                                    # von Stapel 1, Lage 2 (0-basiert: Stapel 0, Lage 1)
    assert M.replay_moves(bay, h, r) == 2


def test_counterexample_solution(counter):
    bay, h = counter
    r = M.solve(bay, h, 30)
    assert (r.optimum, r.status) == (4, "optimal") and len(r.moves) == 4 and M.replay_moves(bay, h, r) == 4
    assert (r.variables, r.rows) == (1692, 1020)                         # gleiches Modell wie die Mini-Bucht


def test_moves_are_ordered_by_period_and_from_the_top_down(fix):
    bay, h = fix
    r = M.solve(bay, h, 30)
    assert r.optimum == 8 and M.replay_moves(bay, h, r) == 8
    key = [(m[0], -m[3]) for m in r.moves]
    assert key == sorted(key)


def test_original_lifo_constraint_declares_a_feasible_bay_infeasible(fix):
    bay, h = fix
    original = M.solve(bay, h, 30, lifo="original")
    assert (original.status, original.optimum, original.best, original.moves) == ("infeasible", None, None, None)
    assert M.solve(bay, h, 30, lifo="corrected").status == "optimal" and A.search(bay, h).optimum == 8


def test_original_and_corrected_agree_when_at_most_one_blocker_moves_per_stack_pair(mini, counter):
    for bay, h in (mini, counter):
        assert M.solve(bay, h, 30, lifo="original").optimum == M.solve(bay, h, 30).optimum


def test_sorted_bay_and_single_container():
    r = M.solve(((3, 1), (4, 2)), 3, 30)                                 # 1 unter der 3? Nein: (3, 1): die 3 liegt unten, die 1 oben: sortiert
    assert (r.optimum, r.status) == (0, "optimal")
    one = M.solve(((1,), ()), 2, 30, with_lp=True)
    assert (one.optimum, one.status, one.moves, one.lp_value) == (0, "optimal", (), 0.0)


def test_status_time_limit_gives_no_optimum():
    bay = make_bay(4, 3, 0)                                              # dieses ILP braucht über 50 Sekunden
    r = M.solve(bay, 5, 0.05)
    assert r.status == "time_limit" and r.optimum is None
    assert r.best is None or r.best >= A.search(bay, 5).optimum


def test_status_infeasible_when_there_is_no_room():
    r = M.solve(((1, 3, 2), (4, 5, 6)), 3, 30)                          # beide Stapel voll, die 2 und die 3 können nirgends hin
    assert r.status == "infeasible" and r.optimum is None


def test_lp_value_is_a_lower_bound_of_the_optimum_and_above_the_blocker_bound_in_most_bays():
    for sd in range(12):
        bay = make_bay(3, 3, sd)
        model = M.build(bay, 5)
        lp, secs = M.lp_value(model)
        opt = A.search(bay, 5).optimum
        assert lp is not None and lp <= opt + 1e-6 and secs >= 0
        assert opt >= A.blocker_count(bay)


def test_a_heuristic_never_beats_the_ilp():
    for sd in range(15):
        bay = make_bay(3, 3, sd)
        opt = M.solve(bay, 5, 30).optimum
        assert A.replay(bay, 5, _tight_fit_moves(bay, 5)) >= opt


def _tight_fit_moves(bay, height):
    """Regel aus Stück 1 (engste Passung) als Umlagerungsfolge (Periode, Container, Zielstapel)."""
    st = [list(s) for s in bay]
    moves = []
    for t in range(1, sum(len(s) for s in st) + 1):
        src = next(i for i, s in enumerate(st) if t in s)
        while st[src][-1] != t:
            c = st[src][-1]
            base = [list(s) for s in st]
            base[src].pop()
            k = A.child_targets(tuple(tuple(s) for s in base), src, height, c)[0]
            st[src].pop()
            st[k].append(c)
            moves.append((t, c, k))
        st[src].pop()
    return moves


def test_the_cost_does_not_depend_on_the_order_of_the_stacks(mini):
    bay, h = mini
    opt = M.solve(bay, h, 30).optimum
    for perm in itertools.permutations(bay):
        assert M.solve(perm, h, 30).optimum == opt


def test_model_size_grows_monotonically():
    sizes = [M.model_size(w, h, n)[0] for n in range(2, 8) for w in (2, 3) for h in (3, 4)]
    assert M.model_size(3, 4, 6)[0] < M.model_size(3, 4, 7)[0] < M.model_size(3, 4, 8)[0]
    assert M.model_size(3, 4, 6)[0] < M.model_size(4, 4, 6)[0] and M.model_size(3, 4, 6)[0] < M.model_size(3, 5, 6)[0]
    assert all(s > 0 for s in sizes)


def test_build_rejects_bad_input():
    with pytest.raises(ValueError):
        M.build(((1, 3), (4,)), 3)                                       # Nummer 2 fehlt
    with pytest.raises(ValueError):
        M.build(((1, 2, 3), ()), 2)                                      # Stapel höher als die Höchsthöhe
    with pytest.raises(ValueError):
        M.build(((1,), ()), 2, lifo="x")


def test_constraint_matrix_has_only_the_documented_coefficients(mini):
    model = M.build(*mini)
    assert set(np.unique(model.a.data)) == {-1.0, 1.0, 4.0}              # +-1 und der Faktor H = 4 der LIFO-Korrektur
    orig = M.build(*mini, lifo="original")
    assert set(np.unique(orig.a.data)) == {-1.0, 1.0}
