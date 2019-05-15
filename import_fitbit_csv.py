#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, time, traceback

from HealthDB import CsvImporter
import FitBitDB
import FileProcessor

import GarminDBConfigManager


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

    def __init__(self, input_file, input_dir, db_params_dict, metric, debug):
        self.metric = metric
        self.fitbitdb = FitBitDB.FitBitDB(db_params_dict, debug)
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, '.*.csv')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, '.*.csv')

    def file_count(self):
        return len(self.file_names)

    def write_entry(self, db_entry):
        FitBitDB.DaysSummary.find_or_create(self.fitbitdb, FitBitDB.DaysSummary.intersection(db_entry))

    def process_files(self):
        for file_name in self.file_names:
            logger.info("Processing file: " + file_name)
            self.csvimporter = CsvImporter(file_name, self.cols_map, self.write_entry)
            self.csvimporter.process_file(not self.metric)



def usage(program):
    print '%s -i <inputfile> ...' % program
    sys.exit()

def main(argv):
    debug = False
    input_file = None

    try:
        opts, args = getopt.getopt(argv,"dhi:", ["debug", "input_file="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-d", "--debug"):
            debug = True
       elif opt in ("-i", "--input_file"):
            logging.debug("Input File: %s" % arg)
            input_file = arg

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    db_params_dict = GarminDBConfigManager.get_db_params()

    fitbit_dir = GarminDBConfigManager.get_or_create_fitbit_dir()
    metric = GarminDBConfigManager.get_metric()
    fd = FitBitData(input_file, fitbit_dir, db_params_dict, metric, debug)
    if fd.file_count() > 0:
        fd.process_files()


if __name__ == "__main__":
    main(sys.argv[1:])


