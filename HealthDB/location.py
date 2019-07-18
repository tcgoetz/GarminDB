"""Objects for implementing location objects."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


class Location(object):
    """Object representing a geographic location."""

    def __init__(self, lat_deg, long_deg):
        """Return a Location instance created with the passed in latitude and longitude."""
        self.lat_deg = lat_deg
        self.long_deg = long_deg

    @classmethod
    def from_objs(cls, lat_obj, long_obj):
        """Return a Location instance created with the passed in latitude object and longitude object."""
        return cls(lat_obj.to_degrees(), long_obj.to_degrees())

    @classmethod
    def google_maps_url(cls, lat_str, long_str):
        """Given a latitude and longitude, return a Google Maps URL for that location."""
        return '"http://maps.google.com/?ie=UTF8&q=" || %s || "," || %s || "&z=13"' % (lat_str, long_str)

    def to_google_maps_url(self):
        """Return a Google Maps URL for the location."""
        return self.google_maps_url(self.lat_deg, self.long_deg)
