from ager.gameplay.rules import BUILDINGS, default_rules


def test_rules_monotonicity_and_bounds():
    """Test that rules follow monotonic growth and stay within bounds."""
    r = default_rules()

    for b in BUILDINGS:
        # Level 1 should have positive values
        assert r.rate(b, 1) > 0
        assert r.cost(b, 1) > 0
        assert r.duration_s(b, 1) > 0

        # Test monotonicity (each level should be higher than previous)
        prev_rate = r.rate(b, 1)
        prev_cost = r.cost(b, 1)
        prev_duration = r.duration_s(b, 1)

        for lvl in range(2, 21):
            cur_rate = r.rate(b, lvl)
            cur_cost = r.cost(b, lvl)
            cur_duration = r.duration_s(b, lvl)

            assert cur_rate > prev_rate, f"{b} rate not monotonic at level {lvl}"
            assert cur_cost > prev_cost, f"{b} cost not monotonic at level {lvl}"
            assert (
                cur_duration > prev_duration
            ), f"{b} duration not monotonic at level {lvl}"

            prev_rate = cur_rate
            prev_cost = cur_cost
            prev_duration = cur_duration


def test_rules_formulas():
    """Test that rules formulas match specifications."""
    r = default_rules()

    # Test lumber_mill at specific levels
    # Level 1: base = 60.0
    assert abs(r.rate("lumber_mill", 1) - 60.0) < 0.01

    # Level 5: 60.0 * (1.15 ** 4) ≈ 104.94
    assert abs(r.rate("lumber_mill", 5) - 104.94) < 0.1

    # Level 10: 60.0 * (1.15 ** 9) ≈ 211.07
    assert abs(r.rate("lumber_mill", 10) - 211.07) < 1.0


def test_rules_version():
    """Test that rules have correct version."""
    r = default_rules()
    assert r.version == "v1"
