"""Class that specializes TCX files for GarminDb."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import re

from Tcx import Tcx
from utilities import Location
from Fit import Distance, Speed
import GarminDB


class GarminDbTcx(Tcx):
    """Read and write TCX files."""

    def __init__(self, debug=False):
        """Return and instance of the GaminDbTcx class."""
        super().__init__(debug)

    def add_lap(self, start_dt, end_dt, distance, calories):
        """Add a lap to the TCX file data."""
        return super().add_lap(start_dt, end_dt, distance.to_meters(), calories)

    def add_point(self, track, dt, location, alititude, heart_rate, speed):
        """Add a point to the lap."""
        return super().add_point(track, dt, (location.lat_deg, location.long_deg), alititude.to_meters(), heart_rate, speed.to_mps())

    def add_creator(self, product, serial_number, product_id=None, version=None):
        """Add a creator element."""
        super().add_creator(product, serial_number, product_id, version)

    def get_manufacturer_and_product(self):
        """Return the product and interperlated manufacturer from the parsed TCX file."""
        product = super().creator_product
        if not product:
            return (None, None)
        manufacturer = GarminDB.Device.Manufacturer.Unknown
        match = re.search('VivoActive|Forerunner|Fenix', product)
        if match:
            manufacturer = GarminDB.Device.Manufacturer.Garmin
        match = re.search('Microsoft', product)
        if match:
            manufacturer = GarminDB.Device.Manufacturer.Microsoft
        return (manufacturer, product)

    @property
    def serial_number(self):
        """Return the serial number of the device that recorded the parsed TCX file."""
        serial_number = super().creator_serialnumber
        return serial_number if serial_number is None or serial_number == 0 else GarminDB.Device.unknown_device_serial_number

    @property
    def start_loc(self):
        """Return the start location of the activity as a Location instance."""
        return Location(location=super().start_loc)

    @property
    def end_loc(self):
        """Return the end location of the activity as a tuple of Location instances."""
        return Location(location=super().end_loc)

    @property
    def distance(self):
        """Return the total distance recorded for the activity."""
        return Distance.from_meters(super().distance)

    @property
    def speed_max(self):
        """Return the maximum of all speed readings in the TCX file."""
        return Speed.from_mps(super().speed_max)

    @property
    def ascent(self):
        """Return the total ascent over the activity."""
        return Distance.from_meters(super().ascent)

    @property
    def descent(self):
        """Return the total descent over the activity."""
        return Distance.from_meters(super().descent)
