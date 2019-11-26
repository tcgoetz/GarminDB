"""Objects for exporting Garmin activity data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


from Fit import Distance, Speed
import GarminDB
from tcx import Tcx


class ActivityExporter(object):
    """Export activities as TCX files from database data."""

    def __init__(self, activity_id, measurement_system, debug):
        """Return a instance of ActivityExporter ready to write a TCX file."""
        self.activity_id = activity_id
        self.measurement_system = measurement_system
        self.debug = debug

    def process(self, db_params_dict):
        """Process database data for an activity into a an XML tree in TCX format."""
        garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug - 1)
        with garmin_act_db.managed_session() as garmin_act_db_session:
            activity = GarminDB.Activities.s_get(garmin_act_db_session, self.activity_id)
            self.tcx = Tcx(activity.sport, activity.start_time)
            laps = GarminDB.ActivityLaps.s_get(garmin_act_db_session, self.activity_id)
            for lap in laps:
                distance = Distance.from_meters_or_feet(lap.distance, self.measurement_system)
                track = self.tcx.add_lap(lap.start_time, lap.stop_time, distance.to_meters(), lap.calories)
                records = GarminDB.ActivityRecords.s_get_for_period(garmin_act_db_session, lap.start_time, lap.stop_time)
                for record in records:
                    alititude = Distance.from_meters_or_feet(record.alititude, self.measurement_system)
                    speed = Speed.from_kph_or_mph(record.speed, self.measurement_system)
                    self.tcx.add_point(track, record.timestamp, record.position, alititude.to_meters(), record.hr, speed.to_mps())
        garmindb = GarminDB.GarminDB(db_params_dict)
        with garmindb.managed_session() as garmin_db_session:
            file = GarminDB.File.s_get(garmin_db_session, self.activity_id)
            device = GarminDB.Device.s_get(garmin_db_session, file.serial_number)
            self.tcx.add_creator(device.product, file.serial_number)

    def write(self, filename):
        """Write the TCX file to disk."""
        self.tcx.write(filename)
