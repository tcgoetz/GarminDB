#!/usr/bin/env python3

"""Script for importing into a DB and summarizing CSV formatted FitBit export data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import getopt
import logging


import FitBitDB
from import_fitbit_csv import FitBitData
from analyze_fitbit import Analyze
import garmin_db_config_manager as GarminDBConfigManager


logging.basicConfig(filename='fitbit.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def usage(program):
    """Print the usage info for the script."""
    print('%s -i <inputfile> ...' % program)
    sys.exit()


def main(argv):
    """Import into a DB and summarize CSV formatted FitBit export data."""
    debug = False
    input_file = None
    _delete_db = False

    try:
        opts, args = getopt.getopt(argv, "dhi:", ["debug", "delete_db", "input_file="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("--delete_db"):
            logging.debug("Delete DB")
            _delete_db = True
        elif opt in ("-i", "--input_file"):
            logging.debug("Input File: %s" % arg)
            input_file = arg

    root_logger = logging.getLogger()
    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    db_params = GarminDBConfigManager.get_db_params()

    if _delete_db:
        FitBitDB.FitBitDB.delete_db(db_params)
        sys.exit()

    fitbit_dir = GarminDBConfigManager.get_or_create_fitbit_dir()
    metric = GarminDBConfigManager.get_metric()
    fd = FitBitData(input_file, fitbit_dir, db_params, metric, debug)
    if fd.file_count() > 0:
        fd.process_files()

    analyze = Analyze(db_params)
    analyze.get_years()
    analyze.summary()


if __name__ == "__main__":
    main(sys.argv[1:])
