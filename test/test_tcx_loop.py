"""Test Tcx file creation."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime

from fitfile import GarminProduct, Distance, Speed, Sport
from idbutils import Location

from garmindb import Tcx


root_logger = logging.getLogger()
handler = logging.FileHandler('loop.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestLoop(unittest.TestCase):
    """Class for testing Tcx file creation."""

    @classmethod
    def setUpClass(cls):
        cls.file_path = 'test_files/tcx'
        cls.tcx_filename_regex = r'.*\.tcx'

    def test_loop(self):
        sport = Sport.boating.name
        start_time = datetime.datetime.now()
        stop_time = start_time + datetime.timedelta(hours=1)
        product = GarminProduct.Fenix.name
        serial_number = 123412341234
        version = (1, 2, 3, 4)
        lap_distance = Distance.from_meters(10)
        lap_calories = 100
        position1 = Location(1, 2)
        position2 = Location(3, 4)
        record_alititude = Distance.from_meters(100)
        record_hr = 100
        record_speed = Speed.from_mph(6.0)
        # create a TCX XML tree
        tcx = Tcx()
        tcx.create(sport, start_time)
        tcx.add_creator(product, serial_number, version=version)
        track = tcx.add_lap(start_time, stop_time, lap_distance, lap_calories)
        tcx.add_point(track, start_time, position1, record_alititude, record_hr, record_speed)
        tcx.add_point(track, stop_time, position2, record_alititude, record_hr, record_speed)
        # now read it back
        tcx.update()
        self.assertEqual(tcx.sport, sport)
        self.assertEqual(tcx.start_time, start_time)
        self.assertEqual(tcx.end_time, stop_time)
        self.assertEqual(tcx.calories, lap_calories)
        self.assertEqual(tcx.distance, lap_distance)
        self.assertEqual(tcx.duration, 60 * 60)
        self.assertEqual(tcx.start_loc, position1)
        self.assertEqual(tcx.end_loc, position2)
        self.assertEqual(tcx.creator_product, product)
        self.assertEqual(int(tcx.creator_serialnumber), serial_number)
        self.assertEqual(tcx.creator_version, version)
        logger.info('hr avg: %f', tcx.hr_avg)
        logger.info('hr max: %f', tcx.hr_max)


if __name__ == '__main__':
    unittest.main(verbosity=2)
