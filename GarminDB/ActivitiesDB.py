#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *

logger = logging.getLogger(__name__)


class ActivitiesDB(DB):
    Base = declarative_base()
    db_name = 'garmin_activities'
    db_version = 11
    view_version = 2

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("ActivitiesDB: %s debug: %s ", repr(db_params_dict), str(debug))
        super(ActivitiesDB, self).__init__(db_params_dict, debug)
        ActivitiesDB.Base.metadata.create_all(self.engine)
        version = ActivitiesDB.DbVersion()
        version.version_check(self, self.db_version)
        #
        db_view_version = version.version_check_key(self, 'view_version', self.view_version)
        if db_view_version != self.view_version:
            RunActivities.delete_view(self)
            WalkActivities.delete_view(self)
            PaddleActivities.delete_view(self)
            EllipticalActivities.delete_view(self)
            version.update_version(self, 'view_version', self.view_version)
        RunActivities.create_view(self)
        WalkActivities.create_view(self)
        PaddleActivities.create_view(self)
        CycleActivities.create_view(self)
        EllipticalActivities.create_view(self)


class ActivitiesLocationSegment(DBObject):
    # degrees
    start_lat = Column(Float)
    start_long = Column(Float)
    stop_lat = Column(Float)
    stop_long = Column(Float)

    @hybrid_property
    def start_loc(self):
        return Location(self.start_lat, self.start_long)

    @start_loc.setter
    def start_loc(self, start_location):
        self.start_lat = start_location.lat_deg
        self.start_long = start_location.long_deg

    @hybrid_property
    def stop_loc(self):
        return Location(self.stop_lat, self.stop_long)

    @stop_loc.setter
    def stop_loc(self, stop_location):
        self.stop_lat = stop_location.lat_deg
        self.stop_long = stop_location.long_deg


class Activities(ActivitiesDB.Base, ActivitiesLocationSegment):
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
    elapsed_time = Column(Time, nullable=False, default=datetime.time.min)
    moving_time = Column(Time, nullable=False, default=datetime.time.min)
    #
    sport = Column(String)
    sub_sport = Column(String)
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

    time_col_name = 'start_time'
    match_col_names = ['activity_id']

    @classmethod
    def get(cls, db, activity_id):
        return cls.find_one(db, {'activity_id' : activity_id})

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'activities'            : cls.row_count_for_period(db, start_ts, end_ts),
            'activities_calories'   : cls.get_col_sum(db, cls.calories, start_ts, end_ts),
            'activities_distance'   : cls.get_col_sum(db, cls.distance, start_ts, end_ts),
        }
        return stats


class ActivityLaps(ActivitiesDB.Base, ActivitiesLocationSegment):
    __tablename__ = 'activity_laps'

    activity_id = Column(Integer, ForeignKey('activities.activity_id'))
    lap = Column(Integer)
    #
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    elapsed_time = Column(Time, nullable=False, default=datetime.time.min)
    moving_time = Column(Time, nullable=False, default=datetime.time.min)
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

    time_col_name = 'start_time'
    match_col_names = ['activity_id', 'lap']

    @hybrid_property
    def start_loc(self):
        return Location(self.start_lat, self.start_long)

    @start_loc.setter
    def start_loc(self, start_location):
        self.start_lat = start_location.lat_deg
        self.start_long = start_location.long_deg


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

    time_col_name = 'timestamp'
    match_col_names = ['activity_id', 'record']

    @hybrid_property
    def position(self):
        return Location(self.position_lat, self.position_long)

    @position.setter
    def position(self, location):
        self.position_lat = location.lat_deg
        self.position_long = location.long_deg


class SportActivities(DBObject):

    match_col_names = ['activity_id']

    @declared_attr
    def activity_id(cls):
        return Column(Integer, ForeignKey(Activities.activity_id), primary_key=True)

    @classmethod
    def create_activity_view(cls, db):
        cls.create_join_view(db, cls.__tablename__ + '_view', Activities)


class RunActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'run_activities'
    steps = Column(Integer)
    # pace in mins/mile
    avg_pace = Column(Time, nullable=False, default=datetime.time.min)
    avg_moving_pace = Column(Time, nullable=False, default=datetime.time.min)
    max_pace = Column(Time, nullable=False, default=datetime.time.min)
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
    avg_ground_contact_time = Column(Time, nullable=False, default=datetime.time.min)
    avg_stance_time_percent = Column(Float)
    vo2_max = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.get_default_view_name()
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
                cls.round_col_text('activities.distance', 'distance') +
                'run_activities.steps AS steps, ' +
                'run_activities.avg_pace AS avg_pace, ' +
                'run_activities.avg_moving_pace AS avg_moving_pace, ' +
                'run_activities.max_pace AS max_pace, ' +
                'run_activities.avg_steps_per_min AS avg_steps_per_min, ' +
                'run_activities.max_steps_per_min AS max_steps_per_min, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_temperature AS avg_temperature, ' +
                cls.round_col_text('activities.avg_speed', 'avg_speed') +
                cls.round_col_text('activities.max_speed', 'max_speed') +
                cls.round_col_text('run_activities.avg_step_length', 'avg_step_length') +
                cls.round_col_text('run_activities.avg_vertical_ratio', 'avg_vertical_ratio') +
                cls.round_col_text('run_activities.avg_vertical_oscillation', 'avg_vertical_oscillation') +
                'run_activities.avg_gct_balance AS avg_gct_balance, ' +
                'run_activities.avg_ground_contact_time AS avg_ground_contact_time, ' +
                'run_activities.avg_stance_time_percent AS avg_stance_time_percent, ' +
                'run_activities.vo2_max AS vo2_max, ' +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect, ' +
                Location.google_maps_url('activities.start_lat', 'activities.start_long') + ' AS start_loc, ' +
                Location.google_maps_url('activities.stop_lat', 'activities.stop_long') + ' AS stop_loc ' +
            'FROM run_activities JOIN activities ON activities.activity_id = run_activities.activity_id ' +
            'ORDER BY activities.start_time DESC'
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)


class WalkActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'walk_activities'
    steps = Column(Integer)
    # pace in mins/mile
    avg_pace = Column(Time, nullable=False, default=datetime.time.min)
    max_pace = Column(Time, nullable=False, default=datetime.time.min)
    vo2_max = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.get_default_view_name()
        query_str = (
            'SELECT ' +
                'activities.activity_id AS activity_id, ' +
                'activities.name AS name, ' +
                'activities.description AS description, ' +
                'activities.type AS type, ' +
                'activities.start_time AS start_time, ' +
                'activities.stop_time AS stop_time, ' +
                'activities.elapsed_time AS elapsed_time, ' +
                cls.round_col_text('activities.distance', 'distance') +
                'walk_activities.steps AS steps, ' +
                'walk_activities.avg_pace AS avg_pace, ' +
                'walk_activities.max_pace AS max_pace, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_temperature AS avg_temperature, ' +
                cls.round_col_text('activities.avg_speed', 'avg_speed') +
                cls.round_col_text('activities.max_speed', 'max_speed') +
                'walk_activities.vo2_max AS vo2_max, ' +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect, ' +
                Location.google_maps_url('activities.start_lat', 'activities.start_long') + ' AS start_loc, ' +
                Location.google_maps_url('activities.stop_lat', 'activities.stop_long') + ' AS stop_loc ' +
            'FROM walk_activities JOIN activities ON activities.activity_id = walk_activities.activity_id ' +
            'ORDER BY activities.start_time DESC'
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)


class PaddleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'paddle_activities'
    strokes = Column(Integer)
    # m or ft
    avg_stroke_distance = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.get_default_view_name()
        query_str = (
            'SELECT ' +
                'activities.activity_id AS activity_id, ' +
                'activities.name AS name, ' +
                'activities.description AS description, ' +
                'activities.type AS type, ' +
                'activities.start_time AS start_time, ' +
                'activities.stop_time AS stop_time, ' +
                'activities.elapsed_time AS elapsed_time, ' +
                cls.round_col_text('activities.distance', 'distance') +
                'paddle_activities.strokes AS strokes, ' +
                cls.round_col_text('paddle_activities.avg_stroke_distance', 'avg_stroke_distance') +
                'activities.avg_cadence AS avg_strokes_per_min, ' +
                'activities.max_cadence AS max_strokes_per_min, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_temperature AS avg_temperature, ' +
                cls.round_col_text('activities.avg_speed', 'avg_speed') +
                cls.round_col_text('activities.max_speed', 'max_speed') +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect, ' +
                Location.google_maps_url('activities.start_lat', 'activities.start_long') + ' AS start_loc, ' +
                Location.google_maps_url('activities.stop_lat', 'activities.stop_long') + ' AS stop_loc ' +
            'FROM paddle_activities JOIN activities ON activities.activity_id = paddle_activities.activity_id ' +
            'ORDER BY activities.start_time DESC'
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)


class CycleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'cycle_activities'
    strokes = Column(Integer)
    vo2_max = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.get_default_view_name()
        query_str = (
            'SELECT ' +
                'activities.activity_id AS activity_id, ' +
                'activities.name AS name, ' +
                'activities.description AS description, ' +
                'activities.type AS type, ' +
                'activities.start_time AS start_time, ' +
                'activities.stop_time AS stop_time, ' +
                'activities.elapsed_time AS elapsed_time, ' +
                cls.round_col_text('activities.distance', 'distance') +
                'cycle_activities.strokes AS strokes, ' +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                'activities.avg_temperature AS avg_temperature, ' +
                'activities.avg_cadence AS avg_rpms, ' +
                'activities.max_cadence AS max_rpms, ' +
                cls.round_col_text('activities.avg_speed', 'avg_speed') +
                cls.round_col_text('activities.max_speed', 'max_speed') +
                'cycle_activities.vo2_max AS vo2_max, ' +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect, ' +
                Location.google_maps_url('activities.start_lat', 'activities.start_long') + ' AS start_loc, ' +
                Location.google_maps_url('activities.stop_lat', 'activities.stop_long') + ' AS stop_loc ' +
            'FROM cycle_activities JOIN activities ON activities.activity_id = cycle_activities.activity_id ' +
            'ORDER BY activities.start_time DESC'
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)


class EllipticalActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'elliptical_activities'
    steps = Column(Integer)
    # kms or miles
    elliptical_distance = Column(Float)

    @classmethod
    def create_view(cls, db):
        view_name = cls.get_default_view_name()
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
                cls.round_col_text('elliptical_activities.elliptical_distance', 'distance') +
                'activities.avg_hr AS avg_hr, ' +
                'activities.max_hr AS max_hr, ' +
                'activities.calories AS calories, ' +
                cls.round_col_text('activities.avg_cadence', 'avg_rpms') +
                'activities.max_cadence AS max_rpms, ' +
                cls.round_col_text('activities.avg_speed', 'avg_speed') +
                'activities.training_effect AS training_effect, ' +
                'activities.anaerobic_training_effect AS anaerobic_training_effect ' +
            'FROM elliptical_activities JOIN activities ON activities.activity_id = elliptical_activities.activity_id ' +
            'ORDER BY activities.start_time DESC'
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)
