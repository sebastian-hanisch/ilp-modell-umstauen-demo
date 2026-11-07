"""Gemeinsame Fixtures: die Mini-Buchten, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Die Mini-Bucht (einzelner Blocker aus Stück 2): 3 Stapel mit je 2 Containern, Höchsthöhe 4, von unten nach oben (1, 4), (5, 2), (6, 3). Untergrenze 1, Optimum 2.

    Handrechnung des Modells (W = 3, H = 4, N = 6): Variablen b: W*H*N*(N+1)/2 = 12 * 21 = 252; Variablen x: W*(W-1)*H^2 * N*(N-1)/2 = 96 * 15 = 1 440; zusammen 1 692.
    Zeilen: 1 020 (Formel in ilm_model.model_size). Die 4 muss in Periode 1 weg (liegt über der 1) und kommt in Periode 2 oder 3 noch einmal in den Weg: 2 Umlagerungen."""
    return ((1, 4), (5, 2), (6, 3)), 4


@pytest.fixture
def counter():
    """Das Gegenbeispiel aus Stück 1: (3, 6), (2, 4), (1, 5), Höchsthöhe 4. Untergrenze 3, Optimum 4; dasselbe Modell wie die Mini-Bucht (gleiche W, H, N)."""
    return ((3, 6), (2, 4), (1, 5)), 4


@pytest.fixture
def fix():
    """Drei Blocker über der 1: (1, 6, 7, 8), (2, 3), (4, 5), Höchsthöhe 4. Optimum 8; die Originalfassung (6) der LIFO-Nebenbedingung erklärt die Bucht für unlösbar."""
    return ((1, 6, 7, 8), (2, 3), (4, 5)), 4
