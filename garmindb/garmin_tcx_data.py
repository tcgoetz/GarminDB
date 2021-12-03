"""Objects for importing Garmin activity data from Tcx files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
from tqdm import tqdm
import traceback

from idbutils import FileProcessor
from .tcx import Tcx

from .garmindb import GarminDb, Device, File, ActivitiesDb, Activities, ActivityRecords, ActivityLaps


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class GarminTcxData():
    """Class for importing Garmin activity data from TCX files."""

    def __init__(self, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminTcxData.

        Parameters:
        ----------
        db_params (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing activities tcx data")
        self.measurement_system = measurement_system
        self.debug = debug
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, Tcx.filename_regex, latest)

    def file_count(self):
        """Return the number of files that will be propcessed."""
        return len(self.file_names)

    def __process_record(self, tcx, activity_id, record_number, point):
        root_logger.debug("Processing record: %r (%d)", point, record_number)
        if not ActivityRecords.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'record' : record_number}):
            record = {
                'activity_id'                       : activity_id,
                'record'                            : record_number,
                'timestamp'                         : tcx.get_point_time(point),
                'hr'                                : tcx.get_point_hr(point),
                'altitude'                          : tcx.get_point_altitude(point).meters_or_feet(measurement_system=self.measurement_system),
                'speed'                             : tcx.get_point_speed(point).kph_or_mph(measurement_system=self.measurement_system)
            }
            loc = tcx.get_point_loc(point)
            if loc is not None:
                record.update({'position_lat': loc.lat_deg, 'position_long': loc.long_deg})
            self.garmin_act_db_session.add(ActivityRecords(**record))

    def __process_lap(self, tcx, activity_id, lap_number, lap):
        root_logger.info("Processing lap: %d", lap_number)
        for record_number, point in enumerate(tcx.get_lap_points(lap)):
            self.__process_record(tcx, activity_id, record_number, point)
        if not ActivityLaps.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'lap' : lap_number}):
            lap_data = {
                'activity_id'                       : activity_id,
                'lap'                               : lap_number,
                'start_time'                        : tcx.get_lap_start(lap),
                'stop_time'                         : tcx.get_lap_end(lap),
                'elapsed_time'                      : tcx.get_lap_duration(lap),
                'distance'                          : tcx.get_lap_distance(lap).meters_or_feet(measurement_system=self.measurement_system),
                'calories'                          : tcx.get_lap_calories(lap)
            }
            start_loc = tcx.get_lap_start_loc(lap)
            if start_loc is not None:
                lap_data.update({'start_lat': start_loc.lat_deg, 'start_long': start_loc.long_deg})
            end_loc = tcx.get_lap_end_loc(lap)
            if end_loc is not None:
                lap_data.update({'stop_lat': end_loc.lat_deg, 'stop_long': end_loc.long_deg})
            root_logger.info("Inserting lap: %r (%d): %r", lap, lap_number, lap_data)
            self.garmin_act_db_session.add(ActivityLaps(**lap_data))

    def __process_file(self, file_name):
        tcx = Tcx()
        tcx.read(file_name)
        start_time = tcx.start_time
        (manufacturer, product) = tcx.get_manufacturer_and_product()
        serial_number = tcx.serial_number
        device = {
            'serial_number'     : serial_number,
            'timestamp'         : start_time,
            'manufacturer'      : manufacturer,
            'product'           : product,
            'hardware_version'  : None,
        }
        Device.s_insert_or_update(self.garmin_db_session, device, ignore_none=True)
        root_logger.info("Processing file: %s for manufacturer %s product %s device %s", file_name, manufacturer, product, serial_number)
        (file_id, file_name) = File.name_and_id_from_path(file_name)
        file = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : File.FileType.tcx,
            'serial_number' : serial_number,
        }
        File.s_insert_or_update(self.garmin_db_session, file)
        activity = {
            'activity_id'               : file_id,
            'name'                      : file_id,
            'start_time'                : start_time,
            'stop_time'                 : tcx.end_time,
            'laps'                      : tcx.lap_count,
            'sport'                     : tcx.sport,
            'calories'                  : tcx.calories,
            'distance'                  : tcx.distance.kms_or_miles(self.measurement_system),
            'avg_hr'                    : tcx.hr_avg,
            'max_hr'                    : tcx.hr_max,
            'max_cadence'               : tcx.cadence_max,
            'avg_cadence'               : tcx.cadence_avg,
            'ascent'                    : tcx.ascent.meters_or_feet(self.measurement_system),
            'descent'                   : tcx.descent.meters_or_feet(self.measurement_system)
        }
        start_loc = tcx.start_loc
        if start_loc is not None:
            activity.update({'start_lat': start_loc.lat_deg, 'start_long': start_loc.long_deg})
        end_loc = tcx.end_loc
        if end_loc is not None:
            activity.update({'stop_lat': end_loc.lat_deg, 'stop_long': end_loc.long_deg})
        Activities.s_insert_or_update(self.garmin_act_db_session, activity, ignore_none=True, ignore_zero=True)
        for lap_number, lap in enumerate(tcx.laps):
            self.__process_lap(tcx, file_id, lap_number, lap)

    def process_files(self, db_params):
        """Import data from TCX files into the database."""
        garmin_db = GarminDb(db_params, self.debug - 1)
        garmin_act_db = ActivitiesDb(db_params, self.debug - 1)
        with garmin_db.managed_session() as self.garmin_db_session, garmin_act_db.managed_session() as self.garmin_act_db_session:
            for file_name in tqdm(self.file_names, unit='files'):
                try:
                    self.__process_file(file_name)
                except Exception as e:
                    logger.error('Failed to processes TCX file %s: %s', file_name, e)
                    root_logger.error('Failed to processes TCX file %s: %s', file_name, traceback.format_exc())
