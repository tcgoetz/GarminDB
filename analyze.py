#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime

import GarminSqlite


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)


class Analyze():

    def __init__(self, database):
        self.db = GarminSqlite.DB(database)

    def get_years(self):
        years = GarminSqlite.Monitoring.get_years(self.db)
        print "Years (%d): %s" % (len(years), str(years))

    def get_months(self, year):
        months = GarminSqlite.Monitoring.get_months(self.db, year)
        print "%s Months (%d): %s" % (year, len(months) , str(months))

    def get_days(self, year):
        days = GarminSqlite.Monitoring.get_days(self.db, year)
        first_day = days[0]
        last_day = days[-1]
        print "%s Days (%d vs %d): %s" % (year, len(days), last_day - first_day + 1, str(days))


def usage(program):
    print '%s -d <database> -m ...' % program
    sys.exit()

def main(argv):
    database = None
    years = False
    months = None
    days = None

    try:
        opts, args = getopt.getopt(argv,"d:i:m:y", ["database=", "days=", "months=", "years"])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-d", "--database"):
            logging.debug("DB file: %s" % arg)
            database = arg
        elif opt in ("-y", "--years"):
            logging.debug("Years")
            years = True
        elif opt in ("-m", "--months"):
            logging.debug("Months")
            months = arg
        elif opt in ("-d", "--days"):
            logging.debug("Days")
            days = arg

    if not database:
        print "Missing arguments:"
        usage(sys.argv[0])

    analyze = Analyze(database)
    if years:
        analyze.get_years()
    if months:
        analyze.get_months(months)
    if days:
        analyze.get_days(days)


if __name__ == "__main__":
    main(sys.argv[1:])


