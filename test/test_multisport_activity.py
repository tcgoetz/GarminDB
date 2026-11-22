"""Test multi-sport (brick / triathlon) activity import — see issue #289."""

__author__ = "Philippe Auriach"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import os
import shutil
import tempfile
import unittest
import logging

import fitfile
from idbutils import DbParams

from garmindb import ActivityFitFileProcessor, GarminConnectConfigManager, PluginManager
from garmindb.garmindb import ActivitiesDb, Activities, ActivityLaps, ActivityRecords, ActivitiesDevices


root_logger = logging.getLogger()
root_logger.addHandler(logging.FileHandler('test_multisport_activity.log', 'w'))
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


# Garmin names each activity FIT file <activity_id>_ACTIVITY.fit; the parent id is the filename prefix.
PARENT_ID = '10000000001'
FIXTURE = f'test_files/fit/activity/{PARENT_ID}_ACTIVITY.fit'
EXPECTED_SESSION_LAP_COUNTS = [14, 1, 6, 1, 3]  # swim / T1 / run / T2 / swim
EXPECTED_RECORD_COUNT = 3682  # the file has one more record, which is outside of every session
EXPECTED_SPORTS = [
    ('swimming', 'lap_swimming'),
    ('transition', 'generic'),
    ('running', 'generic'),
    ('transition', 'generic'),
    ('swimming', 'lap_swimming'),
]
# Seconds in HR zones 1-5 per leg, from each session's time_in_zone message, rounded. Index 0 of
# time_in_hr_zone is the time below zone 1 and is not stored (it is 7 s for the first swim).
EXPECTED_SESSION_HR_ZONE_SECONDS = [
    [40, 419, 519, 231, 0],
    [0, 16, 144, 2, 0],
    [0, 39, 815, 1091, 7],
    [0, 8, 68, 35, 7],
    [0, 252, 187, 0, 0],
]
# First lap of the run leg (the file's 16th lap message).
EXPECTED_RUN_LAP_0_HR_ZONE_SECONDS = [0, 39, 214, 127, 0]


def zone_seconds(row):
    """Return the hrz_1_time .. hrz_5_time columns of a row as rounded seconds."""
    times = [getattr(row, f'hrz_{zone}_time') for zone in range(1, 6)]
    return [round(t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6) for t in times]


class TestMultisportActivity(unittest.TestCase):
    """Verify multi-sport FIT files produce one DB row per leg, with correct partitioning."""

    @classmethod
    def setUpClass(cls):
        cls.gc_config = GarminConnectConfigManager()
        cls.test_db_params = cls.gc_config.get_db_params(test_db=True)
        root_logger.debug("test_db_params %r", cls.test_db_params)
        cls.act_db = ActivitiesDb(cls.test_db_params, debug_level=1)
        plugin_manager = PluginManager(cls.gc_config.get_plugins_dir(), cls.test_db_params)
        processor = ActivityFitFileProcessor(cls.test_db_params, plugin_manager, debug=0)
        cls.fit_file = fitfile.file.File(FIXTURE)
        processor.write_file(cls.fit_file)

    def test_creates_one_row_per_session(self):
        with self.act_db.managed_session() as session:
            ids = sorted(a.activity_id for a in session.query(Activities).all())
        self.assertEqual(ids, [f'{PARENT_ID}_{i}' for i in range(1, 6)])

    def test_nothing_written_under_bare_parent_id(self):
        with self.act_db.managed_session() as session:
            for table in (Activities, ActivityLaps, ActivityRecords, ActivitiesDevices):
                count = session.query(table).filter(table.activity_id == PARENT_ID).count()
                self.assertEqual(count, 0, f'{table.__name__} should have no rows under the bare parent id')

    def test_sports_in_order(self):
        with self.act_db.managed_session() as session:
            rows = session.query(Activities).order_by(Activities.activity_id).all()
            self.assertEqual([(r.sport, r.sub_sport) for r in rows], EXPECTED_SPORTS)

    def test_stop_time_is_after_start_time(self):
        """Garmin reuses the parent start_time as every child's `timestamp`; stop_time must be derived."""
        with self.act_db.managed_session() as session:
            for row in session.query(Activities).all():
                self.assertLess(row.start_time, row.stop_time,
                                f'{row.activity_id}: start={row.start_time} stop={row.stop_time}')

    def test_laps_partitioned_per_session(self):
        for i, expected in enumerate(EXPECTED_SESSION_LAP_COUNTS, start=1):
            activity_id = f'{PARENT_ID}_{i}'
            with self.act_db.managed_session() as session:
                count = session.query(ActivityLaps).filter(ActivityLaps.activity_id == activity_id).count()
            self.assertEqual(count, expected,
                             f'{activity_id}: expected {expected} laps, got {count}')

    def test_laps_indexed_locally_per_session(self):
        for i in range(1, 6):
            activity_id = f'{PARENT_ID}_{i}'
            with self.act_db.managed_session() as session:
                laps = sorted(l.lap for l in session.query(ActivityLaps).filter(ActivityLaps.activity_id == activity_id).all())
            self.assertEqual(laps, list(range(len(laps))),
                             f'{activity_id}: laps should be 0..N contiguous, got {laps}')

    def test_lap_data_populated(self):
        """Regression for the time_in_zone / lap write-order bug: lap rows must have distance and elapsed_time."""
        run_id = f'{PARENT_ID}_3'  # running leg has 6 km laps
        with self.act_db.managed_session() as session:
            laps = session.query(ActivityLaps).filter(ActivityLaps.activity_id == run_id).all()
            for lap in laps:
                self.assertIsNotNone(lap.elapsed_time, f'{run_id} lap {lap.lap}: elapsed_time missing')
                self.assertIsNotNone(lap.distance, f'{run_id} lap {lap.lap}: distance missing')
                self.assertGreater(lap.distance, 0, f'{run_id} lap {lap.lap}: distance should be > 0')

    def test_hr_zone_times_per_session(self):
        """Zone N must come from time_in_hr_zone[N]; index 0 is the time below zone 1."""
        with self.act_db.managed_session() as session:
            for i, expected in enumerate(EXPECTED_SESSION_HR_ZONE_SECONDS, start=1):
                activity_id = f'{PARENT_ID}_{i}'
                row = session.query(Activities).filter(Activities.activity_id == activity_id).one()
                self.assertEqual(zone_seconds(row), expected, f'{activity_id}: seconds in HR zones 1-5')

    def test_hr_zone_times_per_lap(self):
        run_id = f'{PARENT_ID}_3'
        with self.act_db.managed_session() as session:
            lap = session.query(ActivityLaps).filter(ActivityLaps.activity_id == run_id, ActivityLaps.lap == 0).one()
            self.assertEqual(zone_seconds(lap), EXPECTED_RUN_LAP_0_HR_ZONE_SECONDS, f'{run_id} lap 0: seconds in HR zones 1-5')

    def test_records_partitioned_by_session(self):
        with self.act_db.managed_session() as session:
            for i in range(1, 6):
                activity_id = f'{PARENT_ID}_{i}'
                count = session.query(ActivityRecords).filter(ActivityRecords.activity_id == activity_id).count()
                self.assertGreater(count, 0, f'{activity_id} should have at least one record')

    def test_every_record_is_written(self):
        with self.act_db.managed_session() as session:
            count = session.query(ActivityRecords).filter(ActivityRecords.activity_id.like(f'{PARENT_ID}_%')).count()
        self.assertEqual(count, EXPECTED_RECORD_COUNT)

    def test_importing_again_does_not_duplicate_or_lose_records(self):
        plugin_manager = PluginManager(self.gc_config.get_plugins_dir(), self.test_db_params)
        ActivityFitFileProcessor(self.test_db_params, plugin_manager, debug=0).write_file(self.fit_file)
        with self.act_db.managed_session() as session:
            count = session.query(ActivityRecords).filter(ActivityRecords.activity_id.like(f'{PARENT_ID}_%')).count()
        self.assertEqual(count, EXPECTED_RECORD_COUNT)

    def test_devices_linked_to_every_child(self):
        with self.act_db.managed_session() as session:
            for i in range(1, 6):
                activity_id = f'{PARENT_ID}_{i}'
                count = session.query(ActivitiesDevices).filter(ActivitiesDevices.activity_id == activity_id).count()
                self.assertGreater(count, 0, f'{activity_id} should have at least one device association')


if __name__ == '__main__':
    unittest.main()
