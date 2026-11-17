"""Tests for download retry behavior."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import logging
import tempfile
import unittest
from unittest import mock

from garmindb.download import Download
from garmindb.garmin_connect_auth_adapter import GarminConnectNotFoundError, GarminConnectRateLimitError


class FakeConfig:
    """Minimal config stub for Download tests."""

    def get_session_file(self):
        return "/tmp/garth_session"

    def get_garmin_base_domain(self):
        return "garmin.com"


class TestDownload(unittest.TestCase):
    def setUp(self):
        self.download = Download(FakeConfig())

    def test_get_stat_retries_until_success(self):
        attempts = []

        def flaky_stat(directory, day, overwrite):
            attempts.append((directory, day, overwrite))
            if len(attempts) < 3:
                raise RuntimeError("temporary HRV gap")

        start_date = datetime.date(2026, 3, 1)
        with mock.patch("garmindb.download.time.sleep"):
            self.download._Download__get_stat(flaky_stat, "/tmp/hrv", start_date, 1, False)

        self.assertEqual(len(attempts), 3)
        self.assertEqual(attempts[0][0], "/tmp/hrv")
        self.assertEqual(attempts[0][1], start_date)

    def test_get_stat_stops_after_five_failures(self):
        attempts = []

        def always_fail(directory, day, overwrite):
            attempts.append((directory, day, overwrite))
            raise RuntimeError("persistent HRV gap")

        start_date = datetime.date(2026, 3, 1)
        with mock.patch("garmindb.download.time.sleep"):
            self.download._Download__get_stat(always_fail, "/tmp/hrv", start_date, 1, False)

        self.assertEqual(len(attempts), 5)

    def test_get_stat_stops_on_rate_limit_without_retry(self):
        attempts = []

        def rate_limited(directory, day, overwrite):
            attempts.append(day)
            raise GarminConnectRateLimitError("too many requests (HTTP 429)")

        start_date = datetime.date(2026, 3, 1)
        with mock.patch("garmindb.download.time.sleep") as sleep:
            with self.assertRaises(GarminConnectRateLimitError):
                self.download._Download__get_stat(rate_limited, "/tmp/hrv", start_date, 10, False)

        self.assertEqual(attempts, [start_date])
        sleep.assert_not_called()

    def test_get_stat_stops_on_not_found_without_retry(self):
        attempts = []

        def missing_day(directory, day, overwrite):
            attempts.append(day)
            raise GarminConnectNotFoundError("404 Client Error: Not Found")

        start_date = datetime.date(2026, 3, 1)
        with mock.patch("garmindb.download.time.sleep") as sleep:
            self.download._Download__get_stat(missing_day, "/tmp/daily", start_date, 10, False)

        # one attempt per day, no retries of the 404
        self.assertEqual(attempts, [start_date + datetime.timedelta(days=day) for day in range(10)])
        self.assertEqual(sleep.call_count, 10)

    def test_summary_day_logs_not_found_at_debug(self):
        class NotFoundGarmin:
            display_name = "display"

            def connectapi(self, path, **kwargs):
                raise GarminConnectNotFoundError("404 Client Error: Not Found")

        self.download.garmin = NotFoundGarmin()
        self.download.display_name = "display"
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertLogs(level=logging.DEBUG) as captured:
                requested = self.download._Download__get_summary_day(lambda year: temp_dir, datetime.date(2019, 1, 1), False)

        self.assertTrue(requested)
        self.assertEqual([r for r in captured.records if r.levelno >= logging.WARNING], [])
        self.assertTrue(any("No daily summary data for 2019-01-01" in r.getMessage() for r in captured.records))


if __name__ == "__main__":
    unittest.main(verbosity=2)
