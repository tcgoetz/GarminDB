"""Objects for exporting Garmin activity data as TCX files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import logging
import xml.etree.ElementTree as ET
import dateutil.parser
from Fit import Distance
from utilities import Location


logger = logging.getLogger(__file__)


class Tcx(object):
    """Create TCX files from data."""

    filename_regex = r'.*\.tcx'

    namespaces = {
        'xsd': ('xsd', "http://www.w3.org/2001/XMLSchema"),
        'xsi': ('xsi', "http://www.w3.org/2001/XMLSchema-instance"),
        # 'xsi:schemaLocation': "http://www.garmin.com/xmlschemas/ActivityExtension/v2 "
        #                       "http://www.garmin.com/xmlschemas/ActivityExtensionv2.xsd "
        #                       "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 "
        #                       "http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd",
        'ae' : ('', 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'),
        'tcd': ('', "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
    }
    (default_prefix, default_namespace) = namespaces['tcd']

    def __init__(self):
        """Return and instance of the Tcx class."""

    @classmethod
    def __element(cls, tag):
        return ET.Element(cls.__tag_with_default_ns(tag))

    @classmethod
    def __subelement(cls, parent, tag, **kwargs):
        return ET.SubElement(parent, cls.__tag_with_default_ns(tag), **kwargs)

    @classmethod
    def __subelement_ns(cls, parent, ns_name, tag, **kwargs):
        return ET.SubElement(parent, cls.__tag_with_ns(ns_name, tag), **kwargs)

    def create(self, sport, start_dt):
        """Create a new TCX file."""
        for name, (prefix, uri) in self.namespaces.items():
            ET.register_namespace(prefix, uri)
        self.root = self.__element('TrainingCenterDatabase')
        activities = self.__subelement(self.root, 'Activities')
        self.activity = self.__subelement(activities, 'Activity', attrib={'Sport' : sport})
        self.__subelement(self.activity, 'Id').text = start_dt.isoformat()

    @classmethod
    def __namespace(cls, name):
        (prefix, ns) = cls.namespaces[name]
        return ns

    @classmethod
    def __tag_with_ns(cls, name, tag):
        (prefix, ns) = cls.namespaces[name]
        return f'{{{ns}}}{tag}'

    @classmethod
    def __tag_with_default_ns(cls, tag):
        return f'{{{cls.default_namespace}}}{tag}'

    def add_lap(self, start_dt, end_dt, distance, calories):
        """Add a lap to the TCX file data."""
        lap = self.__subelement(self.activity, 'Lap', attrib={'StartTime': start_dt.isoformat()})
        self.__subelement(lap, 'TotalTimeSeconds').text = str((end_dt - start_dt).total_seconds())
        if distance.to_meters() > 0:
            self.__subelement(lap, 'DistanceMeters').text = str(distance.to_meters())
        if calories > 0:
            self.__subelement(lap, 'Calories').text = str(calories)
        return self.__subelement(lap, 'Track')

    def add_point(self, track, dt, location, alititude, heart_rate, speed):
        """Add a point to the lap."""
        point = self.__subelement(track, 'Trackpoint')
        self.__subelement(point, 'Time').text = dt.isoformat()
        if location.lat_deg is not None and location.long_deg is not None:
            position = self.__subelement(point, 'Position')
            self.__subelement(position, 'LatitudeDegrees').text = str(location.lat_deg)
            self.__subelement(position, 'LongitudeDegrees').text = str(location.long_deg)
        if alititude is not None:
            self.__subelement(point, 'AltitudeMeters').text = str(alititude)
        hr = self.__subelement(point, 'HeartRateBpm')
        self.__subelement(hr, 'Value').text = str(heart_rate)
        if speed is not None:
            extensions = self.__subelement(point, 'Extensions')
            ate = self.__subelement_ns(extensions, 'ae', 'ActivityTrackpointExtension')
            self.__subelement_ns(ate, 'ae', 'Speed').text = str(speed)
        return point

    def add_creator(self, name, serial_number, product_id=None, version=None):
        """Add a creator element."""
        creator = self.__subelement(self.activity, 'Creator', attrib={self.__tag_with_ns('xsi', 'type'): 'Device_t'})
        self.__subelement(creator, 'Name').text = name
        self.__subelement(creator, 'UnitId').text = str(serial_number)
        if product_id is not None:
            self.__subelement(creator, 'ProductID').text = str(product_id)
        if version is not None:
            version_tag = self.__subelement(creator, 'Version')
            self.__subelement(version_tag, 'VersionMajor').text = str(version[0])
            self.__subelement(version_tag, 'VersionMinor').text = str(version[1])
            self.__subelement(version_tag, 'BuildMajor').text = str(version[2])
            self.__subelement(version_tag, 'BuildMinor').text = str(version[3])

    @classmethod
    def __find(cls, obj, xpath, namespace=default_namespace):
        return obj.find(xpath, namespaces={'ns': namespace})

    @classmethod
    def __findall(cls, obj, xpath, namespace=default_namespace):
        return obj.findall(xpath, namespaces={'ns': namespace})

    @classmethod
    def __findtext(cls, obj, xpath, namespace=default_namespace):
        return obj.findtext(xpath, namespaces={'ns': namespace})

    @classmethod
    def __find_type(cls, type_func, obj, xpath, default=0, namespace=default_namespace):
        try:
            return type_func(cls.__findtext(obj, xpath))
        except Exception:
            return default

    @classmethod
    def __find_type_none(cls, type_func, obj, xpath, namespace=default_namespace):
        return cls.__find_type(type_func, obj, xpath, None, namespace)

    def __tag_values(self, type_func, tag_path, namespace=default_namespace):
        return [type_func(value.text) for value in self.__findall(self.activity, tag_path, namespace)]

    def __sum_of_tag(self, type_func, tag_path, namespace=default_namespace):
        values = self.__tag_values(type_func, tag_path, namespace)
        if len(values):
            return sum(values)

    def __max_of_tag(self, type_func, tag_path, namespace=default_namespace):
        values = self.__tag_values(type_func, tag_path, namespace)
        if len(values):
            return max(values)

    def __avg_of_tag(self, type_func, tag_path, namespace=default_namespace):
        values = self.__tag_values(type_func, tag_path, namespace)
        if len(values):
            return sum(values) / len(values)

    def update(self):
        """Recaclulate file lists."""
        # print(ET.dump(self.root))
        self.creator = self.__find(self.activity, 'ns:Creator')
        self.laps = self.__find(self.activity, 'ns:Lap')
        self.points = self.__findall(self.activity, './/ns:Trackpoint')
        self.points = self.__findall(self.activity, './/ns:Trackpoint')
        self.hr_values = self.__tag_values(int, './/ns:HeartRateBpm/ns:Value')
        self.cadence_values = self.__tag_values(int, './/ns:Cadence')
        self.altitude_values = self.__tag_values(float, './/ns:AltitudeMeters')
        logger.info('creator %s root %s activity %s', self.creator, self.root, self.activity)
        logger.info('laps (%d) %s', len(self.laps), self.laps)
        logger.info('points (%d) %s', len(self.points), self.points)
        logger.info('hr (%d) %s', len(self.hr_values), self.hr_values)
        logger.info('cadence (%d) %s', len(self.cadence_values), self.cadence_values)
        logger.info('altitude (%d) %s', len(self.altitude_values), self.altitude_values)

    def write(self, filename):
        """Write the TCX XML data to a file."""
        tree = ET.ElementTree(self.root)
        tree.write(filename, encoding='UTF-8', xml_declaration=True)
        self.update()

    def read(self, filename):
        """Update the TCX XML data from a file."""
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()
        self.activity = self.__find(self.root, './/ns:Activity')
        self.update()

    def get_creator(self):
        """Return the Creator data."""
        version_element = self.__find(self.creator, 'ns:Version')
        version_major = self.__find_type(int, version_element, 'ns:VersionMajor')
        version_minor = self.__find_type(int, version_element, 'ns:VersionMinor')
        build_major = self.__find_type(int, version_element, 'ns:BuildMajor')
        build_minor = self.__find_type(int, version_element, 'ns:BuildMinor')
        return {
            'Name'          : self.__findtext(self.creator, 'ns:Name'),
            'SerialNumber'  : self.__findtext(self.creator, 'ns:UnitId'),
            'Version'       : (version_major, version_minor, build_major, build_minor)
        }

    def get_sport(self):
        """Return the sport name as a string."""
        return self.activity.attrib['Sport']

    @classmethod
    def get_point_time(cls, point):
        """Return the time of the trackpoint as a datetime."""
        return cls.__find_type(dateutil.parser.parse, point, 'ns:Time')

    @classmethod
    def get_point_loc(cls, point):
        """Return the position of the trackpoint."""
        position = cls.__find(point, 'ns:Position')
        if position:
            return Location(cls.__findtext(position, 'ns:LatitudeDegrees'), cls.__findtext(position, 'ns:LongitudeDegrees'))

    @classmethod
    def get_point_hr(cls, point):
        """Return the position of the trackpoint."""
        try:
            return cls.__find_type_none(int, point.find('ns:HeartRateBpm'), 'Value')
        except Exception:
            return None

    def get_lap_count(self):
        """Return the number of laps present in the TCX file."""
        return len(self.laps)

    @classmethod
    def get_lap_points(cls, lap):
        """Return a list of the trackpoint of the lap."""
        return cls.__findall(cls.__find(lap, 'ns:Track'), 'ns:Trackpoint')

    @classmethod
    def get_lap_calories(cls, lap):
        """Return the recorded calories for the lap."""
        return cls.__find_type(int, lap, 'ns:Calories')

    @classmethod
    def get_lap_distance(cls, lap):
        """Return the recorded distance for the lap."""
        return cls.__find_type(float, lap, 'ns:DistanceMeters')

    @classmethod
    def get_lap_duration(cls, lap):
        """Return the recorded duration for the lap."""
        return cls.__find_type(float, lap, 'ns:TotalTimeSeconds')

    @classmethod
    def get_lap_start(cls, lap):
        """Return the start time of the lap as a datetime instance."""
        return dateutil.parser.parse(lap.attrib['StartTime'])

    @classmethod
    def get_lap_end(cls, lap):
        """Return the end time of the lap as a datetime instance."""
        return cls.get_point_time(cls.get_lap_points(lap)[-1])

    @classmethod
    def get_lap_start_loc(cls, lap):
        """Return the end location of the lap as a Location instance."""
        return cls.get_point_loc(cls.get_lap_points(lap)[0])

    @classmethod
    def get_lap_end_loc(cls, lap):
        """Return the end location of the lap as a Location instance."""
        return cls.get_point_loc(cls.get_lap_points(lap)[-1])

    def get_start_time(self):
        """Return the start time of the activity as a tuple of datetime instances."""
        if len(self.points) > 0:
            return self.get_point_time(self.points[0])

    def get_end_time(self):
        """Return the end time of the activity as a tuple of datetime instances."""
        if len(self.points) > 0:
            return self.get_point_time(self.points[-1])

    def get_start_loc(self):
        """Return the start location of the activity as a tuple of Location instances."""
        if len(self.points) > 0:
            return self.get_point_loc(self.points[0])

    def get_end_loc(self):
        """Return the end location of the activity as a tuple of Location instances."""
        if len(self.points) > 0:
            return self.get_point_loc(self.points[-1])

    def get_calories(self):
        """Return the total calories recorded for the activity."""
        return self.__sum_of_tag(int, './/ns:Lap/ns:Calories')

    def get_distance(self):
        """Return the total distance recorded for the activity."""
        return Distance.from_meters(self.__sum_of_tag(float, './/ns:Lap/ns:DistanceMeters'))

    def get_duration(self):
        """Return the total duration recorded for the activity."""
        return self.__sum_of_tag(float, './/ns:Lap/ns:TotalTimeSeconds')

    def get_hr_avg(self):
        """Return the average of all heart rate readings in the TCX file."""
        return sum(self.hr_values) / len(self.hr_values)

    def get_hr_max(self):
        """Return the maximum of all heart rate readings in the TCX file."""
        return max(self.hr_values)

    def get_cadence_avg(self):
        """Return the average of all cadence readings in the TCX file."""
        return self.__avg_of_tag(int, './/ns:Lap/ns:Cadence')

    def get_cadence_max(self):
        """Return the maximum of all cadence readings in the TCX file."""
        return self.__max_of_tag(int, './/ns:Lap/ns:Cadence')

    def get_speed_max(self):
        """Return the maximum of all speed readings in the TCX file."""
        return self.__max_of_tag(float, './/ns:Speed', self.__namespace('ae'))

    def get_ascent(self):
        """Return the total ascent over the activity."""
        total_ascent = 0.0
        for index in range(len(self.altitude_values) - 1):
            if self.altitude_values[index+1] > self.altitude_values[index]:
                total_ascent += self.altitude_values[index+1] - self.altitude_values[index]
        return total_ascent

    def get_descent(self):
        """Return the total descent over the activity."""
        total_descent = 0.0
        for index in range(len(self.altitude_values) - 1):
            if self.altitude_values[index+1] < self.altitude_values[index]:
                total_descent += self.altitude_values[index] - self.altitude_values[index+1]
        return total_descent

    def __str__(self):
        return str(self.root)

    def __repr__(self):
        return repr(self.root)
