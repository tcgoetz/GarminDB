"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging

import fitfile
from idbutils import FileProcessor

from garmindb.activity_fit_file_processor import ActivityFitFileProcessor

from test_fit_file import TestFitFile


root_logger = logging.getLogger()
handler = logging.FileHandler('test_activity_fit_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class TestActivityFitFile(TestFitFile):
    """Class for testing activity FIT file parsing."""

    def check_activity_file(self, filename):
        logger.info('parsing %s', filename)
        try:
            fit_file = fitfile.file.File(filename, self.measurement_system)
            logger.info('%s (%s) activity file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
        except Exception as e:
            self.fail('Failed to parse %s: %s', filename, e)
        self.check_message_types(fit_file, dump_message=True)
        self.check_file_id(fit_file, fitfile.FileType.activity)
        (sport, sub_sport) = self.check_sport(fit_file)
        for message_index, message in enumerate(fit_file.record):
            self.check_record(fit_file, sport, sub_sport, message_index, message)
        for message_index, message in enumerate(fit_file.lap):
            self.check_lap_or_session(fit_file, sport, sub_sport, message_index, message)
        for message_index, message in enumerate(fit_file.session):
            self.check_lap_or_session(fit_file, sport, sub_sport, message_index, message)

    def test_parse_activity(self):
        activity_path = self.file_path + '/activity'
        file_names = FileProcessor.dir_to_files(activity_path, fitfile.file.name_regex, False)
        if len(file_names) > 0:
            for file_name in file_names:
                self.check_activity_file(file_name)
        else:
            logger.error("Add test files to %s", activity_path)


class TestHrZoneData(unittest.TestCase):
    """hrz_N_time must be time_in_hr_zone[N]: index 0 is the time below zone 1."""

    def test_hr_zone_times_skip_time_below_zone_1(self):
        fit_file = fitfile.file.File('test_files/fit/activity/10000000001_ACTIVITY.fit')
        # Run leg session: time_in_hr_zone is 0:00 below zone 1, then 0:00, 0:39, 13:34, 18:11, 0:07 in zones 1-5, then 0:00 above.
        message = next(m for m in fit_file.time_in_zone
                       if m.fields.get('hr_zones_timer_type') is fitfile.fields.HeartRateZonesTimerType.session
                       and m.fields.get('reference_index') == 2)
        # __hr_zone_data does not use the processor, so no database is needed.
        zone_data = ActivityFitFileProcessor._ActivityFitFileProcessor__hr_zone_data(None, message.fields)
        seconds = [round(t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6)
                   for t in (zone_data[f'hrz_{zone}_time'] for zone in range(1, 6))]
        self.assertEqual(seconds, [0, 39, 815, 1091, 7])


if __name__ == '__main__':
    unittest.main(verbosity=2)
