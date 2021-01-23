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
from activity_fit_file_processor import ActivityFitFileProcessor
from garmin_db_config_manager import GarminDBConfigManager
from garmin_db_plugin import GarminDbPluginManager

root_logger = logging.getLogger()
root_logger.addHandler(logging.FileHandler('activities_db.log', 'w'))
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

do_fit_import_test = True
do_tcx_import_tests = True
do_summary_import_tests = True
do_details_import_tests = True
do_multiple_import_tests = True


class TestActivitiesDb(TestDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.garmin_act_db = GarminDB.ActivitiesDB(GarminDBConfigManager.get_db_params())
        table_dict = {
            'activities_table' : GarminDB.Activities,
            'activity_laps_table' : GarminDB.ActivityLaps,
            'activity_records_table' : GarminDB.ActivityRecords,
            'run_activities_table' : GarminDB.StepsActivities,
            'paddle_activities_table' : GarminDB.PaddleActivities,
            'cycle_activities_table' : GarminDB.CycleActivities,
        }
        super().setUpClass(cls.garmin_act_db, table_dict, {GarminDB.Activities : [GarminDB.Activities.activity_id]})
        cls.test_db_params = GarminDBConfigManager.get_db_params(test_db=True)
        cls.plugin_manager = GarminDbPluginManager(GarminDBConfigManager.get_or_create_plugins_dir(), cls.test_db_params)
        cls.test_mon_db = GarminDB.GarminDB(cls.test_db_params)
        cls.test_act_db = GarminDB.ActivitiesDB(cls.test_db_params, debug_level=1)
        cls.measurement_system = Fit.field_enums.DisplayMeasure.statute
        print(f"db params {repr(cls.test_db_params)}")

    def test_garmin_act_db_tables_exists(self):
        self.assertGreater(GarminDB.Activities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityLaps.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityRecords.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.StepsActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.PaddleActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.CycleActivities.row_count(self.garmin_act_db), 0)

    def check_activities_fields(self, fields_list):
        self.check_not_none_cols(self.test_act_db, {GarminDB.Activities : fields_list})

    def check_activities_field_value(self, field, min_value, max_value):
        field_max = GarminDB.Activities.get_col_max(self.test_act_db, field)
        if field_max is not None:
            self.assertLessEqual(field_max, max_value)
        field_min = GarminDB.Activities.get_col_min(self.test_act_db, field)
        if field_min is not None:
            self.assertGreaterEqual(field_min, min_value)

    def check_sport(self, activity):
        sport = Fit.Sport.from_string(activity.sport)
        self.assertIsInstance(sport, Fit.Sport, f'sport ({type(sport)}) from {repr(activity)}')
        self.assertEqual(activity.sport, sport.name)
        sub_sport = Fit.SubSport.from_string(activity.sub_sport)
        self.assertIsInstance(sub_sport, Fit.SubSport, f'sub_sport ({type(sub_sport)}) from {repr(activity)}')
        self.assertEqual(activity.sub_sport, sub_sport.name)

    def check_activities(self):
        for activity in GarminDB.Activities.get_all(self.test_act_db):
            self.check_sport(activity)
        self.check_col_type(self.test_act_db, GarminDB.Activities, GarminDB.Activities.activity_id, int)

    def __fit_file_import(self):
        gfd = GarminActivitiesFitData('test_files/fit/activity', latest=False, measurement_system=self.measurement_system, debug=2)
        self.gfd_file_count = gfd.file_count()
        if gfd.file_count() > 0:
            gfd.process_files(ActivityFitFileProcessor(self.test_db_params, self.plugin_manager))

    def fit_file_import(self):
        self.profile_function('fit_activities_import', self.__fit_file_import)
        self.check_db_tables_exists(self.test_mon_db, {'device_table' : GarminDB.Device})
        self.check_db_tables_exists(self.test_mon_db, {'file_table' : GarminDB.File, 'device_info_table' : GarminDB.DeviceInfo}, self.gfd_file_count)

    def summary_json_file_import(self):
        gjsd = GarminJsonSummaryData(self.test_db_params, 'test_files/json/activity/summary', latest=False, measurement_system=self.measurement_system, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()

    def details_json_file_import(self, delete_db=True):
        gjsd = GarminJsonDetailsData(self.test_db_params, 'test_files/json/activity/details', latest=False, measurement_system=self.measurement_system, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()

    def tcx_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        gtd = GarminTcxData('test_files/tcx', latest=False, measurement_system=self.measurement_system, debug=2)
        if gtd.file_count() > 0:
            gtd.process_files(self.test_db_params)

    #
    # The actual tests
    #
    @unittest.skipIf(not do_fit_import_test, "Skipping fit import test")
    def test_fit_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        self.fit_file_import()
        self.check_activities_fields([GarminDB.Activities.start_time, GarminDB.Activities.stop_time, GarminDB.Activities.elapsed_time])
        self.check_activities()
        self.check_activities_field_value(GarminDB.Activities.avg_speed, 0, 50)

    @unittest.skipIf(not do_tcx_import_tests, "Skipping tcx import test")
    def test_tcx_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        self.tcx_file_import()
        self.check_activities_fields([GarminDB.Activities.sport, GarminDB.Activities.laps])

    @unittest.skipIf(not do_summary_import_tests, "Skipping summary import test")
    def test_summary_json_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        self.summary_json_file_import()
        self.check_activities_fields([GarminDB.Activities.name, GarminDB.Activities.type, GarminDB.Activities.sport, GarminDB.Activities.sub_sport])
        self.check_activities_field_value(GarminDB.Activities.avg_speed, 0, 50)

    @unittest.skipIf(not do_details_import_tests, "Skipping details import test")
    def test_details_json_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        self.details_json_file_import()

    @unittest.skipIf(not do_multiple_import_tests, "Skipping multiple import test")
    def test_file_import(self):
        root_logger.info("test_file_import: %r", self.test_db_params)
        self.summary_json_file_import()
        self.details_json_file_import()
        self.tcx_file_import()
        self.fit_file_import()
        self.check_activities_fields([GarminDB.Activities.start_time, GarminDB.Activities.stop_time, GarminDB.Activities.elapsed_time])


if __name__ == '__main__':
    unittest.main(verbosity=2)
