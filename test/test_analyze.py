"""Test Analyze summary generation."""

__author__ = "Christopher Pruijsen"
__copyright__ = "Copyright Christopher Pruijsen"
__license__ = "GPL"

import datetime
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.append('..')

from idbutils import DbParams

from garmindb.analyze import Analyze
from garmindb.garmindb import GarminDb, Attributes, Activities


class FakeConfig:
    def __init__(self, db_params):
        self.db_params = db_params

    def get_db_params(self):
        return self.db_params


class TestAnalyze(unittest.TestCase):
    """Class for testing Analyze."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_params = DbParams(db_type='sqlite', db_path=self.temp_dir.name)
        # Analyze requires a measurement system attribute to be present in the garmin db.
        garmin_db = GarminDb(self.db_params)
        Attributes.set_newer(garmin_db, 'measurement_system', 'statute')

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_summary_ignores_none_years(self):
        analyze = Analyze(FakeConfig(self.db_params), 0)
        # Blank activities rows (no start_time) yield a None year.
        Activities.insert_or_update(analyze.garmin_act_db, {'activity_id': 'blank'})
        Activities.insert_or_update(analyze.garmin_act_db, {'activity_id': 'real', 'start_time': datetime.datetime(2024, 5, 1)})
        with patch.object(Analyze, '_Analyze__calculate_year') as calculate_year:
            analyze.summary()
        calculate_year.assert_called_once_with(2024)


if __name__ == "__main__":
    unittest.main(verbosity=2)
