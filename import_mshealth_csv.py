#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, time, traceback

import csv
import MSHealthDB


logger = logging.getLogger(__name__)


class MSHealthData():

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
    def convert_cols(cls, english_units, csv_col_dict):
        cols_map = {
            'Date': ('day', MSHealthData.map_date),
            'Floors_Climbed': ('floors', MSHealthData.map_identity),
            'Steps': ('steps', MSHealthData.map_identity),
            'HR_Highest': ('hr_max', MSHealthData.map_identity),
            'HR_Lowest': ('hr_min', MSHealthData.map_identity),
            'HR_Average': ('hr_avg', MSHealthData.map_identity),
            'Calories': ('calories', MSHealthData.map_identity),
            'Active_Hours': ('active_hours', MSHealthData.map_identity),
            'Total_Seconds_All_Activities': ('activity_secs', MSHealthData.map_identity),
            'Total_Calories_All_Activities': ('activity_calories', MSHealthData.map_identity),
            'Exercise_Events': ('exercise_events', MSHealthData.map_identity),
            'Exercise_Total_Calories': ('exercise_calories', MSHealthData.map_identity),
            'Exercise_Total_Seconds': ('exercise_secs', MSHealthData.map_identity),
            'Total_Miles_Moved': ('miles_moved', MSHealthData.map_identity),
            'Sleep_Events': ('sleep_events', MSHealthData.map_identity),
            'Sleep_Total_Calories': ('sleep_calories', MSHealthData.map_identity),
            'Total_Seconds_Slept': ('sleep_secs', MSHealthData.map_identity),
            'Walk_Events': ('walk_events', MSHealthData.map_identity),
            'Walk_Total_Seconds': ('walk_secs', MSHealthData.map_identity),
            'Walk_Total_Calories': ('workout_calories', MSHealthData.map_identity),
            'Total_Miles_Walked': ('miles_walked', MSHealthData.map_identity),
            'Run_Events': ('run_ewvents', MSHealthData.map_identity),
            'Run_Total_Calories': ('run_calories', MSHealthData.map_identity),
            'Run_Total_Seconds': ('run_secs', MSHealthData.map_identity),
            'Total_Miles_Run': ('miles_run', MSHealthData.map_identity),
            'Total_Miles_Golfed': ('miles_golfed', MSHealthData.map_identity),
            'Golf_Total_Calories': ('golf_calories', MSHealthData.map_identity),
            'Golf_Events': ('golf_events', MSHealthData.map_identity),
            'Golf_Total_Seconds': ('golf_secs', MSHealthData.map_identity),
            'Total_Miles_Biked': ('miles_biked', MSHealthData.map_identity),
            'UV_Exposure_Minutes': ('uv_mins', MSHealthData.map_identity),
            'Bike_Total_Seconds': ('bike_secs', MSHealthData.map_identity),
            'Bike_Total_Calories': ('bike_calories', MSHealthData.map_identity),
            'Bike_Events': ('bike_events', MSHealthData.map_identity),
            'Guided_Workout_Events': ('guided_workout_events', MSHealthData.map_identity),
            'Guided_Workout_Total_Calories': ('guided_workout_calories', MSHealthData.map_identity),
            'Guided_Workout_Total_Seconds': ('guided_workout_secs', MSHealthData.map_identity),
        }
        return {
            (cols_map[key][0] if key in cols_map else key) :
            (cols_map[key][1](english_units, value) if key in cols_map else value)
            for key, value in csv_col_dict.items()
        }

    def process_files(self, dbpath):
        mshealthdb = MSHealthDB.MSHealthDB(dbpath, self.debug)

        if self.input_file:
            logger.info("Reading file: " + self.input_file)
            with open(self.input_file) as csv_file:
                read_csv = csv.DictReader(csv_file, delimiter=',')
                for row in read_csv:
                    db_entry = self.convert_cols(self.english_units, row)
                    #print "%s  -> %s" % (repr(row), repr(db_entry))
                    MSHealthDB.DaysSummary.find_or_create(mshealthdb, db_entry)



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

    msd = MSHealthData(input_file, english_units, debug)
    msd.process_files(dbpath)


if __name__ == "__main__":
    main(sys.argv[1:])


