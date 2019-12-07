"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime

from tcx import Tcx
import GarminDB
from Fit import Distance, Speed, field_enums
from utilities import Location, FileProcessor


root_logger = logging.getLogger()
handler = logging.FileHandler('tcx.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestTcxFile(unittest.TestCase):
    """Class for testing FIT file parsing."""

    @classmethod
    def setUpClass(cls):
        cls.file_path = 'test_files/tcx'
        cls.tcx_filename_regex = r'.*\.tcx'

    def test_loop(self):
        sport = field_enums.Sport.boating
        start_time = datetime.datetime.now()
        stop_time = start_time + datetime.timedelta(hours=1)
        product = field_enums.GarminProduct.Fenix5X
        serial_number = GarminDB.Device.unknown_device_serial_number
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
        tcx.create(sport.name, start_time)
        tcx.add_creator(product.name, serial_number, version=version)
        track = tcx.add_lap(start_time, stop_time, lap_distance, lap_calories)
        tcx.add_point(track, start_time, position1, record_alititude.to_meters(), record_hr, record_speed.to_mps())
        tcx.add_point(track, stop_time, position2, record_alititude.to_meters(), record_hr, record_speed.to_mps())
        # now read it back
        tcx.update()
        self.assertEqual(field_enums.Sport.from_string(tcx.get_sport()), sport)
        self.assertEqual(tcx.get_start_time(), start_time)
        self.assertEqual(tcx.get_end_time(), stop_time)
        self.assertEqual(tcx.get_calories(), lap_calories)
        self.assertEqual(tcx.get_distance(), lap_distance)
        self.assertEqual(tcx.get_duration(), 60 * 60)
        self.assertEqual(tcx.get_start_loc(), position1)
        self.assertEqual(tcx.get_end_loc(), position2)
        creator = tcx.get_creator()
        self.assertEqual(creator['Name'], product.name)
        self.assertEqual(int(creator['SerialNumber']), serial_number)
        self.assertEqual(creator['Version'], version)
        logger.info('hr avg: %f', tcx.get_hr_avg())
        logger.info('hr max: %f', tcx.get_hr_max())

    def check_activity_file(self, filename):
        logger.info('Parsing: %s', filename)
        tcx = Tcx()
        tcx.read(filename)
        end_time = tcx.get_end_time()
        start_time = tcx.get_start_time()
        creator = tcx.get_creator()
        product = creator['Name']
        serial_number = creator['SerialNumber']
        laps = tcx.get_lap_count()
        distance = tcx.get_distance()
        sport = tcx.get_sport()
        calories = tcx.get_calories()
        start_loc = tcx.get_start_loc()
        stop_loc = tcx.get_end_loc()
        avg_hr = tcx.get_hr_avg()
        max_hr = tcx.get_hr_max()
        max_speed = tcx.get_speed_max()
        max_cadence = tcx.get_cadence_max()
        avg_cadence = tcx.get_cadence_avg()
        logger.info("%s: sport %r end_time %r start_time %r product %r serial_number %r laps %r distance %r calories %r start %r end %r "
                    "hr %r, %r max speed %r cadence %r, %r",
                    filename, sport, end_time, start_time, product, serial_number, laps, distance, calories, start_loc, stop_loc,
                    avg_hr, max_hr, max_speed, avg_cadence, max_cadence)

    def test_parse_tcx(self):
        file_names = FileProcessor.dir_to_files(self.file_path, self.tcx_filename_regex, False)
        for file_name in file_names:
            self.check_activity_file(file_name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
