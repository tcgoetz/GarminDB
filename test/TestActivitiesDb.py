#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest, os, logging, sys, datetime, re

from sqlalchemy.exc import IntegrityError

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


class TestActivitiesDb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = {}
        cls.db_params_dict['db_type'] = 'sqlite'
        cls.db_params_dict['db_path'] = db_dir

    def test_garmin_act_db_tables_exists(self):
        garmin_act_db = GarminDB.ActivitiesDB(self.db_params_dict)
        self.assertGreater(GarminDB.Activities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityLaps.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityRecords.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.RunActivities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.WalkActivities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.PaddleActivities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.CycleActivities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.EllipticalActivities.row_count(garmin_act_db), 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)

