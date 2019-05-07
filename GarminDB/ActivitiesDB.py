#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *
from ExtraData import *


logger = logging.getLogger(__name__)


class ActivitiesDB(DB):
    Base = declarative_base()
    db_name = 'garmin_activities'
    db_version = 11
    view_version = 3

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

    @declared_attr
    def activity(cls):
        return relationship("Activities")

    @classmethod
    def create_activity_view(cls, db, selectable):
        cls.create_join_view(db, cls.get_default_view_name(), selectable, Activities, Activities.start_time.desc())


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
        # The query fails to genarate sql when using the func.round clause.
        cls.create_activity_view(db,
            [
                Activities.activity_id.label('activity_id'),
                Activities.name.label('name'),
                Activities.description.label('description'),
                Activities.type.label('type'),
                Activities.course_id.label('course_id'),
                Activities.start_time.label('start_time'),
                Activities.stop_time.label('stop_time'),
                Activities.elapsed_time.label('elapsed_time'),
                # func.round(Activities.distance).label('distance'),
                cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
                cls.steps.label('steps'),
                cls.avg_pace .label('avg_pace'),
                cls.avg_moving_pace.label('avg_moving_pace'),
                cls.max_pace.label('max_pace'),
                cls.avg_steps_per_min.label('avg_steps_per_min'),
                cls.max_steps_per_min.label('max_steps_per_min'),
                Activities.avg_hr.label('avg_hr'),
                Activities.max_hr.label('max_hr'),
                Activities.calories.label('calories'),
                # func.round(Activities.avg_temperature).label('avg_temperature'),
                # func.round(Activities.avg_speed).label('avg_speed'),
                # func.round(Activities.max_speed).label('max_speed'),
                # func.round(cls.avg_step_length).label('avg_step_length'),
                # func.round(cls.avg_vertical_ratio).label('avg_vertical_ratio'),
                # func.round(cls.avg_vertical_oscillation).label('avg_vertical_oscillation'),
                cls.round_col(Activities.__tablename__ + '.avg_temperature', 'avg_temperature'),
                cls.round_col(Activities.__tablename__ + '.avg_speed', 'avg_speed'),
                cls.round_col(Activities.__tablename__ + '.max_speed', 'max_speed'),
                cls.round_col(cls.__tablename__ + '.avg_step_length', 'avg_step_length'),
                cls.round_col(cls.__tablename__ + '.avg_vertical_ratio', 'avg_vertical_ratio'),
                cls.avg_gct_balance.label('avg_gct_balance'),
                cls.round_col(cls.__tablename__ + '.avg_vertical_oscillation', 'avg_vertical_oscillation'),
                cls.avg_ground_contact_time.label('avg_ground_contact_time'),
                cls.avg_stance_time_percent.label('avg_stance_time_percent'),
                cls.vo2_max.label('vo2_max'),
                Activities.training_effect.label('training_effect'),
                Activities.anaerobic_training_effect.label('anaerobic_training_effect'),
                Location.google_maps_url('activities.start_lat', 'activities.start_long') + ' AS start_loc',
                Location.google_maps_url('activities.stop_lat', 'activities.stop_long') + ' AS stop_loc',
            ]
        )


class WalkActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'walk_activities'
    steps = Column(Integer)
    # pace in mins/mile
    avg_pace = Column(Time, nullable=False, default=datetime.time.min)
    max_pace = Column(Time, nullable=False, default=datetime.time.min)
    vo2_max = Column(Float)

    @classmethod
    def create_view(cls, db):
        cls.create_activity_view(db,
            [
                Activities.activity_id.label('activity_id'),
                Activities.name.label('name'),
                Activities.description.label('description'),
                Activities.sub_sport.label('sport'),
                Activities.start_time.label('start_time'),
                Activities.stop_time.label('stop_time'),
                Activities.elapsed_time.label('elapsed_time'),
                cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
                cls.steps.label('steps'),
                cls.avg_pace .label('avg_pace'),
                cls.max_pace.label('max_pace'),
                Activities.avg_hr.label('avg_hr'),
                Activities.max_hr.label('max_hr'),
                Activities.calories.label('calories'),
                cls.round_col(Activities.__tablename__ + '.avg_temperature', 'avg_temperature'),
                cls.round_col(Activities.__tablename__ + '.avg_speed', 'avg_speed'),
                cls.round_col(Activities.__tablename__ + '.max_speed', 'max_speed'),
                cls.vo2_max.label('vo2_max'),
                Activities.training_effect.label('training_effect'),
                Activities.anaerobic_training_effect.label('anaerobic_training_effect'),
                Location.google_maps_url('activities.start_lat', 'activities.start_long') + ' AS start_loc',
                Location.google_maps_url('activities.stop_lat', 'activities.stop_long') + ' AS stop_loc'
            ]
        )


class PaddleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'paddle_activities'
    strokes = Column(Integer)
    # m or ft
    avg_stroke_distance = Column(Float)

    @classmethod
    def create_view(cls, db):
        cls.create_activity_view(db,
            [
                Activities.activity_id.label('activity_id'),
                Activities.name.label('name'),
                Activities.description.label('description'),
                Activities.type.label('type'),
                Activities.start_time.label('start_time'),
                Activities.stop_time.label('stop_time'),
                Activities.elapsed_time.label('elapsed_time'),
                cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
                cls.strokes.label('strokes'),
                cls.round_col(cls.__tablename__ + '.avg_stroke_distance', 'avg_stroke_distance'),
                Activities.avg_cadence.label('avg_cadence'),
                Activities.max_cadence.label('max_cadence'),
                Activities.avg_hr.label('avg_hr'),
                Activities.max_hr.label('max_hr'),
                Activities.calories.label('calories'),
                cls.round_col(Activities.__tablename__ + '.avg_temperature', 'avg_temperature'),
                cls.round_col(Activities.__tablename__ + '.avg_speed', 'avg_speed'),
                cls.round_col(Activities.__tablename__ + '.max_speed', 'max_speed'),
                Activities.training_effect.label('training_effect'),
                Activities.anaerobic_training_effect.label('anaerobic_training_effect'),
                Location.google_maps_url('activities.start_lat', 'activities.start_long') + ' AS start_loc',
                Location.google_maps_url('activities.stop_lat', 'activities.stop_long') + ' AS stop_loc'
            ]
        )


class CycleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'cycle_activities'
    strokes = Column(Integer)
    vo2_max = Column(Float)

    @classmethod
    def create_view(cls, db):
        cls.create_activity_view(db,
            [
                Activities.activity_id.label('activity_id'),
                Activities.name.label('name'),
                Activities.description.label('description'),
                Activities.type.label('type'),
                Activities.start_time.label('start_time'),
                Activities.stop_time.label('stop_time'),
                Activities.elapsed_time.label('elapsed_time'),
                cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
                cls.strokes.label('strokes'),
                Activities.avg_hr.label('avg_hr'),
                Activities.max_hr.label('max_hr'),
                Activities.calories.label('calories'),
                cls.round_col(Activities.__tablename__ + '.avg_temperature', 'avg_temperature'),
                Activities.avg_cadence.label('avg_rpms'),
                Activities.max_cadence.label('max_rpms'),
                cls.round_col(Activities.__tablename__ + '.avg_speed', 'avg_speed'),
                cls.round_col(Activities.__tablename__ + '.max_speed', 'max_speed'),
                cls.vo2_max.label('vo2_max'),
                Activities.training_effect.label('training_effect'),
                Activities.anaerobic_training_effect.label('anaerobic_training_effect'),
                Location.google_maps_url('activities.start_lat', 'activities.start_long') + ' AS start_loc',
                Location.google_maps_url('activities.stop_lat', 'activities.stop_long') + ' AS stop_loc'
            ]
        )


class EllipticalActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'elliptical_activities'
    steps = Column(Integer)
    # kms or miles
    elliptical_distance = Column(Float)

    @classmethod
    def create_view(cls, db):
        cls.create_activity_view(db,
            [
                Activities.activity_id.label('activity_id'),
                Activities.name.label('name'),
                Activities.description.label('description'),
                Activities.type.label('type'),
                Activities.start_time.label('start_time'),
                Activities.stop_time.label('stop_time'),
                Activities.elapsed_time.label('elapsed_time'),
                cls.steps.label('steps'),
                cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
                Activities.avg_hr.label('avg_hr'),
                Activities.max_hr.label('max_hr'),
                Activities.calories.label('calories'),
                cls.round_col(Activities.__tablename__ + '.avg_cadence', 'avg_rpms'),
                cls.round_col(Activities.__tablename__ + '.max_cadence', 'max_rpms'),
                cls.round_col(Activities.__tablename__ + '.avg_speed', 'avg_speed'),
                Activities.training_effect.label('training_effect'),
                Activities.anaerobic_training_effect.label('anaerobic_training_effect')
            ]
        )


class ActivitiesExtraData(ActivitiesDB.Base, ExtraData):
    __tablename__ = 'activities_extra_data'

    activity_id = Column(Integer, ForeignKey(Activities.activity_id), primary_key=True)

    match_col_names = ['activity_id']

