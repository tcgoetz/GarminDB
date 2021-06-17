"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging

from idbutils import FileProcessor

from garmindb import Tcx


root_logger = logging.getLogger()
handler = logging.FileHandler('tcx_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestTcxFile(unittest.TestCase):
    """Class for testing TCX file parsing."""

    @classmethod
    def setUpClass(cls):
        cls.file_path = 'test_files/tcx'
        cls.tcx_filename_regex = r'.*\.tcx'

    def check_activity_file(self, filename):
        tcx = Tcx()
        tcx.read(filename)
        (manufacturer, product) = tcx.get_manufacturer_and_product()
        logger.info("%s: sport %r end_time %r start_time %r manufacturer %r product %r serial_number %r laps %r distance %r calories %r start %r end %r "
                    "hr %r, %r max speed %r cadence %r, %r",
                    filename, tcx.sport, tcx.end_time, tcx.start_time, manufacturer, product, tcx.serial_number, tcx.lap_count,
                    tcx.distance, tcx.calories, tcx.start_loc, tcx.end_loc, tcx.hr_avg, tcx.hr_max, tcx.speed_max, tcx.cadence_avg, tcx.cadence_max)
        self.assertGreater(tcx.end_time, tcx.start_time)
        self.assertGreater(tcx.lap_count, 0)

    def test_parse_tcx(self):
        file_names = FileProcessor.dir_to_files(self.file_path, self.tcx_filename_regex, False)
        for file_name in file_names:
            self.check_activity_file(file_name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
