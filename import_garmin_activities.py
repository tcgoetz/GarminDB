#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, traceback, json


import Fit
#import Fit.Conversions
import FitFileProcessor
import GarminDB


root_logger = logging.getLogger()
logger = logging.getLogger(__file__)


def pace_to_time(pace):
    if pace is None or pace == '--:--':
        return None
    return datetime.datetime.strptime(pace, "%M:%S").time()


class GarminFitData():

    def __init__(self, input_file, input_dir, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))

        if input_file:
            logger.info("Reading file: " + input_file)
            self.file_names = [input_file]
        if input_dir:
            logger.info("Reading directory: " + input_dir)
            self.file_names = self.dir_to_fit_files(input_dir)

    def dir_to_fit_files(self, input_dir):
        file_names = []
        for file in os.listdir(input_dir):
            match = re.search('.*\.fit', file)
            if match:
                file_names.append(input_dir + "/" + file)
        return file_names

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        fp = FitFileProcessor.FitFileProcessor(db_params_dict, self.english_units, self.debug)
        for file_name in self.file_names:
            try:
                fp.write_file(Fit.File(file_name, self.english_units))
            except ValueError as e:
                logger.info("Failed to parse %s: %s" % (file_name, str(e)))
            except IndexError as e:
                logger.info("Failed to parse %s: %s" % (file_name, str(e)))
            #sys.exit()


class GarminJsonData():

    def __init__(self, input_file, input_dir, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s" % str(debug))

        if input_file:
            logger.info("Reading file: " + input_file)
            self.file_names = [input_file]
        if input_dir:
            logger.info("Reading directory: " + input_dir)
            self.file_names = self.dir_to_json_files(input_dir)

    def dir_to_json_files(self, input_dir):
        file_names = []
        for file in os.listdir(input_dir):
            match = re.search('.*\.json', file)
            if match:
                file_names.append(input_dir + "/" + file)
        return file_names

    def file_count(self):
        return len(self.file_names)

    def get_garmin_json_data(self, json, fieldname, format_str=None, format_func=str, ):
        try:
            if format_str is None:
                return format_func(json[fieldname])
            else:
                return format_func(json[fieldname][format_str])
        except KeyError as e:
            logger.debug("JSON %s[%s] not found in %s: %s" % (fieldname, format_str, repr(json), str(e)))

    def process_running(self, activity_id, activity_summary):
        avg_vertical_oscillation = Fit.Conversions.centimeters_to_meters(self.get_garmin_json_data(activity_summary, 'WeightedMeanVerticalOscillation', 'value', float))
        avg_step_length = self.get_garmin_json_data(activity_summary, 'WeightedMeanStrideLength', 'value', float)
        if self.english_units:
            avg_vertical_oscillation = Fit.Conversions.meters_to_feet(avg_vertical_oscillation)
            avg_step_length = Fit.Conversions.meters_to_feet(avg_step_length)
        run = {
                'activity_id'               : activity_id,

                'steps'                     : self.get_garmin_json_data(activity_summary, 'SumStep', 'value', float),

                'avg_pace'                  : pace_to_time(self.get_garmin_json_data(activity_summary, 'WeightedMeanPace', 'display')),
                'avg_moving_pace'           : pace_to_time(self.get_garmin_json_data(activity_summary, 'WeightedMeanMovingPace', 'display')),
                'max_pace'                  : pace_to_time(self.get_garmin_json_data(activity_summary, 'MaxPace', 'display')),

                'avg_steps_per_min'         : self.get_garmin_json_data(activity_summary, 'WeightedMeanRunCadence', 'value', float),
                'max_steps_per_min'         : self.get_garmin_json_data(activity_summary, 'MaxRunCadence', 'value', float),

                'avg_step_length'           : avg_step_length,
                'avg_gct_balance'           : self.get_garmin_json_data(activity_summary, 'WeightedMeanGroundContactBalanceLeft', 'value', float),
                'lactate_threshold_hr'      : self.get_garmin_json_data(activity_summary, 'DirectLactateThresholdHeartRate', 'value', float),
                'avg_vertical_oscillation'  : avg_vertical_oscillation,
                'avg_ground_contact_time'   : Fit.Conversions.ms_to_dt_time(self.get_garmin_json_data(activity_summary, 'WeightedMeanGroundContactTime', 'value', float)),

                'power'                     : self.get_garmin_json_data(activity_summary, 'DirectFunctionalThresholdPower', 'value', float),
                'vo2_max'                   : self.get_garmin_json_data(activity_summary, 'DirectVO2Max', 'value', float),
        }
        GarminDB.RunActivities.create_or_update_not_none(self.garmin_act_db, run)

    def process_treadmill_running(self, activity_id, activity_summary):
        return self.process_running(activity_id, activity_summary)

    def process_walking(self, activity_id, activity_summary):
        walk = {
                'activity_id'               : activity_id,

                'steps'                     : self.get_garmin_json_data(activity_summary, 'SumStep', 'value', float),

                'avg_pace'                  : pace_to_time(self.get_garmin_json_data(activity_summary, 'WeightedMeanPace', 'display')),
                'max_pace'                  : pace_to_time(self.get_garmin_json_data(activity_summary, 'MaxPace', 'display')),

                'vo2_max'                   : self.get_garmin_json_data(activity_summary, 'DirectVO2Max', 'value', float),
        }
        GarminDB.WalkActivities.create_or_update_not_none(self.garmin_act_db, walk)

    def process_hiking(self, activity_id, activity_summary):
        return self.process_walking(activity_id, activity_summary)

    def process_paddling(self, activity_id, activity_summary):
        avg_stroke_distance = self.get_garmin_json_data(activity_summary, 'WeightedMeanStrokeDistance', 'value', float)
        if self.english_units:
            avg_stroke_distance = Fit.Conversions.meters_to_feet(avg_stroke_distance)
        paddle = {
                'activity_id'               : activity_id,

                'strokes'                   : self.get_garmin_json_data(activity_summary, 'SumStrokes', 'value', float),

                'avg_strokes_per_min'       : self.get_garmin_json_data(activity_summary, 'WeightedMeanStrokeCadence', 'value', float),
                'max_strokes_per_min'       : self.get_garmin_json_data(activity_summary, 'MaxStrokeCadence', 'value', float),

                'avg_stroke_distance'       : avg_stroke_distance,
                'power'                     : self.get_garmin_json_data(activity_summary, 'DirectFunctionalThresholdPower', 'value', float),
        }
        GarminDB.PaddleActivities.create_or_update_not_none(self.garmin_act_db, paddle)

    def process_cycling(self, activity_id, activity_summary):
        ride = {
                'activity_id'               : activity_id,

                'strokes'                   : self.get_garmin_json_data(activity_summary, 'SumStrokes', 'value', float),

                'avg_pace'                  : pace_to_time(self.get_garmin_json_data(activity_summary, 'WeightedMeanPace', 'display')),
                'avg_moving_pace'           : pace_to_time(self.get_garmin_json_data(activity_summary, 'WeightedMeanMovingPace', 'display')),
                'max_pace'                  : pace_to_time(self.get_garmin_json_data(activity_summary, 'MaxPace', 'display')),

                'avg_rpms'                  : self.get_garmin_json_data(activity_summary, 'WeightedMeanBikeCadence', 'value', float),
                'max_rpms'                  : self.get_garmin_json_data(activity_summary, 'MaxBikeCadence', 'value', float),

                'power'                     : self.get_garmin_json_data(activity_summary, 'DirectFunctionalThresholdPower', 'value', float),
                'vo2_max'                   : self.get_garmin_json_data(activity_summary, 'DirectVO2Max', 'value', float),
        }
        GarminDB.CycleActivities.create_or_update_not_none(self.garmin_act_db, ride)

    def process_mountain_biking(self, activity_id, activity_summary):
        return self.process_cycling(activity_id, activity_summary)

    def process_elliptical(self, activity_id, activity_summary):
        workout = {
                'activity_id'               : activity_id,

                'elliptical_distance'       : self.get_garmin_json_data(activity_summary, 'SumDistance', 'value', float),
                'steps'                     : self.get_garmin_json_data(activity_summary, 'SumStep', 'value', float),

                'avg_pace'                  : pace_to_time(self.get_garmin_json_data(activity_summary, 'WeightedMeanPace', 'display')),
                'max_pace'                  : pace_to_time(self.get_garmin_json_data(activity_summary, 'MaxPace', 'display')),

                'avg_rpms'                  : self.get_garmin_json_data(activity_summary, 'WeightedMeanRunCadence', 'value', float),
                'max_rpms'                  : self.get_garmin_json_data(activity_summary, 'MaxRunCadence', 'value', float),

                'power'                     : self.get_garmin_json_data(activity_summary, 'DirectFunctionalThresholdPower', 'value', float),
        }
        GarminDB.EllipticalActivities.create_or_update_not_none(self.garmin_act_db, workout)

    def process_files(self, db_params_dict):
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug)
        for file_name in self.file_names:
            json_data = json.load(open(file_name))
            activity_id = json_data['activityId']
            sub_sport = json_data['activityType']['key']
            activity_summary = json_data['activitySummary']

            activity = {
                'activity_id'               : activity_id,
                'name'                      : json_data['activityName'],
                'description'               : json_data['activityDescription'],
                'type'                      : self.get_garmin_json_data(json_data, 'eventType', 'display'),

                'start_time'                : datetime.datetime.strptime(self.get_garmin_json_data(activity_summary, 'BeginTimestamp', 'value'), "%Y-%m-%dT%H:%M:%S.%fZ"),
                'stop_time'                 : datetime.datetime.strptime(self.get_garmin_json_data(activity_summary, 'EndTimestamp', 'value'), "%Y-%m-%dT%H:%M:%S.%fZ"),

                'elapsed_time'              : Fit.Conversions.secs_to_dt_time(int(self.get_garmin_json_data(activity_summary, 'SumElapsedDuration', 'value', float))),
                'moving_time'               : Fit.Conversions.secs_to_dt_time(int(self.get_garmin_json_data(activity_summary, 'SumMovingDuration', 'value', float))),

                'sport'                     : self.get_garmin_json_data(json_data['activityType'], 'parent', 'key'),
                'sub_sport'                 : sub_sport,

                'start_lat'                 : self.get_garmin_json_data(activity_summary, 'BeginLatitude', 'value', float),
                'start_long'                : self.get_garmin_json_data(activity_summary, 'BeginLongitude', 'value', float),
                'stop_lat'                  : self.get_garmin_json_data(activity_summary, 'EndLatitude', 'value', float),
                'stop_long'                 : self.get_garmin_json_data(activity_summary, 'EndLongitude', 'value', float),

                'distance'                  : self.get_garmin_json_data(activity_summary, 'SumDistance', 'value', float),

                #'laps'                      : self.get_garmin_json_data(json_data, 'totalLaps'),

                'avg_hr'                    : self.get_garmin_json_data(activity_summary, 'WeightedMeanHeartRate', 'value', float),
                'max_hr'                    : self.get_garmin_json_data(activity_summary, 'MaxHeartRate', 'value', float),

                'calories'                  : self.get_garmin_json_data(activity_summary, 'SumEnergy', 'value', float),

                'avg_speed'                 : self.get_garmin_json_data(activity_summary, 'WeightedMeanSpeed', 'value', float),
                'avg_moving_speed'          : self.get_garmin_json_data(activity_summary, 'WeightedMeanMovingSpeed', 'value', float),
                'max_speed'                 : self.get_garmin_json_data(activity_summary, 'MaxSpeed', 'value', float),

                'ascent'                    : self.get_garmin_json_data(activity_summary, 'GainElevation', 'value', float),
                'descent'                   : self.get_garmin_json_data(activity_summary, 'LossElevation', 'value', float),

                'max_tempature'             : self.get_garmin_json_data(activity_summary, 'MaxAirTemperature', 'value', float),
                'min_tempature'             : self.get_garmin_json_data(activity_summary, 'MinAirTemperature', 'value', float),
                'avg_tempature'             : self.get_garmin_json_data(activity_summary, 'WeightedMeanAirTemperature', 'value', float),

                'training_effect'           : self.get_garmin_json_data(activity_summary, 'SumTrainingEffect', 'value', float),
                'anaerobic_training_effect' : self.get_garmin_json_data(activity_summary, 'SumAnaerobicTrainingEffect', 'value', float),
            }
            # only save not None values, don't overwrite Fit file import with None values
            activity_not_none = {key : value for (key,value) in activity.iteritems() if value is not None}
            GarminDB.Activities.create_or_update(self.garmin_act_db, activity_not_none)
            try:
                function = getattr(self, 'process_' + sub_sport)
                function(activity_id, activity_summary)
            except AttributeError:
                logger.info("No sport handler for type %s from %s" % (sub_sport, activity_id))


def usage(program):
    print '%s [-s <sqlite db path> | -m <user,password,host>] [-i <inputfile> | -d <input_dir>] ...' % program
    print '    --trace : turn on debug tracing'
    print '    --english : units - use feet, lbs, etc'
    print '    '
    sys.exit()

def main(argv):
    debug = False
    english_units = False
    input_dir = None
    input_file = None
    db_params_dict = {}

    try:
        opts, args = getopt.getopt(argv,"d:eim::s:t", ["trace", "english", "input_dir=", "input_file=", "mysql=", "sqlite="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--trace"):
            debug = True
        elif opt in ("-e", "--english"):
            english_units = True
        elif opt in ("-d", "--input_dir"):
            input_dir = arg
        elif opt in ("-i", "--input_file"):
            logging.debug("Input File: %s" % arg)
            input_file = arg
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

    if not (input_file or input_dir) or len(db_params_dict) == 0:
        print "Missing arguments:"
        usage(sys.argv[0])

    gjd = GarminJsonData(input_file, input_dir, english_units, debug)
    if gjd.file_count() > 0:
        gjd.process_files(db_params_dict)

    gd = GarminFitData(input_file, input_dir, english_units, debug)
    if gd.file_count() > 0:
        gd.process_files(db_params_dict)


if __name__ == "__main__":
    main(sys.argv[1:])


