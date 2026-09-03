"""Class that takes a parsed sleep FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import datetime

import fitfile

from .garmindb import SleepDb, SleepEvents, SleepAssessments, Sleep
from .fit_file_processor import FitFileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class SleepFitFileProcessor(FitFileProcessor):
    """Class that takes a parsed sleep FIT file object and imports it into a database."""

    def __init__(self, db_params, debug=0):
        """
        Return a new SleepFitFileProcessor instance.

        Paramters:
        db_params (dict): database access configuration
        debug (Boolean): if True, debug logging is enabled
        """
        super().__init__(db_params, debug=debug)
        self.sleep_db = SleepDb(self.db_params, self.debug - 1)

    def write_file(self, fit_file):
        """Given a Fit File object, write all of its messages to the DB."""
        self.sleep_start = None
        self.sleep_stop = None
        self.overall_sleep_score = None
        # the duration of the current sleep event is the time from the last event, so track last events
        self.last_sleep_event = None
        self.last_sleep_level = None
        self.time_in_level = {
            fitfile.fields.SleepActivityLevel.awake : datetime.timedelta(),
            fitfile.fields.SleepActivityLevel.light_sleep : datetime.timedelta(),
            fitfile.fields.SleepActivityLevel.deep_sleep : datetime.timedelta(),
            fitfile.fields.SleepActivityLevel.rem_sleep : datetime.timedelta()
        }
        with self.garmin_db.managed_session() as self.garmin_db_session, self.sleep_db.managed_session() as self.sleep_db_session:
            self._write_message_types(fit_file, fit_file.message_types)
            if self.sleep_start is not None and self.sleep_stop is not None:
                sleep = {
                    'day'           : fit_file.utc_datetime_to_local(self.sleep_stop).replace(hour=0, minute=0, second=0, microsecond=0),
                    'start'         : fit_file.utc_datetime_to_local(self.sleep_start),
                    'end'           : fit_file.utc_datetime_to_local(self.sleep_stop),
                    'total_sleep'   : fitfile.conversions.timedelta_to_time(self.time_in_level[fitfile.fields.SleepActivityLevel.light_sleep]
                                                                            + self.time_in_level[fitfile.fields.SleepActivityLevel.deep_sleep]
                                                                            + self.time_in_level[fitfile.fields.SleepActivityLevel.rem_sleep]),
                    'deep_sleep'    : fitfile.conversions.timedelta_to_time(self.time_in_level[fitfile.fields.SleepActivityLevel.deep_sleep]),
                    'light_sleep'   : fitfile.conversions.timedelta_to_time(self.time_in_level[fitfile.fields.SleepActivityLevel.light_sleep]),
                    'rem_sleep'     : fitfile.conversions.timedelta_to_time(self.time_in_level[fitfile.fields.SleepActivityLevel.rem_sleep]),
                    'awake'         : fitfile.conversions.timedelta_to_time(self.time_in_level[fitfile.fields.SleepActivityLevel.awake]),
                    'score'         : self.overall_sleep_score
                }
                root_logger.debug("sleep summary: %r", sleep)
                Sleep.s_insert_or_update(self.sleep_db_session, sleep)

    def _write_event_entry(self, fit_file, message_fields):
        if message_fields.get('event') == fitfile.fields.Event.sleep:
            if message_fields.get('event_type') == fitfile.fields.EventType.start:
                self.sleep_start = message_fields.timestamp
                self.last_sleep_event = self.sleep_start
                root_logger.debug("sleep start event: %s", self.sleep_start)
            elif message_fields.get('event_type') == fitfile.fields.EventType.stop:
                self.sleep_stop = message_fields.timestamp
                root_logger.debug("sleep stop event: %s", self.sleep_stop)

    def _write_sleep_level_entry(self, fit_file, message_fields):
        sleep_level = message_fields.get('sleep_level')
        # don't record consecutive awake events
        if sleep_level is not fitfile.fields.SleepActivityLevel.awake or self.last_sleep_level is not fitfile.fields.SleepActivityLevel.awake:
            # don't record unmeasurable sleep events
            if sleep_level.value > fitfile.fields.SleepActivityLevel.unmeasurable.value and self.last_sleep_event:
                duration = fitfile.conversions.timedelta_to_time(message_fields.timestamp - self.last_sleep_event)
                self.time_in_level[sleep_level] += fitfile.conversions.time_to_timedelta(duration)
                sleep_event = {
                    'timestamp' : fit_file.utc_datetime_to_local(self.last_sleep_event),
                    'event'     : sleep_level.name,
                    'duration'  : duration
                }
                root_logger.debug("sleep level event: %r -> %r", message_fields, sleep_event)
                SleepEvents.s_insert_or_update(self.sleep_db_session, sleep_event)
            self.last_sleep_event = message_fields.timestamp
            self.last_sleep_level = sleep_level

    def _write_sleep_assessment_entry(self, fit_file, message_fields):
        self.overall_sleep_score = message_fields.get('overall_sleep_score')
        sleep_assessment = {
            'day'                       : fit_file.end_time.date(),
            'combined_awake_score'      : message_fields.get('combined_awake_score'),
            'awake_time_score'          : message_fields.get('awake_time_score'),
            'awakenings_count_score'    : message_fields.get('awakenings_count_score'),
            'sleep_duration_score'      : message_fields.get('sleep_duration_score'),
            'light_sleep_score'         : message_fields.get('light_sleep_score'),
            'overall_sleep_score'       : message_fields.get('overall_sleep_score'),
            'sleep_quality_score'       : message_fields.get('sleep_quality_score'),
            'sleep_recovery_score'      : message_fields.get('sleep_recovery_score'),
            'rem_sleep_score'           : message_fields.get('rem_sleep_score'),
            'sleep_restlessness_score'  : message_fields.get('sleep_restlessness_score'),
            'awakenings_count'          : message_fields.get('awakenings_count'),
        }
        logger.debug("sleep level assessment: %r -> %r", message_fields, sleep_assessment)
        SleepAssessments.s_insert_or_update(self.sleep_db_session, sleep_assessment)
