"""Erzeugt ilm_bands.json: Kennzahlen der festen Buchten (Seeds ab 0, Platz 2) für sechs Auswertungen.

    python generate_precomputed.py

"zeit":      je Zelle Größe und Zeit des ILP (HiGHS, Zeitlimit 60 s) gegen die Suche (ilm_constants.TIME_CELLS).
"lp":        je Zelle LP-Wert gegen Optimum und Untergrenze (LP_CELLS).
"lpzeit":    je Zelle Anteil des Wurzel-LP an der ILP-Zeit (LPTIME_CELLS).
"loeser":    je Zelle HiGHS gegen CP-SAT auf demselben Modell (SOLVER_CELLS; ortools nur hier, im Ordner offline/).
"suche":     je Zelle die Suche auf größeren Buchten bis 8 x 4 (SEARCH_CELLS).
"korrektur": je Zelle Originalfassung (6) der LIFO-Nebenbedingung gegen die Korrektur (9) (FIX_CELLS).

Rechenzeit rund 15 bis 25 Minuten. Die Zeitreihe "zeit" läuft in EINEM Prozess nacheinander (damit sich die Läufe nicht gegenseitig bremsen), die übrigen Auswertungen laufen in anderen
Prozessen daneben. Zeiten sind Einzelmessungen (ein Lauf, diese Maschine) und schwanken. Dieselben Funktionen wie die Tests (`ilm_evaluation.*_rows`, `*_stats`); die Datei
speichert nur Kennzahlen, keine Zeilen. tests/test_presets.py rechnet kleine Zellen neu und vergleicht, was nicht von der Zeit abhängt."""

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import ilm_constants as C
import ilm_evaluation as ev

sys.stdout.reconfigure(encoding="utf-8")


def job(kind, stacks, layers, n):
    seeds = range(n)
    e = C.DEFAULT_EXTRA
    if kind == "lp":
        return kind, stacks, layers, ev.lp_stats(ev.lp_rows(stacks, layers, e, seeds))
    if kind == "lpzeit":
        return kind, stacks, layers, ev.lptime_stats(ev.lptime_rows(stacks, layers, e, seeds))
    if kind == "loeser":
        from offline.cpsat_solver import cpsat
        return kind, stacks, layers, ev.solver_stats(ev.solver_rows(stacks, layers, e, seeds, cpsat))
    if kind == "suche":
        return kind, stacks, layers, ev.search_stats(ev.search_rows(stacks, layers, e, seeds), stacks * layers)
    return kind, stacks, layers, ev.fix_stats(ev.fix_rows(stacks, layers, e, seeds))


def time_job():
    out = []
    for stacks, layers, n in C.TIME_CELLS:
        out.append(("zeit", stacks, layers, ev.time_stats(ev.time_rows(stacks, layers, C.DEFAULT_EXTRA, range(n)))))
        print(f"zeit {stacks} x {layers}: fertig", flush=True)
    return out


def main():
    bands = {"zeit": {}, "lp": {}, "lpzeit": {}, "loeser": {}, "suche": {}, "korrektur": {}}
    tasks = ([("lp", *c) for c in C.LP_CELLS] + [("lpzeit", *c) for c in C.LPTIME_CELLS] + [("loeser", *c) for c in C.SOLVER_CELLS]
             + [("suche", *c) for c in C.SEARCH_CELLS] + [("korrektur", *c) for c in C.FIX_CELLS])
    with ProcessPoolExecutor(max_workers=max(3, min(5, (os.cpu_count() or 3) - 1))) as pool:
        futures = [pool.submit(time_job)] + [pool.submit(job, *t) for t in tasks]
        for f in as_completed(futures):
            res = f.result()
            for kind, stacks, layers, stats in (res if isinstance(res, list) else [res]):
                bands["korrektur" if kind == "korrektur" else kind][ev.cell_key(stacks, layers)] = stats
                print(f"{kind} {stacks} x {layers}: gespeichert", flush=True)
    ev.BANDS_FILE.write_text(json.dumps(bands, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("geschrieben:", ev.BANDS_FILE.name)


if __name__ == "__main__":
    main()
