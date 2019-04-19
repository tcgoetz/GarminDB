#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *

logger = logging.getLogger(__name__)


class ActivitiesDB(DB):
    Base = declarative_base()
    db_name = 'garmin_activities'
    db_version = 10

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("ActivitiesDB: %s debug: %s ", repr(db_params_dict), str(debug))
        super(ActivitiesDB, self).__init__(db_params_dict, debug)
        ActivitiesDB.Base.metadata.create_all(self.engine)
        self.version = ActivitiesDB.DbVersion()
        self.version.version_check(self, self.db_version)

        RunActivities.create_view(self)
        WalkActivities.create_view(self)
        PaddleActivities.create_view(self)
        CycleActivities.create_view(self)
        EllipticalActivities.create_view(self)


class Activities(ActivitiesDB.Base, DBObject):
    __tablename__ = 'activities'

    activity_id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    type = Column(String)
    #
    course_id = Column(Integer)
    #
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    elapsed_time = Column(Time)
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
    # C or F
    max_temperature = Column(Float)
    min_temperature = Column(Float)
    avg_temperature = Column(Float)

    training_effect = Column(Float)
    anaerobic_training_effect = Column(Float)

    time_col = synonym("start_time")
    min_row_values = 3

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.activity_id == values_dict['activity_id'])

    @classmethod
    def get_id(cls, db, activity_id):
        return cls.find_one(db, {'activity_id' : activity_id})

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'activities'            : cls.row_count_for_period(db, start_ts, end_ts),
            'activities_calories'   : cls.get_col_sum(db, cls.calories, start_ts, end_ts),
            'activities_distance'   : cls.get_col_sum(db, cls.distance, start_ts, end_ts),
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


class ActivityLaps(ActivitiesDB.Base, DBObject):
    __tablename__ = 'activity_laps'

    activity_id = Column(Integer, ForeignKey('activities.activity_id'))
    lap = Column(Integer)
    #
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    elapsed_time = Column(Time)
    moving_time = Column(Time)
    # degrees
    start_lat = Column(Float)
    start_long = Column(Float)
    stop_lat = Column(Float)
    stop_long = Column(Float)
    # kms or miles
    distance = Column(Float)
    cycles = Column(Float)
    #
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
    # C or F
    max_temperature = Column(Float)
    min_temperature = Column(Float)
    avg_temperature = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint("activity_id", "lap"),
    )

    time_col = synonym("start_time")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.activity_id == values_dict['activity_id']).filter(cls.lap == values_dict['lap'])


class ActivityRecords(ActivitiesDB.Base, DBObject):
    __tablename__ = 'activity_records'

    activity_id = Column(Integer, ForeignKey('activities.activity_id'))
    record = Column(Integer)
    timestamp = Column(DateTime)
    # degrees
    position_lat = Column(Float)
    position_long = Column(Float)
    distance = Column(Float)
    cadence = Column(Integer)
    hr = Column(Integer)
    # feet or meters
    alititude = Column(Float)
    # kmph or mph
    speed = Column(Float)
    # C or F
    temperature = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint("activity_id", "record"),
    )

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.activity_id == values_dict['activity_id']).filter(cls.record == values_dict['record'])


class SportActivities(DBObject):

    min_row_values = 1

    @declared_attr
    def activity_id(cls):
        return Column(Integer, ForeignKey(Activities.activity_id), primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.activity_id == values_dict['activity_id'])

    @classmethod
    def create_activity_view(cls, db):
        cls.create_join_view(db, cls.__tablename__ + '_view', Activities)


class RunActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'run_activities'
    steps = Column(Integer)
    # pace in mins/mile
    avg_pace = Column(Time)
    avg_moving_pace = Column(Time)
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
    # left % of left right balance
    avg_gct_balance = Column(Float)
    # ground contact time in ms
    avg_ground_contact_time = Column(Time)
    avg_stance_time_percent = Column(Float)
    vo2_max = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'activities.activity_id AS activity_id, ' +
                'activities.name AS name, ' +
                'activities.description AS description, ' +
                'activities.type AS type, ' +
                'activities.course_id AS course_id, ' +
                'activities.start_time AS start_time, ' +
                'activities.stop_time AS stop_time, ' +
                'activities.elapsed_time AS elapsed_time, ' +
                'activities.start_lat AS start_lat, ' +
                'activities.start_long AS start_long, ' +
                'activities.stop_lat AS stop_lat, ' +
                'activities.stop_long AS stop_long, ' +
                'activities.distance AS distance, ' +
                'run_activities.steps AS steps, ' +
                'run_activities.avg_pace AS avg_pace, ' +
                'run_activities.avg_moving_pace AS avg_moving_pace, ' +
                'run_activities.max_pace AS max_pace, ' +
                'run_activities.avg_steps_per_min AS avg_steps_per_min, ' +
                'run_activities.max_steps_per_min AS max_steps_per_min, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_speed AS avg_speed, ' +
                'activities.max_speed AS max_speed, ' +
                'run_activities.avg_step_length AS avg_step_length, ' +
                'run_activities.avg_vertical_ratio AS avg_vertical_ratio, ' +
                'run_activities.avg_vertical_oscillation AS avg_vertical_oscillation, ' +
                'run_activities.avg_gct_balance AS avg_gct_balance, ' +
                'run_activities.avg_ground_contact_time AS avg_ground_contact_time, ' +
                'run_activities.avg_stance_time_percent AS avg_stance_time_percent, ' +
                'run_activities.vo2_max AS vo2_max, ' +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect ' +
            'FROM run_activities JOIN activities ON activities.activity_id = run_activities.activity_id'
        )
        cls._create_view(db, view_name, query_str)


class WalkActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'walk_activities'
    steps = Column(Integer)
    # pace in mins/mile
    avg_pace = Column(Time)
    max_pace = Column(Time)
    vo2_max = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'activities.activity_id AS activity_id, ' +
                'activities.name AS name, ' +
                'activities.description AS description, ' +
                'activities.type AS type, ' +
                'activities.start_time AS start_time, ' +
                'activities.stop_time AS stop_time, ' +
                'activities.elapsed_time AS elapsed_time, ' +
                'activities.start_lat AS start_lat, ' +
                'activities.start_long AS start_long, ' +
                'activities.stop_lat AS stop_lat, ' +
                'activities.stop_long AS stop_long, ' +
                'activities.distance AS distance, ' +
                'walk_activities.steps AS steps, ' +
                'walk_activities.avg_pace AS avg_pace, ' +
                'walk_activities.max_pace AS max_pace, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_speed AS avg_speed, ' +
                'activities.max_speed AS max_speed, ' +
                'walk_activities.vo2_max AS vo2_max, ' +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect ' +
            'FROM walk_activities JOIN activities ON activities.activity_id = walk_activities.activity_id'
        )
        cls._create_view(db, view_name, query_str)


class PaddleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'paddle_activities'
    strokes = Column(Integer)
    # m or ft
    avg_stroke_distance = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'activities.activity_id AS activity_id, ' +
                'activities.name AS name, ' +
                'activities.description AS description, ' +
                'activities.type AS type, ' +
                'activities.start_time AS start_time, ' +
                'activities.stop_time AS stop_time, ' +
                'activities.elapsed_time AS elapsed_time, ' +
                'activities.start_lat AS start_lat, ' +
                'activities.start_long AS start_long, ' +
                'activities.stop_lat AS stop_lat, ' +
                'activities.stop_long AS stop_long, ' +
                'activities.distance AS distance, ' +
                'paddle_activities.strokes AS strokes, ' +
                'paddle_activities.avg_stroke_distance AS avg_stroke_distance, ' +
                'activities.avg_cadence AS avg_strokes_per_min, ' +
                'activities.max_cadence AS max_strokes_per_min, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_speed AS avg_speed, ' +
                'activities.max_speed AS max_speed, ' +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect ' +
            'FROM paddle_activities JOIN activities ON activities.activity_id = paddle_activities.activity_id'
        )
        cls._create_view(db, view_name, query_str)


class CycleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'cycle_activities'
    strokes = Column(Integer)
    vo2_max = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'activities.activity_id AS activity_id, ' +
                'activities.name AS name, ' +
                'activities.description AS description, ' +
                'activities.type AS type, ' +
                'activities.start_time AS start_time, ' +
                'activities.stop_time AS stop_time, ' +
                'activities.elapsed_time AS elapsed_time, ' +
                'activities.start_lat AS start_lat, ' +
                'activities.start_long AS start_long, ' +
                'activities.stop_lat AS stop_lat, ' +
                'activities.stop_long AS stop_long, ' +
                'activities.distance AS distance, ' +
                'cycle_activities.strokes AS strokes, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_cadence AS avg_rpms, ' +
                'activities.max_cadence AS max_rpms, ' +
                'activities.avg_speed AS avg_speed, ' +
                'activities.max_speed AS max_speed, ' +
                'cycle_activities.vo2_max AS vo2_max, ' +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect ' +
            'FROM cycle_activities JOIN activities ON activities.activity_id = cycle_activities.activity_id'
        )
        cls._create_view(db, view_name, query_str)


class EllipticalActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'elliptical_activities'
    steps = Column(Integer)
    # kms or miles
    elliptical_distance = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'activities.activity_id AS activity_id, ' +
                'activities.name AS name, ' +
                'activities.description AS description, ' +
                'activities.type AS type, ' +
                'activities.start_time AS start_time, ' +
                'activities.stop_time AS stop_time, ' +
                'activities.elapsed_time AS elapsed_time, ' +
                'elliptical_activities.steps AS steps, ' +
                'elliptical_activities.elliptical_distance AS distance, ' +
                'activities.cycles AS cycles, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_cadence AS avg_rpms, ' +
                'activities.max_cadence AS max_rpms, ' +
                'activities.avg_speed AS avg_speed, ' +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect ' +
            'FROM elliptical_activities JOIN activities ON activities.activity_id = elliptical_activities.activity_id'
        )
        cls._create_view(db, view_name, query_str)

