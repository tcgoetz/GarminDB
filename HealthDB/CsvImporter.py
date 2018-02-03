#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, datetime, csv

logger = logging.getLogger(__name__)


class CsvImporter():

    def __init__(self, filename, cols_map, write_entry_func):
        self.filename = filename
        self.cols_map = cols_map
        self.write_entry_func = write_entry_func

    @classmethod
    def map_identity(cls, english_units, value):
        return value

    @classmethod
    def map_integer(cls, english_units, value):
        try:
            return int(value)
        except Exception as e:
            return None

    @classmethod
    def map_float(cls, english_units, value):
        try:
            return float(value)
        except Exception as e:
            return None

    @classmethod
    def map_ymd_date(cls, english_units, date_string):
        try:
            return datetime.datetime.strptime(date_string, "%Y-%m-%d").date()
        except Exception as e:
            return None

    @classmethod
    def map_mdy_date(cls, english_units, date_string):
        try:
            return datetime.datetime.strptime(date_string, "%m/%d/%y %H:%M")
        except Exception as e:
            try:
                return datetime.datetime.strptime(date_string, "%m/%d/%y")
            except Exception as e:
                return None

    @classmethod
    def map_time(cls, english_units, time_string):
        try:
            return datetime.datetime.strptime(time_string, "%M:%S").time()
        except Exception as e:
            return None

    @classmethod
    def map_meters(cls, english_units, meters):
        if english_units:
            return float(meters) * 3.28084
        return float(meters)

    @classmethod
    def map_kgs(cls, english_units, kgs):
        if english_units:
            return float(kgs) * 2.20462
        return float(kgs)

    def convert_cols(self, english_units, csv_col_dict):
        return {
            (self.cols_map[key][0] if key in self.cols_map else key) :
            (self.cols_map[key][1](english_units, value) if key in self.cols_map else value) for key, value in csv_col_dict.items()
        }

    def process_file(self, english_units):
        logger.info("Reading file: " + self.filename)
        with open(self.filename) as csv_file:
            read_csv = csv.DictReader(csv_file, delimiter=',')
            for row in read_csv:
                db_entry = self.convert_cols(english_units, row)
                logger.debug("%s  -> %s" % (repr(row), repr(db_entry)))
                self.write_entry_func(db_entry)
