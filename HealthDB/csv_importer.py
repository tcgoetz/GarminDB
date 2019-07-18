"""Class for importing data from a CSV file."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import datetime
import csv


logger = logging.getLogger(__name__)


class CsvImporter(object):
    """Class for importing data from a CSV file."""

    def __init__(self, filename, cols_map, write_entry_func):
        """
        Return an instance of CsvImporter.

        Paramters:
            filename (string): name (full path) of the file to import
            cols_map (dict): A mapping of columns of the form 'source col': ('destination col', map_function)
            write_entry_func (function): Will be called once for each line of data.
        """
        self.filename = filename
        self.cols_map = cols_map
        self.write_entry_func = write_entry_func

    @classmethod
    def map_identity(cls, english_units, value):
        """Identity mapping."""
        return value

    @classmethod
    def map_integer(cls, english_units, value):
        """Map the value to an integer."""
        try:
            return int(value)
        except Exception:
            return None

    @classmethod
    def map_float(cls, english_units, value):
        """Map the value to an float."""
        try:
            return float(value)
        except Exception:
            return None

    @classmethod
    def map_ymd_date(cls, english_units, date_string):
        """Map the year-month-day string to a datetime."""
        try:
            return datetime.datetime.strptime(date_string, "%Y-%m-%d").date()
        except Exception:
            return None

    @classmethod
    def map_mdy_date(cls, english_units, date_string):
        """Map the month/day/year string to a datetime."""
        try:
            return datetime.datetime.strptime(date_string, "%m/%d/%y %H:%M")
        except Exception:
            try:
                return datetime.datetime.strptime(date_string, "%m/%d/%y")
            except Exception:
                return None

    @classmethod
    def map_time(cls, english_units, time_string):
        """Map the minutes:seconds string to a datetime.time."""
        try:
            return datetime.datetime.strptime(time_string, "%M:%S").time()
        except Exception:
            return None

    @classmethod
    def map_meters(cls, english_units, meters):
        """Map meters to feet."""
        if english_units:
            return float(meters) * 3.28084
        return float(meters)

    @classmethod
    def map_kgs(cls, english_units, kgs):
        """Map kilograms to pounds."""
        if english_units:
            return float(kgs) * 2.20462
        return float(kgs)

    def __convert_cols(self, english_units, csv_col_dict):
        return {
            (self.cols_map[key][0] if key in self.cols_map else key) :
            (self.cols_map[key][1](english_units, value) if key in self.cols_map else value) for key, value in csv_col_dict.items()
        }

    def process_file(self, english_units):
        """Import the file ito the database."""
        logger.info("Reading file: " + self.filename)
        with open(self.filename) as csv_file:
            read_csv = csv.DictReader(csv_file, delimiter=',')
            for row in read_csv:
                db_entry = self.__convert_cols(english_units, row)
                logger.debug("%r  -> %r", row, db_entry)
                self.write_entry_func(db_entry)
