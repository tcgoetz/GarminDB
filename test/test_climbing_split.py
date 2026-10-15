"""Test writing the splits of a climbing activity."""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import tempfile
import types
import unittest

import fitfile
from fitfile.data_message import MessageFields
from fitfile.fields.field_enums.sport import BoulderingFontGrade
from idbutils import DbParams

from garmindb import ActivityFitFileProcessor
from garmindb.garmindb import ActivitiesDb, ActivityClimbingSplits


class TestClimbingSplit(unittest.TestCase):
    """Class for testing the import of climbing split messages."""

    def setUp(self):
        db_params = DbParams(db_type='sqlite', db_path=tempfile.mkdtemp())
        self.processor = ActivityFitFileProcessor(db_params)
        self.processor.garmin_act_db = ActivitiesDb(db_params)
        self.processor.activity_fit_file_plugins = []
        self.processor.activity_id = '1'

    def __write(self, split_num, grade):
        fit_file = types.SimpleNamespace(filename='1_ACTIVITY.fit', utc_datetime_to_local=lambda timestamp: timestamp)
        message_fields = MessageFields(start_time=datetime.datetime(2024, 10, 12, 10, split_num), total_elapsed_time=datetime.time(0, 1), grade=grade, completed=True, falls=1)
        with self.processor.garmin_act_db.managed_session() as self.processor.garmin_act_db_session:
            self.processor._write_split_entry(fit_file, message_fields, split_num)
        with self.processor.garmin_act_db.managed_session() as session:
            return session.query(ActivityClimbingSplits.grade).filter(ActivityClimbingSplits.split == split_num).scalar()

    def test_bouldering_grade(self):
        self.assertEqual(self.__write(0, BoulderingFontGrade.grade_5), 'grade_5')

    def test_numeric_grade(self):
        self.assertEqual(self.__write(1, 7), '7')

    def test_split_without_a_grade(self):
        self.assertIsNone(self.__write(2, fitfile.UnknownEnumValue(0xFFFFFFFF)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
