"""Test profile file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging

import fitfile

from garmindb import ConfigManager, GarminProfile
from garmindb.garmindb import GarminDb, Attributes


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
        db_params = ConfigManager.get_db_params(test_db=True)
        gp = GarminProfile(db_params, self.file_path, debug=2)
        if gp.file_count() > 0:
            gp.process()
        gdb = GarminDb(db_params)
        measurement_system = Attributes.measurements_type(gdb)
        self.assertEqual(measurement_system, fitfile.field_enums.DisplayMeasure.statute,
                         'DisplayMeasure expected %r found %r' % (fitfile.field_enums.DisplayMeasure.statute, measurement_system))


if __name__ == '__main__':
    unittest.main(verbosity=2)
