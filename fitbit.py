#!/usr/bin/env python

#
# copyright Tom Goetz
#

import sys, getopt, logging


from import_fitbit_csv import FitBitData
from analyze_fitbit import Analyze


import GarminDBConfigManager


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

    root_logger = logging.getLogger()
    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    db_params_dict = GarminDBConfigManager.get_db_params()

    fitbit_dir = GarminDBConfigManager.get_or_create_fitbit_dir()
    metric = GarminDBConfigManager.get_metric()
    fd = FitBitData(input_file, fitbit_dir, db_params_dict, metric, debug)
    if fd.file_count() > 0:
        fd.process_files()

    analyze = Analyze(db_params_dict)
    analyze.get_years()
    analyze.summary()


if __name__ == "__main__":
    main(sys.argv[1:])
