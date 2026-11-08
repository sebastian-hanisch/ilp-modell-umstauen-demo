# Das ILP-Modell: wo bricht es ein? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-ilp-modell-umstauen-demo.streamlit.app/)** -->

Siebtes Stück der Konzepte-Reihe **„Umstauen: Untergrenze und Suche“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. [Stück 5](https://sebastianhanisch-iterative-vertiefung-umstauen-demo.streamlit.app/) und [Stück 6](https://sebastianhanisch-gleiche-zustaende-umstauen-demo.streamlit.app/) haben die **Suche** gebaut. Dieses Stück stellt ihr das **ganzzahlige lineare Programm (ILP)** gegenüber: ein zeitindiziertes Modell mit einer 0-1-Variable je Container, Platz und Periode, das HiGHS exakt löst. Die Demo **rechnet es live** auf kleinen Buchten, zeigt die Lösung als Umlagerungsfolge und misst vorberechnet, **wo es einbricht**, **warum** und **wo die Suche noch trägt**.

## Warum dieses Problem

Ein Modell lässt sich leicht hinschreiben und einem Löser übergeben; die Frage ist, wie weit es trägt. Hier trägt es nicht weit, **obwohl es korrekt ist und die LP-Schranke bis 12 Container (4 × 3) gut ist** (bei 3 × 4 bleibt eine Lücke von im Median 1). Die Gründe sind die **Größe** (Variablen wachsen mit *N*² · *W*² · *H*²) und ein **schwerer Schwanz** weniger schwieriger Buchten. Die Suche aus Stück 5 und 6 löst dieselben Buchten in Millisekunden und trägt bis 32 Container. Die Hypothese der Gliederung („das ILP bricht bei deutlich kleinerer Blockzahl ein als die Suche“) trifft **der Richtung nach** zu; die Zahlen der Literatur (30 gegen 70) werden nicht reproduziert.

## Modell

**Zeitindiziertes ILP**, ein Nachbau des Modells **BRP-II in der korrigierten Fassung (BRP2c)** aus Eskandari und Azari (Scientia Iranica 22(6), 2015, S. 2722 bis 2728, Volltext gelesen). Das Modell geht auf Caserta, Schwarze und Voß (European Journal of Operational Research 219, 2012) zurück, deren Arbeit im Volltext **nicht** gelesen wurde. Eskandari und Azari zeigen, dass die **Originalfassung** von BRP-II fehlerhaft ist (die LIFO-Nebenbedingung (6) lässt höchstens eine Umlagerung je Stapelpaar und Periode zu); ihre Korrektur (9) multipliziert die linke Seite mit *H*. Verwendet wird nur die korrigierte Fassung, **eigene Umsetzung** mit Variablenreduktion (nur *n* ≥ *t*, nur *i* ≠ *k*), gelöst mit HiGHS über `scipy.optimize.milp`.

- **Perioden:** Periode *t* ist der Abruf des Containers *t*; die Umlagerungen geschehen davor.
- **Variablen:** *b[i,j,n,t]* (Container *n* liegt zu Beginn der Periode *t* auf Stapel *i*, Lage *j*) und *x[i,j,k,l,n,t]* (in Periode *t* wird *n* von (*i*,*j*) nach (*k*,*l*) umgelagert). Alle binär.
- **Zielfunktion:** Zahl der Umlagerungen.
- **Nebenbedingungen:** Übergang der Layouts; Platz und Schwerkraft; nur Container über dem Ziel werden bewegt (restricted); LIFO der Umlagerungen aus einem Stapel (die Korrektur (9)). Der Abruf ist implizit: Was über dem Ziel liegt, muss weg, sonst schwebt im nächsten Layout etwas.
- **Größe:** Variablen = *W* · *H* · *N* (*N* + 1) / 2 + *W* (*W* − 1) *H*² · *N* (*N* − 1) / 2 mit der Höchsthöhe *H* (Lagen + Platz, Standard 2). Formal im Expander „📐 Mathematische Formulierung“.
- **Suche** zum Vergleich: IDA\* mit Untergrenze und Zustandsmerken (Stück 5 und 6), Python.

## Methodik

- **Live:** Das ILP wird nur gerechnet, wenn das Modell höchstens 60 000 Variablen hat (rund 15 Container), mit einstellbarem Zeitlimit (5 bis 30 s, Standard 15 s). Bei Zeitlimit gibt es **keinen** bewiesenen Optimalwert; die Demo behauptet keinen. Darüber zeigt sie die Modellgröße aus der Formel und „nicht gerechnet“.
- **Vorberechnet** (`ilm_bands.json`, erzeugt von `generate_precomputed.py`, rund 20 bis 25 Minuten): ILP-Zeit und Größe in acht Zellen gegen die Suche; LP-Wert gegen Optimum; Anteil des Wurzel-LP an der ILP-Zeit; HiGHS gegen CP-SAT auf demselben Modell (CP-SAT nur offline, Ordner `offline/`, nicht in `requirements.txt`); die Suche auf größeren Buchten; die Originalfassung der LIFO-Nebenbedingung gegen die Korrektur. Die Zeitreihe läuft in **einem** Prozess nacheinander, die übrigen Auswertungen laufen in anderen Prozessen daneben.
- **Alle Zeiten sind Einzelmessungen** (Windows, Python, ein Lauf) und schwanken: Dieselbe Bucht (4 × 3, Nr. 0) brauchte in zwei Läufen 61,9 und 55,6 s; die Zahl der Buchten ohne Beweis in 60 s wechselte zwischen zwei Messläufen (5 × 3: 2 gegen 1 von 8, 4 × 4: 3 gegen 1 von 6). Das ILP läuft in C++ (HiGHS), die Suche in Python: **Sekunden sind kein reines Maß der Methoden.**
- **Abschnitte der App:** Ergebnis (live); das Modell von Hand mit der Mini-Bucht und der Gegenprobe der LIFO-Korrektur; wie das Modell wächst; wo das ILP einbricht; warum; ein zweiter Löser; wo die Suche einbricht; wie oft die Korrektur einen Unterschied macht.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an den festen Buchten 0 bis (Zahl der Buchten − 1) je Zelle bei Platz 2 (Python-Zufallsfolge, `random.shuffle`, **dieselben Buchten wie in Stück 4 bis 6**), nachgerechnet in `tests/test_claims.py`, `tests/test_presets.py` und `tests/test_oracle_ilp_modell_umstauen.py`. **Zeiten sind die gespeicherten Einzelmessungen.**

**A: Größe und Zeit** (Zeitlimit 60 s je ILP; ILP-Zeit Median / Maximum über alle Läufe; Suche = IDA\* mit Merken)

| Zelle (Container), Buchten | Variablen | Zeilen | ILP bewiesen | ILP-Zeit Median / Maximum | Suche Median / Maximum |
|---|---|---|---|---|---|
| 3 × 2 (6), 20 | 1 692 | 1 020 | 20 / 20 | 0,04 s / 0,10 s | 0,1 ms / 0,2 ms |
| 4 × 2 (8), 20 | 5 952 | 2 576 | 20 / 20 | 0,15 s / 0,64 s | 0,1 ms / 0,3 ms |
| 3 × 3 (9), 20 | 6 075 | 2 652 | 20 / 20 | 0,21 s / 2,13 s | 0,3 ms / 0,9 ms |
| 5 × 2 (10), 12 | 15 500 | 5 220 | 12 / 12 | 0,43 s / 0,64 s | 0,2 ms / 0,4 ms |
| 3 × 4 (12), 10 | 15 660 | 5 379 | 10 / 10 | 2,53 s / 25,1 s | 1,5 ms / 8,4 ms |
| 4 × 3 (12), 12 | 21 360 | 6 622 | **11 / 12** | 1,39 s / **60,3 s** | 0,4 ms / 3,0 ms |
| 5 × 3 (15), 8 | 55 500 | 13 335 | **7 / 8** | 11,4 s / 60,9 s | 0,4 ms / 1,7 ms |
| 4 × 4 (16), 6 | 55 104 | 13 380 | **5 / 6** | 33,2 s / 60,8 s | 5,0 ms / 26 ms |

In allen 105 bewiesenen Läufen stimmt das ILP-Optimum mit der Suche überein (0 falsche Werte). „Nicht fertig“ heißt: Status Zeitlimit, kein Beweis. Die Zeiten nicht fertiger Läufe liegen über dem Limit (HiGHS überschreitet es; in der gespeicherten Messung bei unbelasteter Maschine um bis zu 2 %, unter Last deutlich mehr).

**B: Warum? LP-Relaxation und Zeit** (Median über die Buchten der Zelle; LP-Wert = Integralität aufgehoben)

| Zelle (Buchten) | LP-Wert | Optimum | Untergrenze | Optimum − LP-Wert (Median, Maximum) | LP-Wert gleich Optimum |
|---|---|---|---|---|---|
| 3 × 2 (20) | 2 | 2 | 2 | 0, 0 | 20 von 20 |
| 4 × 2 (20) | 2 | 2 | 2 | 0, 0 | 20 von 20 |
| 3 × 3 (20) | 5 | 5 | 3,5 | 0, 1 | 16 von 20 |
| 5 × 2 (12) | 3 | 3 | 2,5 | 0, 0 | 12 von 12 |
| 4 × 3 (12) | 5,5 | 6 | 4 | 0, 1 | 9 von 12 |
| 3 × 4 (10) | 8,5 | 9,5 | 6 | 1, 4 | 4 von 10 |

| Zelle (Buchten) | LP-Zeit Summe | ILP-Zeit Summe | Anteil des Wurzel-LP | Optimum − LP-Wert (Median, Maximum) |
|---|---|---|---|---|
| 3 × 3 (8) | 0,93 s | 3,34 s | 28 % | 0, 1 |
| 4 × 3 (8) | 3,58 s | 72,6 s | 5 % | 0, 1 |
| 3 × 4 (8) | 3,25 s | 51,7 s | 6 % | 0,5, 4 |
| 5 × 3 (6) | 7,09 s | 130,0 s | 5 % | 0, 0 |
| 4 × 4 (4) | 6,30 s | 120,2 s | 5 % | 1, 1 |

**C: Zweiter Löser, dasselbe Modell** (CP-SAT, ein Worker, Zeitlimit 60 s; HiGHS in diesem Lauf neu gerechnet; Median / Summe der Zeiten, richtig bewiesen)

| Zelle (Buchten) | HiGHS | CP-SAT | CP-SAT schneller um |
|---|---|---|---|
| 3 × 3 (10) | 0,22 s / 4,41 s, 10 / 10 | 0,19 s / 2,39 s, 10 / 10 | 1,8-fach |
| 4 × 3 (12) | 1,37 s / 81,5 s, 11 / 12 | 1,01 s / 28,5 s, 12 / 12 | 2,9-fach |
| 3 × 4 (10) | 3,14 s / 57,8 s, 10 / 10 | 0,93 s / 15,6 s, 10 / 10 | 3,7-fach |
| 5 × 3 (6) | 4,50 s / 115,5 s, 5 / 6 | 2,66 s / 57,3 s, 6 / 6 | 2,0-fach |

**D: Wo bricht die Suche ein?** (IDA\* mit Merken, Knotenlimit 1 000 000, Python; Knoten und Zeit der fertigen Läufe; Blocker = Untergrenze, Median)

| Zelle (Container), Buchten | fertig | Blocker | Knoten Median / Maximum | Zeit Median / Maximum |
|---|---|---|---|---|
| 4 × 4 (16), 20 | 20 / 20 | 7 | 251 / 2 299 | 4 ms / 34 ms |
| 5 × 4 (20), 20 | 20 / 20 | 10,5 | 415 / 56 710 | 8 ms / 1,01 s |
| 6 × 3 (18), 10 | 10 / 10 | 6 | 46 / 206 | 1 ms / 3 ms |
| 6 × 4 (24), 10 | **9 / 10** | 11,5 | 2 228 / 72 284 | 37 ms / 1,69 s |
| 5 × 5 (25), 10 | 10 / 10 | 14 | 13 260 / 283 134 | 0,37 s / 6,69 s |
| 7 × 4 (28), 8 | 8 / 8 | 14,5 | 1 483,5 / 167 214 | 38 ms / 3,93 s |
| 6 × 5 (30), 8 | **7 / 8** | 17 | 65 510 / 309 392 | 1,42 s / 6,26 s |
| 8 × 4 (32), 8 | 8 / 8 | 16 | 658 / 151 730 | 13 ms / 3,99 s |

**E: Die Korrektur der LIFO-Nebenbedingung** (Originalfassung (6) gegen die Suche; mit der Korrektur (9) stimmen alle Buchten)

| Zelle (Buchten) | unlösbar | anderer Wert | richtig |
|---|---|---|---|
| 3 × 2 (100) | 0 | 0 | 100 |
| 4 × 2 (60) | 0 | 0 | 60 |
| 3 × 3 (100) | 12 | 13 | 75 |
| 3 × 4 (20) | 11 | 4 | 5 |

| Frage | Befund |
|---|---|
| **Ist das Modell korrekt?** | Ja, in allen geprüften Fällen: das ILP-Optimum gleicht dem der Breitensuche und der Suche in 220 von 220 Buchten (alle 120 3 × 2-Buchten bis auf Stapelvertauschen, 60 × 4 × 2, 40 × 3 × 3); jede Lösung wird mit einem eigenen Simulator nach den Regeln nachgespielt; die optimale Hubfolge der Breitensuche ist ein zulässiger Punkt des Modells (Zertifikat). Mini-Bucht und Gegenbeispiel aus Stück 1: Optimum 2 und 4 bei **1 692 Variablen und 1 020 Zeilen** (dasselbe Modell, gleiche *N*, *W*, *H*). |
| **Wie wächst das Modell?** | Von 1 692 Variablen (6 Container) über 6 075 (9), 21 360 (12, 4 × 3) auf rund **55 000 bei 15 bis 16 Containern**; das Wachstum folgt *N*² · *W*² · *H*² (die Formel stimmt mit dem gebauten Modell in jeder Zelle überein). |
| **Wo bricht das ILP ein?** | Im Median von 0,04 s (6 Container) über 0,21 s (9) und 1,4 bis 2,5 s (12) auf 11 s (15) und 33 s (16). **Zuverlässig fertig** in 60 s sind alle Zellen bis 10 Container; ab **12 Containern** bleiben je Zelle ein bis drei Buchten ohne Beweis (je nach Messlauf und Rechnerlast; 4 × 3: ein bis zwei von 12, 5 × 3: ein bis drei von 8, 4 × 4: ein bis drei von 6). Der **Schwanz** ist schwer: das Maximum liegt bei 4 × 3 beim 43-Fachen des Medians. |
| **Und die Suche?** | Dieselben Buchten in höchstens 26 ms (Median höchstens 5 ms). Sie trägt bis **32 Container mit 16 bis 17 Blockern** (Median höchstens 1,4 s), bei 6 × 4 und 6 × 5 liegt je eine Bucht über einer Million Knoten. Die **Grenze der Suche ist nicht gefunden.** Das ILP lässt ab **12 Containern** je Zelle Buchten ohne Beweis in 60 s; bei der Suche tritt das erst ab **24 Containern** auf (je eine Bucht über einer Million Knoten). Die Suche trägt also **mindestens etwa doppelt so weit**; ihre Grenze ist nicht gefunden. |
| **Ist die LP-Schranke schwach?** | Bis 12 Container (4 × 3) nein, bei 3 × 4 bleibt eine Lücke von im Median 1: Der LP-Wert liegt im Median **auf dem Optimum** (3 × 2 bis 5 × 2), bei 4 × 3 bei 5,5 gegen 6, bei 3 × 4 bei 8,5 gegen 9,5; Optimum minus LP-Wert im Median 0 (3 × 4: 1), höchstens 4. Die Untergrenze aus Stück 2 liegt darunter (Median 3,5 bei 3 × 3, 4 bei 4 × 3, 6 bei 3 × 4). |
| **Wo steckt die Zeit?** | Das Wurzel-LP kostet **5 bis 9 %** der ILP-Zeit (bei 3 × 3 bis 28 %, je nach Lauf); wie sich der Rest auf Verzweigung, Presolve und Heuristiken verteilt, ist nicht gemessen. |
| **Hängt das vom Löser ab?** | CP-SAT ist auf diesem Modell in allen vier Zellen schneller (**1,4- bis 3,7-Fache** je Lauf) und beweist in zwei Zellen eine Bucht mehr. Bis 15 Container sieht die Skalierung ähnlich aus (CP-SAT nur dort gerechnet, ein Worker): Die Lage der Grenze hängt etwas vom Löser ab. |
| **Braucht das Modell die Korrektur?** | Ja: Mit der Originalfassung (6) sind bei 3 × 3 **12 von 100** Buchten unlösbar und **13** haben einen anderen Wert, bei 3 × 4 15 von 20; bei 3 × 2 und 4 × 2 macht sie keinen Unterschied. Ein Beispiel mit drei Blockern über der 1 ((1, 6, 7, 8), (2, 3), (4, 5), Höchsthöhe 4): Korrektur Optimum 8, Originalfassung unlösbar. |
| **Die Mini-Bucht** | (1, 4), (5, 2), (6, 3), Höchsthöhe 4: Das Modell hat 1 692 Variablen, 1 020 Zeilen und 11 700 Nichtnullen, der LP-Wert ist 2, das Optimum 2: Die 4 blockiert die 1 und wird zweimal umgelagert (einmal in Periode 1, einmal später). Die Suche braucht 6 Knoten. |

**Presets** (Eigenschaften in `tests/test_presets.py`): „Alltag“ (3 × 3, Bucht 12: 6 075 Variablen, ILP beweist 5 in einem Sekundenbruchteil, Suche 11 Knoten), „Die Mini-Bucht“ (3 × 2, Bucht 223), „Das ILP wird langsam“ (3 × 4, Bucht 4, Zeitlimit 30 s: ILP rund 4 bis 5 s, Suche wenige ms, Optimum 13), „Das ILP gibt auf“ (4 × 3, Bucht 0, Zeitlimit 5 s: ILP findet keinen Beweis, braucht über 50 s; Optimum 10 durch die Suche; die Berechnung dauert rund 7 Sekunden), „Die Suche trägt weiter“ (5 × 4, Bucht 2: Modell mit 143 100 Variablen nicht gerechnet, Suche 31 Knoten, Optimum 9).

**Korrektur gegenüber dem Plan:** Der Plan nannte „in 60 s nicht fertig: 1 von 12 (4 × 3), 2 von 8 (5 × 3), 3 von 6 (4 × 4)“ aus der Vormessung; der gespeicherte Messlauf der Demo liefert 1, 1 und 1 (HiGHS ist von Lauf zu Lauf unterschiedlich schnell). CP-SAT ist 1,8- bis 3,7-fach schneller (Plan: 1,5- bis 3-fach). Die Originalfassung (6) liefert bei 3 × 3 in 25 von 100 Buchten ein falsches Ergebnis (in den ersten 60 sind es 13). Die Zeiten der Suche bei 6 × 4 (Maximum 1,69 s) und 6 × 5 (6,26 s) liegen unter den Vormesswerten (26,2 und 21,8 s), die unter Last entstanden. **Die Kernaussage (korrekt, aber Größe und Schwanz; die Suche trägt mindestens etwa doppelt so weit) trägt in beiden Läufen.**

## Ehrliche Grenzen

- **Zeiten sind Einzelmessungen** (ein Lauf, eine Windows-Maschine); dieselbe Bucht brauchte 61,9 und 55,6 s. Die Grenze „bricht ein“ ist weich und hängt vom Zeitlimit ab (hier 60 s). Das ILP läuft in C++, die Suche in Python.
- **Ein Modell.** Das ILP ist die zeitindizierte Formulierung (korrigiertes BRP-II). Stärkere Modelle (Zehendner u. a. 2015, Petering und Hussein 2013) sind nicht gebaut und nicht gelesen; der Befund gilt für dieses Modell, **nicht** für das beste bekannte.
- **Kleine Zellen:** 5 × 3 mit 8 und 4 × 4 mit 6 Buchten; der Anteil „nicht fertig“ ist dort grob.
- **Die Grenze der Suche ist nicht gefunden,** nur bis 8 × 4 (32 Container) gemessen.
- **Eigene Buchtfamilie:** Höchsthöhe = Lagen + 2; die Instanzen der Literatur (aus Beispiel 2 der Note von Eskandari und Azari abgeleitet: ein freier Stapel, keine Zusatzlagen) sind nicht nachgebaut. Die Zahlen der Literatur (CPLEX 12.1, Intel i3, 900 s) sind nicht vergleichbar; die Tabelle der Note ist im Textauszug stellenweise verstümmelt.
- **Die Originalarbeit** Caserta u. a. (2012) wurde nicht gelesen; das Modell stammt aus der Wiedergabe in Eskandari und Azari.
- **Nur restricted, nur volle Buchten, Platz 2 in den Tabellen.** Mit anderer Hubmenge (Stück 3) oder anderer Füllung ändern sich Größe und Zeit.
- **Zahlen aus Zufallsbuchten:** feste Buchten aus der Zufallsfolge von Python, keine Messung an einem echten Terminal oder Lager; die CI prüft die Zahlen unter Linux (Zeiten nicht).

## Verifikation

- **Kern:** Modellgröße (Formel gegen gebautes Modell in sechs Zellen und zwei Plätzen, Handzahlen 1 692 / 1 020 / 11 700), Lösung der Mini-Bucht von Hand, Zielwert, LP-Wert, Reihenfolge der Umlagerungen (von oben nach unten), Status „Zeitlimit“ ohne Optimalwert, Status „unlösbar“ ohne Platz, Eingabeprüfung, Koeffizienten der Matrix (±1 und der Faktor *H* der Korrektur).
- **Orakel:** ILP-Optimum gegen eine **Breitensuche** über alle Zustände (alle 3 × 2-Buchten, 4 × 2, 3 × 3) und gegen die Suche; jede ILP-Lösung in einem **eigenen Simulator** nachgespielt; **Zertifikat**: die optimale Hubfolge der Breitensuche, übersetzt in Variablen, erfüllt jede Nebenbedingung mit dem Zielwert des Optimums; ein beschädigter Punkt verletzt eine; bei drei Blockern verletzt dieselbe Hubfolge die Originalfassung (6); die Originalfassung liefert bei 3 × 3 in 13 von 60 Buchten falsche Ergebnisse.
- **Eigenschaften:** LP-Wert ≤ Optimum, Untergrenze ≤ Optimum, keine Heuristik schlägt das ILP, das Optimum ändert sich nicht beim Vertauschen der Stapel, Modellgröße wächst monoton.
- **Zahlen im README:** jede Zahl der Befunde in `tests/test_claims.py` (gespeicherte Messwerte; Strukturen, Verhältnisse, Zuordnungen); kleine Zellen gegen eine frische Rechnung, soweit sie nicht von der Zeit abhängen (`tests/test_presets.py`).
- **Verdikte:** reine Funktionen, jede Schwelle (Suche 10- und 100-fach schneller, LP-Lücke 0,5) und jede genannte Zahl an von Hand gesetzten Werten (`tests/test_verdicts.py`).
- **Presets und Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum), Inhalt (Kennzahlen je Preset ohne feste Zeiten, Tabellenzeilen, Gegenprobe, Permalink), Layout (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben, jede Reglerwirkung), Footer, Laufzeit-Importe (`scipy`, `numpy`; `ortools` nur offline).
- **Abbildungen:** Farben je Rolle des Containers, feste Achsen, logarithmische Achsen, Zeitlimit als Linie.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Aufbau nach DEMO-PLAYBOOK §2) |
| `generate_precomputed.py` | erzeugt `ilm_bands.json` (Zeit, LP, LP-Zeit, Löser, Suche, Korrektur) |
| `offline/` | CP-SAT auf demselben Modell (nur für die Tabelle, `ortools` nicht in `requirements.txt`) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt): streamlit, plotly, scipy, numpy |
| `ilm_algorithm.py` | Suche (IDA\* mit Untergrenze und Merken) und Simulator der Umlagerungen |
| `ilm_bands.json` | vorberechnete Kennzahlen der festen Buchten je Zelle |
| `ilm_constants.py` | Regler-Grenzen, Limits, Zellen, Farben, Sonderbuchten, Presets |
| `ilm_evaluation.py` | Analyse einer Bucht, Stichproben, Verdikte (reine Funktionen) |
| `ilm_layout.py` | Fester Kopf (Stylesheet), Tabellen scrollen im eigenen Rahmen |
| `ilm_model.py` | das ILP: Größe aus der Formel, Bau, Lösen (HiGHS), LP-Wert, Umlagerungen aus der Lösung |
| `ilm_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `ilm_scenario.py` | Buchten (volle Buchten, Zufallsbuchten) |
| `ilm_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Zertifikat, Gegenprobe, Randfälle, Behauptungen, Verdikte, Presets, Abbildungen, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Ein stärkeres ILP** (Zehendner u. a. 2015, Petering und Hussein 2013) und **Branch and Price** (Stück 8).
- **Die Instanzfamilie der Literatur** (erst nach Lesen der Primärquelle).
- **Eine Zeitmessung in der CI:** Zeiten schwanken.
- **Das ILP live jenseits von 60 000 Variablen.**
- **PDF-Export:** nicht vorgesehen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

145 Tests, rund 270 Sekunden (eine Messung unter Windows; das ILP wird live gerechnet).

Gebaut mit Streamlit, Plotly, SciPy (HiGHS).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
