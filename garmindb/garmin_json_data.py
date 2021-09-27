"""Objects for importing Garmin activity data from Garmin Connect downloads and FIT files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
import dateutil.parser

import fitfile
from idbutils import JsonFileProcessor

from .garmin_connect_enums import Event, get_summary_sport, get_details_sport
from .garmindb import ActivitiesDb, Activities, StepsActivities, PaddleActivities, CycleActivities


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class GarminJsonActivityData(JsonFileProcessor):
    """Base class for importing Garmin activity data from JSON formatted Garmin Connect details downloads."""

    def __init__(self, db_params, file_regex, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminJsonDetailsData.

        Parameters:
        ----------
        db_params (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        super().__init__(file_regex, input_dir=input_dir, latest=latest, debug=debug)
        self.measurement_system = measurement_system
        self.garmin_act_db = ActivitiesDb(db_params, self.debug - 1)
        self.conversions = {}

    def _process_common(self, json_data):
        distance = self._get_field_obj(json_data, 'distance', fitfile.Distance.from_meters)
        ascent = self._get_field_obj(json_data, 'elevationGain', fitfile.Distance.from_meters)
        descent = self._get_field_obj(json_data, 'elevationLoss', fitfile.Distance.from_meters)
        avg_speed = self._get_field_obj(json_data, 'averageSpeed', fitfile.Speed.from_mps)
        max_speed = self._get_field_obj(json_data, 'maxSpeed', fitfile.Speed.from_mps)
        max_temperature = self._get_field_obj(json_data, 'maxTemperature', fitfile.Temperature.from_celsius)
        min_temperature = self._get_field_obj(json_data, 'minTemperature', fitfile.Temperature.from_celsius)
        avg_temperature = self._get_field_obj(json_data, 'averageTemperature', fitfile.Temperature.from_celsius)
        start_time = dateutil.parser.parse(self._get_field(json_data, 'startTimeLocal'), ignoretz=True)
        elapsed_time = fitfile.conversions.secs_to_dt_time(self._get_field(json_data, 'elapsedDuration', int))
        return {
            'start_time'                : start_time,
            'stop_time'                 : start_time + fitfile.conversions.time_to_timedelta(elapsed_time),
            'elapsed_time'              : elapsed_time,
            'moving_time'               : fitfile.conversions.secs_to_dt_time(self._get_field(json_data, 'movingDuration', int)),
            'start_lat'                 : self._get_field(json_data, 'startLatitude', float),
            'start_long'                : self._get_field(json_data, 'startLongitude', float),
            'stop_lat'                  : self._get_field(json_data, 'endLatitude', float),
            'stop_long'                 : self._get_field(json_data, 'endLongitude', float),
            'distance'                  : distance.kms_or_miles(self.measurement_system),
            'laps'                      : self._get_field(json_data, 'lapCount'),
            'avg_hr'                    : self._get_field(json_data, 'averageHR', float),
            'max_hr'                    : self._get_field(json_data, 'maxHR', float),
            'calories'                  : self._get_field(json_data, 'calories', float),
            'avg_speed'                 : avg_speed.kph_or_mph(self.measurement_system) if avg_speed is not None else None,
            'max_speed'                 : max_speed.kph_or_mph(self.measurement_system) if max_speed is not None else None,
            'ascent'                    : ascent.meters_or_feet(self.measurement_system) if ascent is not None else None,
            'descent'                   : descent.meters_or_feet(self.measurement_system) if descent is not None else None,
            'max_temperature'           : max_temperature.c_or_f(self.measurement_system) if max_temperature is not None else None,
            'min_temperature'           : min_temperature.c_or_f(self.measurement_system) if min_temperature is not None else None,
            'avg_temperature'           : avg_temperature.c_or_f(self.measurement_system) if avg_temperature is not None else None,
            'training_effect'           : self._get_field(json_data, 'aerobicTrainingEffect', float),
            'anaerobic_training_effect' : self._get_field(json_data, 'anaerobicTrainingEffect', float),
            'max_rr'                    : self._get_field(json_data, 'maxRespirationRate', float),
            'avg_rr'                    : self._get_field(json_data, 'avgRespirationRate', float),
        }

    def _process_json(self, json_data):
        """Import data from files into the database."""
        with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            return self._activities_process_json(json_data)


class GarminJsonSummaryData(GarminJsonActivityData):
    """Class for importing Garmin activity data from JSON formatted Garmin Connect summary downloads."""

    def __init__(self, db_params, input_dir, latest, measurement_system, debug):
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
        logger.info("Processing %s activities summary data from %s", 'latest' if latest else 'all', input_dir)
        super().__init__(db_params, r'activity_\d*\.json', input_dir, latest, measurement_system, debug)

    def _process_steps_activity(self, activity_id, activity_summary):
        root_logger.debug("process_steps_activity for %s", activity_id)
        avg_vertical_oscillation = self._get_field_obj(activity_summary, 'avgVerticalOscillation', fitfile.Distance.from_meters)
        avg_step_length = self._get_field_obj(activity_summary, 'avgStrideLength', fitfile.Distance.from_meters)
        run = {
            'activity_id'               : activity_id,
            'steps'                     : self._get_field(activity_summary, 'steps', float),
            'avg_steps_per_min'         : self._get_field(activity_summary, 'averageRunningCadenceInStepsPerMinute', float),
            'max_steps_per_min'         : self._get_field(activity_summary, 'maxRunningCadenceInStepsPerMinute', float),
            'avg_step_length'           : avg_step_length.meters_or_feet(self.measurement_system),
            'avg_gct_balance'           : self._get_field(activity_summary, 'avgGroundContactBalance', float),
            'avg_vertical_oscillation'  : avg_vertical_oscillation.meters_or_feet(self.measurement_system),
            'avg_ground_contact_time'   : fitfile.conversions.ms_to_dt_time(self._get_field(activity_summary, 'avgGroundContactTime', float)),
            'vo2_max'                   : self._get_field(activity_summary, 'vO2MaxValue', float),
        }
        StepsActivities.s_insert_or_update(self.garmin_act_db_session, run, ignore_none=True)

    def _process_inline_skating(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("inline_skating for %s: %r", activity_id, activity_summary)

    def _process_snowshoeing(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("snow_shoe for %s: %r", activity_id, activity_summary)

    def _process_strength_training(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("strength_training for %s: %r", activity_id, activity_summary)

    def _process_stand_up_paddleboarding(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("stand_up_paddleboarding for %s: %r", activity_id, activity_summary)

    def _process_resort_skiing_snowboarding(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("resort_skiing_snowboarding for %s: %r", activity_id, activity_summary)

    def _process_running(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("process_running for %s", activity_id)
        self._process_steps_activity(activity_id, activity_summary)
    #
    # def _process_treadmill_running(self, sub_sport, activity_id, activity_summary):
    #     root_logger.debug("process_treadmill_running for %s", activity_id)
    #     self._process_steps_activity(activity_id, activity_summary)

    def _process_walking(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("process_walking for %s", activity_id)
        self._process_steps_activity(activity_id, activity_summary)

    def _process_hiking(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("process_hiking for %s", activity_id)
        self._process_steps_activity(activity_id, activity_summary)

    def _process_paddling(self, sub_sport, activity_id, activity_summary):
        activity = {
            'activity_id'               : activity_id,
            'avg_cadence'               : self._get_field(activity_summary, 'avgStrokeCadence', float),
            'max_cadence'               : self._get_field(activity_summary, 'maxStrokeCadence', float),
        }
        Activities.s_insert_or_update(self.garmin_act_db_session, activity, ignore_none=True)
        avg_stroke_distance = fitfile.Distance.from_meters(self._get_field(activity_summary, 'avgStrokeDistance', float))
        paddle = {
            'activity_id'               : activity_id,
            'strokes'                   : self._get_field(activity_summary, 'strokes', float),
            'avg_stroke_distance'       : avg_stroke_distance.meters_or_feet(self.measurement_system),
        }
        PaddleActivities.s_insert_or_update(self.garmin_act_db_session, paddle, ignore_none=True)

    def _process_cycling(self, sub_sport, activity_id, activity_summary):
        activity = {
            'activity_id'               : activity_id,
            'avg_cadence'               : self._get_field(activity_summary, 'averageBikingCadenceInRevPerMinute', float),
            'max_cadence'               : self._get_field(activity_summary, 'maxBikingCadenceInRevPerMinute', float),
        }
        Activities.s_insert_or_update(self.garmin_act_db_session, activity, ignore_none=True)
        ride = {
            'activity_id'               : activity_id,
            'strokes'                   : self._get_field(activity_summary, 'strokes', float),
            'vo2_max'                   : self._get_field(activity_summary, 'vO2MaxValue', float),
        }
        CycleActivities.s_insert_or_update(self.garmin_act_db_session, ride, ignore_none=True)

    def _process_mountain_biking(self, sub_sport, activity_id, activity_summary):
        return self._process_cycling(sub_sport, activity_id, activity_summary)

    def _process_fitness_equipment(self, sub_sport, activity_id, activity_summary):
        root_logger.debug("process_fitness_equipment (%s) for %s", sub_sport, activity_id)
        self._call_process_func(sub_sport.name, None, activity_id, activity_summary)

    def _activities_process_json(self, json_data):
        activity_id = json_data['activityId']
        event = Event.from_json(json_data)
        sport, sub_sport = get_summary_sport(json_data)
        activity = {
            'activity_id'               : activity_id,
            'name'                      : json_data.get('activityName'),
            'description'               : self._get_field(json_data, 'description'),
            'type'                      : event.name,
            'sport'                     : sport.name,
            'sub_sport'                 : sub_sport.name,
            'laps'                      : self._get_field(json_data, 'lapCount'),
        }
        activity.update(self._process_common(json_data))
        Activities.s_insert_or_update(self.garmin_act_db_session, activity, ignore_none=True)
        self._call_process_func(sport.name, sub_sport, activity_id, json_data)
        return 1


class GarminJsonDetailsData(GarminJsonActivityData):
    """Class for importing Garmin activity data from JSON formatted Garmin Connect details downloads."""

    def __init__(self, db_params, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminJsonDetailsData.

        Parameters:
        ----------
        db_params (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing activities detail data")
        super().__init__(db_params, r'activity_details_\d*\.json', input_dir, latest, measurement_system, debug)

    def _process_steps_activity(self, sub_sport, activity_id, json_data):
        summary_dto = json_data['summaryDTO']
        avg_speed = fitfile.conversions.mps_to_mph(summary_dto.get('averageSpeed'))
        avg_moving_speed = fitfile.conversions.mps_to_mph(summary_dto.get('averageMovingSpeed'))
        max_speed = fitfile.conversions.mps_to_mph(summary_dto.get('maxSpeed'))
        run = {
            'activity_id'       : activity_id,
            'avg_pace'          : fitfile.conversions.perhour_speed_to_pace(avg_speed),
            'avg_moving_pace'   : fitfile.conversions.perhour_speed_to_pace(avg_moving_speed),
            'max_pace'          : fitfile.conversions.perhour_speed_to_pace(max_speed),
        }
        root_logger.debug("steps_activity for %d: %r", activity_id, run)
        StepsActivities.s_insert_or_update(self.garmin_act_db_session, run, ignore_none=True)

    def _process_cycling(self, sub_sport, activity_id, json_data):
        root_logger.debug("cycling (%s) for %d: %r", sub_sport, activity_id, json_data)

    def _process_elliptical(self, sub_sport, activity_id, json_data):
        root_logger.debug("elliptical for %d: %r", activity_id, json_data)

    def _process_hiking(self, sub_sport, activity_id, json_data):
        root_logger.debug("hiking for %d: %r", activity_id, json_data)
        self._process_steps_activity(sub_sport, activity_id, json_data)

    def _process_inline_skating(self, sub_sport, activity_id, json_data):
        root_logger.debug("inline_skating for %d: %r", activity_id, json_data)

    def _process_paddling(self, sub_sport, activity_id, json_data):
        root_logger.debug("paddling for %d: %r", activity_id, json_data)
    #
    # def _process_mountain_biking(self, sub_sport, activity_id, json_data):
    #     root_logger.debug("mountain_biking for %d: %r", activity_id, json_data)

    def _process_resort_skiing_snowboarding(self, sub_sport, activity_id, json_data):
        root_logger.debug("resort_skiing_snowboarding for %d: %r", activity_id, json_data)

    def _process_snowshoeing(self, sub_sport, activity_id, json_data):
        root_logger.debug("snow_shoe for %d: %r", activity_id, json_data)

    def _process_strength_training(self, sub_sport, activity_id, json_data):
        root_logger.debug("strength_training for %d: %r", activity_id, json_data)

    def _process_stand_up_paddleboarding(self, sub_sport, activity_id, json_data):
        root_logger.debug("stand_up_paddleboarding for %d: %r", activity_id, json_data)
    #
    # def _process_treadmill_running(self, sub_sport, activity_id, json_data):
    #     root_logger.debug("treadmill_running for %d: %r", activity_id, json_data)
    #     self._process_steps_activity(sub_sport, activity_id, json_data)

    def _process_running(self, sub_sport, activity_id, json_data):
        root_logger.debug("running (%s) for %d: %r", sub_sport, activity_id, json_data)
        self._process_steps_activity(sub_sport, activity_id, json_data)

    def _process_walking(self, sub_sport, activity_id, json_data):
        root_logger.debug("walking (%s) for %d: %r", sub_sport, activity_id, json_data)
        self._process_steps_activity(sub_sport, activity_id, json_data)

    def _process_fitness_equipment(self, sub_sport, activity_id, json_data):
        root_logger.debug("fitness_equipment (%s) for %d: %r", sub_sport, activity_id, json_data)
        self._call_process_func(sub_sport.name, None, activity_id, json_data)

    def _activities_process_json(self, json_data):
        activity_id = json_data['activityId']
        metadata_dto = json_data['metadataDTO']
        summary_dto = json_data['summaryDTO']
        sport, sub_sport = get_details_sport(json_data)
        activity = {
            'activity_id'   : activity_id,
            'course_id'     : self._get_field(metadata_dto, 'associatedCourseId', int)
        }
        activity.update(self._process_common(summary_dto))
        Activities.s_insert_or_update(self.garmin_act_db_session, activity, ignore_none=True)
        self._call_process_func(sport.name, sub_sport, activity_id, json_data)
        return 1
