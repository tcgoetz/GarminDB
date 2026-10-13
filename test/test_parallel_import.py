"""Test that importing FIT files on worker processes builds the same databases as importing them one after the other."""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import shutil
import tempfile
import unittest
from unittest import mock

import fitfile
from idbutils import DbParams, parallel

from garmindb import ActivityFitFileProcessor, GarminActivitiesFitData, PluginManager

from bench_import import compare_runs


FIXTURE = 'test_files/fit/activity/22638574127_ACTIVITY.fit'
FILE_COUNT = 4


class TestParallelImport(unittest.TestCase):
    """Class for testing the parallel import of FIT files."""

    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.base_dir, 'Activities')
        os.makedirs(self.input_dir)
        for file_number in range(FILE_COUNT):
            shutil.copy(FIXTURE, os.path.join(self.input_dir, f'{1000 + file_number}_ACTIVITY.fit'))
        self.plugin_dir = os.path.join(self.base_dir, 'Plugins')
        os.makedirs(self.plugin_dir)

    def tearDown(self):
        parallel.shutdown()
        parallel.set_workers(1)
        shutil.rmtree(self.base_dir)

    def __import(self, run_name, workers):
        db_params = DbParams(db_type='sqlite', db_path=os.path.join(self.base_dir, 'runs', run_name, 'DBs'))
        os.makedirs(db_params.db_path)
        parallel.set_workers(workers)
        fit_data = GarminActivitiesFitData(self.input_dir, False, fitfile.MeasurementSystem.metric, 0, simple_output=True)
        self.assertEqual(fit_data.file_count(), FILE_COUNT)
        with mock.patch.object(parallel, '_MIN_ITEMS_PER_WORKER', 1):
            self.assertEqual(parallel.workers_for(db_params, FILE_COUNT), workers)
            fit_data.process_files(ActivityFitFileProcessor(db_params, PluginManager(self.plugin_dir, db_params), 0))

    def test_same_databases_as_a_sequential_import(self):
        self.__import('sequential', 1)
        self.__import('parallel', 2)
        self.assertEqual(compare_runs(self.base_dir, 'sequential', 'parallel'), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
