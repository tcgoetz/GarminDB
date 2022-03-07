"""Class that takes a parsed monitoring FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys

import fitfile

from .garmindb import SleepEvents
from .fit_file_processor import FitFileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class SleepFitFileProcessor(FitFileProcessor):
    """Class that takes a parsed sleep FIT file object and imports it into a database."""

    def write_file(self, fit_file):
        """Given a Fit File object, write all of its messages to the DB."""
        self.last_sleep_event = None
        self.last_sleep_level = None
        with self.garmin_db.managed_session() as self.garmin_db_session:
            self._write_message_types(fit_file, fit_file.message_types)

    def _write_sleep_level_entry(self, fit_file, message_fields):
        logger.debug("sleep level message: %r", message_fields)
        timestamp = fit_file.utc_datetime_to_local(message_fields.timestamp)
        sleep_level = message_fields.get('sleep_level')
        if sleep_level.value > fitfile.field_enums.SleepActivityLevel.unknown.value and self.last_sleep_event is not None and \
           (sleep_level is not fitfile.field_enums.SleepActivityLevel.awake or self.last_sleep_level is not fitfile.field_enums.SleepActivityLevel.awake):
            sleep_event = {
                'timestamp' : fit_file.utc_datetime_to_local(self.last_sleep_event),
                'event'     : sleep_level.name,
                'duration'  : fitfile.conversions.timedelta_to_time(timestamp - self.last_sleep_event)
            }
            logger.debug("sleep level event: %r", sleep_event)
            SleepEvents.s_insert_or_update(self.garmin_db_session, sleep_event)
        self.last_sleep_event = timestamp
        self.last_sleep_level = sleep_level
