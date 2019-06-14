#!/usr/bin/env python

#
# copyright Tom Goetz
#

import sys, getopt, logging


import MSHealthDB
from import_mshealth_csv import MSHealthData, MSVaultData
from analyze_mshealth import Analyze
import GarminDBConfigManager


logging.basicConfig(filename='mshealth.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def usage(program):
    print '%s -i <inputfile>' % program
    sys.exit()

def main(argv):
    debug = False
    input_file = None
    _delete_db = False

    try:
        opts, args = getopt.getopt(argv,"hi:t", ["help", "delete_db", "trace", "input_file="])
    except getopt.GetoptError:
        print "Bad argument"
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("--delete_db"):
            logging.debug("Delete DB")
            _delete_db = True
        elif opt in ("-t", "--trace"):
            logger.info("Trace:")
            debug = True
        elif opt in ("-i", "--input_file"):
            logger.info("Input File: %s" % arg)
            input_file = arg

    root_logger = logging.getLogger()
    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    db_params_dict = GarminDBConfigManager.get_db_params()

    if _delete_db:
        MSHealthDB.MSHealthDB.delete_db(db_params_dict)
        sys.exit()

    mshealth_dir = GarminDBConfigManager.get_or_create_mshealth_dir()
    metric = GarminDBConfigManager.get_metric()

    msd = MSHealthData(input_file, mshealth_dir, db_params_dict, metric, debug)
    if msd.file_count() > 0:
        msd.process_files()

    mshv = MSVaultData(input_file, mshealth_dir, db_params_dict, metric, debug)
    if mshv.file_count() > 0:
        mshv.process_files()

    analyze = Analyze(db_params_dict)
    analyze.get_years()
    analyze.summary()


if __name__ == "__main__":
    main(sys.argv[1:])
from analyze_mshealth import Analyze


