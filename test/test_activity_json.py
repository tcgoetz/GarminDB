"""Test importing activities from Garmin Connect JSON files."""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import json
import os
import tempfile
import unittest

import fitfile
from idbutils import DbParams

from garmindb import GarminJsonSummaryData, GarminJsonDetailsData
from garmindb.garmindb import ActivitiesDb, Activities


STRENGTH_TRAINING = {'typeId': 13, 'typeKey': 'strength_training', 'parentTypeId': 29}


class TestActivityJson(unittest.TestCase):
    """Class for testing the import of Garmin Connect activity JSON files."""

    def setUp(self):
        self.db_params = DbParams(db_type='sqlite', db_path=tempfile.mkdtemp())
        self.input_dir = tempfile.mkdtemp()
        self.activities_db = ActivitiesDb(self.db_params)

    def __import(self, importer_class, file_name, activity):
        with open(os.path.join(self.input_dir, file_name), 'w') as file:
            json.dump(activity, file)
        importer = importer_class(self.db_params, self.input_dir, False, fitfile.MeasurementSystem.metric, 0, simple_output=True)
        importer.process()
        return importer.total_updates

    def __import_summary(self, activity_id, **fields):
        summary = {
            'activityId': activity_id,
            'activityName': 'Strength',
            'activityType': STRENGTH_TRAINING,
            'eventType': {'typeId': 9, 'typeKey': 'uncategorized'},
            'startTimeLocal': '2024-10-12 10:00:00',
            'elapsedDuration': 1800.0
        }
        summary.update(fields)
        return self.__import(GarminJsonSummaryData, f'activity_{activity_id}.json', summary)

    def test_summary_without_a_distance(self):
        self.assertEqual(self.__import_summary(1), 1)
        activity = Activities.get(self.activities_db, '1')
        self.assertEqual(activity.start_time, datetime.datetime(2024, 10, 12, 10, 0))
        self.assertEqual(activity.stop_time, datetime.datetime(2024, 10, 12, 10, 30))
        self.assertIsNone(activity.distance)

    def test_summary_with_a_distance(self):
        self.assertEqual(self.__import_summary(2, distance=5000.0), 1)
        self.assertEqual(Activities.get(self.activities_db, '2').distance, 5.0)

    def test_details_without_a_summary(self):
        self.assertEqual(self.__import_summary(3, distance=5000.0), 1)
        details = {'activityId': 3, 'activityTypeDTO': STRENGTH_TRAINING, 'metadataDTO': {}, 'summaryDTO': {}}
        self.assertEqual(self.__import(GarminJsonDetailsData, 'activity_details_3.json', details), 1)
        activity = Activities.get(self.activities_db, '3')
        self.assertEqual(activity.start_time, datetime.datetime(2024, 10, 12, 10, 0))
        self.assertEqual(activity.distance, 5.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
