#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime

import Fit
import GarminSqlite


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)


class GarminFitData():

    def __init__(self, input_file, input_dir, english_units):
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

    def write_monitoring_info(self, db):
        monitoring_info = Fit.MonitoringInfoOutputData(self.fitfiles)
        for entry in monitoring_info.fields():
            GarminSqlite.MonitoringInfo.find_or_create(db, entry)

    def write_monitoring(self, db):
        monitoring = Fit.MonitoringOutputData(self.fitfiles)
        entries = monitoring.fields()
        for entry in entries:
            try:
                GarminSqlite.Monitoring.create(db, entry)
            except Exception as e: 
                logger.info("Exeption '%s' on entry: %s" % (str(e), repr(entry)))
        logger.info("Wrote %d entries" % len(entries))

    def write_device_data(self, db):
        device_data = Fit.DeviceOutputData(self.fitfiles)
        for entry in device_data.fields():
            GarminSqlite.Device.find_or_create(db, entry)
            GarminSqlite.DeviceInfo.find_or_create(db, entry)

    def process_files(self, database):
        db = GarminSqlite.DB(database)
        self.write_device_data(db)
        self.write_monitoring_info(db)
        self.write_monitoring(db)


def usage(program):
    print '%s -o <database> -i <inputfile> ...' % program
    sys.exit()

def main(argv):
    english_units = False
    input_dir = None
    input_file = None
    database = None

    try:
        opts, args = getopt.getopt(argv,"d:ei:o:", ["english", "input_dir=", "input_file=","database="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-e", "--english"):
            english_units = True
        elif opt in ("-d", "--input_dir"):
            input_dir = arg
        elif opt in ("-i", "--input_file"):
            logging.debug("Input File: %s" % arg)
            input_file = arg
        elif opt in ("-o", "--database"):
            logging.debug("DB file: %s" % arg)
            database = arg

    if not (input_file or input_dir) or not database:
        print "Missing arguments:"
        usage(sys.argv[0])

    gd = GarminFitData(input_file, input_dir, english_units)
    if gd.fit_file_count() > 0:
        gd.process_files(database)


if __name__ == "__main__":
    main(sys.argv[1:])


