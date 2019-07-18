"""Objects for importing Garmin activity data from Garmin Connect downloads and FIT files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import os
import sys
import re
import logging
import tcxparser
import dateutil.parser
import progressbar

import Fit
from FileProcessor import FileProcessor
from FitFileProcessor import FitFileProcessor
from JsonFileProcessor import JsonFileProcessor
import GarminDB
import GarminConnectEnums


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class GarminActivitiesFitData(object):
    """Class for importing Garmin activity data from FIT files."""

    def __init__(self, input_file, input_dir, latest, measurement_system, debug):
        logger.info("Processing activities FIT data")
        self.measurement_system = measurement_system
        self.debug = debug
        if input_file:
            self.file_names = FileProcessor.match_file(input_file, Fit.file.name_regex)
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, Fit.file.name_regex, latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
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

    def __init__(self, input_file, input_dir, latest, measurement_system, debug):
        logger.debug("Processing activities tcx data")
        self.measurement_system = measurement_system
        self.debug = debug
        if input_file:
            self.file_names = FileProcessor.match_file(input_file, self.tcx_filename_regex)
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, self.tcx_filename_regex, latest)

    def file_count(self):
        return len(self.file_names)

    def process_file(self, file_name):
        root_logger.info("Processing file: " + file_name)
        tcx = tcxparser.TCXParser(file_name)
        end_time = dateutil.parser.parse(tcx.completed_at, ignoretz=True)
        start_time = dateutil.parser.parse(tcx.started_at, ignoretz=True)
        manufacturer = GarminDB.Device.Manufacturer.Unknown
        product = tcx.creator
        if product is not None:
            match = re.search('Microsoft', product)
            if match:
                manufacturer = GarminDB.Device.Manufacturer.Microsoft
        serial_number = tcx.creator_version
        if serial_number is None or serial_number == 0:
            serial_number = GarminDB.Device.unknown_device_serial_number
        device = {
            'serial_number'     : serial_number,
            'timestamp'         : start_time,
            'manufacturer'      : manufacturer,
            'product'           : product,
            'hardware_version'  : None,
        }
        GarminDB.Device._create_or_update_not_none(self.garmin_db_session, device)
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(file_name)
        file = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : GarminDB.File.FileType.tcx,
            'serial_number' : serial_number,
        }
        GarminDB.File._find_or_create(self.garmin_db_session, file)
        distance = Fit.measurement.Distance.from_meters(tcx.distance)
        # ascent = Fit.Distance.from_meters(tcx.ascent)
        # descent = Fit.Distance.from_meters(tcx.descent)
        activity = {
            'activity_id'               : file_id,
            'start_time'                : start_time,
            'stop_time'                 : end_time,
            'laps'                      : len(tcx.activity.Lap),
            # 'sport'                     : tcx.activity_type,
            'calories'                  : tcx.calories,
            'start_lat'                 : tcx.start_latitude,
            'start_long'                : tcx.start_longitude,
            'stop_lat'                  : tcx.end_latitude,
            'stop_long'                 : tcx.end_longitude,
            'distance'                  : distance.kms_or_miles(self.measurement_system),
            'avg_hr'                    : tcx.hr_avg,
            'max_hr'                    : tcx.hr_max,
            'max_cadence'               : tcx.cadence_max,
            'avg_cadence'               : tcx.cadence_avg,
            # 'ascent'                    : ascent.meters_or_feet(self.measurement_system),
            # 'descent'                   : descent.meters_or_feet(self.measurement_system)
        }
        activity_not_zero = {key : value for (key, value) in activity.iteritems() if value}
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity_not_zero)

    def process_files(self, db_params_dict):
        garmin_db = GarminDB.GarminDB(db_params_dict, self.debug - 1)
        garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug)
        with garmin_db.managed_session() as self.garmin_db_session:
            with garmin_act_db.managed_session() as self.garmin_act_db_session:
                for file_name in progressbar.progressbar(self.file_names):
                    self.process_file(file_name)
                    self.garmin_db_session.commit()
                    self.garmin_act_db_session.commit()


class GarminJsonSummaryData(JsonFileProcessor):
    """Class for importing Garmin activity data from JSON formatted Garmin Connect summary downloads."""

    def __init__(self, db_params_dict, input_file, input_dir, latest, measurement_system, debug):
        logger.info("Processing %s activities summary data from %s", 'latest' if latest else 'all', input_dir)
        super(GarminJsonSummaryData, self).__init__(input_file, input_dir, r'activity_\d*\.json', latest, debug)
        self.measurement_system = measurement_system
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug - 1)
        self.conversions = {}

    def commit(self):
        self.garmin_act_db_session.commit()

    def process_steps_activity(self, activity_id, activity_summary):
        root_logger.debug("process_steps_activity for %s", activity_id)
        avg_vertical_oscillation = self.get_field_obj(activity_summary, 'avgVerticalOscillation', Fit.Distance.from_meters)
        avg_step_length = self.get_field_obj(activity_summary, 'avgStrideLength', Fit.Distance.from_meters)
        run = {
            'activity_id'               : activity_id,
            'steps'                     : self.get_field(activity_summary, 'steps', float),
            'avg_steps_per_min'         : self.get_field(activity_summary, 'averageRunningCadenceInStepsPerMinute', float),
            'max_steps_per_min'         : self.get_field(activity_summary, 'maxRunningCadenceInStepsPerMinute', float),
            'avg_step_length'           : avg_step_length.meters_or_feet(self.measurement_system),
            'avg_gct_balance'           : self.get_field(activity_summary, 'avgGroundContactBalance', float),
            'avg_vertical_oscillation'  : avg_vertical_oscillation.meters_or_feet(self.measurement_system),
            'avg_ground_contact_time'   : Fit.conversions.ms_to_dt_time(self.get_field(activity_summary, 'avgGroundContactTime', float)),
            'vo2_max'                   : self.get_field(activity_summary, 'vO2MaxValue', float),
        }
        GarminDB.StepsActivities._create_or_update_not_none(self.garmin_act_db_session, run)

    def process_running(self, activity_id, activity_summary):
        root_logger.debug("process_running for %s", activity_id)
        self.process_steps_activity(activity_id, activity_summary)

    def process_treadmill_running(self, activity_id, activity_summary):
        root_logger.debug("process_treadmill_running for %s", activity_id)
        self.process_steps_activity(activity_id, activity_summary)

    def process_walking(self, activity_id, activity_summary):
        root_logger.debug("process_walking for %s", activity_id)
        self.process_steps_activity(activity_id, activity_summary)

    def process_hiking(self, activity_id, activity_summary):
        root_logger.debug("process_hiking for %s", activity_id)
        self.process_steps_activity(activity_id, activity_summary)

    def process_paddling(self, activity_id, activity_summary):
        activity = {
            'activity_id'               : activity_id,
            'avg_cadence'               : self.get_field(activity_summary, 'avgStrokeCadence', float),
            'max_cadence'               : self.get_field(activity_summary, 'maxStrokeCadence', float),
        }
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity)
        avg_stroke_distance = Fit.Distance.from_meters(self.get_field(activity_summary, 'avgStrokeDistance', float))
        paddle = {
            'activity_id'               : activity_id,
            'strokes'                   : self.get_field(activity_summary, 'strokes', float),
            'avg_stroke_distance'       : avg_stroke_distance.meters_or_feet(self.measurement_system),
        }
        GarminDB.PaddleActivities._create_or_update_not_none(self.garmin_act_db_session, paddle)

    def process_cycling(self, activity_id, activity_summary):
        activity = {
            'activity_id'               : activity_id,
            'avg_cadence'               : self.get_field(activity_summary, 'averageBikingCadenceInRevPerMinute', float),
            'max_cadence'               : self.get_field(activity_summary, 'maxBikingCadenceInRevPerMinute', float),
        }
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db, activity)
        ride = {
            'activity_id'               : activity_id,
            'strokes'                   : self.get_field(activity_summary, 'strokes', float),
            'vo2_max'                   : self.get_field(activity_summary, 'vO2MaxValue', float),
        }
        GarminDB.CycleActivities._create_or_update_not_none(self.garmin_act_db_session, ride)

    def process_mountain_biking(self, activity_id, activity_summary):
        return self.process_cycling(activity_id, activity_summary)

    def process_elliptical(self, activity_id, activity_summary):
        if activity_summary is not None:
            activity = {
                'activity_id'               : activity_id,
                'avg_cadence'               : self.get_field(activity_summary, 'averageRunningCadenceInStepsPerMinute', float),
                'max_cadence'               : self.get_field(activity_summary, 'maxRunningCadenceInStepsPerMinute', float),
            }
            GarminDB.Activities._create_or_update_not_none(self.garmin_act_db, activity)
            workout = {
                'activity_id'               : activity_id,
                'steps'                     : self.get_field(activity_summary, 'steps', float),
            }
            GarminDB.EllipticalActivities._create_or_update_not_none(self.garmin_act_db_session, workout)

    def process_json(self, json_data):
        activity_id = json_data['activityId']
        description_str = self.get_field(json_data, 'description')
        (description, extra_data) = GarminDB.ActivitiesExtraData.from_string(description_str)
        distance = self.get_field_obj(json_data, 'distance', Fit.Distance.from_meters)
        ascent = self.get_field_obj(json_data, 'elevationGain', Fit.Distance.from_meters)
        descent = self.get_field_obj(json_data, 'elevationLoss', Fit.Distance.from_meters)
        avg_speed = self.get_field_obj(json_data, 'averageSpeed', Fit.Speed.from_mps)
        max_speed = self.get_field_obj(json_data, 'maxSpeed', Fit.Speed.from_mps)
        max_temperature = self.get_field_obj(json_data, 'maxTemperature', Fit.Temperature.from_celsius)
        min_temperature = self.get_field_obj(json_data, 'minTemperature', Fit.Temperature.from_celsius)
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
            'start_time'                : dateutil.parser.parse(self.get_field(json_data, 'startTimeLocal'), ignoretz=True),
            'elapsed_time'              : Fit.conversions.secs_to_dt_time(self.get_field(json_data, 'elapsedDuration', int)),
            'moving_time'               : Fit.conversions.secs_to_dt_time(self.get_field(json_data, 'movingDuration', int)),
            'start_lat'                 : self.get_field(json_data, 'startLatitude', float),
            'start_long'                : self.get_field(json_data, 'startLongitude', float),
            'stop_lat'                  : self.get_field(json_data, 'endLatitude', float),
            'stop_long'                 : self.get_field(json_data, 'endLongitude', float),
            'distance'                  : distance.kms_or_miles(self.measurement_system),
            'laps'                      : self.get_field(json_data, 'lapCount'),
            'avg_hr'                    : self.get_field(json_data, 'averageHR', float),
            'max_hr'                    : self.get_field(json_data, 'maxHR', float),
            'calories'                  : self.get_field(json_data, 'calories', float),
            'avg_speed'                 : avg_speed.kph_or_mph(self.measurement_system),
            'max_speed'                 : max_speed.kph_or_mph(self.measurement_system),
            'ascent'                    : ascent.meters_or_feet(self.measurement_system),
            'descent'                   : descent.meters_or_feet(self.measurement_system),
            'max_temperature'           : max_temperature.c_or_f(self.measurement_system),
            'min_temperature'           : min_temperature.c_or_f(self.measurement_system),
            'training_effect'           : self.get_field(json_data, 'aerobicTrainingEffect', float),
            'anaerobic_training_effect' : self.get_field(json_data, 'anaerobicTrainingEffect', float),
        }
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity)
        if extra_data:
            extra_data['activity_id'] = activity_id
            json_filename = self.input_dir + '/extra_data_' + activity_id + '.json'
            if not os.path.isfile(json_filename):
                self.save_json_file(json_filename, extra_data)
        try:
            process_function = 'process_' + sub_sport.name
            function = getattr(self, process_function)
            function(activity_id, json_data)
        except AttributeError:
            root_logger.info("No sport handler %s from %s", process_function, activity_id)
        return 1

    def process(self):
        with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self.process_files()


class GarminJsonDetailsData(JsonFileProcessor):
    """Class for importing Garmin activity data from JSON formatted Garmin Connect details downloads."""

    def __init__(self, db_params_dict, input_file, input_dir, latest, measurement_system, debug):
        logger.info("Processing activities detail data")
        super(GarminJsonDetailsData, self).__init__(input_file, input_dir, r'activity_details_\d*\.json', latest, debug)
        self.measurement_system = measurement_system
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug - 1)
        self.conversions = {}

    def commit(self):
        self.garmin_act_db_session.commit()

    def process_steps_activity(self, activity_id, json_data):
        summary_dto = json_data['summaryDTO']
        avg_moving_speed_mps = summary_dto.get('averageMovingSpeed')
        avg_moving_speed = Fit.conversions.mps_to_mph(avg_moving_speed_mps)
        run = {
            'activity_id'               : activity_id,
            'avg_moving_pace'           : Fit.conversions.speed_to_pace(avg_moving_speed),
        }
        root_logger.info("process_steps_activity for %d: %r", activity_id, run)
        GarminDB.StepsActivities._create_or_update_not_none(self.garmin_act_db_session, run)

    def process_running(self, activity_id, json_data):
        root_logger.info("process_running for %d: %r", activity_id, json_data)
        self.process_steps_activity(activity_id, json_data)

    def process_walking(self, activity_id, json_data):
        root_logger.info("process_walking for %d: %r", activity_id, json_data)
        self.process_steps_activity(activity_id, json_data)

    def process_hiking(self, activity_id, json_data):
        root_logger.info("process_hiking for %d: %r", activity_id, json_data)
        self.process_steps_activity(activity_id, json_data)

    def process_json(self, json_data):
        activity_id = json_data['activityId']
        metadata_dto = json_data['metadataDTO']
        summary_dto = json_data['summaryDTO']
        sport = GarminConnectEnums.Sport.from_details_json(json_data)
        sub_sport = GarminConnectEnums.Sport.subsport_from_details_json(json_data)
        if sport is GarminConnectEnums.Sport.top_level or sport is GarminConnectEnums.Sport.other:
            sport = sub_sport
        avg_temperature = self.get_field_obj(summary_dto, 'averageTemperature', Fit.Temperature.from_celsius)
        activity = {
            'activity_id'               : activity_id,
            'course_id'                 : self.get_field(metadata_dto, 'associatedCourseId', int),
            'avg_temperature'           : avg_temperature.c_or_f(self.measurement_system) if avg_temperature is not None else None,
        }
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity)
        try:
            process_function = 'process_' + sub_sport.name
            function = getattr(self, process_function)
            function(activity_id, json_data)
        except AttributeError:
            root_logger.info("No sport handler %s from %s", process_function, activity_id)
        return 1

    def process(self):
        with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self.process_files()


class GarminActivitiesExtraData(JsonFileProcessor):

    def __init__(self, db_params_dict, input_file, input_dir, latest, debug):
        logger.info("Processing activities extra data")
        super(GarminActivitiesExtraData, self).__init__(input_file, input_dir, r'extra_data_\d*\.json', latest, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)

    def process_json(self, json_data):
        root_logger.info("Extra data: %r", json_data)
        GarminDB.ActivitiesExtraData.create_or_update_not_none(self.garmin_db, GarminDB.DailyExtraData.convert_eums(json_data))
        return 1
