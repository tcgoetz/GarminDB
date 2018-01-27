#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, time, traceback

import csv
import FitBitDB


logger = logging.getLogger(__name__)


class FitBitData():

    def __init__(self, input_file, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.DEBUG)

        self.input_file = input_file

    @classmethod
    def map_identity(cls, english_units, value):
        return value

    @classmethod
    def map_date(cls, english_units, date_string):
        try:
            return datetime.datetime.strptime(date_string, "%Y-%m-%d").date()
        except Exception as e:
            return None

    @classmethod
    def map_time(cls, english_units, time_string):
        try:
            return datetime.datetime.strptime(time_string, "%M:%S").time()
        except Exception as e:
            return None

    @classmethod
    def map_meters(cls, english_units, meters):
        if english_units:
            return float(meters) * 3.28084
        return meters

    @classmethod
    def map_kgs(cls, english_units, meters):
        if english_units:
            return float(meters) * 2.20462
        return meters

    @classmethod
    def convert_cols(cls, english_units, csv_col_dict):
        cols_map = {
            'sleep-minutesAwake': ('awake_mins', FitBitData.map_identity),
            'activities-caloriesBMR': ('calories_bmr', FitBitData.map_identity),
            'sleep-minutesToFallAsleep': ('to_fall_asleep_mins', FitBitData.map_identity),
            'activities-floors': ('floors', FitBitData.map_identity),
            'activities-steps': ('steps', FitBitData.map_identity),
            'activities-distance': ('distance', FitBitData.map_identity),
            'foods-log-caloriesIn': ('calories_in', FitBitData.map_identity),
            'activities-activityCalories': ('activities_calories', FitBitData.map_identity),
            'sleep-minutesAfterWakeup': ('after_wakeup_mins', FitBitData.map_identity),
            'activities-minutesFairlyActive': ('fairly_active_mins', FitBitData.map_identity),
            'sleep-efficiency': ('sleep_efficiency', FitBitData.map_identity),
            'sleep-timeInBed': ('in_bed_mins', FitBitData.map_identity),
            'activities-minutesVeryActive': ('very_active_mins', FitBitData.map_identity),
            'body-weight': ('weight', FitBitData.map_kgs),
            'activities-minutesSedentary': ('sedentary_mins', FitBitData.map_identity),
            'activities-elevation': ('elevation', FitBitData.map_meters),
            'activities-minutesLightlyActive': ('lightly_active_mins', FitBitData.map_identity),
            'sleep-startTime': ('sleep_start', FitBitData.map_time),
            'activities-calories': ('calories', FitBitData.map_identity),
            'foods-log-water': ('log_water', FitBitData.map_identity),
            'sleep-minutesAsleep': ('asleep_mins', FitBitData.map_identity),
            'body-bmi': ('bmi', FitBitData.map_identity),
            'dateTime': ('day', FitBitData.map_date),
            'body-fat': ('body_fat', FitBitData.map_identity),
            'sleep-awakeningsCount': ('awakenings_count', FitBitData.map_identity),
        }
        return {
            (cols_map[key][0] if key in cols_map else key) :
            (cols_map[key][1](english_units, value) if key in cols_map else value)
            for key, value in csv_col_dict.items()
        }

    def process_files(self, dbpath):
        fitbitdb = FitBitDB.FitBitDB(dbpath, self.debug)

        if self.input_file:
            logger.info("Reading file: " + self.input_file)
            with open(self.input_file) as csv_file:
                read_csv = csv.DictReader(csv_file, delimiter=',')
                for row in read_csv:
                    db_entry = self.convert_cols(self.english_units, row)
                    #print "%s  -> %s" % (repr(row), repr(db_entry))
                    FitBitDB.DaysSummary.find_or_create(fitbitdb, db_entry)



def usage(program):
    print '%s -o <dbpath> -i <inputfile> ...' % program
    sys.exit()

def main(argv):
    debug = False
    english_units = False
    input_file = None
    dbpath = None

    try:
        opts, args = getopt.getopt(argv,"ei:o:", ["trace", "english", "input_file=","dbpath="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--trace"):
            debug = True
        elif opt in ("-e", "--english"):
            english_units = True
        elif opt in ("-i", "--input_file"):
            logging.debug("Input File: %s" % arg)
            input_file = arg
        elif opt in ("-o", "--dbpath"):
            logging.debug("DB path: %s" % arg)
            dbpath = arg

    if not input_file or not dbpath:
        print "Missing arguments:"
        usage(sys.argv[0])

    fd = FitBitData(input_file, english_units, debug)
    fd.process_files(dbpath)


if __name__ == "__main__":
    main(sys.argv[1:])


