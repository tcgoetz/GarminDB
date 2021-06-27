"""Test copying FIT files from a USB mounted watch."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime

from garmindb import Copy, ConfigManager, GarminConnectConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('copy.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestCopy(unittest.TestCase):
    """Class for testing FIT file copying."""

    @classmethod
    def setUpClass(cls):
        cls.gc_config = GarminConnectConfigManager()
        cls.copy = Copy(cls.gc_config.device_mount_dir())

    def test_copy_activity(self):
        activities_dir = ConfigManager.get_or_create_activities_dir(test_dir=True)
        logger.info("Copying activities to %s", activities_dir)
        self.copy.copy_activities(activities_dir)

    def test_copy_monitoring(self):
        monitoring_dir = ConfigManager.get_or_create_monitoring_dir(datetime.datetime.now().year, test_dir=True)
        logger.info("Copying monitoring to %s", monitoring_dir)
        self.copy.copy_monitoring(monitoring_dir)

    def test_copy_settings(self):
        settings_dir = ConfigManager.get_or_create_fit_files_dir(test_dir=True)
        root_logger.info("Copying settings to %s", settings_dir)
        self.copy.copy_settings(settings_dir)

    def test_copy_sleep(self):
        monitoring_dir = ConfigManager.get_or_create_monitoring_dir(datetime.datetime.now().year, test_dir=True)
        root_logger.info("Copying sleep to %s", monitoring_dir)
        self.copy.copy_sleep(monitoring_dir)


if __name__ == '__main__':
    unittest.main(verbosity=2)
