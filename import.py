#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, traceback


import Fit
import GarminSqlite


logger = logging.getLogger(__name__)


class GarminFitData():

    def __init__(self, input_file, input_dir, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.DEBUG)

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

        logger.debug(file_names)

        return file_names

    def fit_file_count(self):
        return len(self.fitfiles)

    def write_garmin(self, garmindb, english_units):
        if english_units:
            GarminSqlite.Attributes.find_or_create(garmindb, {'name' : 'units', 'value' : 'english'})
        else:
            GarminSqlite.Attributes.find_or_create(garmindb, {'name' : 'units', 'value' : 'metric'})
        for file in self.fitfiles:
            GarminSqlite.File.find_or_create(garmindb, {'name' : file.filename, 'type' : file.type()})

    def write_monitoring_info(self, garmindb, mondb):
        monitoring_info = Fit.MonitoringInfoOutputData(self.fitfiles)
        for entry in monitoring_info.fields():
            entry['file_id'] = GarminSqlite.File.find_id(garmindb, {'name' : entry['filename']})
            GarminSqlite.MonitoringInfo.find_or_create(mondb, entry)

    def write_monitoring_entry(self, mondb, entry):
        if GarminSqlite.MonitoringHeartRate.matches(entry):
            GarminSqlite.MonitoringHeartRate.find_or_create(mondb, entry)
        elif GarminSqlite.MonitoringIntensityMins.matches(entry):
            GarminSqlite.MonitoringIntensityMins.find_or_create(mondb, entry)
        elif GarminSqlite.MonitoringClimb.matches(entry):
            GarminSqlite.MonitoringClimb.find_or_create(mondb, entry)
        else:
            GarminSqlite.Monitoring.find_or_create(mondb, entry)

    def write_monitoring(self, mondb):
        monitoring = Fit.MonitoringOutputData(self.fitfiles)
        entries = monitoring.fields()
        for entry in entries:
            try:
                self.write_monitoring_entry(mondb, entry)
            except Exception as e: 
                logger.info("Exeption on entry: %s" % repr(entry))
                raise
        logger.info("Wrote %d entries" % len(entries))

    def write_device_data(self, garmindb, mondb):
        device_data = Fit.DeviceOutputData(self.fitfiles)
        for entry in device_data.fields():
            GarminSqlite.Device.find_or_create(mondb, entry)

            entry['file_id'] = GarminSqlite.File.find_id(garmindb, {'name' : entry['filename']})
            GarminSqlite.DeviceInfo.find_or_create(mondb, entry)

    def process_files(self, dbpath):
        garmindb = GarminSqlite.GarminDB(dbpath, self.debug)
        self.write_garmin(garmindb, self.english_units)

        mondb = GarminSqlite.MonitoringDB(dbpath, self.debug)
        self.write_device_data(garmindb, mondb)
        self.write_monitoring_info(garmindb, mondb)
        self.write_monitoring(mondb)


def usage(program):
    print '%s -o <dbpath> -i <inputfile> ...' % program
    sys.exit()

def main(argv):
    debug = False
    english_units = False
    input_dir = None
    input_file = None
    dbpath = None

    try:
        opts, args = getopt.getopt(argv,"d:ei:o:", ["trace", "english", "input_dir=", "input_file=","dbpath="])
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
        elif opt in ("-o", "--dbpath"):
            logging.debug("DB path: %s" % arg)
            dbpath = arg

    if not (input_file or input_dir) or not dbpath:
        print "Missing arguments:"
        usage(sys.argv[0])

    gd = GarminFitData(input_file, input_dir, english_units, debug)
    if gd.fit_file_count() > 0:
        gd.process_files(dbpath)


if __name__ == "__main__":
    main(sys.argv[1:])


