"""Kennzahlen, Verdikt-Logik, vorberechnete Tabellen. Reine Funktionen: die App ruft st.<Art>(Text), die Tests prüfen jede Zahl und jede Schwelle."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

import ilm_algorithm as A
import ilm_constants as C
import ilm_model as M
from ilm_scenario import make_bay, max_height

BANDS_FILE = Path(__file__).resolve().parent / "ilm_bands.json"


@dataclass(frozen=True)
class Settings:
    stacks: int = C.DEFAULT_STACKS
    layers: int = C.DEFAULT_LAYERS
    extra: int = C.DEFAULT_EXTRA
    seed: int = C.EVERYDAY_SEED
    limit: int = C.DEFAULT_LIMIT


@dataclass(frozen=True)
class Analysis:
    bay: tuple
    height: int
    containers: int
    lower: int                      # Untergrenze: blockierende Container (Stück 2)
    size: tuple                     # (Variablen, Zeilen) des Modells aus der Formel
    limit: int                      # Zeitlimit des ILP in Sekunden
    search: A.SearchResult
    search_ms: float                # Zeit der Suche in Millisekunden (diese Sitzung)
    ilp: M.IlpResult | None         # None: Modell zu groß für die Live-Rechnung

    @property
    def optimum(self):
        """Das Optimum, sobald ein Verfahren es bewiesen hat (Suche oder ILP); sonst None."""
        found = {r for r in (self.search.optimum, None if self.ilp is None else self.ilp.optimum) if r is not None}
        assert len(found) <= 1, found
        return found.pop() if found else None


def analyse(settings: Settings, max_vars: int = C.LIVE_MAX_VARS) -> Analysis:
    bay = make_bay(settings.stacks, settings.layers, settings.seed)
    height = max_height(settings.layers, settings.extra)
    n = settings.stacks * settings.layers
    size = M.model_size(settings.stacks, height, n)
    t0 = time.perf_counter()
    search = A.search(bay, height, C.SEARCH_CAP)
    ms = (time.perf_counter() - t0) * 1000
    ilp = M.solve(bay, height, settings.limit, with_lp=True) if size[0] <= max_vars else None
    return Analysis(bay, height, n, A.blocker_count(bay), size, settings.limit, search, ms, ilp)


def num(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def num_f(x: float) -> str:
    """Zahl mit Leerzeichen als Tausendertrenner; hat sie einen Nachkommaanteil (Median einer geraden Zahl von Läufen), mit einer Nachkommastelle und Komma."""
    x = round(float(x), 6)                                           # 0,9999999999999987 (Rundungsrauschen eines Lösers) ist 1
    if x.is_integer():
        return num(int(x))
    whole, frac = f"{x:.1f}".split(".")
    return f"{num(int(whole))},{frac}"


def sec_text(s: float) -> str:
    """Sekunden: unter 10 mit zwei, sonst mit einer Nachkommastelle (Komma)."""
    return (f"{s:.2f}" if s < 10 else f"{s:.1f}").replace(".", ",")


def dur_text(seconds: float) -> str:
    """Dauer: unter einer Sekunde in Millisekunden, sonst in Sekunden."""
    return f"{ms_text(seconds * 1000)} ms" if seconds < 1 else f"{sec_text(seconds)} s"


def ms_text(ms: float) -> str:
    """Millisekunden: unter 10 mit einer Nachkommastelle, sonst ganzzahlig (Komma)."""
    return f"{ms:.1f}".replace(".", ",") if ms < 10 else num(round(ms))


def factor_text(x: float) -> str:
    """Verhältnis mit einer Nachkommastelle unter 10, sonst ganzzahlig gerundet (mit Tausendertrenner)."""
    return f"{x:.1f}".replace(".", ",") if x < 10 else num(round(x))


def ratio_text(x: float) -> str:
    """Verhältnis mit zwei Nachkommastellen (Tabellen)."""
    return f"{x:.2f}".replace(".", ",")


# ---------------------------------------------------------------- Verdikt einer Bucht

def verdict_bay(a: Analysis, max_vars: int = C.LIVE_MAX_VARS) -> tuple[str, str]:
    """Verdikt der Kernfrage: wie viel schneller ist die Suche als das ILP, und wann gibt das ILP auf?"""
    s = a.search
    if s.capped:
        return "warning", f"Auch die Suche gibt bei {num(C.SEARCH_CAP)} Knoten auf (Untergrenze {a.lower}); das ILP wurde {'nicht gerechnet' if a.ilp is None else 'gerechnet, aber ohne Beweis'}."
    if a.ilp is None:
        return "info", (f"Das Modell hätte {num(a.size[0])} Variablen und {num(a.size[1])} Zeilen (mehr als {num(max_vars)}): Das ILP wird hier nicht gerechnet. "
                        f"Die Suche löst die Bucht mit {num(s.nodes)} Knoten in {ms_text(a.search_ms)} ms (Optimum {s.optimum}, Untergrenze {a.lower}).")
    r = a.ilp
    if r.status == "time_limit":
        best = f" (beste gefundene Lösung: {r.best} Hübe)" if r.best is not None else " (keine Lösung gefunden)"
        return "warning", (f"Das ILP erreicht das Zeitlimit von {a.limit} s ohne Optimalitätsbeweis{best}; die Suche beweist das Optimum {s.optimum} in {ms_text(a.search_ms)} ms "
                           f"(Untergrenze {a.lower}).")
    if r.status != "optimal":
        return "warning", f"Das ILP meldet den Status „{r.status}“; die Suche beweist das Optimum {s.optimum} in {ms_text(a.search_ms)} ms."
    factor = r.seconds_solve * 1000 / max(a.search_ms, 0.01)
    text = (f"Das ILP beweist das Optimum {r.optimum} in {sec_text(r.seconds_solve)} s (Modell mit {num(r.variables)} Variablen), die Suche in {ms_text(a.search_ms)} ms: "
            f"das {factor_text(factor)}-Fache schneller (Untergrenze {a.lower}).")
    if factor >= C.SPEED_STRONG:
        return "success", text
    if factor >= C.SPEED_WEAK:
        return "info", text
    return "info", "Die Bucht ist so klein, dass beide schnell sind. " + text


def result_rows(a: Analysis) -> list[dict]:
    """Zeilen der Ergebnistabelle: Verfahren, Ergebnis, Zeit, Größe oder Knoten."""
    rows = []
    s = a.search
    rows.append({"name": "ILP (HiGHS, zeitindiziertes Modell)", **_ilp_row(a)})
    rows.append({"name": "Suche (IDA* mit Untergrenze und Merken)", "result": "nicht bewiesen" if s.capped else str(s.optimum), "time": f"{ms_text(a.search_ms)} ms",
                 "size": f"{num(s.nodes)} Knoten in {s.stages} Budgetstufen"})
    rows.append({"name": "Untergrenze (Stück 2)", "result": str(a.lower), "time": "", "size": "Zahl der Blocker"})
    return rows


def _ilp_row(a: Analysis) -> dict:
    size = f"{num(a.size[0])} Variablen, {num(a.size[1])} Zeilen"
    r = a.ilp
    if r is None:
        return {"result": "nicht gerechnet", "time": "", "size": size}
    if r.status == "optimal":
        lp = "" if r.lp_value is None else f"; LP-Wert {num_f(round(r.lp_value, 2))}"
        return {"result": str(r.optimum), "time": f"{sec_text(r.seconds_solve)} s", "size": size + lp}
    if r.status == "time_limit":
        return {"result": "kein Beweis" + ("" if r.best is None else f" (beste Lösung {r.best})"), "time": f"{sec_text(r.seconds_solve)} s (Limit {a.limit} s)", "size": size}
    return {"result": r.status, "time": f"{sec_text(r.seconds_solve)} s", "size": size}


def move_rows(result: M.IlpResult) -> list[dict]:
    """Die Umlagerungen einer ILP-Lösung als Tabellenzeilen (Stapel und Lagen von 1 an gezählt)."""
    if not result.moves:
        return []
    return [{"period": t, "container": n, "from": f"Stapel {i + 1}, Lage {j + 1}", "to": f"Stapel {k + 1}, Lage {l + 1}"} for t, n, i, j, k, l in result.moves]


# ---------------------------------------------------------------- Stichproben (vorberechnet)

def _stat(xs):
    xs = list(xs)
    if not xs:
        return {"n": 0, "median": None, "mean": None, "min": None, "max": None}
    return {"n": len(xs), "median": median(xs), "mean": mean(xs), "min": min(xs), "max": max(xs)}


def time_rows(stacks: int, layers: int, extra: int, seeds, limit: float = C.BAND_LIMIT) -> list[dict]:
    """Eine Zeile je feste Bucht: Untergrenze, Optimum und Zeit der Suche, Status, Zeit und Wert des ILP. Langsam (bis zum Zeitlimit je Bucht), nur offline und in Tests."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        t0 = time.perf_counter()
        ref = A.search(bay, height, C.SEARCH_CAP)
        ms = (time.perf_counter() - t0) * 1000
        r = M.solve(bay, height, limit)
        rows.append({"seed": sd, "lb": A.blocker_count(bay), "opt": ref.optimum, "nodes": ref.nodes, "search_ms": ms, "status": r.status, "ilp_s": r.seconds_solve, "build_s": r.seconds_build,
                     "ilp_opt": r.optimum, "vars": r.variables, "nrows": r.rows, "containers": stacks * layers})
    return rows


def time_stats(rows: list[dict]) -> dict:
    """Kennzahlen: Modellgröße, Zahl der bewiesenen Läufe, falsche Werte (Optimum ungleich Suche), ILP-Zeit nur des Lösens (alle Läufe und nur die bewiesenen), Zeit des Bauens, Zeit der Suche, Untergrenze und Optimum."""
    solved = [r for r in rows if r["status"] == "optimal"]
    return {"n": len(rows), "containers": rows[0]["containers"], "variables": rows[0]["vars"], "rows": rows[0]["nrows"], "solved": len(solved),
            "wrong": sum(r["ilp_opt"] != r["opt"] for r in solved), "time": _stat(r["ilp_s"] for r in rows), "solved_time": _stat(r["ilp_s"] for r in solved),
            "search_ms": _stat(r["search_ms"] for r in rows), "build": _stat(r["build_s"] for r in rows), "lb": median(r["lb"] for r in rows), "opt": median(r["opt"] for r in rows)}


def lp_rows(stacks: int, layers: int, extra: int, seeds) -> list[dict]:
    """Eine Zeile je feste Bucht: Untergrenze, Optimum (Suche) und Wert der LP-Relaxation."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        lp, _ = M.lp_value(M.build(bay, height))
        rows.append({"seed": sd, "lb": A.blocker_count(bay), "opt": A.search(bay, height, C.SEARCH_CAP).optimum, "lp": lp})
    return rows


def lp_stats(rows: list[dict]) -> dict:
    """Kennzahlen: LP-Wert, Optimum und Untergrenze (Median), Verhältnis LP / Optimum (Median), Optimum minus LP-Wert (Median, Maximum), Zahl der Buchten mit LP-Wert gleich Optimum."""
    gaps = [r["opt"] - r["lp"] for r in rows]
    return {"n": len(rows), "lp": median(r["lp"] for r in rows), "opt": median(r["opt"] for r in rows), "lb": median(r["lb"] for r in rows),
            "lp_opt": median(r["lp"] / r["opt"] for r in rows if r["opt"]) if any(r["opt"] for r in rows) else None,
            "gap": {"median": median(gaps), "max": max(gaps)}, "equal": sum(abs(g) < 1e-6 for g in gaps)}


def lptime_rows(stacks: int, layers: int, extra: int, seeds, limit: float = C.BAND_LIMIT) -> list[dict]:
    """Eine Zeile je feste Bucht: Zeit des Wurzel-LP, Zeit des ILP und Optimum minus LP-Wert."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        model = M.build(bay, height)
        lp, lp_s = M.lp_value(model)
        r = M.solve(bay, height, limit)
        rows.append({"seed": sd, "lp_s": lp_s, "ilp_s": r.seconds_solve, "gap": (r.optimum - lp) if r.optimum is not None else None})
    return rows


def lptime_stats(rows: list[dict]) -> dict:
    gaps = [r["gap"] for r in rows if r["gap"] is not None]
    return {"n": len(rows), "lp_s": {"median": median(r["lp_s"] for r in rows), "sum": sum(r["lp_s"] for r in rows)},
            "ilp_s": {"median": median(r["ilp_s"] for r in rows), "sum": sum(r["ilp_s"] for r in rows)}, "share": sum(r["lp_s"] for r in rows) / sum(r["ilp_s"] for r in rows),
            "gap": {"median": median(gaps) if gaps else None, "max": max(gaps) if gaps else None}}


def solver_rows(stacks: int, layers: int, extra: int, seeds, cpsat, limit: float = C.BAND_LIMIT) -> list[dict]:
    """Eine Zeile je feste Bucht: HiGHS und CP-SAT auf demselben Modell. `cpsat(bay, height, limit)` -> (Optimum oder None, Sekunden); CP-SAT liegt nur im Offline-Ordner."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        ref = A.search(bay, height, C.SEARCH_CAP).optimum
        r = M.solve(bay, height, limit)
        opt, secs = cpsat(bay, height, limit)
        rows.append({"seed": sd, "highs_s": r.seconds_solve, "highs_ok": r.optimum == ref, "cp_s": secs, "cp_ok": opt == ref})
    return rows


def solver_stats(rows: list[dict]) -> dict:
    return {"n": len(rows), "highs": {"median": median(r["highs_s"] for r in rows), "sum": sum(r["highs_s"] for r in rows), "solved": sum(r["highs_ok"] for r in rows)},
            "cpsat": {"median": median(r["cp_s"] for r in rows), "sum": sum(r["cp_s"] for r in rows), "solved": sum(r["cp_ok"] for r in rows)},
            "speed": sum(r["highs_s"] for r in rows) / sum(r["cp_s"] for r in rows)}


def search_rows(stacks: int, layers: int, extra: int, seeds, cap: int = C.SEARCH_CAP) -> list[dict]:
    """Eine Zeile je feste Bucht: Untergrenze, Knoten und Zeit der Suche (done = unter dem Knotenlimit)."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        t0 = time.perf_counter()
        r = A.search(bay, height, cap)
        rows.append({"seed": sd, "lb": A.blocker_count(bay), "nodes": r.nodes, "seconds": time.perf_counter() - t0, "done": not r.capped})
    return rows


def search_stats(rows: list[dict], containers: int) -> dict:
    done = [r for r in rows if r["done"]]
    return {"n": len(rows), "containers": containers, "done": len(done), "blockers": median(r["lb"] for r in rows), "nodes": _stat(r["nodes"] for r in done),
            "time": _stat(r["seconds"] for r in done)}


def fix_rows(stacks: int, layers: int, extra: int, seeds, limit: float = C.BAND_LIMIT) -> list[dict]:
    """Eine Zeile je feste Bucht: Status und Wert des Modells mit der Originalfassung (6) der LIFO-Nebenbedingung, verglichen mit der Suche."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        ref = A.search(bay, height, C.SEARCH_CAP).optimum
        r = M.solve(bay, height, limit, lifo="original")
        rows.append({"seed": sd, "status": r.status, "same": r.optimum == ref})
    return rows


def fix_stats(rows: list[dict]) -> dict:
    infeasible = sum(r["status"] == "infeasible" for r in rows)
    different = sum(r["status"] == "optimal" and not r["same"] for r in rows)
    return {"n": len(rows), "infeasible": infeasible, "different": different, "ok": len(rows) - infeasible - different}


def load_bands() -> dict:
    """Vorberechnete Kennzahlen, erzeugt von generate_precomputed.py: {"zeit", "lp", "lpzeit", "loeser", "suche", "korrektur"} je {"s,l": Kennzahlen}."""
    return json.loads(BANDS_FILE.read_text(encoding="utf-8"))


def cell_key(stacks: int, layers: int) -> str:
    return f"{stacks},{layers}"


# ---------------------------------------------------------------- Verdikte der Tabellen

def verdict_break(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „wo bricht das ILP ein?“ je Zelle: bewiesene Läufe, Zeit gegen die Suche."""
    t, s = stats["time"], stats["search_ms"]
    base = (f"{name} ({stats['containers']} Container, {num(stats['variables'])} Variablen): Das ILP beweist {stats['solved']} von {stats['n']} Buchten innerhalb von {num(round(C.BAND_LIMIT))} s "
            f"(Zeit im Median {sec_text(t['median'])} s, Maximum {sec_text(t['max'])} s); die Suche braucht im Median {ms_text(s['median'])} ms, höchstens {ms_text(s['max'])} ms.")
    if stats["wrong"]:
        return "warning", base + f" {stats['wrong']} bewiesene Werte weichen von der Suche ab."
    if stats["solved"] == stats["n"]:
        return "info", base
    return "warning", base + f" {stats['n'] - stats['solved']} Buchten sind nicht fertig."


def verdict_lp(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „ist die LP-Schranke schwach?“: Optimum minus LP-Wert im Median."""
    g = stats["gap"]
    text = (f"{name}: LP-Wert im Median {num_f(stats['lp'])}, Optimum {num_f(stats['opt'])}, Untergrenze {num_f(stats['lb'])}; Optimum minus LP-Wert im Median {num_f(g['median'])}, "
            f"höchstens {num_f(round(g['max'], 2))} ({stats['equal']} von {stats['n']} Buchten mit LP-Wert gleich Optimum).")
    if g["median"] <= C.LP_TIGHT:
        return "info", text + " Die LP-Schranke ist hier gut: Das Problem des ILP ist nicht die Schranke."
    return "info", text + " Die LP-Schranke lässt hier eine Lücke."


def verdict_lptime(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „wo steckt die Zeit?“: Anteil des Wurzel-LP an der ILP-Zeit."""
    text = (f"{name}: Das Wurzel-LP kostet {stats['share'] * 100:.0f} % der ILP-Zeit (Summe {sec_text(stats['lp_s']['sum'])} s von {sec_text(stats['ilp_s']['sum'])} s); "
            f"der Rest ist Verzweigung.")
    return "info", text


def verdict_solvers(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „hängt der Befund vom Löser ab?“: HiGHS gegen CP-SAT auf demselben Modell."""
    h, c = stats["highs"], stats["cpsat"]
    text = (f"{name}: HiGHS Median {sec_text(h['median'])} s (Summe {sec_text(h['sum'])} s, {h['solved']} von {stats['n']} richtig), CP-SAT Median {sec_text(c['median'])} s "
            f"(Summe {sec_text(c['sum'])} s, {c['solved']} von {stats['n']} richtig): CP-SAT ist insgesamt das {factor_text(stats['speed'])}-Fache schneller.")
    return "info", text


def verdict_search(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „wo bricht die Suche ein?“: fertige Läufe unter dem Knotenlimit."""
    n, t = stats["n"], stats["time"]
    if stats["done"] == 0:
        return "warning", f"{name} ({stats['containers']} Container): Alle {n} Buchten liegen über {num(C.SEARCH_CAP)} Knoten."
    text = (f"{name} ({stats['containers']} Container, {num_f(stats['blockers'])} Blocker im Median): {stats['done']} von {n} Buchten unter {num(C.SEARCH_CAP)} Knoten, "
            f"Knoten im Median {num_f(stats['nodes']['median'])}, höchstens {num(stats['nodes']['max'])}; Zeit im Median {dur_text(t['median'])}, höchstens {dur_text(t['max'])}.")
    return ("info" if stats["done"] == n else "warning"), text


def verdict_fix(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „braucht das Modell die Korrektur?“: Buchten, in denen die Originalfassung (6) unlösbar ist oder einen anderen Wert liefert."""
    wrong = stats["infeasible"] + stats["different"]
    text = (f"{name}: Mit der Originalfassung (6) sind {stats['infeasible']} von {stats['n']} Buchten unlösbar und {stats['different']} haben einen anderen Wert als die Suche; "
            f"mit der Korrektur (9) stimmen alle.")
    if wrong:
        return "warning", text
    return "info", f"{name}: Hier macht die Korrektur (9) keinen Unterschied: In allen {stats['n']} Buchten stimmt auch die Originalfassung (6)."
