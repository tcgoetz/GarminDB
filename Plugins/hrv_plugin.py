"""Plugin for processing heart rate variance data from the IQ application Heart Monitor + HRV from fbbbrown."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
from sqlalchemy import Integer, DateTime


logger = logging.getLogger(__file__)


class hrv():
    """A GarminDb plugin for saving data from the IQ application Heart Monitor + HRV from fbbbrown."""

    _dev_fields = ['hrv_s', 'hrv_btb', 'hrv_hr', 'min_hr', 'hrv_rmssd', 'hrv_sdrr_f', 'hrv_pnn50']

    _records_tablename = 'hrv_records'
    _records_version = 1
    _records_pk = ("activity_id", "record")
    _records_cols = {
        'activity_id': Integer,
        'record': Integer,
        'timestamp': DateTime,
        'hrv_s': Integer,
        'hrv_btb': Integer,
        'hrv_hr': Integer
    }

    _sessions_tablename = 'hrv_sessions'
    _sessions_version = 1
    _sessions_pk = ("activity_id", )
    _sessions_cols = {
        'activity_id': Integer,
        'timestamp': DateTime,
        'min_hr': Integer,
        'hrv_rmssd': Integer,
        'hrv_sdrr_f': Integer,
        'hrv_sdrr_l': Integer,
        'hrv_pnn50': Integer,
        'hrv_pnn20': Integer
    }

    @classmethod
    def matches_activity(cls, fit_file):
        """Return if the filematches this plugin."""
        for dev_field in cls._dev_fields:
            if dev_field not in fit_file.dev_fields:
                logger.info("dev field %s not in %s", dev_field, fit_file.filename)
                return False
        return True

    def __init__(self, dynamic_db, act_db_class):
        """Instantiate an instance of the Hrv plugin."""
        logger.info("init_tables %s cols %r", self._records_tablename, self._records_cols)
        self.record_table_class = dynamic_db.CreateTable(self._records_tablename, act_db_class, self._records_version, self._records_pk, self._records_cols)
        logger.info("init_tables %s cols %r", self._sessions_tablename, self._sessions_cols)
        self.session_table_class = dynamic_db.CreateTable(self._sessions_tablename, act_db_class, self._sessions_version, self._sessions_pk, self._sessions_cols)

    def write_record_entry(self, activity_db_session, fit_file, activity_id, message_fields, record_num):
        """Write a record message into the plugin records table."""
        if not self.record_table_class.s_exists(activity_db_session, {'activity_id' : activity_id, 'record' : record_num}):
            record = {
                'activity_id'   : activity_id,
                'record'        : record_num,
                'timestamp'     : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'hrv_s'         : message_fields.get('dev_hrv_s'),
                'hrv_btb'       : message_fields.get('dev_hrv_btb'),
                'hrv_hr'        : message_fields.get('dev_hrv_hr'),
            }
            logger.info("writing hrv record %r for %s", record, fit_file.filename)
            activity_db_session.add(self.record_table_class(**record))

    def write_session_entry(self, activity_db_session, fit_file, activity_id, message_fields):
        """Write a session message into the plugin sessions table."""
        if not self.session_table_class.s_exists(activity_db_session, {'activity_id' : activity_id}):
            session = {
                'activity_id'   : activity_id,
                'timestamp'     : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'min_hr'        : message_fields.get('dev_min_hr'),
                'hrv_rmssd'     : message_fields.get('dev_hrv_rmssd'),
                'hrv_sdrr_f'    : message_fields.get('dev_hrv_sdrr_f'),
                'hrv_sdrr_l'    : message_fields.get('dev_hrv_sdrr_l'),
                'hrv_pnn50'     : message_fields.get('dev_hrv_pnn50'),
                'hrv_pnn20'     : message_fields.get('dev_hrv_pnn20'),
            }
            logger.info("writing hrv session %r for %s", session, fit_file.filename)
            activity_db_session.add(self.session_table_class(**session))

    def __str__(self):
        """Return a string representation of the class instance."""
        return f'hrv(tables {self._records_tablename} and {self._sessions_tablename} from dev fields {self._dev_fields})'