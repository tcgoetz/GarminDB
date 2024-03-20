"""Test profile file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging

import fitfile

from garmindb import GarminConnectConfigManager, GarminUserSettings, GarminPersonalInformation, GarminSocialProfile
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
        cls.gc_config = GarminConnectConfigManager()
        cls.file_path = 'test_files'

    def test_parse_usersettings(self):
        db_params = self.gc_config.get_db_params(test_db=True)
        gus = GarminUserSettings(db_params, self.file_path, debug=2)
        if gus.file_count() > 0:
            gus.process()
        gdb = GarminDb(db_params)
        measurement_system = Attributes.measurements_type(gdb)
        self.assertEqual(measurement_system, fitfile.field_enums.DisplayMeasure.statute,
                         'DisplayMeasure expected %r found %r from %r' % (fitfile.field_enums.DisplayMeasure.statute, measurement_system, gus.file_names))

    def test_parse_personalinfo(self):
        db_params = self.gc_config.get_db_params(test_db=True)
        gpi = GarminPersonalInformation(db_params, self.file_path, debug=2)
        if gpi.file_count() > 0:
            gpi.process()
        gdb = GarminDb(db_params)
        locale = Attributes.get_string(gdb, 'locale')
        self.assertEqual(locale, 'en', 'locale expected %r found %r from %r' % ('en', locale, gpi.file_names))

    def test_parse_socialprofile(self):
        db_params = self.gc_config.get_db_params(test_db=True)
        gsp = GarminSocialProfile(db_params, self.file_path, debug=2)
        if gsp.file_count() > 0:
            gsp.process()
        gdb = GarminDb(db_params)
        id = Attributes.get_string(gdb, 'id')
        self.assertEqual(id, '346745092', 'Id expected %r found %r from %r' % ('346745092', id, gsp.file_names))


if __name__ == '__main__':
    unittest.main(verbosity=2)
