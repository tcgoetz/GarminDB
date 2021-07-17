#!/usr/bin/env python3

"""Class running a checkup against the DB data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import logging
import argparse

from garmindb import format_version
from garmindb import Checkup


logging.basicConfig(filename='checkup.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def main(argv):
    """Run a data checkup of the user's choice."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="print the program's version", action='version', version=format_version(sys.argv[0]))
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    checks_group = parser.add_argument_group('Checks')
    checks_group.add_argument("-b", "--battery", help="Check for low battery levels.", action="store_true", default=False)
    checks_group.add_argument("-c", "--course", help="Show statistics from all workouts for a single course.", type=int, default=None)
    checks_group.add_argument("-g", "--goals", help="Run a checkup on the user\'s goals.", action="store_true", default=False)
    checks_group.add_argument("-a", "--all", help="Run a checkup on all of the the user\'s stats.", action="store_true", default=False)
    args = parser.parse_args()

    checkup = Checkup(debug=args.trace)
    if args.all or args.battery:
        checkup.battery_status()
    if args.course:
        checkup.activity_course(args.course)
    if args.all or args.goals:
        checkup.goals()


if __name__ == "__main__":
    main(sys.argv[1:])
