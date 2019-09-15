"""Objects for importing Garmin activity data from Garmin Connect downloads and FIT files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import os
import sys
import logging
import progressbar
import dateutil.parser

import Fit
import GarminDB
from file_processor import FileProcessor
from fit_file_processor import FitFileProcessor
from json_file_processor import JsonFileProcessor
import garmin_connect_enums as GarminConnectEnums
import tcx_file


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class GarminActivitiesFitData(object):
    """Class for importing Garmin activity data from FIT files."""

    def __init__(self, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminActivitiesFitData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing activities FIT data")
        self.measurement_system = measurement_system
        self.debug = debug
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, Fit.file.name_regex, latest)

    def file_count(self):
        """Return the number of files that will be propcessed."""
        return len(self.file_names)

    def process_files(self, db_params_dict):
        """Process files into the database."""
        fp = FitFileProcessor(db_params_dict, self.debug)
        for file_name in progressbar.progressbar(self.file_names):
            try:
                fp.write_file(Fit.file.File(file_name, self.measurement_system))
            except Exception as e:
                logger.error("Failed to parse %s: %s", file_name, e)
                raise


class GarminTcxData(object):
    """Class for importing Garmin activity data from TCX files."""

    tcx_filename_regex = r'.*\.tcx'

    def __init__(self, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminTcxData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.debug("Processing activities tcx data")
        self.measurement_system = measurement_system
        self.debug = debug
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, self.tcx_filename_regex, latest)

    def file_count(self):
        """Return the number of files that will be propcessed."""
        return len(self.file_names)

    def __process_file(self, file_name):
        root_logger.info("Processing file: " + file_name)
        tcx = tcx_file.TcxFile(file_name)
        end_time = tcx.get_date('completed_at')
        start_time = tcx.get_date('started_at')
        (manufacturer, product) = tcx.get_manufacturer_and_product()
        serial_number = tcx.get_value('creator_version')
        serial_number = tcx.get_serial_number()
        device = {
            'serial_number'     : serial_number,
            'timestamp'         : start_time,
            'manufacturer'      : manufacturer,
            'product'           : product,
            'hardware_version'  : None,
        }
        GarminDB.Device.s_create_or_update(self.garmin_db_session, device, ignore_none=True)
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(file_name)
        file = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : GarminDB.File.FileType.tcx,
            'serial_number' : serial_number,
        }
        GarminDB.File.s_find_or_create(self.garmin_db_session, file)
        distance = Fit.measurement.Distance.from_meters(tcx.get_value('distance'))
        activity = {
            'activity_id'               : file_id,
            'start_time'                : start_time,
            'stop_time'                 : end_time,
            'laps'                      : tcx.get_lap_count(),
            'sport'                     : tcx.get_sport(),
            'calories'                  : tcx.get_value('calories'),
            'start_lat'                 : tcx.get_value('start_latitude'),
            'start_long'                : tcx.get_value('start_longitude'),
            'stop_lat'                  : tcx.get_value('end_latitude'),
            'stop_long'                 : tcx.get_value('end_longitude'),
            'distance'                  : distance.kms_or_miles(self.measurement_system),
            'avg_hr'                    : tcx.get_value('hr_avg'),
            'max_hr'                    : tcx.get_value('hr_max'),
            'max_cadence'               : tcx.get_value('cadence_max'),
            'avg_cadence'               : tcx.get_value('cadence_avg'),
            # 'ascent'                    : ascent.meters_or_feet(self.measurement_system),
            # 'descent'                   : descent.meters_or_feet(self.measurement_system)
        }
        activity_not_zero = {key : value for (key, value) in activity.iteritems() if value}
        GarminDB.Activities.s_create_or_update(self.garmin_act_db_session, activity_not_zero, ignore_none=True)

    def process_files(self, db_params_dict):
        """Import data from TCX files into the database."""
        garmin_db = GarminDB.GarminDB(db_params_dict, self.debug - 1)
        garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug - 1)
        with garmin_db.managed_session() as self.garmin_db_session:
            with garmin_act_db.managed_session() as self.garmin_act_db_session:
                for file_name in progressbar.progressbar(self.file_names):
                    self.__process_file(file_name)
                    self.garmin_db_session.commit()
                    self.garmin_act_db_session.commit()


class GarminJsonSummaryData(JsonFileProcessor):
    """Class for importing Garmin activity data from JSON formatted Garmin Connect summary downloads."""

    def __init__(self, db_params_dict, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminTcxData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing %s activities summary data from %s", 'latest' if latest else 'all', input_dir)
        super(GarminJsonSummaryData, self).__init__(None, input_dir, r'activity_\d*\.json', latest, debug)
        self.input_dir = input_dir
        self.measurement_system = measurement_system
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug - 1)
        self.conversions = {}

    def _commit(self):
        self.garmin_act_db_session.commit()

    def _process_steps_activity(self, activity_id, activity_summary):
        root_logger.debug("process_steps_activity for %s", activity_id)
        avg_vertical_oscillation = self._get_field_obj(activity_summary, 'avgVerticalOscillation', Fit.Distance.from_meters)
        avg_step_length = self._get_field_obj(activity_summary, 'avgStrideLength', Fit.Distance.from_meters)
        run = {
            'activity_id'               : activity_id,
            'steps'                     : self._get_field(activity_summary, 'steps', float),
            'avg_steps_per_min'         : self._get_field(activity_summary, 'averageRunningCadenceInStepsPerMinute', float),
            'max_steps_per_min'         : self._get_field(activity_summary, 'maxRunningCadenceInStepsPerMinute', float),
            'avg_step_length'           : avg_step_length.meters_or_feet(self.measurement_system),
            'avg_gct_balance'           : self._get_field(activity_summary, 'avgGroundContactBalance', float),
            'avg_vertical_oscillation'  : avg_vertical_oscillation.meters_or_feet(self.measurement_system),
            'avg_ground_contact_time'   : Fit.conversions.ms_to_dt_time(self._get_field(activity_summary, 'avgGroundContactTime', float)),
            'vo2_max'                   : self._get_field(activity_summary, 'vO2MaxValue', float),
        }
        GarminDB.StepsActivities.s_create_or_update(self.garmin_act_db_session, run, ignore_none=True)

    def _process_running(self, activity_id, activity_summary):
        root_logger.debug("process_running for %s", activity_id)
        self._process_steps_activity(activity_id, activity_summary)

    def _process_treadmill_running(self, activity_id, activity_summary):
        root_logger.debug("process_treadmill_running for %s", activity_id)
        self._process_steps_activity(activity_id, activity_summary)

    def _process_walking(self, activity_id, activity_summary):
        root_logger.debug("process_walking for %s", activity_id)
        self._process_steps_activity(activity_id, activity_summary)

    def _process_hiking(self, activity_id, activity_summary):
        root_logger.debug("process_hiking for %s", activity_id)
        self._process_steps_activity(activity_id, activity_summary)

    def _process_paddling(self, activity_id, activity_summary):
        activity = {
            'activity_id'               : activity_id,
            'avg_cadence'               : self._get_field(activity_summary, 'avgStrokeCadence', float),
            'max_cadence'               : self._get_field(activity_summary, 'maxStrokeCadence', float),
        }
        GarminDB.Activities.s_create_or_update(self.garmin_act_db_session, activity, ignore_none=True)
        avg_stroke_distance = Fit.Distance.from_meters(self._get_field(activity_summary, 'avgStrokeDistance', float))
        paddle = {
            'activity_id'               : activity_id,
            'strokes'                   : self._get_field(activity_summary, 'strokes', float),
            'avg_stroke_distance'       : avg_stroke_distance.meters_or_feet(self.measurement_system),
        }
        GarminDB.PaddleActivities.s_create_or_update(self.garmin_act_db_session, paddle, ignore_none=True)

    def _process_cycling(self, activity_id, activity_summary):
        activity = {
            'activity_id'               : activity_id,
            'avg_cadence'               : self._get_field(activity_summary, 'averageBikingCadenceInRevPerMinute', float),
            'max_cadence'               : self._get_field(activity_summary, 'maxBikingCadenceInRevPerMinute', float),
        }
        GarminDB.Activities.s_create_or_update(self.garmin_act_db_session, activity, ignore_none=True)
        ride = {
            'activity_id'               : activity_id,
            'strokes'                   : self._get_field(activity_summary, 'strokes', float),
            'vo2_max'                   : self._get_field(activity_summary, 'vO2MaxValue', float),
        }
        GarminDB.CycleActivities.s_create_or_update(self.garmin_act_db_session, ride, ignore_none=True)

    def _process_mountain_biking(self, activity_id, activity_summary):
        return self._process_cycling(activity_id, activity_summary)

    def _process_elliptical(self, activity_id, activity_summary):
        if activity_summary is not None:
            activity = {
                'activity_id'               : activity_id,
                'avg_cadence'               : self._get_field(activity_summary, 'averageRunningCadenceInStepsPerMinute', float),
                'max_cadence'               : self._get_field(activity_summary, 'maxRunningCadenceInStepsPerMinute', float),
            }
            GarminDB.Activities.s_create_or_update(self.garmin_act_db_session, activity, ignore_none=True)
            workout = {
                'activity_id'               : activity_id,
                'steps'                     : self._get_field(activity_summary, 'steps', float),
            }
            GarminDB.EllipticalActivities.s_create_or_update(self.garmin_act_db_session, workout, ignore_none=True)

    def _process_json(self, json_data):
        activity_id = json_data['activityId']
        description_str = self._get_field(json_data, 'description')
        (description, extra_data) = GarminDB.ActivitiesExtraData.from_string(description_str)
        distance = self._get_field_obj(json_data, 'distance', Fit.Distance.from_meters)
        ascent = self._get_field_obj(json_data, 'elevationGain', Fit.Distance.from_meters)
        descent = self._get_field_obj(json_data, 'elevationLoss', Fit.Distance.from_meters)
        avg_speed = self._get_field_obj(json_data, 'averageSpeed', Fit.Speed.from_mps)
        max_speed = self._get_field_obj(json_data, 'maxSpeed', Fit.Speed.from_mps)
        max_temperature = self._get_field_obj(json_data, 'maxTemperature', Fit.Temperature.from_celsius)
        min_temperature = self._get_field_obj(json_data, 'minTemperature', Fit.Temperature.from_celsius)
        event = GarminConnectEnums.Event.from_json(json_data)
        sport = GarminConnectEnums.Sport.from_json(json_data)
        sub_sport = GarminConnectEnums.Sport.subsport_from_json(json_data)
        if sport is GarminConnectEnums.Sport.top_level or sport is GarminConnectEnums.Sport.other:
            sport = sub_sport
        activity = {
            'activity_id'               : activity_id,
            'name'                      : json_data['activityName'],
            'description'               : description,
            'type'                      : event.name,
            'sport'                     : sport.name,
            'sub_sport'                 : sub_sport.name,
            'start_time'                : dateutil.parser.parse(self._get_field(json_data, 'startTimeLocal'), ignoretz=True),
            'elapsed_time'              : Fit.conversions.secs_to_dt_time(self._get_field(json_data, 'elapsedDuration', int)),
            'moving_time'               : Fit.conversions.secs_to_dt_time(self._get_field(json_data, 'movingDuration', int)),
            'start_lat'                 : self._get_field(json_data, 'startLatitude', float),
            'start_long'                : self._get_field(json_data, 'startLongitude', float),
            'stop_lat'                  : self._get_field(json_data, 'endLatitude', float),
            'stop_long'                 : self._get_field(json_data, 'endLongitude', float),
            'distance'                  : distance.kms_or_miles(self.measurement_system),
            'laps'                      : self._get_field(json_data, 'lapCount'),
            'avg_hr'                    : self._get_field(json_data, 'averageHR', float),
            'max_hr'                    : self._get_field(json_data, 'maxHR', float),
            'calories'                  : self._get_field(json_data, 'calories', float),
            'avg_speed'                 : avg_speed.kph_or_mph(self.measurement_system),
            'max_speed'                 : max_speed.kph_or_mph(self.measurement_system),
            'ascent'                    : ascent.meters_or_feet(self.measurement_system),
            'descent'                   : descent.meters_or_feet(self.measurement_system),
            'max_temperature'           : max_temperature.c_or_f(self.measurement_system),
            'min_temperature'           : min_temperature.c_or_f(self.measurement_system),
            'training_effect'           : self._get_field(json_data, 'aerobicTrainingEffect', float),
            'anaerobic_training_effect' : self._get_field(json_data, 'anaerobicTrainingEffect', float),
        }
        GarminDB.Activities.s_create_or_update(self.garmin_act_db_session, activity, ignore_none=True)
        if extra_data:
            extra_data['activity_id'] = activity_id
            json_filename = '%s/extra_data_%s.json' % (self.input_dir, activity_id)
            if not os.path.isfile(json_filename):
                self._save_json_file(json_filename, extra_data)
        self.call_process_func(sub_sport.name, activity_id, json_data)
        return 1

    def process(self):
        """Import data from files into the databse."""
        with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self._process_files()


class GarminJsonDetailsData(JsonFileProcessor):
    """Class for importing Garmin activity data from JSON formatted Garmin Connect details downloads."""

    def __init__(self, db_params_dict, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminJsonDetailsData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing activities detail data")
        super(GarminJsonDetailsData, self).__init__(None, input_dir, r'activity_details_\d*\.json', latest, debug)
        self.measurement_system = measurement_system
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug - 1)
        self.conversions = {}

    def _commit(self):
        self.garmin_act_db_session.commit()

    def _process_steps_activity(self, activity_id, json_data):
        summary_dto = json_data['summaryDTO']
        avg_moving_speed_mps = summary_dto.get('averageMovingSpeed')
        avg_moving_speed = Fit.conversions.mps_to_mph(avg_moving_speed_mps)
        run = {
            'activity_id'               : activity_id,
            'avg_moving_pace'           : Fit.conversions.speed_to_pace(avg_moving_speed),
        }
        root_logger.debug("process_steps_activity for %d: %r", activity_id, run)
        GarminDB.StepsActivities.s_create_or_update(self.garmin_act_db_session, run, ignore_none=True)

    def _process_running(self, activity_id, json_data):
        root_logger.debug("process_running for %d: %r", activity_id, json_data)
        self._process_steps_activity(activity_id, json_data)

    def _process_walking(self, activity_id, json_data):
        root_logger.debug("process_walking for %d: %r", activity_id, json_data)
        self._process_steps_activity(activity_id, json_data)

    def _process_hiking(self, activity_id, json_data):
        root_logger.debug("process_hiking for %d: %r", activity_id, json_data)
        self._process_steps_activity(activity_id, json_data)

    def _process_json(self, json_data):
        activity_id = json_data['activityId']
        metadata_dto = json_data['metadataDTO']
        summary_dto = json_data['summaryDTO']
        sport = GarminConnectEnums.Sport.from_details_json(json_data)
        sub_sport = GarminConnectEnums.Sport.subsport_from_details_json(json_data)
        if sport is GarminConnectEnums.Sport.top_level or sport is GarminConnectEnums.Sport.other:
            sport = sub_sport
        avg_temperature = self._get_field_obj(summary_dto, 'averageTemperature', Fit.Temperature.from_celsius)
        activity = {
            'activity_id'               : activity_id,
            'course_id'                 : self._get_field(metadata_dto, 'associatedCourseId', int),
            'avg_temperature'           : avg_temperature.c_or_f(self.measurement_system) if avg_temperature is not None else None,
        }
        GarminDB.Activities.s_create_or_update(self.garmin_act_db_session, activity, ignore_none=True)
        self.call_process_func(sub_sport.name, activity_id, json_data)
        return 1

    def process(self):
        """Import data from files into the databse."""
        with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self._process_files()


class GarminActivitiesExtraData(JsonFileProcessor):
    """Class that manages extra JSON data stored in string fields."""

    def __init__(self, db_params_dict, input_dir, latest, debug):
        """
        Return an instance of GarminActivitiesExtraData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing activities extra data")
        super(GarminActivitiesExtraData, self).__init__(None, input_dir, r'extra_data_\d*\.json', latest, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)

    def _process_json(self, json_data):
        root_logger.info("Extra data: %r", json_data)
        GarminDB.ActivitiesExtraData.create_or_update(self.garmin_db, GarminDB.DailyExtraData.convert_eums(json_data), ignore_none=True)
        return 1
