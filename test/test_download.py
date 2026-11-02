"""Tests for download retry behavior."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import unittest
from unittest import mock

from garmindb.download import Download
from garmindb.garmin_connect_auth_adapter import GarminConnectRateLimitError


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
