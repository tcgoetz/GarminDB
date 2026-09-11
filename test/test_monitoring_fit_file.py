"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging

import fitfile
from idbutils import FileProcessor

from test_fit_file import TestFitFile



root_logger = logging.getLogger()
handler = logging.FileHandler('test_monitoring_fit_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class TestMonitoringFitFile(TestFitFile):
    """Class for testing FIT file parsing."""

    def check_monitoring_messages(self, fit_file):
        last_steps = {}
        last_timestamp = None
        for message in fit_file.monitoring:
            if 'steps' in message.fields:
                steps = message.fields.steps
                activity_type = message.fields.activity_type
                if activity_type in last_steps:
                    activity_last_steps = last_steps[activity_type]
                    self.assertGreaterEqual(steps, activity_last_steps, f'{fit_file.filename}: {repr(message)} - steps not greater than last steps')
                last_steps[activity_type] = steps
                if last_timestamp:
                    self.check_timestamp_delta(fit_file, last_timestamp, message.fields.timestamp, (0, 43200))
                last_timestamp = message.fields.timestamp
            self.check_message_fields(fit_file, message.type, message)
            self.check_value_range(fit_file, message, 'distance', 0, 100 * 5280, True)
            self.check_value_range(fit_file, message, 'cum_ascent', 0, 5280, True)
            self.check_value_range(fit_file, message, 'cum_descent', 0, 5280, True)

    def check_monitoring_file(self, filename):
        fit_file = fitfile.file.File(filename, self.measurement_system)
        self.check_message_types(fit_file, dump_message=True)
        logger.info('%s (%s) monitoring file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
        self.check_file_id(fit_file, fitfile.FileType.monitoring_b)
        self.check_monitoring_messages(fit_file)

    def test_parse_monitoring(self):
        monitoring_path = self.file_path + '/monitoring'
        file_names = FileProcessor.dir_to_files(monitoring_path, fitfile.file.name_regex, False)
        if len(file_names) > 0:
            for file_name in file_names:
                self.check_monitoring_file(file_name)
        else:
            logger.error("Add test files to %s", monitoring_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
