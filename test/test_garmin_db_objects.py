"""Test Garmin database data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
from sqlalchemy.exc import IntegrityError

import GarminDB
import Fit
from garmin_db_config_manager import GarminDBConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('garmin_db_objects.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestGarminDbObjects(unittest.TestCase):
    """Class for testing Garmin database data."""

    @classmethod
    def setUpClass(cls):
        cls.db_params = GarminDBConfigManager.get_db_params(test_db=True)
        cls.garmin_db = GarminDB.GarminDB(cls.db_params)

    def check_file_obj(self, filename_with_path, file_type, file_serial_number):
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(filename_with_path)
        file_dict = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : file_type,
            'serial_number' : file_serial_number,
        }
        logger.info("check_file_table: %r", file_dict)
        GarminDB.File.insert_or_update(self.garmin_db, file_dict)
        file = GarminDB.File.get(self.garmin_db, file_id)
        self.assertEqual(file.id, file_dict['id'])
        self.assertEqual(file.name, file_dict['name'])
        self.assertEqual(file.type, file_dict['type'])
        self.assertEqual(file.serial_number, file_dict['serial_number'])

    def test_file_good(self):
        file_id = 123345678
        filename = '%d.fit' % file_id
        filename_with_path = '/test/directory/' + filename
        file_type = GarminDB.File.FileType.fit_goals
        file_serial_number = 987654321
        self.check_file_obj(filename_with_path, file_type, file_serial_number)

    def test_file_good_with_activity_name(self):
        file_id = 123345678
        filename = '%d_ACTIVITY.fit' % file_id
        filename_with_path = '/test/directory/' + filename
        file_type = GarminDB.File.FileType.fit_goals
        file_serial_number = 987654321
        self.check_file_obj(filename_with_path, file_type, file_serial_number)

    def test_file_bad_type(self):
        file_id = 123345678
        filename = '%d.fit' % file_id
        filename_with_path = '/test/directory/' + filename
        file_type = 'xxxxx'
        file_serial_number = 987654321
        with self.assertRaises(IntegrityError):
            self.check_file_obj(filename_with_path, file_type, file_serial_number)

    def test_file_type(self):
        file_types_list = list(GarminDB.File.FileType)
        self.assertIn(GarminDB.File.FileType.convert(Fit.FileType.goals), file_types_list)

    def test_get_default(self):
        result = GarminDB.Attributes.get(self.garmin_db, 'test_String')
        self.assertEqual(result, None)
        result = GarminDB.Attributes.get(self.garmin_db, 'test_String', 'default_value')
        self.assertEqual(result, 'default_value')
        #
        result = GarminDB.Attributes.get_string(self.garmin_db, 'test_String')
        self.assertEqual(result, None)
        result = GarminDB.Attributes.get_string(self.garmin_db, 'test_String', 'default_value')
        self.assertEqual(result, 'default_value')

    def test_set_get_default(self):
        GarminDB.Attributes.set(self.garmin_db, 'test_String', 'test_value')
        result = GarminDB.Attributes.get_string(self.garmin_db, 'test_String')
        self.assertEqual(result, 'test_value')
        result = GarminDB.Attributes.get_string(self.garmin_db, 'test_String', 'default_value')
        self.assertEqual(result, 'test_value')
        #
        GarminDB.Attributes.set_if_unset(self.garmin_db, 'test_String', 'test_value2')
        result = GarminDB.Attributes.get_string(self.garmin_db, 'test_String')
        self.assertEqual(result, 'test_value')

    def test_get_float(self):
        GarminDB.Attributes.set(self.garmin_db, 'test_String', 2.2)
        result = GarminDB.Attributes.get_float(self.garmin_db, 'test_String')
        self.assertEqual(result, 2.2)
        result = GarminDB.Attributes.get_float(self.garmin_db, 'test_String', 'default_value')
        self.assertEqual(result, 2.2)
        #
        GarminDB.Attributes.set_if_unset(self.garmin_db, 'test_String', 2.2)
        result = GarminDB.Attributes.get_float(self.garmin_db, 2.2)

    def test_measurement_system(self):
        result = GarminDB.Attributes.measurements_type(self.garmin_db, Fit.field_enums.DisplayMeasure.metric)
        self.assertEqual(result, Fit.field_enums.DisplayMeasure.metric)
        for value in Fit.field_enums.DisplayMeasure:
            GarminDB.Attributes.set(self.garmin_db, 'measurement_system', value)
            result = GarminDB.Attributes.measurements_type(self.garmin_db)
            self.assertEqual(result, value)


if __name__ == '__main__':
    unittest.main(verbosity=2)
