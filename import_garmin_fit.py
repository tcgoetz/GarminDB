#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, traceback


import Fit
import GarminDB


logger = logging.getLogger(__file__)


class GarminFitData():

    def __init__(self, input_file, input_dir, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))

        self.fitfiles = []

        if input_file:
            logger.info("Reading file: " + input_file)
            self.fitfiles.append(Fit.File(input_file, english_units))
        if input_dir:
            logger.info("Reading directory: " + input_dir)
            file_names = self.dir_to_fit_files(input_dir)
            for file_name in file_names:
                self.fitfiles.append(Fit.File(file_name, english_units))

    def dir_to_fit_files(self, input_dir):
        file_names = []
        for file in os.listdir(input_dir):
            match = re.search('.*\.fit', file)
            if match:
                file_names.append(input_dir + "/" + file)
        return file_names

    def fit_file_count(self):
        return len(self.fitfiles)

    def write_garmin(self, garmindb, english_units):
        if english_units:
            GarminDB.Attributes.find_or_create(garmindb, {'name' : 'units', 'value' : 'english'})
        else:
            GarminSqlite.Attributes.find_or_create(garmindb, {'name' : 'units', 'value' : 'metric'})
        for file in self.fitfiles:
            GarminDB.File.find_or_create(garmindb, {'name' : file.filename, 'type' : file.type()})

    def write_monitoring_info(self, garmindb, mondb):
        monitoring_info = Fit.MonitoringInfoOutputData(self.fitfiles)
        for entry in monitoring_info.fields():
            entry['file_id'] = GarminDB.File.find_id(garmindb, {'name' : entry['filename']})
            GarminDB.MonitoringInfo.find_or_create(mondb, entry)

    def write_monitoring_entry(self, mondb, entry):
        if GarminDB.MonitoringHeartRate.matches(entry):
            GarminDB.MonitoringHeartRate.find_or_create(mondb, entry)
        elif GarminDB.MonitoringIntensityMins.matches(entry):
            GarminDB.MonitoringIntensityMins.find_or_create(mondb, entry)
        elif GarminDB.MonitoringClimb.matches(entry):
            GarminDB.MonitoringClimb.find_or_create(mondb, entry)
        else:
            GarminDB.Monitoring.find_or_create(mondb, entry)

    def write_monitoring(self, mondb):
        monitoring = Fit.MonitoringOutputData(self.fitfiles)
        entries = monitoring.fields()
        for entry in entries:
            try:
                self.write_monitoring_entry(mondb, entry)
            except ValueError as e:
                logger.info("ValueError on entry: %s" % repr(entry))
            except Exception as e:
                logger.info("Exception on entry: %s" % repr(entry))
                raise
        logger.info("Wrote %d entries" % len(entries))

    def write_device_data(self, garmindb, mondb):
        device_data = Fit.DeviceOutputData(self.fitfiles)
        for entry in device_data.fields():
            GarminDB.Device.find_or_create(mondb, entry)

            entry['file_id'] = GarminDB.File.find_id(garmindb, {'name' : entry['filename']})
            GarminDB.DeviceInfo.find_or_create(mondb, entry)

    def process_files(self, db_params_dict):
        garmindb = GarminDB.GarminDB(db_params_dict, self.debug)
        self.write_garmin(garmindb, self.english_units)

        mondb = GarminDB.MonitoringDB(db_params_dict, self.debug)
        self.write_device_data(garmindb, mondb)
        self.write_monitoring_info(garmindb, mondb)
        self.write_monitoring(mondb)


def usage(program):
    print '%s -s <sqlite db path> -i <inputfile> ...' % program
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
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not (input_file or input_dir) or len(db_params_dict) == 0:
        print "Missing arguments:"
        usage(sys.argv[0])

    gd = GarminFitData(input_file, input_dir, english_units, debug)
    if gd.fit_file_count() > 0:
        gd.process_files(db_params_dict)


if __name__ == "__main__":
    main(sys.argv[1:])


