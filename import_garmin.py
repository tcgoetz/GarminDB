#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, string, logging, datetime, traceback, enum
import dateutil.parser

import Fit
from JsonFileProcessor import *
from FileProcessor import *
from FitFileProcessor import *
import GarminDB


root_logger = logging.getLogger()
logger = logging.getLogger(__file__)


class GarminWeightData(JsonFileProcessor):

    def __init__(self, db_params_dict, input_file, input_dir, latest, english_units, debug):
        super(GarminWeightData, self).__init__(input_file, input_dir, 'weight_\d{4}-\d{2}-\d{2}\.json', latest, debug)
        self.english_units = english_units
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'startDate' : dateutil.parser.parse}

    def process_json(self, json_data):
        weight_list = json_data['dateWeightList']
        if len(weight_list) > 0:
            weight = Fit.Conversions.Weight.from_grams(weight_list[0]['weight'])
            point = {
                'timestamp' : json_data['startDate'],
                'weight'    : weight.kgs_or_lbs(not self.english_units)
            }
            GarminDB.Weight.create_or_update_not_none(self.garmin_db, point)
            return 1


class GarminFitData():

    def __init__(self, input_file, input_dir, latest, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s", str(debug), str(english_units))
        if input_file:
            self.file_names = FileProcessor.match_file(input_file, '.*\.fit')
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, '.*\.fit', latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        fp = FitFileProcessor(db_params_dict, self.debug)
        for file_name in self.file_names:
            try:
                fp.write_file(Fit.File(file_name, self.english_units))
            except Fit.FitFileError as e:
                logger.error("Failed to parse %s: %s" % (file_name, str(e)))


class SleepActivityLevels(enum.Enum):
    deep_sleep = 0.0
    light_sleep = 1.0
    awake = 2.0
    more_awake = 3.0


class RemSleepActivityLevels(enum.Enum):
    unmeasurable = -1.0
    deep_sleep = 0.0
    light_sleep = 1.0
    rem_sleep = 2.0
    awake = 3.0


class GarminSleepData(JsonFileProcessor):

    def __init__(self, db_params_dict, input_file, input_dir, latest, debug):
        super(GarminSleepData, self).__init__(input_file, input_dir, 'sleep_\d{4}-\d{2}-\d{2}\.json', latest, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {
            'calendarDate'              : dateutil.parser.parse,
            'sleepTimeSeconds'          : Fit.Conversions.secs_to_dt_time,
            'sleepStartTimestampGMT'    : Fit.Conversions.epoch_ms_to_dt,
            'sleepEndTimestampGMT'      : Fit.Conversions.epoch_ms_to_dt,
            'deepSleepSeconds'          : Fit.Conversions.secs_to_dt_time,
            'lightSleepSeconds'         : Fit.Conversions.secs_to_dt_time,
            'remSleepSeconds'           : Fit.Conversions.secs_to_dt_time,
            'awakeSleepSeconds'         : Fit.Conversions.secs_to_dt_time,
            'startGMT'                  : dateutil.parser.parse,
            'endGMT'                    : dateutil.parser.parse
        }

    def process_json(self, json_data):
            daily_sleep = json_data.get('dailySleepDTO', None)
            if daily_sleep is None:
                return 0
            date = daily_sleep.get('calendarDate', None)
            if date is None:
                return 0
            day = date.date()
            if json_data.get('remSleepData', None):
                logger.info("Importing %s with REM data", day)
                sleep_activity_levels = RemSleepActivityLevels
            else:
                logger.info("Importing %s without REM data", day)
                sleep_activity_levels = SleepActivityLevels
            day_data = {
                'day' : day,
                'start' : daily_sleep.get('sleepStartTimestampGMT', None),
                'end' : daily_sleep.get('sleepEndTimestampGMT', None),
                'total_sleep' : daily_sleep.get('sleepTimeSeconds', None),
                'deep_sleep' : daily_sleep.get('deepSleepSeconds', None),
                'light_sleep' : daily_sleep.get('lightSleepSeconds', None),
                'rem_sleep' : daily_sleep.get('remSleepSeconds', None),
                'awake' : daily_sleep.get('awakeSleepSeconds', None)
            }
            GarminDB.Sleep.create_or_update_not_none(self.garmin_db, day_data)
            sleep_levels = json_data.get('sleepLevels', None)
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
                GarminDB.SleepEvents.create_or_update_not_none(self.garmin_db, level_data)
            return len(sleep_levels)


class GarminRhrData(JsonFileProcessor):

    def __init__(self, db_params_dict, input_file, input_dir, latest, debug):
        super(GarminRhrData, self).__init__(input_file, input_dir, 'rhr_\d{4}-\d{2}-\d{2}\.json', latest, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'statisticsStartDate' : dateutil.parser.parse}

    def process_json(self, json_data):
        rhr_list = json_data['allMetrics']['metricsMap']['WELLNESS_RESTING_HEART_RATE']
        if len(rhr_list) > 0:
            rhr = rhr_list[0].get('value')
            if rhr:
                point = {
                    'day'                   : json_data['statisticsStartDate'].date(),
                    'resting_heart_rate'    : rhr
                }
                GarminDB.RestingHeartRate.create_or_update_not_none(self.garmin_db, point)
                return 1


class GarminProfile(JsonFileProcessor):

    def __init__(self, db_params_dict, input_dir, debug):
        super(GarminProfile, self).__init__(None, input_dir, 'profile\.json', False, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'calendarDate' : dateutil.parser.parse}

    def process_json(self, json_data):
        measurement_system = Fit.FieldEnums.DisplayMeasure.from_string(json_data['measurementSystem'])
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

    def __init__(self, db_params_dict, input_file, input_dir, latest, english_units, debug):
        super(GarminSummaryData, self).__init__(input_file, input_dir, 'daily_summary_\d{4}-\d{2}-\d{2}\.json', latest, debug)
        self.input_dir = input_dir
        self.english_units = english_units
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'calendarDate' : dateutil.parser.parse}

    def process_json(self, json_data):
        day = json_data['calendarDate'].date()
        description_str = json_data['wellnessDescription']
        (description, extra_data) = GarminDB.DailyExtraData.from_string(description_str)
        distance = Fit.Conversions.Distance.from_meters(json_data['totalDistanceMeters'])
        summary = {
            'day'                   : day,
            'step_goal'             : json_data['dailyStepGoal'],
            'steps'                 : json_data['totalSteps'],
            'intensity_mins_goal'   : json_data['intensityMinutesGoal'],
            'floors_up'             : json_data['floorsAscended'],
            'floors_down'           : json_data['floorsDescended'],
            'distance'              : distance.to_miles() if self.english_units else distance.to_kms(),
            'calories_goal'         : json_data['netCalorieGoal'],
            'calories_total'        : json_data['totalKilocalories'],
            'calories_bmr'          : json_data['bmrKilocalories'],
            'calories_active'       : json_data['activeKilocalories'],
            'calories_consumed'     : json_data['consumedKilocalories'],
            'description'           : description,
        }
        GarminDB.DailySummary.create_or_update_not_none(self.garmin_db, summary)
        if extra_data:
            extra_data['day'] = day
            logger.info("Extra data: %s", repr(extra_data))
            json_filename = self.input_dir + '/extra_data_' + day.strftime("%Y-%m-%d") + '.json'
            if not os.path.isfile(json_filename):
                self.save_json_file(json_filename, extra_data)
        return 1


class GarminExtraData(JsonFileProcessor):

    def __init__(self, db_params_dict, input_file, input_dir, latest, debug):
        super(GarminExtraData, self).__init__(input_file, input_dir, 'extra_data_\d{4}-\d{2}-\d{2}\.json', latest, debug)
        self.garmin_db = GarminDB.GarminDB(db_params_dict)
        self.conversions = {'day' : dateutil.parser.parse}

    def process_json(self, json_data):
        logger.info("Extra data: %s", repr(json_data))
        json_data['day'] = json_data['day'].date()
        GarminDB.DailyExtraData.create_or_update_not_none(self.garmin_db, GarminDB.DailyExtraData.convert_eums(json_data))
        return 1


def usage(program):
    print '%s [-s <sqlite db path> | -m <user,password,host>] [-i <fit_inputfile> | -d <fit_input_dir>] ...' % program
    print '    --trace : turn on debug tracing'
    print '    --english : units - use feet, lbs, etc'
    print '    '
    sys.exit()

def main(argv):
    debug = 0
    profile_dir = None
    fit_input_dir = None
    fit_input_file = None
    weight_input_dir = None
    weight_input_file = None
    rhr_input_dir = None
    rhr_input_file = None
    sleep_input_dir = None
    sleep_input_file = None
    latest = False
    db_params_dict = {}

    try:
        opts, args = getopt.getopt(argv,"f:F:lm:p:r:R:s:t:w:W:",
            ["trace=", "fit_input_dir=", "fit_input_file=", "latest", "mysql=", "profile_dir=", "sqlite=",
             "rhr_input_dir=", "rhr_input_file=", "sleep_input_dir=", "sleep_input_file=", "weight_input_dir=", "weight_input_file="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--trace"):
            debug = int(arg)
        elif opt in ("-f", "--fit_input_dir"):
            logging.debug("Fit input dir: %s" % arg)
            fit_input_dir = arg
        elif opt in ("-F", "--fit_input_file"):
            logging.debug("Fit input File: %s" % arg)
            fit_input_file = arg
        elif opt in ("-l", "--latest"):
            latest = True
        elif opt in ("-p", "--profile_dir"):
            logging.debug("Profile input dir: %s" % arg)
            profile_dir = arg
        elif opt in ("-r", "--rhr_input_dir"):
            logging.debug("RHR input dir: %s" % arg)
            rhr_input_dir = arg
        elif opt in ("-R", "--rhr_input_file"):
            logging.debug("RHR input file: %s" % arg)
            rhr_input_file = arg
        elif opt in ("-S", "--sleep_input_dir"):
            logging.debug("Sleep input dir: %s" % arg)
            sleep_input_dir = arg
        elif opt in ("--sleep_input_file"):
            logging.debug("Sleep input file: %s" % arg)
            sleep_input_file = arg
        elif opt in ("-w", "--weight_input_dir"):
            logging.debug("Weight input dir: %s" % arg)
            weight_input_dir = arg
        elif opt in ("-W", "--weight_input_file"):
            logging.debug("Weight input file: %s" % arg)
            weight_input_file = arg
        elif opt in ("-s", "--sqlite"):
            logging.debug("Sqlite DB path: %s" % arg)
            db_params_dict['db_type'] = 'sqlite'
            db_params_dict['db_path'] = arg
        elif opt in ("-m", "--mysql"):
            logging.debug("Mysql DB string: %s" % arg)
            db_args = arg.split(',')
            db_params_dict['db_type'] = 'mysql'
            db_params_dict['db_username'] = db_args[0]
            db_params_dict['db_password'] = db_args[1]
            db_params_dict['db_host'] = db_args[2]

    if debug > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    if (not profile_dir  and not (fit_input_file or fit_input_dir) and not (weight_input_file or weight_input_dir)
        and not (sleep_input_file or sleep_input_dir) and not (rhr_input_file or rhr_input_dir)):
        print "Missing or incorrect arguments: Fit or weight input files or directory"
        usage(sys.argv[0])
    if len(db_params_dict) == 0:
        print "Missing or incorrect arguments: db params"
        usage(sys.argv[0])

    if profile_dir:
        gp = GarminProfile(db_params_dict, profile_dir, debug)
        if gp.file_count() > 0:
            gp.process()

    garmindb = GarminDB.GarminDB(db_params_dict)
    english_units = GarminDB.Attributes.measurements_type_metric(garmindb) == False

    if weight_input_file or weight_input_dir:
        gwd = GarminWeightData(db_params_dict, weight_input_file, weight_input_dir, latest, english_units, debug)
        if gwd.file_count() > 0:
            gwd.process()

    if fit_input_file or fit_input_dir:
        gsd = GarminSummaryData(db_params_dict, fit_input_file, fit_input_dir, latest, english_units, debug)
        if gsd.file_count() > 0:
            gsd.process()
        ged = GarminExtraData(db_params_dict, fit_input_file, fit_input_dir, latest, debug)
        if ged.file_count() > 0:
            ged.process()
        gfd = GarminFitData(fit_input_file, fit_input_dir, latest, english_units, debug)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)

    if sleep_input_file or sleep_input_dir:
        gsd = GarminSleepData(db_params_dict, sleep_input_file, sleep_input_dir, latest, debug)
        if gsd.file_count() > 0:
            gsd.process()

    if rhr_input_file or rhr_input_dir:
        grhrd = GarminRhrData(db_params_dict, rhr_input_file, rhr_input_dir, latest, debug)
        if grhrd.file_count() > 0:
            grhrd.process()


if __name__ == "__main__":
    main(sys.argv[1:])


