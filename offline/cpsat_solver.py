"""CP-SAT (OR-Tools) auf demselben 0-1-Modell wie das ILP: nur für die Tabelle „HiGHS gegen CP-SAT“. ortools gehört nicht in requirements.txt (nur offline gebraucht)."""

import time

import numpy as np

import ilm_model as M


def cpsat(bay, height, limit):
    """(Optimum oder None, Sekunden) von CP-SAT mit einem Worker und Zeitlimit `limit`; Bauen des Modells zählt nicht mit."""
    from ortools.sat.python import cp_model
    model = M.build(bay, height)
    m = cp_model.CpModel()
    xs = [m.NewIntVar(int(model.lb[i]), int(model.ub[i]), f"v{i}") for i in range(len(model.c))]
    a = model.a
    for r in range(a.shape[0]):
        s, e = a.indptr[r], a.indptr[r + 1]
        expr = sum(int(a.data[k]) * xs[a.indices[k]] for k in range(s, e))
        lo, hi = model.lo[r], model.hi[r]
        if np.isfinite(lo) and np.isfinite(hi) and lo == hi:
            m.Add(expr == int(lo))
        else:
            if np.isfinite(lo):
                m.Add(expr >= int(lo))
            if np.isfinite(hi):
                m.Add(expr <= int(hi))
    m.Minimize(sum(xs[i] for i in range(len(model.c)) if model.c[i] > 0))
    sol = cp_model.CpSolver()
    sol.parameters.max_time_in_seconds = float(limit)
    sol.parameters.num_workers = 1
    t = time.perf_counter()
    status = sol.Solve(m)
    secs = time.perf_counter() - t
    return (int(round(sol.ObjectiveValue())) if status == cp_model.OPTIMAL else None), secs
