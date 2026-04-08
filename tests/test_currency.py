"""Currency math tests — confirms the game's actual ratios from Price.cs:467
  return copper + silver * 100 + gold * 10000;
"""


def to_copper(g, s, c):
    """Mirror the game's MPGKNMPCBOP() converter."""
    return g * 10000 + s * 100 + c


def from_copper(total):
    g = total // 10000
    s = (total % 10000) // 100
    c = total % 100
    return g, s, c


def test_round_trip():
    for g, s, c in [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
                    (13, 53, 67), (99, 99, 99), (1, 35, 67)]:
        cp = to_copper(g, s, c)
        assert from_copper(cp) == (g, s, c)


def test_known_values():
    # 135367 copper = 13g 53s 67c (the user's actual save value)
    assert from_copper(135367) == (13, 53, 67)
    # 1g = 10,000c
    assert to_copper(1, 0, 0) == 10000
    # 1s = 100c
    assert to_copper(0, 1, 0) == 100


def test_aging_multipliers():
    """From Money.CalculatePriceWithModifiers (dumps/Money.cs:418-426).
    Rank 2 = +10%, rank 3 = +20%, rank 4 = +30%."""
    from planner.plan.brewing import AGING_PRICE_MULT
    assert AGING_PRICE_MULT[0] == 1.0
    assert AGING_PRICE_MULT[1] == 1.0
    assert AGING_PRICE_MULT[2] == 1.10
    assert AGING_PRICE_MULT[3] == 1.20
    assert AGING_PRICE_MULT[4] == 1.30


def test_aging_hours():
    """From AgingBarrel.StartTimer (dumps/AgingBarrel.cs:950).
    24h per rank, 48h for the rank 3→4 step. Total = 5 days."""
    from planner.plan.brewing import AGING_HOURS_TO_REACH
    assert AGING_HOURS_TO_REACH[0] == 0
    assert AGING_HOURS_TO_REACH[1] == 24
    assert AGING_HOURS_TO_REACH[2] == 48
    assert AGING_HOURS_TO_REACH[3] == 72
    assert AGING_HOURS_TO_REACH[4] == 120


def test_trend_bonus():
    """From Trends.cs:64 — trendPriceMultiplier = 0.2f (flat +20%)."""
    from planner.plan.brewing import TREND_BONUS
    assert TREND_BONUS == 0.20
