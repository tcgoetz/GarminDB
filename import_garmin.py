#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, string, logging, datetime, traceback, json, dateutil.parser

import Fit
import FileProcessor
import FitFileProcessor
import GarminDB


root_logger = logging.getLogger()
logger = logging.getLogger(__file__)


class GarminWeightData():

    def __init__(self, input_file, input_dir, latest, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, 'weight_.*\.json')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, 'weight_.*\.json', latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        garmindb = GarminDB.GarminDB(db_params_dict)
        def json_parser(entry):
            if 'timestamp' in entry:
                entry['timestamp'] = dateutil.parser.parse(entry['timestamp'])
            return entry
        for file_name in self.file_names:
            json_data = json.load(open(file_name), object_hook=json_parser)
            for sample in json_data:
                timestamp_ms = sample.get('date', None)
                if timestamp_ms is None:
                    break
                weight = sample['weight'] / 1000.0
                if self.english_units:
                    weight *= 2.204623
                point = {
                    'timestamp' : Fit.Conversions.epoch_ms_to_dt(timestamp_ms),
                    'weight' : weight
                }
                GarminDB.Weight.create_or_update_not_none(garmindb, point)
            logger.info("DB updated with %d weight entries" % len(json_data))


class GarminFitData():

    def __init__(self, input_file, input_dir, latest, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, '.*\.fit')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, '.*\.fit', latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        fp = FitFileProcessor.FitFileProcessor(db_params_dict, self.english_units, self.debug)
        for file_name in self.file_names:
            fp.write_file(Fit.File(file_name, self.english_units))


class GarminSleepData():

    old_activity_levels = {
        0.0 : 'deep_sleep',
        1.0 : 'light_sleep',
        2.0 : 'rem',
        2.0 : 'awake',
    }
    rem_activity_levels = {
        -1.0    : 'unmeasurable',
        0.0     : 'deep_sleep',
        1.0     : 'light_sleep',
        2.0     : 'rem',
        3.0     : 'awake',
    }

    def __init__(self, input_file, input_dir, latest, debug):
        self.debug = debug
        logger.info("Debug: %s" % str(debug))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, 'sleep_.*\.json')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, 'sleep_.*\.json', latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        garmindb = GarminDB.GarminDB(db_params_dict)
        def json_parser(entry):
            if 'calendarDate' in entry and entry['calendarDate'] is not None:
                entry['calendarDate'] = dateutil.parser.parse(entry['calendarDate'])
            if 'sleepTimeSeconds' in entry and entry['sleepTimeSeconds'] is not None:
                entry['sleepTimeSeconds'] = Fit.Conversions.secs_to_dt_time(entry['sleepTimeSeconds'])
            if 'sleepStartTimestampGMT' in entry and entry['sleepStartTimestampGMT'] is not None:
                entry['sleepStartTimestampGMT'] = Fit.Conversions.epoch_ms_to_dt(entry['sleepStartTimestampGMT'])
            if 'sleepEndTimestampGMT' in entry and entry['sleepEndTimestampGMT'] is not None:
                entry['sleepEndTimestampGMT'] = Fit.Conversions.epoch_ms_to_dt(entry['sleepEndTimestampGMT'])
            if 'deepSleepSeconds' in entry and entry['deepSleepSeconds'] is not None:
                entry['deepSleepSeconds'] = Fit.Conversions.secs_to_dt_time(entry['deepSleepSeconds'])
            if 'lightSleepSeconds' in entry and entry['lightSleepSeconds'] is not None:
                entry['lightSleepSeconds'] = Fit.Conversions.secs_to_dt_time(entry['lightSleepSeconds'])
            if 'awakeSleepSeconds' in entry and entry['awakeSleepSeconds'] is not None:
                entry['awakeSleepSeconds'] = Fit.Conversions.secs_to_dt_time(entry['awakeSleepSeconds'])
            if 'startGMT' in entry and entry['startGMT'] is not None:
                entry['startGMT'] = dateutil.parser.parse(entry['startGMT'])
            if 'endGMT' in entry and entry['endGMT'] is not None:
                entry['endGMT'] = dateutil.parser.parse(entry['endGMT'])
            return entry
        for file_name in self.file_names:
            json_data = json.load(open(file_name), object_hook=json_parser)
            daily_sleep = json_data.get('dailySleepDTO', None)
            if daily_sleep is None:
                continue
            date = daily_sleep.get('calendarDate', None)
            if date is None:
                continue
            logger.info("Importing %s" % file_name)
            day = date.date()
            day_data = {
                'day' : day,
                'start' : daily_sleep.get('sleepStartTimestampGMT', None),
                'end' : daily_sleep.get('sleepEndTimestampGMT', None),
                'total_sleep' : daily_sleep.get('sleepTimeSeconds', None),
                'deep_sleep' : daily_sleep.get('deepSleepSeconds', None),
                'light_sleep' : daily_sleep.get('lightSleepSeconds', None),
                'awake' : daily_sleep.get('awakeSleepSeconds', None)
            }
            GarminDB.Sleep.create_or_update_not_none(garmindb, day_data)
            sleep_levels = json_data.get('sleepLevels', None)
            if sleep_levels is None:
                continue
            if json_data.get('remSleepData', None):
                sleep_activity_levels = self.rem_activity_levels
                logger.info("Importing %s (%s) with REM data", file_name, day_data['day'])
            else:
                logger.info("Importing %s (%s) without REM data", file_name, day_data['day'])
                sleep_activity_levels = self.old_activity_levels
            for sleep_level in sleep_levels:
                start = sleep_level['startGMT']
                end = sleep_level['endGMT']
                event = sleep_activity_levels[sleep_level['activityLevel']]
                duration = (datetime.datetime.min + (end - start)).time()
                level_data = {
                    'timestamp' : start,
                    'event' : event,
                    'duration' : duration
                }
                GarminDB.SleepEvents.create_or_update_not_none(garmindb, level_data)
            logger.info("DB updated %s with %d sleep level entries" % (str(day), len(sleep_levels)))
        logger.info("DB updated with %d sleep entries" % self.file_count())


class GarminRhrData():

    def __init__(self, input_file, input_dir, latest, debug):
        self.debug = debug
        logger.info("Debug: %s" % str(debug))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, 'rhr_.*\.json')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, 'rhr_.*\.json', latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        garmindb = GarminDB.GarminDB(db_params_dict)
        def json_parser(entry):
            if 'calendarDate' in entry:
                entry['calendarDate'] = dateutil.parser.parse(entry['calendarDate'])
            return entry
        for file_name in self.file_names:
            json_data = json.load(open(file_name), object_hook=json_parser)
            for sample in json_data:
                data = {
                    'day' : sample['calendarDate'].date(),
                    'resting_heart_rate' : sample['value']
                }
                GarminDB.RestingHeartRate.create_or_update_not_none(garmindb, data)
            logger.info("DB updated with %d rhr entries" % len(json_data))


def usage(program):
    print '%s [-s <sqlite db path> | -m <user,password,host>] [-i <fit_inputfile> | -d <fit_input_dir>] ...' % program
    print '    --trace : turn on debug tracing'
    print '    --english : units - use feet, lbs, etc'
    print '    '
    sys.exit()

def main(argv):
    debug = False
    english_units = False
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
        opts, args = getopt.getopt(argv,"f:F:elm:r:R:s:tw:W:",
            ["trace", "english", "fit_input_dir=", "fit_input_file=", "latest", "mysql=", "sqlite=",
             "rhr_input_dir=", "rhr_input_file=", "sleep_input_dir=", "sleep_input_file=", "weight_input_dir=", "weight_input_file="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--trace"):
            debug = True
        elif opt in ("-e", "--english"):
            english_units = True
        elif opt in ("-f", "--fit_input_dir"):
            logging.debug("Fit input dir: %s" % arg)
            fit_input_dir = arg
        elif opt in ("-F", "--fit_input_file"):
            logging.debug("Fit input File: %s" % arg)
            fit_input_file = arg
        elif opt in ("-l", "--latest"):
            latest = True
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

    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    if (not (fit_input_file or fit_input_dir) and not (weight_input_file or weight_input_dir)
        and not (sleep_input_file or sleep_input_dir) and not (rhr_input_file or rhr_input_dir)):
        print "Missing or incorrect arguments: Fit or weight input files or directory"
        usage(sys.argv[0])
    if len(db_params_dict) == 0:
        print "Missing or incorrect arguments: db params"
        usage(sys.argv[0])

    if weight_input_file or weight_input_dir:
        gwd = GarminWeightData(weight_input_file, weight_input_dir, latest, english_units, debug)
        if gwd.file_count() > 0:
            gwd.process_files(db_params_dict)

    if fit_input_file or fit_input_dir:
        gfd = GarminFitData(fit_input_file, fit_input_dir, latest, english_units, debug)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)

    if sleep_input_file or sleep_input_dir:
        gsd = GarminSleepData(sleep_input_file, sleep_input_dir, latest, debug)
        if gsd.file_count() > 0:
            gsd.process_files(db_params_dict)

    if rhr_input_file or rhr_input_dir:
        grhrd = GarminRhrData(rhr_input_file, rhr_input_dir, latest, debug)
        if grhrd.file_count() > 0:
            grhrd.process_files(db_params_dict)


if __name__ == "__main__":
    main(sys.argv[1:])


