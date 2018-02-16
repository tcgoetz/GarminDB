#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, traceback


import Fit
import FitFileProcessor


root_logger = logging.getLogger()
logger = logging.getLogger(__file__)


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

    def fit_file_count(self):
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

    gd = GarminFitData(input_file, input_dir, english_units, debug)
    if gd.fit_file_count() > 0:
        gd.process_files(db_params_dict)


if __name__ == "__main__":
    main(sys.argv[1:])


