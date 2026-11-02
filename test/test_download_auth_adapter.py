"""Test Download integration with the Garmin Connect auth adapter."""

__author__ = "Ilya Verchenko"
__copyright__ = "Copyright Ilya Verchenko"
__license__ = "GPL"

import json
import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

from garmindb.download import Download
from garmindb.garmin_connect_auth_adapter import GarminConnectRateLimitError


class FakeConfig:
    def __init__(self, fit_files_dir):
        self.fit_files_dir = fit_files_dir

    def get_fit_files_dir(self):
        return self.fit_files_dir


class FakeAdapter:
    instances = []

    def __init__(self, _gc_config):
        self.profile = {"displayName": "display", "fullName": "Full Name"}
        self.display_name = "display"
        self.full_name = "Full Name"
        self.connectapi_calls = []
        self.download_calls = []
        self.rate_limited = False
        FakeAdapter.instances.append(self)

    def login(self):
        return True

    def connectapi(self, path, **kwargs):
        self.connectapi_calls.append((path, kwargs))
        if self.rate_limited:
            raise GarminConnectRateLimitError("too many requests (HTTP 429)")
        return {"path": path, "kwargs": kwargs}

    def download(self, path):
        self.download_calls.append(path)
        return b"binary-data"


class TestDownloadAuthAdapter(unittest.TestCase):
    def setUp(self):
        FakeAdapter.instances = []
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = FakeConfig(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_download(self):
        with patch("garmindb.download.GarminConnectAuthAdapter", FakeAdapter):
            return Download(self.config)

    def test_daily_downloads_stop_at_first_rate_limit(self):
        download = self.create_download()
        download.display_name = "display"
        adapter = FakeAdapter.instances[0]
        adapter.rate_limited = True
        start_date = datetime.date(2024, 1, 1)
        directory = self.temp_dir.name

        def year_dir(_year):
            return directory

        stats = [
            lambda: download.get_sleep(directory, start_date, 10, False),
            lambda: download.get_rhr(directory, start_date, 10, False),
            lambda: download.get_hrv(directory, start_date, 10, False),
            lambda: download.get_weight(directory, start_date, 10, False),
            lambda: download.get_daily_summaries(year_dir, start_date, 10, False),
            lambda: download.get_hydration(year_dir, start_date, 10, False),
            lambda: download.get_lifestyle_logging(directory, start_date, 10, False),
        ]
        with patch("garmindb.download.time.sleep"):
            for get_stat in stats:
                adapter.connectapi_calls = []
                with self.assertRaises(GarminConnectRateLimitError):
                    get_stat()
                self.assertEqual(len(adapter.connectapi_calls), 1)

    def test_activity_download_stops_at_rate_limit(self):
        download = self.create_download()
        adapter = FakeAdapter.instances[0]
        adapter.rate_limited = True

        with patch("garmindb.download.time.sleep"):
            with self.assertRaises(GarminConnectRateLimitError):
                download.get_activities(self.temp_dir.name, 10)
        self.assertEqual(len(adapter.connectapi_calls), 1)

    def test_login_uses_adapter_and_saves_profile_files(self):
        download = self.create_download()

        self.assertTrue(download.login())

        adapter = FakeAdapter.instances[0]
        self.assertEqual(download.display_name, "display")
        self.assertEqual(download.full_name, "Full Name")
        self.assertEqual(
            adapter.connectapi_calls,
            [
                ("/userprofile-service/userprofile/user-settings", {}),
                ("/userprofile-service/userprofile/personal-information", {}),
            ],
        )

        with open(os.path.join(self.temp_dir.name, "social-profile.json"), encoding="utf-8") as file:
            self.assertEqual(json.load(file), {"displayName": "display", "fullName": "Full Name"})

    def test_save_binary_file_uses_adapter_download(self):
        download = self.create_download()
        filename = os.path.join(self.temp_dir.name, "activity.zip")

        download.save_binary_file(filename, "/download-service/files/activity/123")

        self.assertEqual(FakeAdapter.instances[0].download_calls, ["/download-service/files/activity/123"])
        with open(filename, "rb") as file:
            self.assertEqual(file.read(), b"binary-data")

    def test_summary_download_uses_adapter_connectapi(self):
        download = self.create_download()
        download.display_name = "display"

        download._Download__get_summary_day(
            lambda _year: self.temp_dir.name,
            datetime.date(2024, 1, 2),
            overwrite=True,
        )

        path, kwargs = FakeAdapter.instances[0].connectapi_calls[0]
        self.assertEqual(path, "/usersummary-service/usersummary/daily/display")
        self.assertEqual(kwargs["params"]["calendarDate"], "2024-01-02")

    def daily_stat_downloads(self, download):
        """Return (file name prefix, function downloading one day) for every daily stat."""
        directory = self.temp_dir.name

        def year_dir(_year):
            return directory

        return [
            ("daily_summary_", lambda day, overwrite: download._Download__get_summary_day(year_dir, day, overwrite)),
            ("weight_", lambda day, overwrite: download._Download__get_weight_day(directory, day, overwrite)),
            ("sleep_", lambda day, overwrite: download._Download__get_sleep_day(directory, day, overwrite)),
            ("rhr_", lambda day, overwrite: download._Download__get_rhr_day(directory, day, overwrite)),
            ("hydration_", lambda day, overwrite: download._Download__get_hydration_day(year_dir, day, overwrite)),
            ("hrv_", lambda day, overwrite: download._Download__get_hrv_day(directory, day, overwrite)),
            ("lifestyle_logging_", lambda day, overwrite: download._Download__get_lifestyle_logging_day(directory, day, overwrite)),
        ]

    def test_daily_stats_skip_request_for_existing_files(self):
        download = self.create_download()
        download.display_name = "display"
        adapter = FakeAdapter.instances[0]
        day = datetime.date(2024, 1, 2)

        for prefix, get_day in self.daily_stat_downloads(download):
            filename = os.path.join(self.temp_dir.name, f"{prefix}{day}.json")
            with open(filename, "w", encoding="utf-8") as file:
                file.write('{"existing": true}')
            adapter.connectapi_calls = []

            get_day(day, False)
            self.assertEqual(adapter.connectapi_calls, [], f"{prefix}: existing file requested again")
            with open(filename, encoding="utf-8") as file:
                self.assertEqual(json.load(file), {"existing": True})

            get_day(day, True)
            self.assertEqual(len(adapter.connectapi_calls), 1, f"{prefix}: overwrite did not request")

    def test_daily_stats_request_missing_files(self):
        download = self.create_download()
        download.display_name = "display"
        adapter = FakeAdapter.instances[0]
        day = datetime.date(2024, 1, 2)

        for prefix, get_day in self.daily_stat_downloads(download):
            adapter.connectapi_calls = []
            get_day(day, False)
            self.assertEqual(len(adapter.connectapi_calls), 1, f"{prefix}: missing file not requested")
            self.assertTrue(os.path.isfile(os.path.join(self.temp_dir.name, f"{prefix}{day}.json")))

    def test_recent_existing_days_are_downloaded_again(self):
        download = self.create_download()
        download.display_name = "display"
        adapter = FakeAdapter.instances[0]
        today = datetime.datetime.now().date()
        old_day = today - datetime.timedelta(days=Download.download_days_overlap + 5)
        for day in (old_day, today):
            with open(os.path.join(self.temp_dir.name, f"sleep_{day}.json"), "w", encoding="utf-8") as file:
                file.write("{}")

        with patch("garmindb.download.time.sleep"):
            download.get_sleep(self.temp_dir.name, old_day, (today - old_day).days + 1, False)

        requested = [kwargs["params"]["date"] for _path, kwargs in adapter.connectapi_calls]
        self.assertNotIn(old_day.strftime("%Y-%m-%d"), requested)
        self.assertIn(today.strftime("%Y-%m-%d"), requested)

    def test_get_stat_only_pauses_after_requests(self):
        download = self.create_download()
        download.display_name = "display"
        adapter = FakeAdapter.instances[0]
        start_date = datetime.date(2024, 1, 1)
        for day in range(0, 5):
            with open(os.path.join(self.temp_dir.name, f"sleep_{start_date + datetime.timedelta(days=day)}.json"), "w", encoding="utf-8") as file:
                file.write("{}")

        with patch("garmindb.download.time.sleep") as sleep:
            download.get_sleep(self.temp_dir.name, start_date, 8, False)

        self.assertEqual(len(adapter.connectapi_calls), 3)
        self.assertEqual(sleep.call_count, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
