"""Tests for CeleryEventMonitor reconnect / backoff behaviour."""

from unittest.mock import MagicMock, patch

import pytest

from monitor import (
    CeleryEventMonitor,
    _RECONNECT_BASE_DELAY,
    _RECONNECT_MAX_DELAY,
    _RECONNECT_MULTIPLIER,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_monitor(broker_url: str = "redis://localhost/0") -> CeleryEventMonitor:
    """Return a monitor with a fully mocked Celery app."""
    with patch("monitor.Celery") as mock_celery_cls:
        mock_celery_cls.return_value = MagicMock()
        monitor = CeleryEventMonitor(broker_url=broker_url)
    return monitor


# ---------------------------------------------------------------------------
# stop() flag
# ---------------------------------------------------------------------------

class TestStopFlag:
    def test_stop_sets_flag(self):
        monitor = _make_monitor()
        assert not monitor._stop
        monitor.stop()
        assert monitor._stop

    def test_start_monitoring_exits_immediately_when_already_stopped(self):
        monitor = _make_monitor()
        monitor.stop()

        run_once_calls = []

        def fake_run_once():
            run_once_calls.append(1)

        monitor._run_once = fake_run_once
        monitor.start_monitoring()

        assert run_once_calls == [], "_run_once should never be called after stop()"


# ---------------------------------------------------------------------------
# Reconnect on error
# ---------------------------------------------------------------------------

class TestReconnectOnError:
    def test_reconnects_after_broker_error(self):
        """A connection error should not kill the loop; it should retry."""
        monitor = _make_monitor()

        call_count = {"n": 0}

        def fake_run_once():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise OSError("Connection closed by server.")
            monitor.stop()  # clean exit after 3rd attempt

        monitor._run_once = fake_run_once

        with patch("monitor.time.sleep"):  # don't actually sleep
            monitor.start_monitoring()

        assert call_count["n"] == 3

    def test_stop_during_sleep_exits_loop(self):
        """Calling stop() while sleeping between retries should cause an exit."""
        monitor = _make_monitor()
        call_count = {"n": 0}

        def fake_run_once():
            call_count["n"] += 1
            raise OSError("boom")

        def fake_sleep(delay):
            monitor.stop()  # simulate stop() being called from another thread

        monitor._run_once = fake_run_once

        with patch("monitor.time.sleep", side_effect=fake_sleep):
            monitor.start_monitoring()

        assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# Exponential backoff
# ---------------------------------------------------------------------------

class TestExponentialBackoff:
    def test_backoff_increases_on_repeated_errors(self):
        monitor = _make_monitor()
        sleeps = []
        call_count = {"n": 0}

        def fake_run_once():
            call_count["n"] += 1
            if call_count["n"] >= 5:
                monitor.stop()
                return
            raise OSError("error")

        def fake_sleep(delay):
            sleeps.append(delay)

        monitor._run_once = fake_run_once

        with patch("monitor.time.sleep", side_effect=fake_sleep):
            monitor.start_monitoring()

        # Delays should be non-decreasing and follow the multiplier
        for i in range(1, len(sleeps)):
            assert sleeps[i] >= sleeps[i - 1], "Backoff should not decrease"
        assert sleeps[-1] <= _RECONNECT_MAX_DELAY, "Delay must not exceed the cap"

    def test_backoff_capped_at_max(self):
        monitor = _make_monitor()
        sleeps = []
        call_count = {"n": 0}

        # Force enough failures to hit the cap
        iterations = 20

        def fake_run_once():
            call_count["n"] += 1
            if call_count["n"] > iterations:
                monitor.stop()
                return
            raise OSError("error")

        monitor._run_once = fake_run_once

        with patch("monitor.time.sleep", side_effect=lambda d: sleeps.append(d)):
            monitor.start_monitoring()

        assert all(d <= _RECONNECT_MAX_DELAY for d in sleeps)

    def test_backoff_resets_after_clean_close(self):
        """After a clean connection close, the next sleep uses the base delay."""
        monitor = _make_monitor()
        sleeps = []
        call_count = {"n": 0}

        def fake_run_once():
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise OSError("error")  # triggers backoff increase
            if call_count["n"] == 2:
                raise OSError("error")  # triggers more backoff
            if call_count["n"] == 3:
                return  # clean close → resets backoff
            monitor.stop()

        monitor._run_once = fake_run_once

        with patch("monitor.time.sleep", side_effect=lambda d: sleeps.append(d)):
            monitor.start_monitoring()

        # The clean close on attempt 3 triggers the else-branch which resets
        # delay to base and sleeps once before looping.  That sleep (the last
        # entry in sleeps[]) should be the base delay, not the backed-off value
        # accumulated from attempts 1 and 2.
        assert sleeps[-1] == _RECONNECT_BASE_DELAY


# ---------------------------------------------------------------------------
# State reset on reconnect
# ---------------------------------------------------------------------------

class TestStateReset:
    def test_state_is_reset_on_each_reconnect(self):
        """self.state must be a fresh Events.State on every connection attempt."""
        monitor = _make_monitor()
        states_seen = []
        call_count = {"n": 0}

        def fake_run_once():
            states_seen.append(monitor.state)
            call_count["n"] += 1
            if call_count["n"] >= 3:
                monitor.stop()
                return
            raise OSError("disconnected")

        monitor._run_once = fake_run_once
        monitor.app.events.State = MagicMock(side_effect=lambda: object())

        with patch("monitor.time.sleep"):
            monitor.start_monitoring()

        assert len(states_seen) == 3
        # Each attempt should have gotten a distinct State instance
        assert len(set(id(s) for s in states_seen)) == 3, (
            "state should be reset to a new object on each reconnect"
        )


# ---------------------------------------------------------------------------
# KeyboardInterrupt exits cleanly
# ---------------------------------------------------------------------------

class TestKeyboardInterrupt:
    def test_keyboard_interrupt_exits_without_reconnect(self):
        monitor = _make_monitor()
        call_count = {"n": 0}

        def fake_run_once():
            call_count["n"] += 1
            raise KeyboardInterrupt

        monitor._run_once = fake_run_once

        with patch("monitor.time.sleep") as mock_sleep:
            monitor.start_monitoring()

        assert call_count["n"] == 1
        mock_sleep.assert_not_called()
