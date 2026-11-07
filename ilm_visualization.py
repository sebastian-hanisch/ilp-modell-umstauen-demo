"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import ilm_algorithm as A
import ilm_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def blocker_cells(stacks) -> set:
    """Container, die über einem früher abzurufenden im selben Stapel liegen (Position (Stapel, Lage))."""
    out = set()
    for i, s in enumerate(stacks):
        lowest = A.INF
        for j, c in enumerate(s):
            if c > lowest:
                out.add((i, j))
            else:
                lowest = c
    return out


def build_bay(stacks, height, target=None):
    """Die Bucht als Säulen: je Lage ein Balken mit der Abrufnummer. Rot: blockiert einen früher abzurufenden, grün: nächster Abruf
    (`target`, eine Abrufnummer oder None), grau-blau: übrige."""
    blockers = blocker_cells(stacks)
    fig = go.Figure()
    xs = list(range(len(stacks)))
    for j in range(height):
        ys, colors, texts = [], [], []
        for i, s in enumerate(stacks):
            if j < len(s):
                c = s[j]
                ys.append(1)
                texts.append(str(c))
                colors.append(C.COLOR_TARGET if c == target else C.COLOR_BLOCK if (i, j) in blockers else C.COLOR_CELL)
            else:
                ys.append(0)
                texts.append("")
                colors.append(C.COLOR_CELL)
        fig.add_trace(go.Bar(x=xs, y=ys, base=j, marker_color=colors, text=texts, textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="#ffffff", size=16), width=0.78, showlegend=False,
                             hovertemplate="Abruf %{text}<extra></extra>", marker_line=dict(width=0)))
    fig.update_layout(barmode="overlay")
    fig.add_hline(y=height, line_dash="dot", line_color="rgba(128,128,128,0.7)", annotation_text="Höchsthöhe", annotation_position="top left")
    fig.update_xaxes(tickvals=xs, ticktext=[f"Stapel {i + 1}" for i in xs], showgrid=False)
    fig.update_yaxes(range=[0, height + 0.35], showticklabels=False, showgrid=False, zeroline=False)
    return _base(fig, height=48 * height + 90)


def build_times(analysis_rows):
    """Zeit des ILP gegen die Suche an einer Bucht (logarithmisch, Millisekunden). `analysis_rows`: [{"name", "ms", "limit"}]; Läufe am Zeitlimit sind rot."""
    fig = go.Figure(go.Bar(x=[r["name"] for r in analysis_rows], y=[max(r["ms"], 0.01) for r in analysis_rows],
                           marker_color=[C.COLOR_LIMIT if r["limit"] else r["color"] for r in analysis_rows],
                           text=[r["text"] for r in analysis_rows], textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{text}<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Zeit in Millisekunden (logarithmisch)", type="log")
    return _base(fig, height=300)


def build_size(cells):
    """Variablen und Zeilen des Modells je Zelle, nach Containerzahl geordnet (logarithmisch). `cells`: {Zellname: time_stats}."""
    names = sorted(cells, key=lambda n: (cells[n]["containers"], cells[n]["variables"]))
    fig = go.Figure()
    for label, key, color in (("Variablen", "variables", C.COLOR_LINES[2]), ("Zeilen", "rows", C.COLOR_LINES[3])):
        fig.add_trace(go.Bar(x=[f"{n} ({cells[n]['containers']})" for n in names], y=[cells[n][key] for n in names], name=label, marker_color=color,
                             hovertemplate="%{x}: %{y:,.0f}<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", title_text="Zelle (Container)")
    fig.update_yaxes(title_text="Anzahl (logarithmisch)", type="log")
    return _base(fig, height=360)


def build_break(cells, limit):
    """Zeit des ILP (Median und Maximum) und der Suche (Median) über die Containerzahl, logarithmisch, mit dem Zeitlimit als gestrichelter Kurve. `cells`: {Zellname: time_stats}."""
    names = sorted(cells, key=lambda n: (cells[n]["containers"], cells[n]["variables"]))
    x = [f"{n} ({cells[n]['containers']})" for n in names]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=[cells[n]["time"]["median"] for n in names], mode="lines+markers", name="ILP, Median", line=dict(color=C.COLOR_ILP, width=3),
                             hovertemplate="%{x}: %{y:.2f} s<extra>%{fullData.name}</extra>"))
    fig.add_trace(go.Scatter(x=x, y=[cells[n]["time"]["max"] for n in names], mode="lines+markers", name="ILP, Maximum", line=dict(color=C.COLOR_ILP, width=2, dash="dot"),
                             hovertemplate="%{x}: %{y:.2f} s<extra>%{fullData.name}</extra>"))
    fig.add_trace(go.Scatter(x=x, y=[cells[n]["search_ms"]["median"] / 1000 for n in names], mode="lines+markers", name="Suche, Median", line=dict(color=C.COLOR_SEARCH, width=3),
                             hovertemplate="%{x}: %{y:.4f} s<extra>%{fullData.name}</extra>"))
    fig.add_trace(go.Scatter(x=[x[0], x[-1]], y=[limit, limit], mode="lines", name="Zeitlimit", line=dict(color="rgba(181,84,90,0.8)", width=2, dash="dash"),
                             hovertemplate="Zeitlimit %{y:.0f} s<extra></extra>"))                  # kein add_hline: auf einer Log-Achse liest Plotly y einer Form als Exponenten
    fig.update_xaxes(type="category", title_text="Zelle (Container)")
    fig.update_yaxes(title_text="Sekunden (logarithmisch)", type="log")
    return _base(fig, height=400)


def build_lp(cells):
    """LP-Wert, Optimum und Untergrenze je Zelle, Median (Balken). `cells`: {Zellname: lp_stats}."""
    names = list(cells)
    fig = go.Figure()
    for label, key, color in (("Untergrenze (Stück 2)", "lb", C.COLOR_LB), ("LP-Relaxation des ILP", "lp", C.COLOR_LP), ("Optimum", "opt", C.COLOR_SEARCH)):
        fig.add_trace(go.Bar(x=names, y=[cells[n][key] for n in names], name=label, marker_color=color, hovertemplate="%{x}: Median %{y:.2f}<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Median (Hübe)", rangemode="tozero")
    return _base(fig, height=340)


def build_solvers(cells):
    """HiGHS gegen CP-SAT auf demselben Modell: Summe der Zeiten je Zelle (logarithmisch). `cells`: {Zellname: solver_stats}."""
    names = list(cells)
    fig = go.Figure()
    for label, key, color in (("HiGHS", "highs", C.COLOR_ILP), ("CP-SAT", "cpsat", C.COLOR_CPSAT)):
        fig.add_trace(go.Bar(x=names, y=[cells[n][key]["sum"] for n in names], name=label, marker_color=color, hovertemplate="%{x}: %{y:.1f} s<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Summe der Zeiten in Sekunden (logarithmisch)", type="log")
    return _base(fig, height=340)


def build_search(cells):
    """Knoten der Suche (Median und Maximum) je Zelle, nach Containerzahl geordnet (logarithmisch); Zellen ohne fertigen Lauf fehlen. `cells`: {Zellname: search_stats}."""
    names = sorted((n for n in cells if cells[n]["nodes"]["median"] is not None), key=lambda n: cells[n]["containers"])
    x = [f"{n} ({cells[n]['containers']})" for n in names]
    fig = go.Figure()
    for label, key, color in (("Median", "median", C.COLOR_LINES[1]), ("Maximum", "max", C.COLOR_LINES[3])):
        fig.add_trace(go.Bar(x=x, y=[cells[n]["nodes"][key] for n in names], name=label, marker_color=color, hovertemplate="%{x}: %{y:,.0f} Knoten<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", title_text="Zelle (Container)")
    fig.update_yaxes(title_text="Knoten der Suche (logarithmisch)", type="log")
    return _base(fig, height=340)
