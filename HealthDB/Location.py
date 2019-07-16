#
# copyright Tom Goetz
#


class Location(object):
    def __init__(self, lat_deg, long_deg):
        self.lat_deg = lat_deg
        self.long_deg = long_deg

    @classmethod
    def from_objs(cls, lat_obj, long_obj):
        return cls(lat_obj.to_degrees(), long_obj.to_degrees())

    @classmethod
    def google_maps_url(cls, lat_str, long_str):
        return '"http://maps.google.com/?ie=UTF8&q=" || %s || "," || %s || "&z=13"' % (lat_str, long_str)

    def to_google_maps_url(self):
        return self.google_maps_url(self.lat_deg, self.long_deg)
