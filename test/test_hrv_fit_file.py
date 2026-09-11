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
handler = logging.FileHandler('test_hrv_fit_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class TestHrvFitFile(TestFitFile):
    """Class for testing FIT file parsing."""

    def check_hrv_status_file(self, filename):
        logger.info('parsing %s', filename)
        fit_file = fitfile.file.File(filename, self.measurement_system)
        logger.info('%s (%s) hrv status file message types: %s', filename, fit_file.time_created_local, fit_file.message_types)
        self.check_message_types(fit_file, dump_message=True)
        self.check_file_id(fit_file, fitfile.FileType.hrv_status)

    def test_parse_hrv_status(self):
        # root_logger.setLevel(logging.DEBUG)
        hrv_path = self.file_path + '/hrv'
        file_names = FileProcessor.dir_to_files(hrv_path, fitfile.file.name_regex, False)
        if len(file_names) > 0:
            for file_name in file_names:
                self.check_hrv_status_file(file_name)
        else:
            logger.error("Add test files to %s", hrv_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
