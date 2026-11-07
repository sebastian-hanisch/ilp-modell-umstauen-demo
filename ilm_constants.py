"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

STACKS_MIN, STACKS_MAX, DEFAULT_STACKS = 3, 5, 3          # Zahl der Stapel
LAYERS_MIN, LAYERS_MAX, DEFAULT_LAYERS = 2, 4, 3          # Anfangsfüllung je Stapel (Lagen)
EXTRA_MIN, EXTRA_MAX, DEFAULT_EXTRA = 1, 4, 2             # Platz: Höchsthöhe = Lagen + Zuschlag (Standard 2 wie in Stück 1 bis 6)
LIMIT_MIN, LIMIT_MAX, DEFAULT_LIMIT = 5, 30, 15           # Zeitlimit für das ILP live in Sekunden
SEED_MAX = 999999

LIVE_MAX_VARS = 60_000                                    # das ILP wird live nur gerechnet, wenn das Modell höchstens so viele Variablen hat (rund 15 Container)
SEARCH_CAP = 1_000_000                                    # Knotenlimit der Suche (live und in den Tabellen)
BAND_LIMIT = 60.0                                         # Zeitlimit der vorberechneten ILP-Läufe in Sekunden
SAMPLE_SEEDS = tuple(range(100))                          # feste Buchten: nie eine einzelne Bucht als Befund

# Zellen der vorberechneten Tabellen: (Stapel, Lagen, Zahl der festen Buchten). Dieselben Buchten wie in Stück 4 bis 6 (Seeds ab 0, Platz 2).
TIME_CELLS = ((3, 2, 20), (4, 2, 20), (3, 3, 20), (5, 2, 12), (4, 3, 12), (3, 4, 10), (5, 3, 8), (4, 4, 6))     # Größe und Zeit des ILP gegen die Suche (A)
LP_CELLS = ((3, 2, 20), (4, 2, 20), (3, 3, 20), (5, 2, 12), (4, 3, 12), (3, 4, 10))                            # LP-Wert gegen Optimum (B)
LPTIME_CELLS = ((3, 3, 8), (4, 3, 8), (3, 4, 8), (5, 3, 6), (4, 4, 4))                                         # Anteil des Wurzel-LP an der ILP-Zeit (B)
SOLVER_CELLS = ((3, 3, 10), (4, 3, 12), (3, 4, 10), (5, 3, 6))                                                 # HiGHS gegen CP-SAT, dasselbe Modell (C)
SEARCH_CELLS = ((4, 4, 20), (5, 4, 20), (6, 3, 10), (6, 4, 10), (5, 5, 10), (7, 4, 8), (6, 5, 8), (8, 4, 8))    # Wo bricht die Suche ein? (D)
FIX_CELLS = ((3, 2, 100), (4, 2, 60), (3, 3, 100), (3, 4, 20))                                                 # Gegenprobe: Originalfassung (6) gegen Korrektur (9)

SPEED_STRONG, SPEED_WEAK = 100.0, 10.0                    # Verdikt „die Suche ist schneller“: ILP-Sekunden / Suche-Sekunden
SOLVED_ALL_BELOW = 1.0                                    # Verdikt „das ILP bricht ein“: Anteil der in 60 s bewiesenen Läufe
LP_TIGHT = 0.5                                            # Verdikt „die LP-Schranke ist gut“: Optimum minus LP-Wert im Median höchstens so groß

COLOR_CELL = "#7a8fa6"
COLOR_BLOCK = "#b5545a"        # blockierend (liegt über einem früher abzurufenden)
COLOR_TARGET = "#2F6B65"       # nächster Abruf
COLOR_LIMIT = "#b5545a"        # Lauf am Zeit- oder Knotenlimit
COLOR_ILP, COLOR_SEARCH, COLOR_CPSAT, COLOR_LP, COLOR_LB = "#d9822b", "#2F6B65", "#4c78a8", "#7a8fa6", "#1c4742"
COLOR_LINES = ("#7a8fa6", "#2F6B65", "#d9822b", "#4c78a8")

# Sonderbuchten (in der Vormessung gefunden, Eigenschaften in tests/test_presets.py festgehalten)
MINI_SEED = 223        # 3 x 2: (5, 2), (1, 4), (6, 3) = der einzelne Blocker aus Stück 2 bis auf Vertauschen der Stapel: Modell mit 1 692 Variablen, Optimum 2
EVERYDAY_SEED = 12     # 3 x 3, Platz 2: ILP in unter einer halben Sekunde
SLOW_SEED = 4          # 3 x 4, Platz 2: ILP rund 4 bis 5 Sekunden, Suche wenige Millisekunden
GIVEUP_SEED = 0        # 4 x 3, Platz 2: ILP braucht über 50 Sekunden (Zeitlimit 5 s: kein Beweis), Suche unter einer Millisekunde
SEARCH_SEED = 2        # 5 x 4, Platz 2: Modell mit 143 100 Variablen (nicht gerechnet), Suche 31 Knoten
MINI_BAY = ((1, 4), (5, 2), (6, 3))                       # die Mini-Bucht des Modells von Hand (Stück 2: einzelner Blocker), Höchsthöhe 4
MINI_HEIGHT = 4
FIX_BAY = ((1, 6, 7, 8), (2, 3), (4, 5))                  # drei Blocker über der 1, Höchsthöhe 4: die Originalfassung (6) erklärt sie für unlösbar, das Optimum ist 8
FIX_HEIGHT = 4

PRESETS = {
    "Alltag (3 Stapel, 3 Lagen)": {"stacks": 3, "layers": 3, "extra": DEFAULT_EXTRA, "seed": EVERYDAY_SEED, "limit": DEFAULT_LIMIT},
    "Die Mini-Bucht": {"stacks": 3, "layers": 2, "extra": DEFAULT_EXTRA, "seed": MINI_SEED, "limit": DEFAULT_LIMIT},
    "Das ILP wird langsam (3 Stapel, 4 Lagen)": {"stacks": 3, "layers": 4, "extra": DEFAULT_EXTRA, "seed": SLOW_SEED, "limit": 30},
    "Das ILP gibt auf (4 Stapel, 3 Lagen)": {"stacks": 4, "layers": 3, "extra": DEFAULT_EXTRA, "seed": GIVEUP_SEED, "limit": LIMIT_MIN},
    "Die Suche trägt weiter (5 Stapel, 4 Lagen)": {"stacks": 5, "layers": 4, "extra": DEFAULT_EXTRA, "seed": SEARCH_SEED, "limit": DEFAULT_LIMIT},
}
PRESET_HELP = {
    "Alltag (3 Stapel, 3 Lagen)": "9 Container: das ILP hat rund 6 000 Variablen und löst die Bucht in einem Sekundenbruchteil, die Suche in unter einer Millisekunde.",
    "Die Mini-Bucht": "6 Container, ein einziger Blocker: das Modell hat 1 692 Variablen, das Optimum ist 2; die Suche braucht 6 Knoten.",
    "Das ILP wird langsam (3 Stapel, 4 Lagen)": "12 Container: das ILP braucht rund 4 bis 5 Sekunden, die Suche wenige Millisekunden (Zeitlimit 30 s).",
    "Das ILP gibt auf (4 Stapel, 3 Lagen)": "12 Container: das ILP findet in 5 Sekunden keinen Beweis, es braucht über 50 Sekunden; die Suche löst die Bucht in unter einer Millisekunde. Dauert rund 7 Sekunden.",
    "Die Suche trägt weiter (5 Stapel, 4 Lagen)": "20 Container: das Modell hätte 143 100 Variablen und wird nicht gerechnet; die Suche löst die Bucht mit 31 Knoten.",
}
