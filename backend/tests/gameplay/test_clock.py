from datetime import UTC, datetime

from ager.gameplay.clock import FixedClock, SystemClock


def test_system_clock_returns_current_time():
    """Test that SystemClock returns current UTC time."""
    clock = SystemClock()
    before = datetime.now(UTC)
    now = clock.now()
    after = datetime.now(UTC)

    assert before <= now <= after
    assert now.tzinfo == UTC


def test_fixed_clock_returns_fixed_time():
    """Test that FixedClock always returns the same fixed time."""
    fixed_time = datetime(2025, 10, 22, 14, 30, 0, tzinfo=UTC)
    clock = FixedClock(fixed_time)

    # Multiple calls should return same time
    assert clock.now() == fixed_time
    assert clock.now() == fixed_time
    assert clock.now().tzinfo == UTC


def test_fixed_clock_adds_timezone_if_missing():
    """Test that FixedClock adds UTC timezone if not provided."""
    naive_time = datetime(2025, 10, 22, 14, 30, 0)  # No timezone
    clock = FixedClock(naive_time)

    result = clock.now()
    assert result.tzinfo == UTC
    assert result.year == 2025
    assert result.month == 10
    assert result.day == 22
