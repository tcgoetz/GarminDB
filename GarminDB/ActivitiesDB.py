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



class SportType(ActivitiesDB.Base, DBObject):
    __tablename__ = 'sport_type'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    min_row_values = 1

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.name == values_dict['name'])

    @classmethod
    def get_id(cls, db, name):
        return cls.find_or_create_id(db, {'name' : name})


class Activities(ActivitiesDB.Base, DBObject):
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer)
    start_time = Column(DateTime, unique=True)
    stop_time = Column(DateTime, unique=True)
    cycles = Column(Float)
    laps = Column(Integer)
    sport_type_id = Column(Integer, ForeignKey('sport_type.id'))
    avg_hr = Column(Integer)
    max_hr = Column(Integer)
    calories = Column(Integer)
    avg_cadence = Column(Integer)
    # feet per sec or meters per sec
    avg_speed = Column(Float)
    max_speed = Column(Float)
    # feet or meters
    ascent = Column(Float)
    descent = Column(Float)
    training_effect = Column(Float)
    anaerobic_training_effect = Column(Float)

    _relational_mappings = {
        'sport_type' : ('sport_type_id', SportType.get_id)
    }
    time_col = synonym("start_time")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.start_time == values_dict['start_time'])
