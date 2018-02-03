#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, time, traceback

from HealthDB import CsvImporter
import FitBitDB


logger = logging.getLogger(__file__)


class FitBitData():

    cols_map = {
        'sleep-minutesAwake': ('awake_mins', CsvImporter.map_integer),
        'activities-caloriesBMR': ('calories_bmr', CsvImporter.map_integer),
        'sleep-minutesToFallAsleep': ('to_fall_asleep_mins', CsvImporter.map_integer),
        'activities-floors': ('floors', CsvImporter.map_integer),
        'activities-steps': ('steps', CsvImporter.map_integer),
        'activities-distance': ('distance', CsvImporter.map_float),
        'foods-log-caloriesIn': ('calories_in', CsvImporter.map_integer),
        'activities-activityCalories': ('activities_calories', CsvImporter.map_integer),
        'sleep-minutesAfterWakeup': ('after_wakeup_mins', CsvImporter.map_integer),
        'activities-minutesFairlyActive': ('fairly_active_mins', CsvImporter.map_integer),
        'sleep-efficiency': ('sleep_efficiency', CsvImporter.map_integer),
        'sleep-timeInBed': ('in_bed_mins', CsvImporter.map_integer),
        'activities-minutesVeryActive': ('very_active_mins', CsvImporter.map_integer),
        'body-weight': ('weight', CsvImporter.map_kgs),
        'activities-minutesSedentary': ('sedentary_mins', CsvImporter.map_integer),
        'activities-elevation': ('elevation', CsvImporter.map_meters),
        'activities-minutesLightlyActive': ('lightly_active_mins', CsvImporter.map_integer),
        'sleep-startTime': ('sleep_start', CsvImporter.map_time),
        'activities-calories': ('calories', CsvImporter.map_integer),
        'foods-log-water': ('log_water', CsvImporter.map_float),
        'sleep-minutesAsleep': ('asleep_mins', CsvImporter.map_integer),
        'body-bmi': ('bmi', CsvImporter.map_float),
        'dateTime': ('day', CsvImporter.map_ymd_date),
        'body-fat': ('body_fat', CsvImporter.map_float),
        'sleep-awakeningsCount': ('awakenings_count', CsvImporter.map_integer),
    }

    def __init__(self, input_file, db_params_dict, english_units, debug):
        self.english_units = english_units
        self.fitbitdb = FitBitDB.FitBitDB(db_params_dict, debug)
        self.csvimporter = CsvImporter(input_file, self.cols_map, self.write_entry)

    def write_entry(self, db_entry):
        FitBitDB.DaysSummary.find_or_create(self.fitbitdb, db_entry)

    def process_files(self):
        self.csvimporter.process_file(self.english_units)



def usage(program):
    print '%s -o <dbpath> -i <inputfile> ...' % program
    sys.exit()

def main(argv):
    debug = False
    english_units = False
    input_file = None
    db_params_dict = {}

    try:
        opts, args = getopt.getopt(argv,"dei:s:", ["debug", "english", "input_file=","sqlite="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-e", "--english"):
            english_units = True
        elif opt in ("-i", "--input_file"):
            logging.debug("Input File: %s" % arg)
            input_file = arg
        elif opt in ("-s", "--sqlite"):
            logging.debug("Sqlite DB path: %s" % arg)
            db_params_dict['db_type'] = 'sqlite'
            db_params_dict['db_path'] = arg

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not input_file or not (db_params_dict['db_path']):
        print "Missing arguments:"
        usage(sys.argv[0])

    fd = FitBitData(input_file, db_params_dict, english_units, debug)
    fd.process_files()


if __name__ == "__main__":
    main(sys.argv[1:])


