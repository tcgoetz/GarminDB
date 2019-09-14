"""Objects for importing Garmin activity data from Garmin Connect downloads and FIT files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
import dateutil.parser
import re

import tcxparser
import GarminDB

logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class TcxFile(object):
    """Wraps third party TCX library and handles requests for nonexistent fields."""

    def __init__(self, filename):
        self.tcx = tcxparser.TCXParser(filename)

    def get_value(self, attribute):
        """Return a value named 'attribute' from the parsed TCX file."""
        return getattr(self.tcx, attribute, None)

    def get_date(self, attribute):
        """Return a datetime named 'attribute' from the parsed TCX file."""
        date_str = self.get_value(attribute)
        if date_str:
            try:
                return dateutil.parser.parse(date_str, ignoretz=True)
            except (ValueError, AttributeError) as e:
                logger.error("%s for %s value %r", e, attribute, date_str)

    def get_manufacturer_and_product(self):
        """Return the product and interperlated manufacturer from the parsed TCX file."""
        product = self.get_value('creator')
        if product:
            manufacturer = GarminDB.Device.Manufacturer.Unknown
            if product is not None:
                match = re.search('Forerunner|Fenix', product)
                if match:
                    manufacturer = GarminDB.Device.Manufacturer.Garmin
                match = re.search('Microsoft', product)
                if match:
                    manufacturer = GarminDB.Device.Manufacturer.Microsoft
            return (manufacturer, product)
        return (None, None)

    def get_serial_number(self):
        """Return the serial number of the device that recorded the parsed TCX file."""
        serial_number = self.get_value('creator_version')
        if serial_number is None or serial_number == 0:
            serial_number = GarminDB.Device.unknown_device_serial_number
        return serial_number

    def get_lap_count(self):
        """Return the number of laps recorded in the parsed TCX file."""
        return self.get_value('lap_count')

    def get_sport(self):
        """Return the sport recorded in the parsed TCX file."""
        return self.get_value('activity_type')
