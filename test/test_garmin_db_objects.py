"""Test Garmin database data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
from sqlalchemy.exc import IntegrityError

import GarminDB
import Fit
import garmin_db_config_manager as GarminDBConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('garmin_b_objects.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestGarminDbObjects(unittest.TestCase):
    """Class for testing Garmin database data."""

    @classmethod
    def setUpClass(cls):
        cls.db_params = GarminDBConfigManager.get_db_params(test_db=True)

    def check_file_obj(self, filename_with_path, file_type, file_serial_number):
        garmindb = GarminDB.GarminDB(self.db_params)
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(filename_with_path)
        file_dict = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : file_type,
            'serial_number' : file_serial_number,
        }
        logger.info("check_file_table: %r", file_dict)
        GarminDB.File.insert_or_update(garmindb, file_dict)
        file = GarminDB.File.s_get(garmindb, file_id)
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
