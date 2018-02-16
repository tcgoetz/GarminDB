#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class ActivitiesDB(DB):
    Base = declarative_base()
    db_name = 'garmin_activities'

    def __init__(self, db_params_dict, debug=False):
        logger.info("ActivitiesDB: %s debug: %s " % (repr(db_params_dict), str(debug)))
        DB.__init__(self, db_params_dict, debug)
        ActivitiesDB.Base.metadata.create_all(self.engine)


class Activities(ActivitiesDB.Base, DBObject):
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    start_time = Column(DateTime, unique=True)
    stop_time = Column(DateTime, unique=True)
    #
    time = Column(Time)
    moving_time = Column(Time)
    #
    sport = Column(String)
    sub_sport = Column(String)
    # degrees
    start_lat = Column(Float)
    start_long = Column(Float)
    stop_lat = Column(Float)
    stop_long = Column(Float)
    # kms or miles
    distance = Column(Float)
    cycles = Column(Float)
    laps = Column(Integer)
    avg_hr = Column(Integer)
    max_hr = Column(Integer)
    calories = Column(Integer)
    avg_cadence = Column(Integer)
    max_cadence = Column(Integer)
    # kmph or mph
    avg_speed = Column(Float)
    max_speed = Column(Float)
    # feet or meters
    ascent = Column(Float)
    descent = Column(Float)
    max_tempature = Column(Float)
    avg_tempature = Column(Float)
    training_effect = Column(Float)
    anaerobic_training_effect = Column(Float)

    _relational_mappings = {}
    time_col = synonym("start_time")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.start_time == values_dict['start_time'])
