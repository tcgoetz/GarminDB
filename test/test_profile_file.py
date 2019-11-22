"""Test profile file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging

import Fit
import GarminDB
import garmin_db_config_manager as GarminDBConfigManager
from import_garmin import GarminProfile


root_logger = logging.getLogger()
handler = logging.FileHandler('profile_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestProfileFile(unittest.TestCase):
    """Class for testing profile JSON file parsing."""

    @classmethod
    def setUpClass(cls):
        cls.file_path = 'test_files'

    def test_parse_uprofile(self):
        db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)
        gp = GarminProfile(db_params_dict, self.file_path, debug=2)
        if gp.file_count() > 0:
            gp.process()
        garmindb = GarminDB.GarminDB(db_params_dict)
        measurement_system = GarminDB.Attributes.measurements_type(garmindb)
        self.assertEqual(measurement_system, Fit.field_enums.DisplayMeasure.statute,
                         'DisplayMeasure expected %r found %r' % (Fit.field_enums.DisplayMeasure.statute, measurement_system))


if __name__ == '__main__':
    unittest.main(verbosity=2)
