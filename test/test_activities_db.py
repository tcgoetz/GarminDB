"""Test activities db."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import unittest
import logging

from test_db_base import TestDBBase
import GarminDB
import Fit
from import_garmin_activities import GarminActivitiesFitData, GarminTcxData, GarminJsonSummaryData, GarminJsonDetailsData
import garmin_db_config_manager as GarminDBConfigManager


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
                'run_activities_table' : GarminDB.StepsActivities,
                'paddle_activities_table' : GarminDB.PaddleActivities,
                'cycle_activities_table' : GarminDB.CycleActivities,
                'elliptical_activities_table' : GarminDB.EllipticalActivities
            },
            {
                GarminDB.Activities : [GarminDB.Activities.name]
            }
        )

    def test_garmin_act_db_tables_exists(self):
        self.assertGreater(GarminDB.Activities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityLaps.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityRecords.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.StepsActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.PaddleActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.CycleActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.EllipticalActivities.row_count(self.garmin_act_db), 0)

    def fit_file_import(self, db_params_dict):
        gfd = GarminActivitiesFitData('test_files/fit/activity', latest=False, measurement_system=Fit.field_enums.DisplayMeasure.statute, debug=2)
        self.gfd_file_count = gfd.file_count()
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)

    def test_fit_file_import(self):
        db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)
        self.profile_function('fit_activities_import', self.fit_file_import, db_params_dict)
        test_mon_db = GarminDB.GarminDB(db_params_dict)
        self.check_db_tables_exists(test_mon_db, {'device_table' : GarminDB.Device})
        self.check_db_tables_exists(test_mon_db, {'file_table' : GarminDB.File, 'device_info_table' : GarminDB.DeviceInfo}, self.gfd_file_count)
        activities_fields = [GarminDB.Activities.start_time, GarminDB.Activities.stop_time, GarminDB.Activities.elapsed_time]
        self.check_not_none_cols(GarminDB.ActivitiesDB(db_params_dict), {GarminDB.Activities : activities_fields})

    def test_tcx_file_import(self):
        db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)
        gtd = GarminTcxData('test_files/tcx', latest=False, measurement_system=Fit.field_enums.DisplayMeasure.statute, debug=2)
        if gtd.file_count() > 0:
            gtd.process_files(db_params_dict)
        self.check_not_none_cols(GarminDB.ActivitiesDB(db_params_dict), {GarminDB.Activities : [GarminDB.Activities.sport, GarminDB.Activities.laps]})

    def test_summary_json_file_import(self):
        db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)
        gjsd = GarminJsonSummaryData(db_params_dict, 'test_files/json/activity/summary', latest=False, measurement_system=Fit.field_enums.DisplayMeasure.statute, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()
        activities_fields = [GarminDB.Activities.name, GarminDB.Activities.type, GarminDB.Activities.sport, GarminDB.Activities.sub_sport]
        self.check_not_none_cols(GarminDB.ActivitiesDB(db_params_dict), {GarminDB.Activities : activities_fields})

    def test_details_json_file_import(self):
        db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)
        gjsd = GarminJsonDetailsData(db_params_dict, 'test_files/json/activity/details', latest=False, measurement_system=Fit.field_enums.DisplayMeasure.statute, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()


if __name__ == '__main__':
    unittest.main(verbosity=2)
