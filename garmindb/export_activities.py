"""Objects for exporting Garmin activity data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os

from fitfile import Distance, Speed

from .garmindb import GarminDb, File, Device, ActivitiesDb, Activities, ActivityLaps, ActivityRecords
from .tcx import Tcx


class ActivityExporter():
    """Export activities as TCX files from database data."""

    def __init__(self, directory, activity_id, measurement_system, debug):
        """Return a instance of ActivityExporter ready to write a TCX file."""
        self.directory = directory
        self.activity_id = activity_id
        self.measurement_system = measurement_system
        self.debug = debug

    def process(self, db_params):
        """Process database data for an activity into a an XML tree in TCX format."""
        garmin_act_db = ActivitiesDb(db_params, self.debug - 1)
        with garmin_act_db.managed_session() as garmin_act_db_session:
            activity = Activities.s_get(garmin_act_db_session, self.activity_id)
            self.tcx = Tcx()
            self.tcx.create(activity.sport, activity.start_time)
            laps = ActivityLaps.s_get_activity(garmin_act_db_session, self.activity_id)
            records = ActivityRecords.s_get_activity(garmin_act_db_session, self.activity_id)
            for lap in laps:
                distance = Distance.from_meters_or_feet(lap.distance, self.measurement_system)
                track = self.tcx.add_lap(lap.start_time, lap.stop_time, distance, lap.calories)
                for record in records:
                    if record.timestamp >= lap.start_time and record.timestamp <= lap.stop_time:
                        alititude = Distance.from_meters_or_feet(record.altitude, self.measurement_system)
                        speed = Speed.from_kph_or_mph(record.speed, self.measurement_system)
                        self.tcx.add_point(track, record.timestamp, record.position, alititude, record.hr, speed)
        gdb = GarminDb(db_params)
        with gdb.managed_session() as garmin_db_session:
            file = File.s_get(garmin_db_session, self.activity_id)
            device = Device.s_get(garmin_db_session, file.serial_number)
            self.tcx.add_creator(device.product, file.serial_number)

    def write(self, filename):
        """Write the TCX file to disk."""
        full_path = self.directory + os.path.sep + filename
        self.tcx.write(full_path)
        return full_path
