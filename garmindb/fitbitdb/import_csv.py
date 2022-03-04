"""A script for importing CSV formatted FitBit export data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import logging
from tqdm import tqdm

from idbutils import CsvImporter
from idbutils import FileProcessor

from .fitbit_db import FitBitDb, DaysSummary


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class FitBitData():
    """A object for importing CSV formatted FitBit export data."""

    cols_map = {
        'sleep-minutesAwake': ('awake_mins', CsvImporter.map_integer),
        'activities-caloriesBMR': ('calories_bmr', CsvImporter.map_integer),
        'sleep-minutesToFallAsleep': ('to_fall_asleep_mins', CsvImporter.map_integer),
        'activities-floors': ('floors', CsvImporter.map_integer),
        'activities-steps': ('steps', CsvImporter.map_integer),
        'activities-distance': ('distance', CsvImporter.map_float),
        'foods-log-caloriesIn': ('calories_in', CsvImporter.map_integer),
        'activities-activityCalories': ('activities_calories', CsvImporter.map_integer),
        'sleep-minutesAfterWakeup': ('after_wakeup_mins', CsvImporter.map_integer),
        'activities-minutesFairlyActive': ('fairly_active_mins', CsvImporter.map_integer),
        'sleep-efficiency': ('sleep_efficiency', CsvImporter.map_integer),
        'sleep-timeInBed': ('in_bed_mins', CsvImporter.map_integer),
        'activities-minutesVeryActive': ('very_active_mins', CsvImporter.map_integer),
        'body-weight': ('weight', CsvImporter.map_kgs),
        'activities-minutesSedentary': ('sedentary_mins', CsvImporter.map_integer),
        'activities-elevation': ('elevation', CsvImporter.map_meters),
        'activities-minutesLightlyActive': ('lightly_active_mins', CsvImporter.map_integer),
        'sleep-startTime': ('sleep_start', CsvImporter.map_time),
        'activities-calories': ('calories', CsvImporter.map_integer),
        'foods-log-water': ('log_water', CsvImporter.map_float),
        'sleep-minutesAsleep': ('asleep_mins', CsvImporter.map_integer),
        'body-bmi': ('bmi', CsvImporter.map_float),
        'dateTime': ('day', CsvImporter.map_ymd_date),
        'body-fat': ('body_fat', CsvImporter.map_float),
        'sleep-awakeningsCount': ('awakenings_count', CsvImporter.map_integer),
    }

    def __init__(self, input_file, input_dir, db_params, metric, debug):
        """Return a new instance of FitBitData given the location of the data files, paramters for accessing the database, and if the data should be stored in metric units."""
        self.metric = metric
        self.fitbitdb = FitBitDb(db_params, debug)
        if input_file:
            self.file_names = FileProcessor.match_file(input_file, r'.*\.csv')
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, r'.*\.csv')

    def file_count(self):
        """Return the number of files that will be propcessed."""
        return len(self.file_names)

    def __write_entry(self, db_entry):
        DaysSummary.insert_or_update(self.fitbitdb, DaysSummary.intersection(db_entry))

    def process_files(self):
        """Import files into a database."""
        for file_name in tqdm(self.file_names, unit='files'):
            logger.info("Processing file: " + file_name)
            self.csvimporter = CsvImporter(file_name, self.cols_map, self.__write_entry)
            self.csvimporter.process_file(not self.metric)
