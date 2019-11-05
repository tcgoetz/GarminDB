"""Objects for importing Garmin data from Garmin Connect downloads and FIT files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import os
import sys
import string
import logging
import datetime
import enum
import dateutil.parser
import progressbar

import Fit
import GarminDB
from utilities import JsonFileProcessor, FileProcessor
from fit_file_processor import FitFileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class GarminWeightData(JsonFileProcessor):
    """Class for importing JSON formatted Garmin Connect weight data into a database."""

    def __init__(self, db_params_dict, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminWeightData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for weight data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing weight data")
        super(GarminWeightData, self).__init__(None, input_dir, r'weight_\d{4}-\d{2}-\d{2}\.json', latest, debug)
        self.measurement_system = measurement_system
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'startDate' : dateutil.parser.parse}

    def _process_json(self, json_data):
        weight_list = json_data['dateWeightList']
        if len(weight_list) > 0:
            weight = Fit.Weight.from_grams(weight_list[0]['weight'])
            point = {
                'day'       : json_data['startDate'].date(),
                'weight'    : weight.kgs_or_lbs(self.measurement_system)
            }
            GarminDB.Weight.find_or_create(self.garmin_db, point)
            return 1


class GarminMonitoringFitData(object):
    """Class for importing monitoring FIT files into a database."""

    def __init__(self, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminMonitoringFitData.

        Parameters:
        input_dir (string): directory (full path) to check for monitoring data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing daily monitoring FIT data")
        self.measurement_system = measurement_system
        self.debug = debug
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, Fit.file.name_regex, latest, True)

    def file_count(self):
        """Return the number of files that will be processed."""
        return len(self.file_names)

    def process_files(self, db_params_dict):
        """Import monitoring FIT files into the database."""
        fp = FitFileProcessor(db_params_dict, self.debug)
        for file_name in progressbar.progressbar(self.file_names):
            try:
                fit_file = Fit.file.File(file_name, self.measurement_system)
                if fit_file.type() == Fit.field_enums.FileType.monitoring_b:
                    fp.write_file(fit_file)
                else:
                    root_logger.info("skipping non monitoring file %s type %r message types %r", file_name, fit_file.type(), fit_file.message_types())
            except Fit.exceptions.FitFileError as e:
                logger.error("Failed to parse %s: %s", file_name, e)


class SleepActivityLevels(enum.Enum):
    """Enum of values used to encode activity levels during sleep on Gamin Connect."""

    deep_sleep = 0.0
    light_sleep = 1.0
    awake = 2.0
    more_awake = 3.0


class RemSleepActivityLevels(enum.Enum):
    """Enum of values used to encode activity levels during sleep (including REM sleep) on Gamin Connect."""

    unmeasurable = -1.0
    deep_sleep = 0.0
    light_sleep = 1.0
    rem_sleep = 2.0
    awake = 3.0


class GarminSleepData(JsonFileProcessor):
    """Class for importing JSON formatted Garmin Connect sleep data into a database."""

    def __init__(self, db_params_dict, input_dir, latest, debug):
        """
        Return an instance of GarminSleepData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for sleep data files
        latest (Boolean): check for latest files only
        debug (Boolean): enable debug logging

        """
        logger.info("Processing sleep data")
        super(GarminSleepData, self).__init__(None, input_dir, r'sleep_\d{4}-\d{2}-\d{2}\.json', latest, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {
            'calendarDate'              : dateutil.parser.parse,
            'sleepTimeSeconds'          : Fit.conversions.secs_to_dt_time,
            'sleepStartTimestampGMT'    : Fit.conversions.epoch_ms_to_dt,
            'sleepEndTimestampGMT'      : Fit.conversions.epoch_ms_to_dt,
            'deepSleepSeconds'          : Fit.conversions.secs_to_dt_time,
            'lightSleepSeconds'         : Fit.conversions.secs_to_dt_time,
            'remSleepSeconds'           : Fit.conversions.secs_to_dt_time,
            'awakeSleepSeconds'         : Fit.conversions.secs_to_dt_time,
            'startGMT'                  : dateutil.parser.parse,
            'endGMT'                    : dateutil.parser.parse
        }

    def _process_json(self, json_data):
        daily_sleep = json_data.get('dailySleepDTO')
        if daily_sleep is None:
            return 0
        date = daily_sleep.get('calendarDate')
        if date is None:
            return 0
        day = date.date()
        if json_data.get('remSleepData'):
            root_logger.info("Importing %s with REM data", day)
            sleep_activity_levels = RemSleepActivityLevels
        else:
            root_logger.info("Importing %s without REM data", day)
            sleep_activity_levels = SleepActivityLevels
        day_data = {
            'day' : day,
            'start' : daily_sleep.get('sleepStartTimestampGMT'),
            'end' : daily_sleep.get('sleepEndTimestampGMT'),
            'total_sleep' : daily_sleep.get('sleepTimeSeconds'),
            'deep_sleep' : daily_sleep.get('deepSleepSeconds'),
            'light_sleep' : daily_sleep.get('lightSleepSeconds'),
            'rem_sleep' : daily_sleep.get('remSleepSeconds'),
            'awake' : daily_sleep.get('awakeSleepSeconds')
        }
        GarminDB.Sleep.create_or_update(self.garmin_db, day_data, ignore_none=True)
        sleep_levels = json_data.get('sleepLevels')
        if sleep_levels is None:
            return 0
        for sleep_level in sleep_levels:
            start = sleep_level['startGMT']
            end = sleep_level['endGMT']
            event = sleep_activity_levels(sleep_level['activityLevel'])
            duration = (datetime.datetime.min + (end - start)).time()
            level_data = {
                'timestamp' : start,
                'event' : event.name,
                'duration' : duration
            }
            GarminDB.SleepEvents.create_or_update(self.garmin_db, level_data, ignore_none=True)
        return len(sleep_levels)


class GarminRhrData(JsonFileProcessor):
    """Class for importing JSON formatted Garmin Connect resting heart rate data into a database."""

    def __init__(self, db_params_dict, input_dir, latest, debug):
        """
        Return an instance of GarminRhrData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for resting heart rate data files
        latest (Boolean): check for latest files only
        debug (Boolean): enable debug logging

        """
        logger.info("Processing rhr data")
        super(GarminRhrData, self).__init__(None, input_dir, r'rhr_\d{4}-\d{2}-\d{2}\.json', latest, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'statisticsStartDate' : dateutil.parser.parse}

    def _process_json(self, json_data):
        rhr_list = json_data['allMetrics']['metricsMap']['WELLNESS_RESTING_HEART_RATE']
        if len(rhr_list) > 0:
            rhr = rhr_list[0].get('value')
            if rhr:
                point = {
                    'day'                   : json_data['statisticsStartDate'].date(),
                    'resting_heart_rate'    : rhr
                }
                GarminDB.RestingHeartRate.create_or_update(self.garmin_db, point, ignore_none=True)
                return 1


class GarminProfile(JsonFileProcessor):
    """Class for importing JSON formatted Garmin Connect profile data into a database."""

    def __init__(self, db_params_dict, input_dir, debug):
        """
        Return an instance of GarminProfile.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for profile data files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing profile data")
        super(GarminProfile, self).__init__(None, input_dir, r'profile\.json', False, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'calendarDate' : dateutil.parser.parse}

    def _process_json(self, json_data):
        measurement_system = Fit.field_enums.DisplayMeasure.from_string(json_data['measurementSystem'])
        attributes = {
            'name'                  : string.replace(json_data['displayName'], '_', ' '),
            'time_zone'             : json_data['timeZone'],
            'measurement_system'    : str(measurement_system),
            'date_format'           : json_data['dateFormat']['formatKey'],
        }
        for attribute_name, attribute_value in attributes.items():
            GarminDB.Attributes.set_newer(self.garmin_db, attribute_name, attribute_value)
        return len(attributes)


class GarminSummaryData(JsonFileProcessor):
    """Class for importing JSON formatted Garmin Connect daily summary data into a database."""

    def __init__(self, db_params_dict, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminSleepData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        logger.info("Processing daily summary data")
        super(GarminSummaryData, self).__init__(None, input_dir, r'daily_summary_\d{4}-\d{2}-\d{2}\.json', latest, debug, recursive=True)
        self.input_dir = input_dir
        self.measurement_system = measurement_system
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {
            'calendarDate'              : dateutil.parser.parse,
            'moderateIntensityMinutes'  : Fit.conversions.min_to_dt_time,
            'vigorousIntensityMinutes'  : Fit.conversions.min_to_dt_time,
            'intensityMinutesGoal'      : Fit.conversions.min_to_dt_time,
        }

    def _process_json(self, json_data):
        day = json_data['calendarDate'].date()
        description_str = json_data['wellnessDescription']
        (description, extra_data) = GarminDB.DailyExtraData.from_string(description_str)
        distance = Fit.Distance.from_meters(json_data['totalDistanceMeters'])
        summary = {
            'day'                       : day,
            'hr_min'                    : json_data['minHeartRate'],
            'hr_max'                    : json_data['maxHeartRate'],
            'rhr'                       : json_data['restingHeartRate'],
            'stress_avg'                : json_data['averageStressLevel'],
            'step_goal'                 : json_data['dailyStepGoal'],
            'steps'                     : json_data['totalSteps'],
            'floors_goal'               : json_data['userFloorsAscendedGoal'],
            'moderate_activity_time'    : json_data['moderateIntensityMinutes'],
            'vigorous_activity_time'    : json_data['vigorousIntensityMinutes'],
            'intensity_time_goal'       : json_data['intensityMinutesGoal'],
            'floors_up'                 : json_data['floorsAscended'],
            'floors_down'               : json_data['floorsDescended'],
            'distance'                  : distance.kms_or_miles(self.measurement_system),
            'calories_goal'             : json_data['netCalorieGoal'],
            'calories_total'            : json_data['totalKilocalories'],
            'calories_bmr'              : json_data['bmrKilocalories'],
            'calories_active'           : json_data['activeKilocalories'],
            'calories_consumed'         : json_data['consumedKilocalories'],
            'description'               : description,
        }
        GarminDB.DailySummary.create_or_update(self.garmin_db, summary, ignore_none=True)
        if extra_data:
            extra_data['day'] = day
            logger.info("Extra data: %r", extra_data)
            json_filename = self.input_dir + '/extra_data_' + day.strftime("%Y-%m-%d") + '.json'
            if not os.path.isfile(json_filename):
                self._save_json_file(json_filename, extra_data)
        return 1


class GarminMonitoringExtraData(JsonFileProcessor):
    """Class for importing JSON formatted Garmin Connect extra data into a database."""

    def __init__(self, db_params_dict, input_dir, latest, debug):
        """
        Return an instance of GarminMonitoringExtraData.

        Parameters:
        db_params_dict (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        debug (Boolean): enable debug logging

        """
        logger.info("Processing daily extra data")
        super(GarminMonitoringExtraData, self).__init__(None, input_dir, r'extra_data_\d{4}-\d{2}-\d{2}\.json', latest, debug, recursive=True)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'day' : dateutil.parser.parse}

    def _process_json(self, json_data):
        root_logger.info("Extra data: %r", json_data)
        json_data['day'] = json_data['day'].date()
        GarminDB.DailyExtraData.create_or_update(self.garmin_db, GarminDB.DailyExtraData.convert_eums(json_data), ignore_none=True)
        return 1
