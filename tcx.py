"""Objects for exporting Garmin activity data as TCX files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
import xml.etree.ElementTree as ET


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class Tcx(object):
    """Create TCX files form data."""

    def __init__(self, sport, start_dt):
        """Return and instance of the Tcx class."""
        attribs = {
            'xmlns:xsd': "http://www.w3.org/2001/XMLSchema",
            'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
            'xsi:schemaLocation': "http://www.garmin.com/xmlschemas/ActivityExtension/v2 "
                                  "http://www.garmin.com/xmlschemas/ActivityExtensionv2.xsd "
                                  "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 "
                                  "http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd",
            'xmlns': "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
        }
        self.root = ET.Element('TrainingCenterDatabase', attrib=attribs)
        activities = ET.SubElement(self.root, 'Activities')
        self.activity = ET.SubElement(activities, 'Activity', attrib={'Sport' : sport})
        ET.SubElement(self.activity, 'Id').text = start_dt.isoformat()

    def lap(self, start_dt, end_dt, distance, calories):
        """Add a lap to the TCX file data."""
        lap = ET.SubElement(self.activity, 'Lap', attrib={'StartTime': start_dt.isoformat()})
        ET.SubElement(lap, 'TotalTimeSeconds').text = str((end_dt - start_dt).total_seconds())
        if distance > 0:
            ET.SubElement(lap, 'DistanceMeters').text = str(distance)
        if calories > 0:
            ET.SubElement(lap, 'Calories').text = str(calories)
        track = ET.SubElement(lap, 'Track')
        return track

    def point(self, track, dt, location, alititude, heart_rate, speed):
        """Add a point to the lap."""
        point = ET.SubElement(track, 'Trackpoint')
        ET.SubElement(point, 'Time').text = dt.isoformat()
        if location.lat_deg is not None and location.long_deg is not None:
            position = ET.SubElement(point, 'Position')
            ET.SubElement(position, 'LatitudeDegrees').text = str(location.lat_deg)
            ET.SubElement(position, 'LongitudeDegrees').text = str(location.long_deg)
        if alititude is not None:
            ET.SubElement(point, 'AltitudeMeters').text = str(alititude)
        hr = ET.SubElement(point, 'HeartRateBpm')
        ET.SubElement(hr, 'Value').text = str(heart_rate)
        if speed is not None:
            extensions = ET.SubElement(point, 'Extensions')
            attrib = {'xmlns': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'}
            ate = ET.SubElement(extensions, 'ActivityTrackpointExtension', atrib=attrib)
            ET.SubElement(ate, 'Speed').text = str(speed)
        return point

    def write(self, filename):
        """Write the TCX XML data to a file."""
        tree = ET.ElementTree(self.root)
        tree.write(filename, encoding='UTF-8', xml_declaration=True)
