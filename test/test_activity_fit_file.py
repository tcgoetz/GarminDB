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
handler = logging.FileHandler('test_activity_fit_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class TestActivityFitFile(TestFitFile):
    """Class for testing activity FIT file parsing."""

    def check_activity_file(self, filename):
        logger.info('parsing %s', filename)
        fit_file = fitfile.file.File(filename, self.measurement_system)
        logger.info('%s (%s) activity file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
