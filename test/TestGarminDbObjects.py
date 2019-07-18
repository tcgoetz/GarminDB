#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest
import logging
import sys

from sqlalchemy.exc import IntegrityError

sys.path.append('../.')

import GarminDB
import Fit
from FileProcessor import FileProcessor
import GarminDBConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('garmin_b_objects.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestGarminDbObjects(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)

    def check_file_obj(self, filename_with_path, file_type, file_serial_number):
        garmindb = GarminDB.GarminDB(self.db_params_dict)
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(filename_with_path)
        file_dict = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : file_type,
            'serial_number' : file_serial_number,
        }
        logger.info("check_file_table: %r", file_dict)
        GarminDB.File.find_or_create(garmindb, file_dict)
        file = GarminDB.File.find_one(garmindb, file_dict)
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
        self.assertIn(GarminDB.File.FileType.convert(Fit.fieldenums.FileType.goals), file_types_list)


if __name__ == '__main__':
    unittest.main(verbosity=2)
