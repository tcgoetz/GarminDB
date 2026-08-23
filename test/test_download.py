"""Tests for download retry behavior."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import unittest
from unittest import mock

from garmindb.download import Download


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
