"""Test config handling."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import unittest
import logging
import sys

from garmindb import GarminConnectConfigManager
import fitfile
import idbutils
import tcxfile

sys.path.append('..')
from fitfile import version_string as fit_version_string
from idbutils import version_string as utilities_version_string
from tcxfile import version_string as tcx_version_string


root_logger = logging.getLogger()
handler = logging.FileHandler('copy.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestConfig(unittest.TestCase):
    """Class for testing config handling."""

    @classmethod
    def setUpClass(cls):
        cls.gc_config = GarminConnectConfigManager()
        cls.homedir = os.path.expanduser('~')

    def test_versions(self):
        print(f"fitfile version {fitfile.__version__}")
        self.assertEqual(fitfile.__version__, fit_version_string(), f'Fit version actual {fitfile.__version__} expected {fit_version_string()}')
        print(f"idbutils version {idbutils.__version__}")
        self.assertEqual(idbutils.__version__, utilities_version_string(), f'Utilities version actual {idbutils.__version__} expected {utilities_version_string()}')
        print(f"tcxfile version {tcxfile.__version__}")
        self.assertEqual(tcxfile.__version__, tcx_version_string(), f'Tcx version actual {tcxfile.__version__} expected {tcx_version_string()}')

    def test_directories(self):
        # config_dir
        expected_config_dir = self.homedir + os.sep + '.GarminDb'
        config_dir = self.gc_config.get_config_dir()
        self.assertEqual(config_dir, expected_config_dir, f'actual {config_dir} expected {expected_config_dir}')
        # base_dir
        expected_base_dir = self.homedir + os.sep + 'HealthData'
        base_dir = self.gc_config.get_base_dir()
        self.assertEqual(base_dir, expected_base_dir, f'actual {base_dir} expected {expected_base_dir}')
        # monitoring_dir
        year = 2023
        expected_monitoring_dir = expected_base_dir + os.sep + 'Monitoring' + os.sep + str(year)
        monitoring_dir = self.gc_config.get_monitoring_dir(year)
        self.assertEqual(monitoring_dir, expected_monitoring_dir, f'actual {monitoring_dir} expected {expected_monitoring_dir}')

    def test_db(self):
        db_params = self.gc_config.get_db_params()
        expect_db_type = 'sqlite'
        self.assertEqual(db_params.db_type, expect_db_type, f"expected {expect_db_type} actual {db_params.db_type}")
        expected_db_path = self.homedir + os.sep + 'HealthData' + os.sep + 'DBs'
        self.assertEqual(db_params.db_path, expected_db_path, f"expected {expected_db_path} actual {db_params.db_path}")

if __name__ == '__main__':
    unittest.main(verbosity=2)