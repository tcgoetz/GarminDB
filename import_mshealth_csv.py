#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, time, traceback

from HealthDB import CsvImporter
import MSHealthDB
import FileProcessor


logger = logging.getLogger(__file__)


class MSHealthData():

    cols_map = {
        'Date': ('day', CsvImporter.map_ymd_date),
        'Floors_Climbed': ('floors', CsvImporter.map_identity),
        'Steps': ('steps', CsvImporter.map_integer),
        'HR_Highest': ('hr_max', CsvImporter.map_integer),
        'HR_Lowest': ('hr_min', CsvImporter.map_integer),
        'HR_Average': ('hr_avg', CsvImporter.map_integer),
        'Calories': ('calories', CsvImporter.map_integer),
        'Active_Hours': ('active_hours', CsvImporter.map_integer),
        'Total_Seconds_All_Activities': ('activity_secs', CsvImporter.map_integer),
        'Total_Calories_All_Activities': ('activity_calories', CsvImporter.map_integer),
        'Exercise_Events': ('exercise_events', CsvImporter.map_integer),
        'Exercise_Total_Calories': ('exercise_calories', CsvImporter.map_integer),
        'Exercise_Total_Seconds': ('exercise_secs', CsvImporter.map_integer),
        'Total_Miles_Moved': ('miles_moved', CsvImporter.map_float),
        'Sleep_Events': ('sleep_events', CsvImporter.map_integer),
        'Sleep_Total_Calories': ('sleep_calories', CsvImporter.map_integer),
        'Total_Seconds_Slept': ('sleep_secs', CsvImporter.map_integer),
        'Walk_Events': ('walk_events', CsvImporter.map_integer),
        'Walk_Total_Seconds': ('walk_secs', CsvImporter.map_integer),
        'Walk_Total_Calories': ('workout_calories', CsvImporter.map_integer),
        'Total_Miles_Walked': ('miles_walked', CsvImporter.map_float),
        'Run_Events': ('run_ewvents', CsvImporter.map_integer),
        'Run_Total_Calories': ('run_calories', CsvImporter.map_integer),
        'Run_Total_Seconds': ('run_secs', CsvImporter.map_integer),
        'Total_Miles_Run': ('miles_run', CsvImporter.map_float),
        'Total_Miles_Golfed': ('miles_golfed', CsvImporter.map_float),
        'Golf_Total_Calories': ('golf_calories', CsvImporter.map_integer),
        'Golf_Events': ('golf_events', CsvImporter.map_integer),
        'Golf_Total_Seconds': ('golf_secs', CsvImporter.map_integer),
        'Total_Miles_Biked': ('miles_biked', CsvImporter.map_float),
        'UV_Exposure_Minutes': ('uv_mins', CsvImporter.map_integer),
        'Bike_Total_Seconds': ('bike_secs', CsvImporter.map_integer),
        'Bike_Total_Calories': ('bike_calories', CsvImporter.map_integer),
        'Bike_Events': ('bike_events', CsvImporter.map_integer),
        'Guided_Workout_Events': ('guided_workout_events', CsvImporter.map_integer),
        'Guided_Workout_Total_Calories': ('guided_workout_calories', CsvImporter.map_integer),
        'Guided_Workout_Total_Seconds': ('guided_workout_secs', CsvImporter.map_integer),
    }

    def __init__(self, input_file, input_dir, db_params_dict, english_units, debug):
        self.english_units = english_units
        self.mshealthdb = MSHealthDB.MSHealthDB(db_params_dict, debug)
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, 'Daily_Summary_.*.csv')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, 'Daily_Summary_.*.csv')

    def file_count(self):
        return len(self.file_names)

    def write_entry(self, db_entry):
        MSHealthDB.DaysSummary.find_or_create(self.mshealthdb, db_entry)

    def process_files(self):
        for file_name in self.file_names:
            logger.info("Processing file: " + file_name)
            csvimporter = CsvImporter(file_name, self.cols_map, self.write_entry)
            csvimporter.process_file(self.english_units)


class MSVaultData():

    def __init__(self, input_file, input_dir, db_params_dict, english_units, debug):
        self.english_units = english_units
        self.mshealthdb = MSHealthDB.MSHealthDB(db_params_dict, debug)
        self.cols_map = {
            'Date': ('timestamp', CsvImporter.map_mdy_date),
            'Weight': ('weight', MSVaultData.map_weight),
        }
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, 'HealthVault_Weight_.*.csv')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, 'HealthVault_Weight_.*.csv')

    def file_count(self):
        return len(self.file_names)

    def write_entry(self, db_entry):
        MSHealthDB.MSVaultWeight.find_or_create(self.mshealthdb, db_entry)

    def process_files(self):
        for file_name in self.file_names:
            logger.info("Processing file: " + file_name)
            csvimporter = CsvImporter(file_name, self.cols_map, self.write_entry)
            csvimporter.process_file(self.english_units)

    @classmethod
    def map_weight(cls, english_units, value):
        m = re.search(r"(\d{2,3}\.\d{2}) .*", value)
        if m:
            logger.debug("Matched weight: " + m.group(1))
            return float(m.group(1))
        else:
            logger.debug("Unmatched weight: " + value)
            return None


def usage(program):
    print '%s -o <dbpath> -i <inputfile> [-m | -v]' % program
    sys.exit()

def main(argv):
    debug = False
    english_units = False
    input_file = None
    input_dir = None
    db_params_dict = {}

    try:
        opts, args = getopt.getopt(argv,"d:ehi:s:",
            ["help", "input_dir=", "trace", "english", "input_file=", "mysql=", "sqlite="])
    except getopt.GetoptError:
        print "Bad argument"
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--trace"):
            logger.info("Trace:")
            debug = True
        elif opt in ("-e", "--english"):
            logger.info("English:")
            english_units = True
        elif opt in ("-i", "--input_file"):
            logger.info("Input File: %s" % arg)
            input_file = arg
        elif opt in ("-d", "--input_dir"):
            input_dir = arg
        elif opt in ("-s", "--sqlite"):
            logging.debug("Sqlite DB path: %s" % arg)
            db_params_dict['db_type'] = 'sqlite'
            db_params_dict['db_path'] = arg
        elif opt in ("--mysql"):
            logging.debug("Mysql DB string: %s" % arg)
            db_args = arg.split(',')
            db_params_dict['db_type'] = 'mysql'
            db_params_dict['db_username'] = db_args[0]
            db_params_dict['db_password'] = db_args[1]
            db_params_dict['db_host'] = db_args[2]

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if (not input_file and not input_dir) or len(db_params_dict) == 0:
        print "Missing arguments:"
        usage(sys.argv[0])

    msd = MSHealthData(input_file, input_dir, db_params_dict, english_units, debug)
    if msd.file_count() > 0:
        msd.process_files()

    mshv = MSVaultData(input_file, input_dir, db_params_dict, english_units, debug)
    if mshv.file_count() > 0:
        mshv.process_files()


if __name__ == "__main__":
    main(sys.argv[1:])


