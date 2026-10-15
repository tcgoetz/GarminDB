"""Test writing the devices an activity used."""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import tempfile
import types
import unittest

import fitfile
from fitfile.data_message import MessageFields
from idbutils import DbParams

from garmindb import ActivityFitFileProcessor
from garmindb.garmindb import ActivitiesDb, ActivitiesDeviceUsed


class TestDeviceUsed(unittest.TestCase):
    """Class for testing the import of device_used messages."""

    def setUp(self):
        db_params = DbParams(db_type='sqlite', db_path=tempfile.mkdtemp())
        self.processor = ActivityFitFileProcessor(db_params)
        self.processor.garmin_act_db = ActivitiesDb(db_params)
        self.processor.activity_id = '1'
        self.processor.device_index_to_serial_number = {1: 3456789012}

    def __write(self, **message_fields):
        fit_file = types.SimpleNamespace(filename='1_ACTIVITY.fit')
        with self.processor.garmin_act_db.managed_session() as self.processor.garmin_act_db_session:
            self.processor._write_device_used_entry(fit_file, MessageFields(message_fields))
        return ActivitiesDeviceUsed.get(self.processor.garmin_act_db, '1')

    def test_devices_with_a_serial_number(self):
        device_used = self.__write(speed=1, heart_rate=1)
        self.assertEqual(device_used.speed_device_serial_number, 3456789012)
        self.assertEqual(device_used.heart_rate_device_serial_number, 3456789012)

    def test_device_without_a_serial_number(self):
        device_used = self.__write(speed=9, heart_rate=1)
        self.assertIsNone(device_used.speed_device_serial_number)
        self.assertEqual(device_used.heart_rate_device_serial_number, 3456789012)

    def test_device_indexes_do_not_carry_over_to_the_next_file(self):
        self.processor._write_file_id(types.SimpleNamespace(filename='2_ACTIVITY.fit'), fitfile.MessageType.file_id, [])
        device_used = self.__write(speed=1, heart_rate=1)
        self.assertIsNone(device_used.speed_device_serial_number)
        self.assertIsNone(device_used.heart_rate_device_serial_number)


if __name__ == '__main__':
    unittest.main(verbosity=2)
