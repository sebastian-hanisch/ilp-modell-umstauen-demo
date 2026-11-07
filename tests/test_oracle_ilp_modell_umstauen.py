"""Orakel-Test ilp-modell-umstauen-demo (ORACLE-PLAYBOOK, DEMO-PLAYBOOK §12): ILP-Optimum, Lösungen und Zertifikat gegen ANDERE Rechenwege.

Orakel 1: Breitensuche über alle Buchtzustände (restricted) liefert das Optimum; das ILP muss es treffen (3 x 2 vollständig, 4 x 2, 3 x 3).
Orakel 2: Jede ILP-Lösung wird mit einem **eigenen Simulator** (nicht dem des Kerns) nach den Regeln nachgespielt: nur Blocker, LIFO-Reihenfolge, Platz, Hubzahl = Zielwert.
Orakel 3: **Zertifikat**: die optimale Hubfolge der Breitensuche wird in Variablen des ILP übersetzt und erfüllt jede Nebenbedingung mit dem Zielwert des Optimums (und verletzt
          bei der Originalfassung (6) die LIFO-Nebenbedingung, wenn drei Blocker auf zwei Stapel müssen).
Orakel 4: Die Originalfassung (6) der LIFO-Nebenbedingung liefert auf 3 x 3 falsche Optima (die Korrektur ist nötig).
Vorher an den Handzahlen geprüft: Mini-Bucht 1 692 Variablen und Optimum 2, Gegenbeispiel Optimum 4."""

from itertools import permutations

import numpy as np

import ilm_algorithm as A
import ilm_model as M
from ilm_scenario import canonical, make_bay, max_height

INF = 10 ** 9


def _pop(st):
    st = [list(s) for s in st]
    while True:
        items = [c for s in st for c in s]
        if not items:
            return tuple(tuple(s) for s in st)
        t = min(items)
        hit = [s for s in st if s and s[-1] == t]
        if not hit:
            return tuple(tuple(s) for s in st)
        hit[0].pop()


def own_children(state, height):
    """(Zielstapel, Bucht nach dem Hub) für alle Zielstapel in Stapelreihenfolge."""
    items = [c for s in state for c in s]
    t = min(items)
    src = next(i for i, s in enumerate(state) if t in s)
    c = state[src][-1]
    out = []
    for dst in range(len(state)):
        if dst == src or len(state[dst]) >= height:
            continue
        nxt = [list(s) for s in state]
        nxt[src].pop()
        nxt[dst].append(c)
        out.append((c, dst, tuple(tuple(s) for s in nxt)))
    return out


def bfs_sequence(bay, height):
    """Kürzeste Hubfolge [(Container, Zielstapel)] per Breitensuche mit Elternzeigern (eigener Rechenweg)."""
    start = _pop(bay)
    if not any(start):
        return []
    parent = {start: None}
    frontier = [start]
    while frontier:
        nxt = []
        for state in frontier:
            for c, dst, child in own_children(state, height):
                new = _pop(child)
                if new in parent:
                    continue
                parent[new] = (state, (c, dst))
                if not any(new):
                    seq, cur = [], new
                    while parent[cur] is not None:
                        cur, mv = parent[cur][0], parent[cur][1]
                        seq.append(mv)
                    return seq[::-1]
                nxt.append(new)
        frontier = nxt
    raise AssertionError("keine Lösung")


def own_replay(bay, height, moves):
    """Eigener Simulator: moves = [(Periode, Container, Zielstapel)] in Ausführungsreihenfolge. Gibt die Hubzahl zurück, wirft AssertionError bei Regelverstoß."""
    st = [list(s) for s in bay]
    n = sum(len(s) for s in st)
    todo = list(moves)
    hubs = 0
    for t in range(1, n + 1):
        src = next(i for i, s in enumerate(st) if t in s)
        pos_t = st[src].index(t)
        while todo and todo[0][0] == t:
            _, c, k = todo.pop(0)
            assert st[src][-1] == c and st[src].index(c) > pos_t, "nur der oberste Container über dem Ziel darf bewegt werden"
            assert k != src and len(st[k]) < height, "Zielstapel ungültig oder voll"
            st[k].append(st[src].pop())
            hubs += 1
        assert st[src][-1] == t, "das Ziel liegt nicht oben"
        st[src].pop()
    assert not todo and not any(st)
    return hubs


def certificate_vector(model, bay, height, hubs):
    """Übersetzt eine Hubfolge [(Container, Zielstapel)] in einen Wertevektor des Modells (b und x)."""
    v = np.zeros(len(model.c))
    st = [list(s) for s in bay]
    n = sum(len(s) for s in st)
    todo = list(hubs)
    for t in range(1, n + 1):
        for i, s in enumerate(st):
            for j, c in enumerate(s):
                if c >= t:
                    v[model.b_index[(i, j, c, t)]] = 1.0
        src = next(i for i, s in enumerate(st) if t in s)
        while st[src][-1] != t:
            c, k = todo.pop(0)
            assert st[src][-1] == c
            i, j, l = src, len(st[src]) - 1, len(st[k])
            v[model.x_index[(i, j, k, l, c, t)]] = 1.0
            st[k].append(st[src].pop())
        st[src].pop()
    assert not todo
    return v


def all_bays_3x2():
    seen = {}
    for perm in permutations(range(1, 7)):
        bay = tuple(tuple(perm[i * 2:(i + 1) * 2]) for i in range(3))
        seen.setdefault(canonical(bay), bay)
    return list(seen.values())


def test_oracle_on_the_hand_numbers(mini, counter, fix):
    assert len(bfs_sequence(*mini)) == 2 and len(bfs_sequence(*counter)) == 4 and len(bfs_sequence(*fix)) == 8
    assert M.solve(*mini, 30).optimum == 2 and M.solve(*counter, 30).optimum == 4 and M.solve(*fix, 30).optimum == 8


def test_ilp_optimum_equals_the_breadth_first_search_and_the_solution_replays_with_an_own_simulator():
    checked = 0
    for stacks, layers, seeds in ((3, 2, 0), (4, 2, 60), (3, 3, 40)):
        h = max_height(layers, 2)
        bays = all_bays_3x2() if (stacks, layers) == (3, 2) else [make_bay(stacks, layers, sd) for sd in range(seeds)]
        for bay in bays:
            r = M.solve(bay, h, 120)
            opt = len(bfs_sequence(bay, h))
            assert r.status == "optimal" and r.optimum == opt, (stacks, layers, bay)
            assert own_replay(bay, h, [(t, n, k) for (t, n, _i, _j, k, _l) in r.moves]) == opt
            assert M.replay_moves(bay, h, r) == opt                                 # und der Simulator des Kerns stimmt zu
            checked += 1
    assert checked > 150


def test_the_optimal_sequence_of_the_breadth_first_search_is_a_feasible_point_of_the_model():
    for stacks, layers, seeds in ((3, 2, 40), (3, 3, 20)):
        h = max_height(layers, 2)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            model = M.build(bay, h)
            hubs = bfs_sequence(bay, h)
            v = certificate_vector(model, bay, h, hubs)
            act = model.a @ v
            assert np.all(v >= model.lb - 1e-9) and np.all(v <= model.ub + 1e-9), (stacks, layers, sd)
            assert np.all(act >= model.lo - 1e-9) and np.all(act <= model.hi + 1e-9), (stacks, layers, sd)
            assert round(model.c @ v) == len(hubs)


def test_a_sequence_that_breaks_a_rule_is_not_a_feasible_point():
    bay, h = ((1, 4), (5, 2), (6, 3)), 4
    model = M.build(bay, h)
    v = certificate_vector(model, bay, h, bfs_sequence(bay, h))
    assert np.all(model.a @ v <= model.hi + 1e-9)
    # die 4 schwebt: ein Container wird aus dem Layout genommen, ohne dass er umgelagert wurde
    broken = v.copy()
    for (i, j, k, l, n, t), idx in model.x_index.items():
        if broken[idx] > 0.5:
            broken[idx] = 0.0
            break
    act = model.a @ broken
    assert np.any(act < model.lo - 1e-9) or np.any(act > model.hi + 1e-9)


def test_the_original_lifo_constraint_rejects_the_certificate_of_a_three_blocker_bay(fix):
    bay, h = fix
    hubs = bfs_sequence(bay, h)
    corrected, original = M.build(bay, h), M.build(bay, h, lifo="original")
    v = certificate_vector(corrected, bay, h, hubs)
    assert np.all(corrected.a @ v <= corrected.hi + 1e-9) and np.all(corrected.a @ v >= corrected.lo - 1e-9)
    vo = certificate_vector(original, bay, h, hubs)
    act = original.a @ vo
    assert np.any(act > original.hi + 1e-9) or np.any(act < original.lo - 1e-9)       # die Originalfassung lässt die bekannte Lösung nicht zu


def test_the_original_lifo_constraint_gives_wrong_results_on_3x3_bays():
    infeasible = different = 0
    for sd in range(60):
        bay = make_bay(3, 3, sd)
        ref = len(bfs_sequence(bay, 5))
        r = M.solve(bay, 5, 60, lifo="original")
        if r.status == "infeasible":
            infeasible += 1
        elif r.optimum != ref:
            different += 1
    assert (infeasible, different) == (6, 7)                                            # 13 von 60 Buchten mit falschem Ergebnis
    for sd in range(40):                                                                # auf 3 x 2 und 4 x 2 macht die Korrektur keinen Unterschied
        for stacks in (3, 4):
            bay = make_bay(stacks, 2, sd)
            assert M.solve(bay, 4, 60, lifo="original").optimum == len(bfs_sequence(bay, 4))
