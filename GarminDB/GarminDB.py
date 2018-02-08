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


class FileType(GarminDB.Base, DBObject):
    __tablename__ = 'file_types'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    min_row_values = 1

    @classmethod
    def _find_query(cls, session, values_dict):
        logger.debug("%s::_find_query %s" % (cls.__name__, repr(values_dict)))
        return  session.query(cls).filter(cls.name == values_dict['name'])

    @classmethod
    def get_id(cls, db, name):
        logger.debug("%s::get_id %s" % (cls.__name__, name))
        return cls.find_or_create_id(db, {'name' : name})


class File(GarminDB.Base, DBObject):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    type_id = Column(Integer)

    _relational_mappings = {
        'type' : ('type_id', FileType.get_id)
    }
    col_translations = {
        'name' : DBObject.filename_from_pathname
    }
    min_row_values = 1

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.name == values_dict['name'])


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
