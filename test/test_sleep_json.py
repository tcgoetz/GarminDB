"""Test importing sleep data from Garmin Connect JSON files."""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import json
import os
import tempfile
import unittest

from idbutils import DbParams

from garmindb import GarminConnectSleepData
from garmindb.garmindb import SleepDb, Sleep, SleepEvents


class TestSleepJson(unittest.TestCase):
    """Class for testing the import of Garmin Connect sleep JSON files."""

    def setUp(self):
        self.db_params = DbParams(db_type='sqlite', db_path=tempfile.mkdtemp())
        self.input_dir = tempfile.mkdtemp()

    def __import(self, day, sleep_levels):
        sleep = {
            'dailySleepDTO': {
                'calendarDate': day,
                'sleepTimeSeconds': 27000,
                'sleepStartTimestampGMT': 1728684000000,
                'sleepEndTimestampGMT': 1728711000000,
                'sleepStartTimestampLocal': 1728691200000,
                'sleepEndTimestampLocal': 1728718200000,
                'deepSleepSeconds': 5400,
                'lightSleepSeconds': 16200,
                'remSleepSeconds': 5400,
                'awakeSleepSeconds': 600
            },
            'remSleepData': True,
            'sleepLevels': sleep_levels
        }
        with open(os.path.join(self.input_dir, f'sleep_{day}.json'), 'w') as file:
            json.dump(sleep, file)
        sleep_data = GarminConnectSleepData(self.db_params, self.input_dir, False, 0, simple_output=True)
        sleep_data.process()
        return sleep_data.total_updates

    def test_day_without_sleep_levels(self):
        self.assertEqual(self.__import('2024-10-12', None), 1)
        sleep_db = SleepDb(self.db_params)
        day = Sleep.get(sleep_db, datetime.datetime(2024, 10, 12))
        self.assertEqual(day.total_sleep, datetime.time(7, 30))
        self.assertEqual(SleepEvents.row_count(sleep_db), 0)

    def test_day_with_sleep_levels(self):
        sleep_levels = [
            {'startGMT': '2024-10-11T22:00:00.0', 'endGMT': '2024-10-11T23:30:00.0', 'activityLevel': 1.0},
            {'startGMT': '2024-10-11T23:30:00.0', 'endGMT': '2024-10-12T00:15:00.0', 'activityLevel': 0.0}
        ]
        self.assertEqual(self.__import('2024-10-12', sleep_levels), 3)
        sleep_db = SleepDb(self.db_params)
        self.assertIsNotNone(Sleep.get(sleep_db, datetime.datetime(2024, 10, 12)))
        self.assertEqual(SleepEvents.row_count(sleep_db), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
