#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class GarminDB(DB):
    Base = declarative_base()
    db_name = 'garmin'

    def __init__(self, db_params_dict, debug=False):
        logger.info("GarminDB: %s debug: %s " % (repr(db_params_dict), str(debug)))
        DB.__init__(self, db_params_dict, debug)
        GarminDB.Base.metadata.create_all(self.engine)


class Attributes(GarminDB.Base, KeyValueObject):
    __tablename__ = 'attributes'


class Device(GarminDB.Base, DBObject):
    __tablename__ = 'devices'

    serial_number = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    manufacturer = Column(String)
    product = Column(String)
    hardware_version = Column(String)

    min_row_values = 2
    _updateable_fields = ['hardware_version']

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.serial_number == values_dict['serial_number'])

    @classmethod
    def get(cls, db, serial_number):
        return cls.find_id(db, {'serial_number' : serial_number})


class DeviceInfo(GarminDB.Base, DBObject):
    __tablename__ = 'device_info'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    file_id = Column(Integer, ForeignKey('files.id'))
    serial_number = Column(Integer, ForeignKey('devices.serial_number'), nullable=False)
    software_version = Column(String)
    cum_operating_time = Column(Integer)
    battery_voltage = Column(String)

    min_row_values = 3

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])


def gc_id_from_path(pathname):
    return DBObject.filename_from_pathname(pathname).split('.')[0]


class File(GarminDB.Base, DBObject):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    type = Column(String)
    serial_number = Column(Integer, ForeignKey('devices.serial_number'), nullable=False)


    _col_mappings = {
        'name' : ('id', gc_id_from_path)
    }
    _col_translations = {
        'name' : DBObject.filename_from_pathname
    }
    min_row_values = 1

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.name == values_dict['name'])

    @classmethod
    def get(cls, db, name):
        return cls.find_id(db, {'name' : DBObject.filename_from_pathname(name)})


class Weight(GarminDB.Base, DBObject):
    __tablename__ = 'weight'

    timestamp = Column(DateTime, primary_key=True, unique=True)
    weight = Column(Float)

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'weight_avg' : cls.get_col_avg(db, cls.weight, start_ts, end_ts, True),
            'weight_min' : cls.get_col_min(db, cls.weight, start_ts, end_ts, True),
            'weight_max' : cls.get_col_max(db, cls.weight, start_ts, end_ts),
        }
        return stats

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        stats = cls.get_stats(db, day_ts, day_ts + datetime.timedelta(1))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        stats = cls.get_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        stats = cls.get_stats(db, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts
        return stats


class Stress(GarminDB.Base, DBObject):
    __tablename__ = 'stress'

    timestamp = Column(DateTime, primary_key=True, unique=True)
    stress = Column(Integer)

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'stress_avg' : cls.get_col_avg(db, cls.stress, start_ts, end_ts, True),
            'stress_min' : cls.get_col_min(db, cls.stress, start_ts, end_ts, True),
            'stress_max' : cls.get_col_max(db, cls.stress, start_ts, end_ts),
        }
        return stats

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        stats = cls.get_stats(db, day_ts, day_ts + datetime.timedelta(1))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        stats = cls.get_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        stats = cls.get_stats(db, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts
        return stats
