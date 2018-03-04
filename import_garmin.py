#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, string, logging, datetime, traceback, json, dateutil.parser

import Fit
import FileProcessor
import FitFileProcessor
import GarminDB


root_logger = logging.getLogger()
logger = logging.getLogger(__file__)


class GarminWeightData():

    def __init__(self, input_file, input_dir, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, 'weight_.*\.json')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, 'weight_.*\.json', latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        garmindb = GarminDB.GarminDB(db_params_dict)
        def json_parser(entry):
            if 'timestamp' in entry:
                entry['timestamp'] = dateutil.parser.parse(entry['timestamp'])
            return entry
        for file_name in self.file_names:
            json_data = json.load(open(file_name), object_hook=json_parser)
            for sample in json_data:
                GarminDB.Weight.create_or_update(garmindb, sample)
            logger.info("DB updated with weight data for %s (%d)" % (str(json_data[0]['timestamp']), len(json_data)))


class GarminFitData():

    def __init__(self, input_file, input_dir, latest, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, '.*\.fit')
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, '.*\.fit', latest)

    def file_count(self):
        return len(self.file_names)

    def process_files(self, db_params_dict):
        fp = FitFileProcessor.FitFileProcessor(db_params_dict, self.english_units, self.debug)
        for file_name in self.file_names:
            fp.write_file(Fit.File(file_name, self.english_units))



def usage(program):
    print '%s [-s <sqlite db path> | -m <user,password,host>] [-i <fit_inputfile> | -d <fit_input_dir>] ...' % program
    print '    --trace : turn on debug tracing'
    print '    --english : units - use feet, lbs, etc'
    print '    '
    sys.exit()

def main(argv):
    debug = False
    english_units = False
    fit_input_dir = None
    fit_input_file = None
    weight_input_dir = None
    weight_input_file = None
    latest = False
    db_params_dict = {}

    try:
        opts, args = getopt.getopt(argv,"f:F:elm:s:tw:W:",
            ["trace", "english", "fit_input_dir=", "fit_input_file=", "latest", "mysql=", "sqlite=", "weight_input_dir=", "weight_input_file="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--trace"):
            debug = True
        elif opt in ("-e", "--english"):
            english_units = True
        elif opt in ("-f", "--fit_input_dir"):
            logging.debug("Fit input dir: %s" % arg)
            fit_input_dir = arg
        elif opt in ("-F", "--fit_input_file"):
            logging.debug("Fit input File: %s" % arg)
            fit_input_file = arg
        elif opt in ("-l", "--latest"):
            latest = True
        elif opt in ("-w", "--weight_input_dir"):
            logging.debug("Weight input dir: %s" % arg)
            weight_input_dir = arg
        elif opt in ("-W", "--weight_input_file"):
            logging.debug("Weight input file: %s" % arg)
            weight_input_file = arg
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

    if not (fit_input_file or fit_input_dir) and not (weight_input_file or weight_input_dir):
        print "Missing or incorrect arguments: Fit or weight input files or directory"
        usage(sys.argv[0])
    if len(db_params_dict) == 0:
        print "Missing or incorrect arguments: db params"
        usage(sys.argv[0])

    if weight_input_file or weight_input_dir:
        gwd = GarminWeightData(weight_input_file, weight_input_dir, latest, english_units, debug)
        if gwd.file_count() > 0:
            gwd.process_files(db_params_dict)

    if fit_input_file or fit_input_dir:
        gfd = GarminFitData(fit_input_file, fit_input_dir, latest, english_units, debug)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)


if __name__ == "__main__":
    main(sys.argv[1:])


