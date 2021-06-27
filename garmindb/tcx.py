"""Class that specializes TCX files for GarminDb."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import re
from cached_property import cached_property

import tcxfile
from idbutils import Location
from fitfile import Distance, Speed, conversions

from .garmindb import Device


class Tcx(tcxfile.Tcx):
    """Read and write TCX files."""

    __product_to_manufactuer_cache = {}

    __default_device_serial_numbers = {
        (Device.Manufacturer.Microsoft, 'Microsoft Band') : Device.unknown_device_serial_number + 1
    }

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

    def __manufacturer_from_product(self, product):
        for manufacturer in Device.Manufacturer:
            if manufacturer.name.lower() in product.lower():
                return manufacturer
        mappings = {
            r'VivoActive|Forerunner|Fenix' : Device.Manufacturer.Garmin,
        }
        for regex, manufacturer in mappings.items():
            if re.search(regex, product, re.IGNORECASE):
                return manufacturer

    def _manufacturer_from_product(self, product):
        if product in self.__product_to_manufactuer_cache:
            return self.__product_to_manufactuer_cache[product]
        manufacturer = self.__manufacturer_from_product(product)
        if manufacturer is not None:
            self.__product_to_manufactuer_cache[product] = manufacturer
        return manufacturer

    def get_manufacturer_and_product(self):
        """Return the product and interperlated manufacturer from the parsed TCX file."""
        product = super().creator_product
        if not product:
            return (None, None)
        return (self._manufacturer_from_product(product), product)

    @cached_property
    def serial_number(self):
        """Return the serial number of the device that recorded the parsed TCX file."""
        serial_number = super().creator_serialnumber
        if not serial_number or serial_number == '0':
            (manufactuer, product) = self.get_manufacturer_and_product()
            if (manufactuer, product) in self.__default_device_serial_numbers:
                serial_number = self.__default_device_serial_numbers[(manufactuer, product)]
            else:
                serial_number = Device.unknown_device_serial_number
        return serial_number

    @cached_property
    def start_loc(self):
        """Return the start location of the activity as a Location instance."""
        return Location(location=super().start_loc)

    @cached_property
    def end_loc(self):
        """Return the end location of the activity as a tuple of Location instances."""
        return Location(location=super().end_loc)

    @cached_property
    def distance(self):
        """Return the total distance recorded for the activity."""
        return Distance.from_meters(super().distance)

    @cached_property
    def speed_max(self):
        """Return the maximum of all speed readings in the TCX file."""
        return Speed.from_mps(super().speed_max)

    @cached_property
    def ascent(self):
        """Return the total ascent over the activity."""
        return Distance.from_meters(super().ascent)

    @cached_property
    def descent(self):
        """Return the total descent over the activity."""
        return Distance.from_meters(super().descent)

    def get_lap_duration(self, lap):
        """Return the recorded duration for the lap."""
        return conversions.secs_to_dt_time(super().get_lap_duration(lap))

    def get_lap_distance(self, lap):
        """Return the recorded distance for the lap."""
        return Distance.from_meters(super().get_lap_distance(lap))

    def get_point_loc(self, point):
        """Return the position of the trackpoint."""
        return Location(location=super().get_point_loc(point))

    def get_point_altitude(self, point):
        """Return the altitude of the trackpoint."""
        return Distance.from_meters(super().get_point_altitude(point))

    def get_point_speed(self, point):
        """Return the speed readings in the point."""
        return Speed.from_mps(super().get_point_speed(point))
