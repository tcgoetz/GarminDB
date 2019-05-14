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


root_logger = logging.getLogger()
handler = logging.FileHandler('activities_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
db_dir = os.environ['DB_DIR']


class TestActivitiesDb(TestDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = {}
        cls.db_params_dict['db_type'] = 'sqlite'
        cls.db_params_dict['db_path'] = db_dir
        cls.garmin_act_db = GarminDB.ActivitiesDB(cls.db_params_dict)
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

if __name__ == '__main__':
    unittest.main(verbosity=2)

