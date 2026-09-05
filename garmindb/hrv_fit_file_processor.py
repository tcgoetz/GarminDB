"""Class that takes a parsed sleep FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys

import fitfile

from .garmindb import HrvDb, HrvValue, HrvStatusSummary
from .fit_file_processor import FitFileProcessor
from .fit_data import FitData


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class GarminHrvFitData(FitData):
    """Class for importing heart rate variance FIT files into a database."""

    def __init__(self, input_dir, latest, measurement_system, debug):
        """
        Return an instance of GarminHrvFitData.

        Parameters:
        ----------
        input_dir (string): directory (full path) to check for monitoring data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging

        """
        super().__init__(input_dir, debug, latest, True, [fitfile.FileType.hrv_status], measurement_system)


class HrvFitFileProcessor(FitFileProcessor):
    """Class that takes a parsed heart rate variance FIT file object and imports it into a database."""

    def __init__(self, db_params, debug=0):
        """
        Return a new HrvFitFileProcessor instance.

        Paramters:
        db_params (dict): database access configuration
        debug (Boolean): if True, debug logging is enabled
        """
        super().__init__(db_params, debug=debug)
        self.hrv_db = HrvDb(self.db_params, self.debug - 1)

    def write_file(self, fit_file):
        """Given a Fit File object, write all of its messages to the DB."""
        with self.garmin_db.managed_session() as self.garmin_db_session, self.hrv_db.managed_session() as self.hrv_db_session:
            self._write_message_types(fit_file, fit_file.message_types)

    def _write_hrv_value_entry(self, fit_file, message_fields):
        hrv_value = message_fields.get('hrv_value')
        if hrv_value is not None and hrv_value > 0:
            hrv_entry = {
                'timestamp': fit_file.utc_datetime_to_local(message_fields.timestamp),
                'hrv_value': hrv_value
            }
            root_logger.debug("hrv value event: %r -> %r", message_fields, hrv_entry)
            HrvValue.s_insert_or_update(self.hrv_db_session, hrv_entry)

    def _write_hrv_status_summary_entry(self, fit_file, message_fields):
        self.overall_sleep_score = message_fields.get('overall_sleep_score')
        hrv_status_summary = {
            'day'                       : message_fields['timestamp'],
            'weekly_average'            : message_fields.get('weekly_average'),
            'last_night'                : message_fields.get('last_night'),
            'last_night_average'        : message_fields.get('last_night_average'),
            'baseline_high'             : message_fields.get('baseline_high'),
            'baseline_low'              : message_fields.get('baseline_low'),
            'baseline_balanced_high'    : message_fields.get('baseline_balanced_high'),
            'baseline_balanced_low'     : message_fields.get('baseline_balanced_low'),
            'hrv_status'                : message_fields.get('hrv_status'),
            'reading_count'             : message_fields.get('reading_count'),
        }
        logger.debug("hrv status summary: %r -> %r", message_fields, hrv_status_summary)
        HrvStatusSummary.s_insert_or_update(self.hrv_db_session, hrv_status_summary)
