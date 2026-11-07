"""Das ILP-Modell: wo bricht es ein? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 7 der Reihe „Umstauen: Untergrenze und Suche“. Stück 4 bis 6 haben die Suche gebaut. Hier das ganzzahlige lineare Programm für dieselbe Aufgabe: ein zeitindiziertes Modell
(korrigiertes BRP-II nach Eskandari und Azari), das HiGHS exakt löst. Die Demo rechnet es live auf kleinen Buchten, zeigt die Lösung als Umlagerungsfolge, misst vorberechnet,
wo es einbricht (Größe, Zeit, Schwanz), warum (LP-Schranke gut, Modell groß) und wo die Suche noch trägt.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import ilm_constants as C
import ilm_model as M
from ilm_evaluation import (
    Settings,
    analyse,
    cell_key,
    dur_text,
    factor_text,
    load_bands,
    move_rows,
    ms_text,
    num,
    num_f,
    ratio_text,
    result_rows,
    sec_text,
    verdict_bay,
    verdict_break,
    verdict_fix,
    verdict_lp,
    verdict_lptime,
    verdict_search,
    verdict_solvers,
)
from ilm_layout import dunkles_design, kopf_css
from ilm_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from ilm_visualization import build_bay, build_break, build_lp, build_search, build_size, build_solvers, build_times

st.set_page_config(page_title="ILP-Modell – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _bands():
    return load_bands()


@st.cache_data(show_spinner=False)
def _hand():
    """Das Modell der Mini-Bucht mit Lösung und die Gegenprobe der LIFO-Nebenbedingung (Beispiel mit drei Blockern)."""
    mini = M.solve(C.MINI_BAY, C.MINI_HEIGHT, 30, with_lp=True)
    fixed = M.solve(C.FIX_BAY, C.FIX_HEIGHT, 30)
    original = M.solve(C.FIX_BAY, C.FIX_HEIGHT, 30, lifo="original")
    return mini, M.replay_moves(C.MINI_BAY, C.MINI_HEIGHT, mini), fixed, original


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in ilm_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧮 Das ILP-Modell: wo bricht es ein?")
st.markdown(
    """
Stück 4 bis 6 haben die **Suche** gebaut. Hier das **ganzzahlige lineare Programm (ILP)** für dieselbe Aufgabe: ein Modell mit einer 0-1-Variable je Container, Platz und Periode, das ein Standardlöser (**HiGHS**) **exakt** löst. Es ist korrekt, wächst aber mit **N² · W² · H²**. Die Demo **rechnet es live** auf kleinen Buchten, zeigt die Lösung als Umlagerungsfolge und misst, **wo es einbricht**, **warum** und **wo die Suche noch trägt**.

Weiter unten: die Abschnitte **🔬 Experiment** (das Modell von Hand und warum die LIFO-Korrektur nötig ist, wie das Modell wächst, wo das ILP einbricht, warum, ein zweiter Löser, wo die Suche einbricht), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Dies ist das siebte Stück der Reihe „Umstauen: Untergrenze und Suche“.
"""
)

with st.expander("So funktioniert das Modell", expanded=True):
    st.markdown(
        """
1. **Perioden:** Periode *t* ist der Abruf des Containers *t*; die Umlagerungen dieser Periode geschehen davor.
2. **Variablen:** *b* (Container *n* liegt zu Beginn der Periode *t* auf Stapel *i*, Lage *j*) und *x* (in Periode *t* wird *n* von (*i*,*j*) nach (*k*,*l*) umgelagert). Alle 0-1.
3. **Zielfunktion:** die Zahl der Umlagerungen (Summe aller *x*).
4. **Nebenbedingungen:** Das Layout geht aus dem vorigen und den Umlagerungen hervor; jeder Container hat genau einen Platz, jeder Platz höchstens einen Container, nichts schwebt; nur Container **über dem Ziel** im Zielstapel werden bewegt (restricted); und die Umlagerungen aus einem Stapel folgen **LIFO** (die oberste zuerst, sie liegt danach am tiefsten).
5. **Der Abruf ist implizit:** Was über dem Ziel liegt, muss weg, sonst würde im nächsten Layout etwas schweben.
6. **Gelöst** wird mit HiGHS (`scipy.optimize.milp`) mit einem Zeitlimit. Bei Zeitlimit gibt es keinen bewiesenen Optimalwert, und die Demo behauptet keinen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Bucht**")
    stacks = st.slider("Stapel", *bounds("stacks_slider"), key="stacks_slider", help="Wie viele Stapel die Bucht hat.")
    layers = st.slider("Lagen je Stapel", *bounds("layers_slider"), key="layers_slider", help="So viele Container stehen anfangs auf jedem Stapel.")
    extra = st.slider("Platz (Lagen über der Anfangshöhe)", *bounds("extra_slider"), key="extra_slider",
                      help="Höchsthöhe = Lagen + Platz. Standard 2. Die vorberechneten Tabellen gelten für Platz 2.")
    seed = st.number_input("Bucht-Nummer (Seed)", *bounds("seed_input"), key="seed_input", step=1, help="Die Nummer bestimmt, wie die Abrufnummern auf die Plätze verteilt sind.")
    st.button("🎲 Neue Bucht würfeln", width="stretch", on_click=randomize_seed)
    st.markdown("**ILP**")
    limit = st.slider("Zeitlimit des ILP (Sekunden)", *bounds("limit_slider"), key="limit_slider",
                      help=f"Das ILP wird nur gerechnet, wenn das Modell höchstens {num(C.LIVE_MAX_VARS)} Variablen hat (rund 15 Container). Das Limit gilt für das Lösen; HiGHS überschreitet es leicht.")

sync_query_params({"stacks_slider": int(stacks), "layers_slider": int(layers), "extra_slider": int(extra), "seed_input": int(seed), "limit_slider": int(limit)})

settings = Settings(int(stacks), int(layers), int(extra), int(seed), int(limit))
with st.spinner(f"Rechne die Suche und, wenn das Modell klein genug ist, das ILP (höchstens {settings.limit} s) …"):
    a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
ilp = a.ilp
m1, m2, m3, m4 = st.columns(4)
m1.metric("Modell (Variablen)", num(a.size[0]), delta=f"{num(a.size[1])} Zeilen", delta_color="off", help="Aus der Formel; unabhängig davon, ob das ILP gerechnet wird.")
if ilp is None:
    m2.metric("ILP-Zeit", "nicht gerechnet", delta=f"mehr als {num(C.LIVE_MAX_VARS)} Variablen", delta_color="off")
elif ilp.status == "optimal":
    m2.metric("ILP-Zeit", f"{sec_text(ilp.seconds_solve)} s", delta="Optimum bewiesen", delta_color="off", help="Nur das Lösen; Bauen des Modells zählt nicht mit.")
else:
    m2.metric("ILP-Zeit", f"Limit ({a.limit} s)" if ilp.status == "time_limit" else ilp.status, delta="kein Beweis", delta_color="off")
m3.metric("Suche (Zeit)", f"{ms_text(a.search_ms)} ms", delta=f"{num(a.search.nodes)} Knoten", delta_color="off", help="IDA* mit Untergrenze und Zustandsmerken (Stück 5 und 6), Python.")
m4.metric("Optimum", "nicht bewiesen" if a.optimum is None else a.optimum, delta=f"Untergrenze {a.lower}, Bucht {settings.stacks} × {settings.layers}", delta_color="off")
st.plotly_chart(build_bay(a.bay, a.height, target=min(c for s in a.bay for c in s)), width="stretch", key="chart_bay")
st.caption("Rot: blockierende Container (liegen über einem früher abzurufenden), grün: der nächste Abruf, grau-blau: alle übrigen.")
table = ["| Verfahren | Ergebnis | Zeit | Größe |", "|---|---|---|---|"]
for r in result_rows(a):
    table.append(f"| {r['name']} | {r['result']} | {r['time']} | {r['size']} |")
st.markdown("\n".join(table))
st.caption("Zeiten sind Einzelmessungen auf dem Rechner dieser Sitzung und schwanken. Das ILP läuft in C++ (HiGHS), die Suche in Python: Sekunden sind kein reines Maß der Methoden.")
bars = [{"name": "Suche (IDA* + Merken)", "ms": a.search_ms, "limit": False, "color": C.COLOR_SEARCH, "text": f"{ms_text(a.search_ms)} ms"}]
if ilp is not None and ilp.status in ("optimal", "time_limit"):
    bars.insert(0, {"name": "ILP (HiGHS)", "ms": ilp.seconds_solve * 1000, "limit": ilp.status == "time_limit", "color": C.COLOR_ILP,
                    "text": f"{sec_text(ilp.seconds_solve)} s" + (" (Limit)" if ilp.status == "time_limit" else "")})
st.plotly_chart(build_times(bars), width="stretch", key="chart_times")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wo bricht das ILP-Modell ein?")
kind, text = verdict_bay(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: das Modell von Hand -------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Das Modell von Hand")
mini, mini_hubs, fixed, original = _hand()
st.caption("3 Stapel mit je 2 Containern, Höchsthöhe 4, von unten nach oben (1, 4), (5, 2), (6, 3): nur die 4 blockiert (Untergrenze 1). Das Modell hat "
           f"**{num(mini.variables)} Variablen**, **{num(mini.rows)} Zeilen** und {num(mini.nonzeros)} Nichtnullen; der LP-Wert ist {num_f(round(mini.lp_value, 2))}.")
st.plotly_chart(build_bay(C.MINI_BAY, C.MINI_HEIGHT, target=1), width="stretch", key="chart_mini")
mt = ["| Periode | Container | von | nach |", "|---|---|---|---|"]
for r in move_rows(mini):
    mt.append(f"| {r['period']} | {r['container']} | {r['from']} | {r['to']} |")
st.markdown("\n".join(mt))
st.success(f"Optimum {mini.optimum}: Die 4 blockiert die 1 und wird in der Periode des Abrufs der 1 umgelagert. Sie landet dabei über einem Container, der früher abzurufen ist (der 2 oder der 3), "
           f"und muss in einer späteren Periode noch einmal weg: zwei Umlagerungen, wie in Stück 2 und 5. Welche der beiden gleichwertigen Lösungen HiGHS liefert, kann je Version wechseln. "
           f"Die Lösung wurde mit dem Simulator der Suche nach den Regeln nachgespielt ({mini_hubs} Hübe).")
st.markdown("**Warum die Korrektur der LIFO-Nebenbedingung nötig ist.** Eskandari und Azari zeigen, dass die ursprüngliche Fassung (6) von BRP-II höchstens eine Umlagerung je Stapelpaar und Periode zulässt "
            "und damit lösbare Buchten für unlösbar erklärt; die Korrektur (9) multipliziert die linke Seite mit *H*. Ein Beispiel mit drei Blockern über der 1 "
            "(Stapel von unten nach oben: (1, 6, 7, 8), (2, 3), (4, 5), Höchsthöhe 4):")
ft = ["| Fassung der LIFO-Nebenbedingung | Status | Optimum |", "|---|---|---|",
      f"| Korrektur (9) | {fixed.status} | {fixed.optimum} |", f"| Originalfassung (6) | {original.status} | {'–' if original.optimum is None else original.optimum} |"]
st.markdown("\n".join(ft))

st.markdown("---")

# --- Experiment: Wie wächst das Modell? ----------------------------------------------------------------------------------------------------------

bands = _bands()
zeit = bands["zeit"]
st.subheader("🔬 Experiment: Wie wächst das Modell?")
st.caption("Variablen = W · H · N (N + 1) / 2 + W (W − 1) H² · N (N − 1) / 2 mit W Stapeln, Höchsthöhe H und N Containern (Platz 2); die Zahlen stammen aus gebauten Modellen und stimmen mit der Formel überein.")
cells_z = {f"{s_} × {l_}": zeit[cell_key(s_, l_)] for s_, l_, _ in C.TIME_CELLS}
tg = ["| Zelle | Container | Variablen | Zeilen |", "|---|---|---|---|"]
for name, c in sorted(cells_z.items(), key=lambda kv: (kv[1]["containers"], kv[1]["variables"])):
    tg.append(f"| {name} | {c['containers']} | {num(c['variables'])} | {num(c['rows'])} |")
st.markdown("\n".join(tg))
st.plotly_chart(build_size(cells_z), width="stretch", key="chart_size")

st.markdown("---")

# --- Experiment: Wo bricht das ILP ein? ----------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wo bricht das ILP ein?")
st.caption(f"Je Zelle feste Buchten (Platz 2, dieselben wie in Stück 4 bis 6), ILP mit HiGHS und Zeitlimit {num(round(C.BAND_LIMIT))} s je Bucht, Suche daneben; vorberechnet (`generate_precomputed.py`). "
           "Zeiten: Windows, Python, ein Lauf, sie schwanken. „Bewiesen“: Optimalität innerhalb des Limits belegt.")
tb = ["| Zelle (Container), Buchten | Variablen | ILP bewiesen | ILP-Zeit Median / Maximum | Suche Median / Maximum | Untergrenze, Optimum (Median) |", "|---|---|---|---|---|---|"]
for name, c in sorted(cells_z.items(), key=lambda kv: (kv[1]["containers"], kv[1]["variables"])):
    tb.append(f"| {name} ({c['containers']}), {c['n']} | {num(c['variables'])} | {c['solved']} / {c['n']} | {sec_text(c['time']['median'])} s / {sec_text(c['time']['max'])} s | "
              f"{ms_text(c['search_ms']['median'])} ms / {ms_text(c['search_ms']['max'])} ms | {num_f(c['lb'])}, {num_f(c['opt'])} |")
st.markdown("\n".join(tb))
st.plotly_chart(build_break(cells_z, C.BAND_LIMIT), width="stretch", key="chart_break")
here = zeit.get(cell_key(settings.stacks, settings.layers))
st.markdown(f"**Zelle {settings.stacks} × {settings.layers} (Ihre Einstellung)**" + ("" if settings.extra == C.DEFAULT_EXTRA else f", Tabellen gelten für Platz {C.DEFAULT_EXTRA}, hier ist Platz {settings.extra} eingestellt") + ":")
if here is None:
    st.info(f"Für {settings.stacks} × {settings.layers} wurde das ILP nicht vorberechnet (zu groß); die Tabelle zeigt die Zellen, die gerechnet wurden.")
else:
    kind, text = verdict_break(here, f"{settings.stacks} × {settings.layers}")
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Warum? ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Warum bricht es ein?")
lp, lpt = bands["lp"], bands["lpzeit"]
st.caption("Ist die LP-Schranke des Modells schwach? LP-Wert (Integralität aufgehoben) gegen Optimum und Untergrenze, Median über die Buchten der Zelle.")
tl = ["| Zelle (Buchten) | LP-Wert | Optimum | Untergrenze | Optimum minus LP-Wert (Median, Maximum) | Buchten mit LP-Wert gleich Optimum |", "|---|---|---|---|---|---|"]
for s_, l_, n_ in C.LP_CELLS:
    c = lp[cell_key(s_, l_)]
    tl.append(f"| {s_} × {l_} ({c['n']}) | {num_f(c['lp'])} | {num_f(c['opt'])} | {num_f(c['lb'])} | {num_f(c['gap']['median'])}, {num_f(round(c['gap']['max'], 2))} | {c['equal']} von {c['n']} |")
st.markdown("\n".join(tl))
cells_l = {f"{s_} × {l_}": lp[cell_key(s_, l_)] for s_, l_, _ in C.LP_CELLS}
st.plotly_chart(build_lp(cells_l), width="stretch", key="chart_lp")
st.caption("Wie viel der ILP-Zeit steckt im Wurzel-LP? Summe über die Buchten der Zelle.")
tp = ["| Zelle (Buchten) | LP-Zeit Summe | ILP-Zeit Summe | Anteil des LP | Optimum minus LP-Wert (Median, Maximum) |", "|---|---|---|---|---|"]
for s_, l_, n_ in C.LPTIME_CELLS:
    c = lpt[cell_key(s_, l_)]
    tp.append(f"| {s_} × {l_} ({c['n']}) | {sec_text(c['lp_s']['sum'])} s | {sec_text(c['ilp_s']['sum'])} s | {c['share'] * 100:.0f} % | {num_f(c['gap']['median'])}, {num_f(round(c['gap']['max'], 2))} |")
st.markdown("\n".join(tp))
for s_, l_ in ((3, 4), (4, 4)):
    for verdict, data in ((verdict_lp, lp), (verdict_lptime, lpt)):
        if cell_key(s_, l_) in data:
            kind, text = verdict(data[cell_key(s_, l_)], f"{s_} × {l_}")
            getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Ein zweiter Löser ----------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Hängt das vom Löser ab?")
sv = bands["loeser"]
st.caption("Dasselbe Modell mit HiGHS und mit CP-SAT (OR-Tools, ein Worker, Zeitlimit 60 s); CP-SAT wurde nur offline gerechnet. Zeiten je Bucht summiert.")
ts = ["| Zelle (Buchten) | HiGHS Median / Summe | CP-SAT Median / Summe | CP-SAT schneller um |", "|---|---|---|---|"]
for s_, l_, n_ in C.SOLVER_CELLS:
    c = sv[cell_key(s_, l_)]
    ts.append(f"| {s_} × {l_} ({c['n']}) | {sec_text(c['highs']['median'])} s / {sec_text(c['highs']['sum'])} s | {sec_text(c['cpsat']['median'])} s / {sec_text(c['cpsat']['sum'])} s | {factor_text(c['speed'])}-fach |")
st.markdown("\n".join(ts))
st.plotly_chart(build_solvers({f"{s_} × {l_}": sv[cell_key(s_, l_)] for s_, l_, _ in C.SOLVER_CELLS}), width="stretch", key="chart_solvers")
kind, text = verdict_solvers(sv[cell_key(4, 3)], "4 × 3")
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Wo bricht die Suche ein? ---------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wo bricht die Suche ein?")
sc = bands["suche"]
st.caption(f"IDA* mit Untergrenze und Merken auf größeren Buchten (Platz 2), Knotenlimit {num(C.SEARCH_CAP)}; Knoten und Zeit der fertigen Läufe, vorberechnet. **Die Grenze der Suche ist damit nicht gefunden**, nur ein Bereich, in dem sie noch trägt.")
tc = ["| Zelle (Container), Buchten | fertig | Blocker (Median) | Knoten Median / Maximum | Zeit Median / Maximum |", "|---|---|---|---|---|"]
for s_, l_, n_ in C.SEARCH_CELLS:
    c = sc[cell_key(s_, l_)]
    tc.append(f"| {s_} × {l_} ({c['containers']}), {c['n']} | {c['done']} / {c['n']} | {num_f(c['blockers'])} | {num_f(c['nodes']['median'])} / {num(c['nodes']['max'])} | "
              f"{dur_text(c['time']['median'])} / {dur_text(c['time']['max'])} |")
st.markdown("\n".join(tc))
st.plotly_chart(build_search({f"{s_} × {l_}": sc[cell_key(s_, l_)] for s_, l_, _ in C.SEARCH_CELLS}), width="stretch", key="chart_search")
for s_, l_ in ((6, 4), (6, 5)):
    kind, text = verdict_search(sc[cell_key(s_, l_)], f"{s_} × {l_}")
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Die Korrektur -------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie oft macht die Korrektur einen Unterschied?")
fx = bands["korrektur"]
st.caption("Das Modell mit der Originalfassung (6) der LIFO-Nebenbedingung gegen die Suche; mit der Korrektur (9) stimmen alle Buchten (siehe oben).")
tf = ["| Zelle (Buchten) | unlösbar | anderer Wert | richtig |", "|---|---|---|---|"]
for s_, l_, n_ in C.FIX_CELLS:
    c = fx[cell_key(s_, l_)]
    tf.append(f"| {s_} × {l_} ({c['n']}) | {c['infeasible']} | {c['different']} | {c['ok']} |")
st.markdown("\n".join(tf))
kind, text = verdict_fix(fx[cell_key(3, 3)], "3 × 3")
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Zeiten sind Einzelmessungen** | Ein Lauf auf einer Windows-Maschine; dieselbe Bucht brauchte 61,9 und 55,6 s. Das ILP läuft in C++, die Suche in Python. Die Grenze ist weich und hängt vom Zeitlimit ab (hier 60 s). | – |
| **Ein Modell, ein Löser live** | Das ILP ist die zeitindizierte Formulierung (korrigiertes BRP-II). Stärkere Modelle (Zehendner u. a. 2015, Petering und Hussein 2013) sind nicht gebaut; der Befund gilt für dieses Modell, nicht für das beste bekannte. | – |
| **Nur bis 60 000 Variablen live** | Darüber zeigt die App die Modellgröße und „nicht gerechnet“. | – |
| **Kleine Zellen** | 5 × 3 mit 8 und 4 × 4 mit 6 Buchten: der Anteil „nicht fertig“ ist dort grob. | – |
| **Die Grenze der Suche ist nicht gefunden** | Gemessen bis 8 × 4 (32 Container). | – |
| **Eigene Buchtfamilie** | Höchsthöhe = Lagen + 2; die Instanzen der Literatur (ein freier Stapel, keine Zusatzlagen) sind nicht nachgebaut. Die Zahlen der Literatur sind nicht vergleichbar. | – |
| **Nur restricted, nur volle Buchten, Platz 2 in den Tabellen** | Mit anderer Hubmenge (Stück 3) oder anderer Füllung ändern sich Größe und Zeit. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben:** $W$ Stapel mit Höchsthöhe $H$, $N$ Container mit den Abrufnummern $1, \dots, N$ (kleiner = früher), die Anfangsbucht. Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; im *restricted* Modell werden nur Container über der nächsten abzurufenden Nummer bewegt.

**Variablen** (alle binär). $b_{ijnt}$: Container $n \ge t$ liegt zu Beginn der Periode $t$ auf Stapel $i$, Lage $j$. $x_{ijklnt}$: In Periode $t$ wird $n > t$ von $(i,j)$ nach $(k,l)$ umgelagert ($i \ne k$). Periode $t$ ist der Abruf des Containers $t$; seine Umlagerungen geschehen davor. Die Anfangsbucht legt $b_{ijn1}$ fest.

**Zielfunktion.** $\min \sum x_{ijklnt}$.

**Nebenbedingungen.**
- *Übergang:* $b_{ij,n,t+1} = b_{ijnt} - \sum_{k,l} x_{ijklnt} + \sum_{k,l} x_{klijnt}$ für $n > t$.
- *Platz:* Für die Layouts $t = 2, \dots, N$: $\sum_{i,j} b_{ijnt} = 1$ für jeden verbleibenden Container; $\sum_n b_{ijnt} \le 1$ je Platz; $\sum_n b_{i,j+1,n,t} \le \sum_n b_{ijnt}$ (nichts schwebt).
- *Restricted:* $\sum_{k,l,n} x_{ijklnt} \le \sum_{j_0 < j} b_{i j_0 t t}$ (nur Container über dem Ziel $t$ im Zielstapel) und $\sum_{k,l} x_{ijklnt} \le b_{ijnt}$ (ein Container kann nur von seinem Platz weg).
- *LIFO* (Korrektur (9) von Eskandari und Azari): $H \sum_n x_{ijklnt} + \sum_{j' > j} \sum_{l' > l} \sum_n x_{ij'kl'nt} \le H$. Der höher liegende Container wird zuerst umgelagert und liegt danach tiefer. Die Originalfassung (6) hat den Faktor $1$ statt $H$ und lässt höchstens eine solche Umlagerung je Stapelpaar zu.

Der **Abruf ist implizit:** Was über dem Ziel $t$ liegt, muss weg, sonst verletzt das Layout $t+1$ die Platz-Bedingung (ein Loch unter schwebenden Containern).

**Größe.** $|b| = W H \tfrac{N(N+1)}{2}$, $|x| = W (W-1) H^2 \tfrac{N(N-1)}{2}$: Das Modell wächst mit $N^2 W^2 H^2$.

**Literatur.** Das Modell BRP-II stammt von Caserta, Schwarze und Voß, European Journal of Operational Research 219 (2012), S. 96–104 (Fundstelle geprüft, Volltext **nicht** gelesen). Eskandari und Azari, Scientia Iranica 22(6), 2015, S. 2722–2728 (Volltext gelesen), zeigen, dass die Originalfassung fehlerhaft ist, und geben die Korrektur an; die Formeln hier sind eine eigene Umsetzung nach deren Wiedergabe mit Variablenreduktion, geprüft gegen die Suche und die Breitensuche der Reihe.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
