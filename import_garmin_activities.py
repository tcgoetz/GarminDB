#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, traceback, json, tcxparser, dateutil.parser, traceback

import Fit
import FileProcessor
from FitFileProcessor import FitFileProcessor
from JsonFileProcessor import *
import GarminDB
import GarminConnectEnums


root_logger = logging.getLogger()
logger = logging.getLogger(__file__)


def pace_to_time(pace):
    if pace is not None and pace != '--:--':
        return datetime.datetime.strptime(pace, "%M:%S").time()


class GarminFitData():

    def __init__(self, input_file, input_dir, latest, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s", str(debug), str(english_units))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, '.*\.fit')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, '.*\.fit', latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        fp = FitFileProcessor(db_params_dict, self.debug)
        for file_name in self.file_names:
            try:
                fp.write_file(Fit.File(file_name, self.english_units))
            except Exception as e:
                logger.error("Failed to parse %s: %s", file_name, str(e))
                raise


class GarminTcxData():

    def __init__(self, input_file, input_dir, latest, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s", str(debug), str(english_units))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, '.*\.tcx')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, '.*\.tcx', latest)

    def file_count(self):
        return len(self.file_names)

    def process_file(self, file_name):
        logger.info("Processing file: " + file_name)
        tcx = tcxparser.TCXParser(file_name)
        end_time = dateutil.parser.parse(tcx.completed_at, ignoretz=True)
        start_time = dateutil.parser.parse(tcx.started_at, ignoretz=True)
        manufacturer = GarminDB.Device.Manufacturer.Unknown
        product = tcx.creator
        if product is not None:
            match = re.search('Microsoft', product)
            if match:
                manufacturer = GarminDB.Device.Manufacturer.Microsoft
        serial_number = tcx.creator_version
        if serial_number is None or serial_number == 0:
            serial_number = GarminDB.Device.unknown_device_serial_number
        device = {
            'serial_number'     : serial_number,
            'timestamp'         : start_time,
            'manufacturer'      : manufacturer,
            'product'           : product,
            'hardware_version'  : None,
        }
        GarminDB.Device._create_or_update_not_none(self.garmin_db_session, device)
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(file_name)
        file = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : GarminDB.File.FileType.tcx,
            'serial_number' : serial_number,
        }
        GarminDB.File._find_or_create(self.garmin_db_session, file)
        distance = Fit.Conversions.Distance.from_meters(tcx.distance)
        ascent = Fit.Conversions.Distance.from_meters(tcx.ascent)
        descent = Fit.Conversions.Distance.from_meters(tcx.descent)
        activity = {
            'activity_id'               : file_id,
            'start_time'                : start_time,
            'stop_time'                 : end_time,
            'laps'                      : len(tcx.activity.Lap),
            # 'sport'                     : tcx.activity_type,
            'calories'                  : tcx.calories,
            'start_lat'                 : tcx.start_latitude,
            'start_long'                : tcx.start_longitude,
            'stop_lat'                  : tcx.end_latitude,
            'stop_long'                 : tcx.end_longitude,
            'distance'                  : distance.kms_or_miles(not self.english_units),
            'avg_hr'                    : tcx.hr_avg,
            'max_hr'                    : tcx.hr_max,
            'max_cadence'               : tcx.cadence_max,
            'avg_cadence'               : tcx.cadence_avg,
            #'ascent'                    : ascent.meters_or_feet(not self.english_units),
            #'descent'                   : descent.meters_or_feet(not self.english_units)
        }
        activity_not_zero = {key : value for (key,value) in activity.iteritems() if value}
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity_not_zero)

    def process_files(self, db_params_dict):
        garmin_db = GarminDB.GarminDB(db_params_dict, self.debug - 1)
        garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug)
        with garmin_db.managed_session() as self.garmin_db_session:
            with garmin_act_db.managed_session() as self.garmin_act_db_session:
                for file_name in self.file_names:
                    self.process_file(file_name)
                    self.garmin_db_session.commit()
                    self.garmin_act_db_session.commit()


class GarminJsonSummaryData(JsonFileProcessor):

    def __init__(self, db_params_dict, input_file, input_dir, latest, english_units, debug):
        super(GarminJsonSummaryData, self).__init__(input_file, input_dir, 'activity_\\d*\.json', latest, debug)
        self.english_units = english_units
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug - 1)
        self.conversions = {}

    def commit(self):
        self.garmin_act_db_session.commit()

    def process_running(self, activity_id, activity_summary):
        logger.debug("process_running for %s", activity_id)
        avg_vertical_oscillation = self.get_field_obj(activity_summary, 'avgVerticalOscillation', Fit.Conversions.Distance.from_meters)
        avg_step_length = self.get_field_obj(activity_summary, 'avgStrideLength', Fit.Conversions.Distance.from_meters)
        run = {
            'activity_id'               : activity_id,
            'steps'                     : self.get_field(activity_summary, 'steps', float),
            'avg_steps_per_min'         : self.get_field(activity_summary, 'averageRunningCadenceInStepsPerMinute', float),
            'max_steps_per_min'         : self.get_field(activity_summary, 'maxRunningCadenceInStepsPerMinute', float),
            'avg_step_length'           : avg_step_length.meters_or_feet(not self.english_units),
            'avg_gct_balance'           : self.get_field(activity_summary, 'avgGroundContactBalance', float),
            'avg_vertical_oscillation'  : avg_vertical_oscillation.meters_or_feet(not self.english_units),
            'avg_ground_contact_time'   : Fit.Conversions.ms_to_dt_time(self.get_field(activity_summary, 'avgGroundContactTime', float)),
            'vo2_max'                   : self.get_field(activity_summary, 'vO2MaxValue', float),
        }
        GarminDB.RunActivities._create_or_update_not_none(self.garmin_act_db_session, run)

    def process_treadmill_running(self, activity_id, activity_summary):
        return self.process_running(activity_id, activity_summary)

    def process_walking(self, activity_id, activity_summary):
        walk = {
            'activity_id'               : activity_id,
            'steps'                     : self.get_field(activity_summary, 'steps', float),
            'vo2_max'                   : self.get_field(activity_summary, 'vO2MaxValue', float),
        }
        GarminDB.WalkActivities._create_or_update_not_none(self.garmin_act_db_session, walk)

    def process_hiking(self, activity_id, activity_summary):
        return self.process_walking(activity_id, activity_summary)

    def process_paddling(self, activity_id, activity_summary):
        activity = {
            'activity_id'               : activity_id,
            'avg_cadence'               : self.get_field(activity_summary, 'avgStrokeCadence', float),
            'max_cadence'               : self.get_field(activity_summary, 'maxStrokeCadence', float),
        }
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity)
        avg_stroke_distance = self.get_field(activity_summary, 'avgStrokeDistance', float)
        if self.english_units:
            avg_stroke_distance = Fit.Conversions.meters_to_feet(avg_stroke_distance)
        paddle = {
            'activity_id'               : activity_id,
            'strokes'                   : self.get_field(activity_summary, 'strokes', float),
            'avg_stroke_distance'       : avg_stroke_distance,
        }
        GarminDB.PaddleActivities._create_or_update_not_none(self.garmin_act_db_session, paddle)

    def process_cycling(self, activity_id, activity_summary):
        activity = {
            'activity_id'               : activity_id,
            'avg_cadence'               : self.get_field(activity_summary, 'averageBikingCadenceInRevPerMinute', float),
            'max_cadence'               : self.get_field(activity_summary, 'maxBikingCadenceInRevPerMinute', float),
        }
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db, activity)
        ride = {
            'activity_id'               : activity_id,
            'strokes'                   : self.get_field(activity_summary, 'strokes', float),
            'vo2_max'                   : self.get_field(activity_summary, 'vO2MaxValue', float),
        }
        GarminDB.CycleActivities._create_or_update_not_none(self.garmin_act_db_session, ride)

    def process_mountain_biking(self, activity_id, activity_summary):
        return self.process_cycling(activity_id, activity_summary)

    def process_elliptical(self, activity_id, activity_summary):
        if activity_summary is not None:
            activity = {
                'activity_id'               : activity_id,
                'avg_cadence'               : self.get_field(activity_summary, 'averageRunningCadenceInStepsPerMinute', float),
                'max_cadence'               : self.get_field(activity_summary, 'maxRunningCadenceInStepsPerMinute', float),
            }
            GarminDB.Activities._create_or_update_not_none(self.garmin_act_db, activity)
            workout = {
                'activity_id'               : activity_id,
                'steps'                     : self.get_field(activity_summary, 'steps', float),
            }
            GarminDB.EllipticalActivities._create_or_update_not_none(self.garmin_act_db_session, workout)

    def process_json(self, json_data):
        activity_id = json_data['activityId']
        distance = self.get_field_obj(json_data, 'distance', Fit.Conversions.Distance.from_meters)
        ascent = self.get_field_obj(json_data, 'elevationGain', Fit.Conversions.Distance.from_meters)
        descent = self.get_field_obj(json_data, 'elevationLoss', Fit.Conversions.Distance.from_meters)
        avg_speed = self.get_field_obj(json_data, 'averageSpeed', Fit.Conversions.Speed.from_mps)
        max_speed = self.get_field_obj(json_data, 'maxSpeed', Fit.Conversions.Speed.from_mps)
        max_temperature = self.get_field_obj(json_data, 'maxTemperature', Fit.Conversions.Temperature.from_celsius)
        min_temperature = self.get_field_obj(json_data, 'minTemperature', Fit.Conversions.Temperature.from_celsius)
        event = GarminConnectEnums.Event.from_json(json_data)
        sport = GarminConnectEnums.Sport.from_json(json_data)
        sub_sport = GarminConnectEnums.Sport.subsport_from_json(json_data)
        if sport is GarminConnectEnums.Sport.top_level or sport is GarminConnectEnums.Sport.other:
            sport = sub_sport
        activity = {
            'activity_id'               : activity_id,
            'name'                      : json_data['activityName'],
            'description'               : self.get_field(json_data, 'description'),
            'type'                      : event.name,
            'sport'                     : sport.name,
            'sub_sport'                 : sub_sport.name,
            'start_time'                : dateutil.parser.parse(self.get_field(json_data, 'startTimeLocal'), ignoretz=True),
            'elapsed_time'              : Fit.Conversions.secs_to_dt_time(self.get_field(json_data, 'elapsedDuration', int)),
            'moving_time'               : Fit.Conversions.secs_to_dt_time(self.get_field(json_data, 'movingDuration', int)),
            'start_lat'                 : self.get_field(json_data, 'startLatitude', float),
            'start_long'                : self.get_field(json_data, 'startLongitude', float),
            'stop_lat'                  : self.get_field(json_data, 'endLatitude', float),
            'stop_long'                 : self.get_field(json_data, 'endLongitude', float),
            'distance'                  : distance.kms_or_miles(not self.english_units),
            'laps'                      : self.get_field(json_data, 'lapCount'),
            'avg_hr'                    : self.get_field(json_data, 'averageHR', float),
            'max_hr'                    : self.get_field(json_data, 'maxHR', float),
            'calories'                  : self.get_field(json_data, 'calories', float),
            'avg_speed'                 : avg_speed.kph_or_mph(not self.english_units),
            'max_speed'                 : max_speed.kph_or_mph(not self.english_units),
            'ascent'                    : ascent.meters_or_feet(not self.english_units),
            'descent'                   : descent.meters_or_feet(not self.english_units),
            'max_temperature'           : max_temperature.c_or_f(not self.english_units),
            'min_temperature'           : min_temperature.c_or_f(not self.english_units),
            'training_effect'           : self.get_field(json_data, 'aerobicTrainingEffect', float),
            'anaerobic_training_effect' : self.get_field(json_data, 'anaerobicTrainingEffect', float),
        }
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity)
        try:
            process_function = 'process_' + sub_sport.name
            function = getattr(self, process_function)
            function(activity_id, json_data)
        except AttributeError:
            logger.info("No sport handler %s from %s", process_function, activity_id)
        return 1

    def process(self):
        with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self.process_files()


class GarminJsonDetailsData(JsonFileProcessor):

    def __init__(self, db_params_dict, input_file, input_dir, latest, english_units, debug):
        super(GarminJsonDetailsData, self).__init__(input_file, input_dir, 'activity_details_\\d*\.json', latest, debug)
        self.english_units = english_units
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, self.debug - 1)
        self.conversions = {}

    def commit(self):
        self.garmin_act_db_session.commit()

    def process_running(self, activity_id, json_data):
        summary_dto = json_data['summaryDTO']
        avg_moving_speed_mps = summary_dto.get('averageMovingSpeed', None)
        avg_moving_speed = Fit.Conversions.mps_to_mph(avg_moving_speed_mps)
        run = {
            'activity_id'               : activity_id,
            'avg_moving_pace'           : Fit.Conversions.speed_to_pace(avg_moving_speed),
        }
        logger.info("process_running for %d: %s", activity_id, repr(run))
        GarminDB.RunActivities._create_or_update_not_none(self.garmin_act_db_session, run)

    def process_json(self, json_data):
        activity_id = json_data['activityId']
        metadata_dto = json_data['metadataDTO']
        summary_dto = json_data['summaryDTO']
        sport = GarminConnectEnums.Sport.from_details_json(json_data)
        sub_sport = GarminConnectEnums.Sport.subsport_from_details_json(json_data)
        if sport is GarminConnectEnums.Sport.top_level or sport is GarminConnectEnums.Sport.other:
            sport = sub_sport
        avg_temperature = self.get_field_obj(summary_dto, 'averageTemperature', Fit.Conversions.Temperature.from_celsius)
        activity = {
            'activity_id'               : activity_id,
            'course_id'                 : self.get_field(metadata_dto, 'associatedCourseId', int),
            'avg_temperature'           : avg_temperature.c_or_f(not self.english_units) if avg_temperature is not None else None,
        }
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity)
        try:
            process_function = 'process_' + sub_sport.name
            function = getattr(self, process_function)
            function(activity_id, json_data)
        except AttributeError:
            logger.info("No sport handler %s from %s", process_function, activity_id)
        return 1

    def process(self):
        with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self.process_files()


def usage(program):
    print '%s [-s <sqlite db path> | -m <user,password,host>] [-i <inputfile> | -d <input_dir>] ...' % program
    print '    --trace : turn on debug tracing'
    print '    --english : units - use feet, lbs, etc'
    print '    '
    sys.exit()

def main(argv):
    debug = 0
    input_dir = None
    input_file = None
    latest = False
    db_params_dict = {}

    try:
        opts, args = getopt.getopt(argv,"d:eilm::s:t:", ["trace=", "latest", "input_dir=", "input_file=", "mysql=", "sqlite="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--trace"):
            debug = int(arg)
        elif opt in ("-d", "--input_dir"):
            input_dir = arg
        elif opt in ("-i", "--input_file"):
            logging.debug("Input File: %s" % arg)
            input_file = arg
        elif opt in ("-l", "--latest"):
            latest = True
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

    garmindb = GarminDB.GarminDB(db_params_dict)
    english_units = GarminDB.Attributes.measurements_type_metric(garmindb) == False

    if not (input_file or input_dir) or len(db_params_dict) == 0:
        print "Missing arguments:"
        usage(sys.argv[0])

    gjsd = GarminJsonSummaryData(db_params_dict, input_file, input_dir, latest, english_units, debug)
    if gjsd.file_count() > 0:
        gjsd.process()

    gdjd = GarminJsonDetailsData(db_params_dict, input_file, input_dir, latest, english_units, debug)
    if gdjd.file_count() > 0:
        gdjd.process()

    gtd = GarminTcxData(input_file, input_dir, latest, english_units, debug)
    if gtd.file_count() > 0:
        gtd.process_files(db_params_dict)

    gfd = GarminFitData(input_file, input_dir, latest, english_units, debug)
    if gfd.file_count() > 0:
        gfd.process_files(db_params_dict)


if __name__ == "__main__":
    main(sys.argv[1:])


