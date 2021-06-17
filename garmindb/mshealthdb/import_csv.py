"""A script for importing CSV formatted Microsoft Health export data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import re
import logging
from tqdm import tqdm

from idbutils import CsvImporter
from idbutils import FileProcessor

from .mshealth_db import MSHealthDb, MSVaultWeight, DaysSummary

logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class MSHealthData(object):
    """A classs for importing CSV formatted Microsoft Health export data."""

    cols_map = {
        'Date': ('day', CsvImporter.map_ymd_date),
        'Floors_Climbed': ('floors', CsvImporter.map_identity),
        'Steps': ('steps', CsvImporter.map_integer),
        'HR_Highest': ('hr_max', CsvImporter.map_integer),
        'HR_Lowest': ('hr_min', CsvImporter.map_integer),
        'HR_Average': ('hr_avg', CsvImporter.map_integer),
        'Calories': ('calories', CsvImporter.map_integer),
        'Active_Hours': ('active_hours', CsvImporter.map_integer),
        'Total_Seconds_All_Activities': ('activity_secs', CsvImporter.map_integer),
        'Total_Calories_All_Activities': ('activity_calories', CsvImporter.map_integer),
        'Exercise_Events': ('exercise_events', CsvImporter.map_integer),
        'Exercise_Total_Calories': ('exercise_calories', CsvImporter.map_integer),
        'Exercise_Total_Seconds': ('exercise_secs', CsvImporter.map_integer),
        'Total_Miles_Moved': ('miles_moved', CsvImporter.map_float),
        'Sleep_Events': ('sleep_events', CsvImporter.map_integer),
        'Sleep_Total_Calories': ('sleep_calories', CsvImporter.map_integer),
        'Total_Seconds_Slept': ('sleep_secs', CsvImporter.map_integer),
        'Walk_Events': ('walk_events', CsvImporter.map_integer),
        'Walk_Total_Seconds': ('walk_secs', CsvImporter.map_integer),
        'Walk_Total_Calories': ('workout_calories', CsvImporter.map_integer),
        'Total_Miles_Walked': ('miles_walked', CsvImporter.map_float),
        'Run_Events': ('run_ewvents', CsvImporter.map_integer),
        'Run_Total_Calories': ('run_calories', CsvImporter.map_integer),
        'Run_Total_Seconds': ('run_secs', CsvImporter.map_integer),
        'Total_Miles_Run': ('miles_run', CsvImporter.map_float),
        'Total_Miles_Golfed': ('miles_golfed', CsvImporter.map_float),
        'Golf_Total_Calories': ('golf_calories', CsvImporter.map_integer),
        'Golf_Events': ('golf_events', CsvImporter.map_integer),
        'Golf_Total_Seconds': ('golf_secs', CsvImporter.map_integer),
        'Total_Miles_Biked': ('miles_biked', CsvImporter.map_float),
        'UV_Exposure_Minutes': ('uv_mins', CsvImporter.map_integer),
        'Bike_Total_Seconds': ('bike_secs', CsvImporter.map_integer),
        'Bike_Total_Calories': ('bike_calories', CsvImporter.map_integer),
        'Bike_Events': ('bike_events', CsvImporter.map_integer),
        'Guided_Workout_Events': ('guided_workout_events', CsvImporter.map_integer),
        'Guided_Workout_Total_Calories': ('guided_workout_calories', CsvImporter.map_integer),
        'Guided_Workout_Total_Seconds': ('guided_workout_secs', CsvImporter.map_integer),
    }

    def __init__(self, input_file, input_dir, db_params, metric, debug):
        """Return an instance of MSHealthData given an input file or files and information on the databse to put it in."""
        self.metric = metric
        self.mshealth_db = MSHealthDb(db_params, debug)
        if input_file:
            self.file_names = FileProcessor.match_file(input_file, r'Daily_Summary_.*\.csv')
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, r'Daily_Summary_.*\.csv')

    def file_count(self):
        """Return the number of files that will be processed."""
        return len(self.file_names)

    def __write_entry(self, db_entry):
        DaysSummary.insert_or_update(self.mshealth_db, db_entry)

    def process_files(self):
        """Import files into the databse."""
        for file_name in tqdm(self.file_names, unit='files'):
            logger.info("Processing file: " + file_name)
            csvimporter = CsvImporter(file_name, self.cols_map, self.__write_entry)
            csvimporter.process_file(not self.metric)


class MSVaultData(object):
    """A class for importing CSV formatted Microsoft Health Vault export data."""

    def __init__(self, input_file, input_dir, db_params, metric, debug):
        """Return an instance of MSVaultData given an input file or files and information on the databse to put it in."""
        self.metric = metric
        self.mshealth_db = MSHealthDb(db_params, debug)
        self.cols_map = {
            'Date': ('timestamp', CsvImporter.map_mdy_date),
            'Weight': ('weight', MSVaultData.__map_weight),
        }
        if input_file:
            self.file_names = FileProcessor.match_file(input_file, r'HealthVault_Weight_.*\.csv')
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, r'HealthVault_Weight_.*\.csv')

    def file_count(self):
        """Return the number of files that will be processed."""
        return len(self.file_names)

    def __write_entry(self, db_entry):
        try:
            MSVaultWeight.insert_or_update(self.mshealth_db, MSVaultWeight.intersection(db_entry))
        except Exception as e:
            logger.error('Failed to save %r to db: %s', db_entry, e)

    def process_files(self):
        """Import files into the databse."""
        for file_name in tqdm(self.file_names, unit='files'):
            logger.info("Processing file: " + file_name)
            csvimporter = CsvImporter(file_name, self.cols_map, self.__write_entry)
            csvimporter.process_file(not self.metric)

    @classmethod
    def __map_weight(cls, metric, value):
        m = re.search(r'(\d{2,3}\.\d{2}) .*', value)
        if m:
            logger.debug("Matched weight: " + m.group(1))
            return float(m.group(1))
        else:
            logger.debug("Unmatched weight: " + value)
            return None
