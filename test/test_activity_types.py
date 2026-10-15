"""Test mapping Garmin Connect activity types to sports."""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import json
import os
import tempfile
import unittest

import fitfile
from idbutils import DbParams

from garmindb import GarminJsonSummaryData, GarminJsonDetailsData
from garmindb.garmin_connect_enums import get_summary_sport, get_details_sport
from garmindb.garmindb import ActivitiesDb, Activities


MULTI_SPORT = {'typeId': 89, 'typeKey': 'multi_sport', 'parentTypeId': 17}
PILATES = {'typeId': 160, 'typeKey': 'pilates', 'parentTypeId': 29}
UNKNOWN = {'typeId': 99999, 'typeKey': 'not_known_yet', 'parentTypeId': 99998}
UNKNOWN_FITNESS_EQUIPMENT = {'typeId': 99999, 'typeKey': 'not_known_yet', 'parentTypeId': 29}


class TestActivityTypes(unittest.TestCase):
    """Class for testing Garmin Connect activity types."""

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

    def __import_summary(self, activity_id, activity_type):
        summary = {
            'activityId': activity_id,
            'activityName': 'Activity',
            'activityType': activity_type,
            'eventType': {'typeId': 9, 'typeKey': 'uncategorized'},
            'startTimeLocal': '2024-10-12 10:00:00',
            'elapsedDuration': 1800.0,
            'distance': 5000.0
        }
        return self.__import(GarminJsonSummaryData, f'activity_{activity_id}.json', summary)

    def __import_details(self, activity_id, activity_type):
        details = {
            'activityId': activity_id,
            'activityTypeDTO': activity_type,
            'metadataDTO': {},
            'summaryDTO': {'startTimeLocal': '2024-10-12T10:00:00.0', 'elapsedDuration': 1800.0, 'distance': 5000.0}
        }
        return self.__import(GarminJsonDetailsData, f'activity_details_{activity_id}.json', details)

    def test_multi_sport(self):
        sport, sub_sport = get_summary_sport({'activityType': MULTI_SPORT})
        self.assertEqual(sport, fitfile.fields.Sport.multisport)
        self.assertEqual(get_details_sport({'activityTypeDTO': MULTI_SPORT})[0], fitfile.fields.Sport.multisport)

    def test_pilates(self):
        self.assertEqual(get_summary_sport({'activityType': PILATES}), (fitfile.fields.Sport.fitness_equipment, fitfile.fields.SubSport.pilates))

    def test_import_multi_sport_and_pilates(self):
        self.assertEqual(self.__import_summary(1, MULTI_SPORT), 1)
        self.assertEqual(self.__import_details(1, MULTI_SPORT), 1)
        self.__import_summary(2, PILATES)
        self.__import_details(2, PILATES)
        self.assertEqual(Activities.get(self.activities_db, '1').sport, 'multisport')
        pilates = Activities.get(self.activities_db, '2')
        self.assertEqual((pilates.sport, pilates.sub_sport), ('fitness_equipment', 'pilates'))

    def test_import_unknown_type(self):
        self.assertEqual(self.__import_summary(3, UNKNOWN), 1)
        self.assertEqual(self.__import_details(3, UNKNOWN), 1)
        activity = Activities.get(self.activities_db, '3')
        self.assertEqual(activity.distance, 5.0)
        self.assertIsNone(activity.sport)
        self.assertIsNone(activity.sub_sport)

    def test_import_unknown_fitness_equipment_type(self):
        self.assertEqual(self.__import_summary(4, UNKNOWN_FITNESS_EQUIPMENT), 1)
        self.assertEqual(self.__import_details(4, UNKNOWN_FITNESS_EQUIPMENT), 1)
        activity = Activities.get(self.activities_db, '4')
        self.assertEqual(activity.sport, 'fitness_equipment')
        self.assertIsNone(activity.sub_sport)


if __name__ == '__main__':
    unittest.main(verbosity=2)
