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
root_logger.addHandler(logging.FileHandler('multisport_activity.log', 'w'))
root_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Garmin names each activity FIT file <activity_id>_ACTIVITY.fit; the parent id is the filename prefix.
PARENT_ID = '22638574127'
FIXTURE = f'test_files/fit/activity/{PARENT_ID}_ACTIVITY.fit'
EXPECTED_SESSION_LAP_COUNTS = [14, 1, 6, 1, 3]  # swim / T1 / run / T2 / swim
EXPECTED_SPORTS = [
    ('swimming', 'lap_swimming'),
    ('transition', 'generic'),
    ('running', 'generic'),
    ('transition', 'generic'),
    ('swimming', 'lap_swimming'),
]


class TestMultisportActivity(unittest.TestCase):
    """Verify multi-sport FIT files produce one DB row per leg, with correct partitioning."""

    @classmethod
    def setUpClass(cls):
        cls.gc_config = GarminConnectConfigManager()
        cls.tmp_dir = tempfile.mkdtemp(prefix='garmindb_multisport_test_')
        cls.db_params = DbParams(db_type='sqlite', db_path=cls.tmp_dir)
        cls.act_db = ActivitiesDb(cls.db_params)
        plugin_manager = PluginManager(cls.gc_config.get_plugins_dir(), cls.db_params)
        processor = ActivityFitFileProcessor(cls.db_params, plugin_manager, debug=0)
        processor.write_file(fitfile.file.File(FIXTURE))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

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
        """Regression for the hr_zones_timer / lap write-order bug: lap rows must have distance and elapsed_time."""
        run_id = f'{PARENT_ID}_3'  # running leg has 6 km laps
        with self.act_db.managed_session() as session:
            laps = session.query(ActivityLaps).filter(ActivityLaps.activity_id == run_id).all()
            for lap in laps:
                self.assertIsNotNone(lap.elapsed_time, f'{run_id} lap {lap.lap}: elapsed_time missing')
                self.assertIsNotNone(lap.distance, f'{run_id} lap {lap.lap}: distance missing')
                self.assertGreater(lap.distance, 0, f'{run_id} lap {lap.lap}: distance should be > 0')

    def test_records_partitioned_by_session(self):
        with self.act_db.managed_session() as session:
            for i in range(1, 6):
                activity_id = f'{PARENT_ID}_{i}'
                count = session.query(ActivityRecords).filter(ActivityRecords.activity_id == activity_id).count()
                self.assertGreater(count, 0, f'{activity_id} should have at least one record')

    def test_devices_linked_to_every_child(self):
        with self.act_db.managed_session() as session:
            for i in range(1, 6):
                activity_id = f'{PARENT_ID}_{i}'
                count = session.query(ActivitiesDevices).filter(ActivitiesDevices.activity_id == activity_id).count()
                self.assertGreater(count, 0, f'{activity_id} should have at least one device association')


if __name__ == '__main__':
    unittest.main()
