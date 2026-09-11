"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime
import re

import fitfile
from idbutils import FileProcessor

from test_fit_file import TestFitFile

root_logger = logging.getLogger()
handler = logging.FileHandler('test_sleep_disruptions_fit_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class TestSleepDisruptionsFitFile(TestFitFile):
    """Class for testing FIT file parsing."""

    def test_parse_leep_disruptions(self):
        sleep_path = self.file_path + '/sleep_disruptions'
        file_names = FileProcessor.dir_to_files(sleep_path, fitfile.file.name_regex, False)
        if len(file_names) > 0:
            for file_name in file_names:
                self.check_unknown_file(file_name)
        else:
            logger.error("Add test files to %s", sleep_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
