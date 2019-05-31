#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest, os, logging, sys, datetime, re

from sqlalchemy.exc import IntegrityError

from TestDBBase import TestDBBase

sys.path.append('../.')

import GarminDB
import Fit
from FileProcessor import *
from import_garmin_activities import GarminActivitiesFitData
import GarminDBConfigManager


root_logger = logging.getLogger()
root_logger.addHandler(logging.FileHandler('activities_db.log', 'w'))
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestActivitiesDb(TestDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_params_dict = GarminDBConfigManager.get_db_params()
        cls.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict)
        super(TestActivitiesDb, cls).setUpClass(cls.garmin_act_db,
            {
                'activities_table' : GarminDB.Activities,
                'activity_laps_table' : GarminDB.ActivityLaps,
                'activity_records_table' : GarminDB.ActivityRecords,
                'run_activities_table' : GarminDB.RunActivities,
                'walk_activities_table' : GarminDB.WalkActivities,
                'paddle_activities_table' : GarminDB.PaddleActivities,
                'cycle_activities_table' : GarminDB.CycleActivities,
                'elliptical_activities_table' : GarminDB.EllipticalActivities
            }
        )

    def test_garmin_act_db_tables_exists(self):
        self.assertGreater(GarminDB.Activities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityLaps.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityRecords.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.RunActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.WalkActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.PaddleActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.CycleActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.EllipticalActivities.row_count(self.garmin_act_db), 0)

    def test_fit_file_import(self):
        db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)
        gfd = GarminActivitiesFitData(None, 'test_files/fit/activity', latest=False, measurement_system=Fit.DisplayMeasure.statute, debug=2)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)

