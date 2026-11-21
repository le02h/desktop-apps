import pytest

from pomodoro.timer import FocusTimer, State

SECOND = 10**9


@pytest.mark.parametrize("minutes", [0, 181, -1, 2.5, "2", True])
def test_invalid_duration(minutes):
    timer = FocusTimer()
    assert not timer.configure(minutes)
    assert timer.minutes == 25


@pytest.mark.parametrize("minutes", [1, 180])
def test_elapsed_time_and_completion(minutes):
    timer = FocusTimer()
    assert timer.configure(minutes)
    timer.start(0, 0)
    assert not timer.configure(25)
    assert not timer.refresh(7_500_000_000)
    assert timer.remaining_ns == minutes * 60 * SECOND - 7_500_000_000
    assert timer.refresh(minutes * 60 * SECOND)
    assert timer.state is State.COMPLETE
    assert timer.remaining_ns == 0
    assert not timer.refresh(minutes * 60 * SECOND + SECOND)


@pytest.mark.parametrize("sleep_seconds", [10, 40, 50])
def test_suspend_resume(sleep_seconds):
    timer = FocusTimer()
    timer.configure(1)
    timer.start(0, 0)
    timer.suspend(20 * SECOND)
    assert not timer.refresh(25 * SECOND)
    assert timer.resume_system(20 * SECOND, (20 + sleep_seconds) * SECOND) == (
        sleep_seconds >= 40
    )
    assert not timer.resume_system(20 * SECOND, 90 * SECOND)
    assert timer.remaining_ns == (0 if sleep_seconds >= 40 else 40 * SECOND)
    if sleep_seconds < 40:
        timer.refresh(21 * SECOND)
        assert timer.remaining_ns == 39 * SECOND


def test_pause_continue_and_reset():
    timer = FocusTimer()
    timer.configure(2)
    timer.start(0, 0)
    timer.pause(10 * SECOND + 1)
    assert timer.state is State.PAUSED
    assert not timer.configure(1)
    timer.suspend(30 * SECOND)
    assert not timer.resume_system(30 * SECOND, 500 * SECOND)
    assert timer.remaining_ns == 110 * SECOND - 1
    timer.continue_session(30 * SECOND, 500 * SECOND)
    timer.refresh(31 * SECOND)
    assert timer.remaining_ns == 109 * SECOND - 1
    timer.reset()
    assert not timer.refresh(600 * SECOND)
    assert timer.state is State.READY
    assert timer.remaining_ns == 120 * SECOND


def test_pause_at_deadline_completes():
    timer = FocusTimer()
    timer.configure(1)
    timer.start(0, 0)
    assert timer.pause(60 * SECOND)
    assert timer.state is State.COMPLETE
    timer.reset()
    assert timer.remaining_ns == 60 * SECOND
