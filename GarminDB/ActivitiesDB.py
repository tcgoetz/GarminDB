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
    type = Column(String)
    #
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
    #
    cycles = Column(Float)
    #
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

    time_col = synonym("start_time")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.start_time == values_dict['start_time'])


class SportActivities(DBObject):

    id = Column(Integer, primary_key=True)
    min_row_values = 1

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.id == values_dict['id'])


class RunActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'run_activities'
    steps = Column(Integer)
    # pace in mins/mile
    avg_pace = Column(Time)
    max_pace = Column(Time)
    # steps per minute
    avg_steps_per_min = Column(Integer)
    max_steps_per_min = Column(Integer)
    # m or ft
    avg_step_length = Column(Float)
    # %
    avg_vertical_ratio = Column(Float)
    # m or ft
    avg_vertical_oscillation = Column(Float)
    # left % or left right balance
    avg_gct_balance = Column(Float)
    # ground contact time in ms
    avg_ground_contact_time = Column(Time)
    avg_stance_time_percent = Column(Float)


class WalkActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'walk_activities'
    steps = Column(Integer)
    # pace in mins/mile
    avg_pace = Column(Time)
    max_pace = Column(Time)


class PaddleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'paddle_activities'
    strokes = Column(Integer)
    # m or ft
    avg_stroke_distance = Column(Float)
    avg_strokes_per_min = Column(Float)
    max_strokes_per_min = Column(Float)


class CycleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'cycle_activities'
    strokes = Column(Integer)


class EllipticalActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'elliptical_activities'
    steps = Column(Integer)
    # kms or miles
    elliptical_distance = Column(Float)
    avg_rpm = Column(Integer)


# class StrokeActivities(ActivitiesDB.Base, DBObject):
#     __tablename__ = 'stroke_activities'

#     id = Column(Integer, primary_key=True)
#     strokes = Column(Integer)


# class RpmActivities(ActivitiesDB.Base, DBObject):
#     __tablename__ = 'rpm_activities'

#     id = Column(Integer, primary_key=True)
#     strokes = Column(Integer)
