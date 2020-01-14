"""Objects representing a database and databse objects for storing activities data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Time, ForeignKey, PrimaryKeyConstraint, desc, exists, literal_column
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

import HealthDB
import utilities


logger = logging.getLogger(__name__)


class ActivitiesDB(utilities.DB):
    """Object representing a database for storing activities data."""

    Base = declarative_base()
    db_name = 'garmin_activities'
    db_version = 12

    class _DbVersion(Base, utilities.DbVersionObject):
        pass

    def __init__(self, db_params, debug=False):
        """
        Return an instance of ActivitiesDB.

        Paramters:
            db_params (dict): Config data for accessing the database
            debug (Boolean): enable debug logging
        """
        super().__init__(db_params, debug)
        ActivitiesDB.Base.metadata.create_all(self.engine)
        self.version = ActivitiesDB._DbVersion()
        self.version.version_check(self, self.db_version)
        #
        self.tables = [Activities, ActivityLaps, ActivityRecords, ActivityRecords, StepsActivities, PaddleActivities, EllipticalActivities]
        for table in self.tables:
            self.version.table_version_check(self, table)
            if not self.version.view_version_check(self, table):
                table.delete_view(self)
        # Create or Recreate views
        StepsActivities.create_view(self)
        PaddleActivities.create_view(self)
        CycleActivities.create_view(self)
        EllipticalActivities.create_view(self)


class ActivitiesLocationSegment(utilities.DBObject):
    """Object representing a databse object for storing location segnment from an activity."""

    # degrees
    start_lat = Column(Float)
    start_long = Column(Float)
    stop_lat = Column(Float)
    stop_long = Column(Float)

    @hybrid_property
    def start_loc(self):
        """Return the starting location of activity segment as a Location instance."""
        return HealthDB.Location(self.start_lat, self.start_long)

    @start_loc.setter
    def start_loc(self, start_location):
        self.start_lat = start_location.lat_deg
        self.start_long = start_location.long_deg

    @hybrid_property
    def stop_loc(self):
        """Return the ending location of activity segment as a Location instance."""
        return HealthDB.Location(self.stop_lat, self.stop_long)

    @stop_loc.setter
    def stop_loc(self, stop_location):
        self.stop_lat = stop_location.lat_deg
        self.stop_long = stop_location.long_deg


class Activities(ActivitiesDB.Base, ActivitiesLocationSegment):
    """Class represents a databse table that contains data about recorded activities."""

    __tablename__ = 'activities'
    table_version = 3

    activity_id = Column(String, primary_key=True)
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
    # beats per minute
    avg_hr = Column(Integer)
    max_hr = Column(Integer)
    # breaths per minute
    avg_rr = Column(Float)
    max_rr = Column(Float)
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

    @classmethod
    def s_find_one(cls, session, values_dict):
        """Find a table row that matches the values in the values_dict."""
        return session.query(cls).filter(cls.activity_id == values_dict['activity_id']).one_or_none()

    def is_steps_activity(self):
        """Return if the activity is a steps based activity."""
        return self.sport in ['walking', 'running', 'hiking']

    @classmethod
    def get(cls, db, activity_id):
        """Return a single activity instance for the given id."""
        return cls.find_one(db, {'activity_id' : activity_id})

    @classmethod
    def s_get(cls, session, activity_id):
        """Return a single activity instance for the given id."""
        return session.query(cls).filter(cls.activity_id == activity_id).one_or_none()

    @classmethod
    def get_by_course_id(cls, db, course_id):
        """Return all activities records for activities with the matching course_id."""
        with db.managed_session() as session:
            return session.query(cls).filter(cls.course_id == course_id).order_by(cls.start_time).all()

    @classmethod
    def get_fastest_by_course_id(cls, db, course_id):
        """Return an activities record for the activity with the matching course_id with the fastest speed."""
        with db.managed_session() as session:
            return session.query(cls).filter(cls.course_id == course_id).order_by(desc(cls.avg_speed)).limit(1).one_or_none()

    @classmethod
    def get_slowest_by_course_id(cls, db, course_id):
        """Return an activities record for the activity with the matching course_id with the slowest speed."""
        with db.managed_session() as session:
            return session.query(cls).filter(cls.course_id == course_id).order_by(cls.avg_speed).limit(1).one_or_none()

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for the time range."""
        stats = {
            'activities'            : cls.s_row_count_for_period(session, start_ts, end_ts),
            'activities_calories'   : cls.s_get_col_sum(session, cls.calories, start_ts, end_ts),
            'activities_distance'   : cls.s_get_col_sum(session, cls.distance, start_ts, end_ts),
        }
        return stats


class ActivityLaps(ActivitiesDB.Base, ActivitiesLocationSegment):
    """Class that holds data for an activity lap."""

    __tablename__ = 'activity_laps'
    table_version = 3

    activity_id = Column(String, ForeignKey('activities.activity_id'))
    lap = Column(Integer)
    #
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    elapsed_time = Column(Time, nullable=False, default=datetime.time.min)
    moving_time = Column(Time, nullable=False, default=datetime.time.min)
    # kms or miles
    distance = Column(Float)
    cycles = Column(Float)
    # beats per minute
    avg_hr = Column(Integer)
    max_hr = Column(Integer)
    # breaths per minute
    avg_rr = Column(Float)
    max_rr = Column(Float)
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

    @classmethod
    def s_exists(cls, session, values_dict):
        """Return if a matching lap instance exists."""
        return session.query(exists().where(cls.activity_id == values_dict['activity_id']).where(cls.lap == values_dict['lap'])).scalar()

    @classmethod
    def s_find_one(cls, session, values_dict):
        """Find a table row that matches the values in the values_dict."""
        return session.query(cls).filter(cls.activity_id == values_dict['activity_id']).filter(cls.lap == values_dict['lap']).one_or_none()

    @classmethod
    def get(cls, db, activity_id):
        """Return all laps for the activity with id activity_id."""
        return cls.find(db, {'activity_id' : activity_id})

    @classmethod
    def s_get(cls, session, activity_id):
        """Return all laps for the activity with id activity_id."""
        return session.query(cls).filter(cls.activity_id == activity_id).all()

    @hybrid_property
    def start_loc(self):
        """Return the lap start location."""
        return HealthDB.Location(self.start_lat, self.start_long)

    @start_loc.setter
    def start_loc(self, start_location):
        self.start_lat = start_location.lat_deg
        self.start_long = start_location.long_deg


class ActivityRecords(ActivitiesDB.Base, utilities.DBObject):
    """Encapsilates record for a single point in time from an activity."""

    __tablename__ = 'activity_records'
    table_version = 3

    activity_id = Column(String, ForeignKey('activities.activity_id'))
    record = Column(Integer)
    timestamp = Column(DateTime)
    position_lat = Column(Float)    # degrees
    position_long = Column(Float)   # degrees
    distance = Column(Float)
    cadence = Column(Integer)
    altitude = Column(Float)
    hr = Column(Integer)            # beats per minute
    rr = Column(Float)              # breaths per minute
    altitude = Column(Float)        # feet or meters
    speed = Column(Float)           # kmph or mph
    temperature = Column(Float)     # C or F

    __table_args__ = (
        PrimaryKeyConstraint("activity_id", "record"),
    )

    time_col_name = 'timestamp'

    @classmethod
    def s_exists(cls, session, values_dict):
        """Return if a matching record exists in the database."""
        return session.query(exists().where(cls.activity_id == values_dict['activity_id']).where(cls.record == values_dict['record'])).scalar()

    @classmethod
    def s_find_one(cls, session, values_dict):
        """Find a table row that matches the values in the values_dict."""
        return session.query(cls).filter(cls.activity_id == values_dict['activity_id']).filter(cls.record == values_dict['record']).one_or_none()

    @hybrid_property
    def position(self):
        """Return the location where the record was recorded."""
        return utilities.Location(self.position_lat, self.position_long)

    @position.setter
    def position(self, location):
        self.position_lat = location.lat_deg
        self.position_long = location.long_deg


class SportActivities(utilities.DBObject):
    """Base class for all sport based activity tables."""

    match_col_names = ['activity_id']

    @declared_attr
    def activity_id(cls):
        return Column(String, ForeignKey(Activities.activity_id), primary_key=True)

    @declared_attr
    def activity(cls):
        return relationship("Activities")

    @classmethod
    def _create_activity_view(cls, db, selectable):
        view_name = cls._get_default_view_name()
        logger.info("Creating activity view %s if needed.", view_name)
        cls.create_join_view(db, view_name, selectable, Activities, order_by=Activities.start_time.desc())

    @classmethod
    def _create_sport_view(cls, db, selectable, sport):
        filter = literal_column(f'{Activities.sport} == "{sport}"')
        cls.create_join_view(db, f'{sport}_activities_view', selectable, Activities, filter, Activities.start_time.desc())

    @classmethod
    def _create_course_view(cls, db, selectable, course_id):
        filter = literal_column(f'{Activities.course_id} == {course_id}')
        cls.create_join_view(db, f'course_{course_id}_view', selectable, Activities, filter, Activities.start_time.desc())

    @classmethod
    def create_view(cls, db):
        cls._create_activity_view(db, cls._view_selectable())

    @classmethod
    def get(cls, db, activity_id):
        return cls.find_one(db, {'activity_id' : activity_id})

    @classmethod
    def google_map_loc(cls, label):
        """Return a literal column composed of a google map URL for either the start or stop location off the activity."""
        return literal_column(utilities.Location.google_maps_url('activities.%s_lat' % label, 'activities.%s_long' % label) + ' AS %s_loc' % label)


class StepsActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'steps_activities'
    table_version = 3
    view_version = 5

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
    def _view_selectable(cls, include_sport=False, include_subsport=False, include_type=False, include_course=False, include_rr=False,
                         include_running_dynamics=False):
        # The query fails to genarate sql when using the func.round clause.
        selectable = [
            Activities.activity_id.label('activity_id'),
            Activities.name.label('name'),
            Activities.description.label('description')
        ]
        if include_sport:
            selectable.append(Activities.sport.label('sport'))
        if include_subsport:
            selectable.append(Activities.sub_sport.label('sub_sport'))
        if include_type:
            selectable.append(Activities.type.label('type'))
        if include_course:
            selectable.append(Activities.course_id.label('course_id'))
        selectable += [
            Activities.start_time.label('start_time'),
            Activities.stop_time.label('stop_time'),
            Activities.elapsed_time.label('elapsed_time'),
            cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
            cls.steps.label('steps'),
            cls.avg_pace .label('avg_pace'),
            cls.avg_moving_pace.label('avg_moving_pace'),
            cls.max_pace.label('max_pace'),
            cls.round_col(cls.__tablename__ + '.avg_steps_per_min', 'avg_steps_per_min'),
            cls.round_col(cls.__tablename__ + '.max_steps_per_min', 'max_steps_per_min'),
            Activities.avg_hr.label('avg_hr'),
            Activities.max_hr.label('max_hr')
        ]
        if include_rr:
            selectable += [Activities.avg_rr.label('avg_rr'), Activities.max_rr.label('max_rr')]
        selectable += [
            Activities.calories.label('calories'),
            cls.round_col(Activities.__tablename__ + '.avg_temperature', 'avg_temperature'),
            cls.round_col(Activities.__tablename__ + '.avg_speed', 'avg_speed'),
            cls.round_col(Activities.__tablename__ + '.max_speed', 'max_speed'),
            cls.round_col(cls.__tablename__ + '.avg_step_length', 'avg_step_length'),
        ]
        if include_running_dynamics:
            selectable += [
                cls.round_col(cls.__tablename__ + '.avg_vertical_ratio', 'avg_vertical_ratio'),
                cls.avg_gct_balance.label('avg_gct_balance'),
                cls.round_col(cls.__tablename__ + '.avg_vertical_oscillation', 'avg_vertical_oscillation'),
                cls.avg_ground_contact_time.label('avg_ground_contact_time'),
                cls.avg_stance_time_percent.label('avg_stance_time_percent')
            ]
        selectable += [
            cls.vo2_max.label('vo2_max'),
            Activities.training_effect.label('training_effect'),
            Activities.anaerobic_training_effect.label('anaerobic_training_effect'),
            cls.google_map_loc('start'),
            cls.google_map_loc('stop')
        ]
        return selectable

    @classmethod
    def create_view(cls, db):
        cls._create_activity_view(db, cls._view_selectable(include_sport=True, include_subsport=True, include_type=True, include_course=True))
        cls._create_sport_view(db, cls._view_selectable(), "walking")
        cls._create_sport_view(db, cls._view_selectable(include_course=True, include_subsport=True, include_rr=True,
                                                        include_running_dynamics=True), "running")
        cls._create_sport_view(db, cls._view_selectable(), "hiking")

    @classmethod
    def create_course_view(cls, db, course_id):
        # The query fails to genarate sql when using the func.round clause.
        selectable = [
            Activities.activity_id.label('activity_id'),
            Activities.name.label('name'),
            Activities.description.label('description'),
            Activities.sport.label('sport'),
            Activities.sub_sport.label('sub_sport'),
            Activities.start_time.label('start_time'),
            Activities.stop_time.label('stop_time'),
            Activities.elapsed_time.label('elapsed_time'),
            cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
            cls.steps.label('steps'),
            cls.avg_pace .label('avg_pace'),
            cls.avg_moving_pace.label('avg_moving_pace'),
            cls.max_pace.label('max_pace'),
            cls.round_col(cls.__tablename__ + '.avg_steps_per_min', 'avg_steps_per_min'),
            cls.round_col(cls.__tablename__ + '.max_steps_per_min', 'max_steps_per_min'),
            Activities.avg_hr.label('avg_hr'),
            Activities.max_hr.label('max_hr'),
            Activities.avg_rr.label('avg_rr'),
            Activities.max_rr.label('max_rr'),
            Activities.calories.label('calories'),
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
            Activities.anaerobic_training_effect.label('anaerobic_training_effect')
        ]
        cls._create_course_view(db, selectable, course_id)


class PaddleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'paddle_activities'
    table_version = 2
    view_version = 5

    strokes = Column(Integer)
    # m or ft
    avg_stroke_distance = Column(Float)

    @classmethod
    def _view_selectable(cls):
        return [
            Activities.activity_id.label('activity_id'),
            Activities.name.label('name'),
            Activities.description.label('description'),
            Activities.sport.label('sport'),
            Activities.sub_sport.label('sub_sport'),
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
            cls.google_map_loc('start'),
            cls.google_map_loc('stop'),
        ]


class CycleActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'cycle_activities'
    table_version = 2
    view_version = 6

    strokes = Column(Integer)
    vo2_max = Column(Float)

    @classmethod
    def _view_selectable(cls):
        return [
            Activities.activity_id.label('activity_id'),
            Activities.name.label('name'),
            Activities.description.label('description'),
            Activities.sub_sport.label('sub_sport'),
            Activities.start_time.label('start_time'),
            Activities.stop_time.label('stop_time'),
            Activities.elapsed_time.label('elapsed_time'),
            cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
            cls.strokes.label('strokes'),
            Activities.avg_hr.label('avg_hr'),
            Activities.max_hr.label('max_hr'),
            Activities.avg_rr.label('avg_rr'),
            Activities.max_rr.label('max_rr'),
            Activities.calories.label('calories'),
            cls.round_col(Activities.__tablename__ + '.avg_temperature', 'avg_temperature'),
            Activities.avg_cadence.label('avg_rpms'),
            Activities.max_cadence.label('max_rpms'),
            cls.round_col(Activities.__tablename__ + '.avg_speed', 'avg_speed'),
            cls.round_col(Activities.__tablename__ + '.max_speed', 'max_speed'),
            cls.vo2_max.label('vo2_max'),
            Activities.training_effect.label('training_effect'),
            Activities.anaerobic_training_effect.label('anaerobic_training_effect'),
            cls.google_map_loc('start'),
            cls.google_map_loc('stop'),
        ]


class EllipticalActivities(ActivitiesDB.Base, SportActivities):
    __tablename__ = 'elliptical_activities'
    table_version = 2
    view_version = 5

    steps = Column(Integer)
    # kms or miles
    elliptical_distance = Column(Float)

    @classmethod
    def _view_selectable(cls):
        return [
            Activities.activity_id.label('activity_id'),
            Activities.name.label('name'),
            Activities.description.label('description'),
            Activities.start_time.label('start_time'),
            Activities.stop_time.label('stop_time'),
            Activities.elapsed_time.label('elapsed_time'),
            cls.steps.label('steps'),
            cls.round_col(Activities.__tablename__ + '.distance', 'distance'),
            Activities.avg_hr.label('avg_hr'),
            Activities.max_hr.label('max_hr'),
            Activities.avg_rr.label('avg_rr'),
            Activities.max_rr.label('max_rr'),
            Activities.calories.label('calories'),
            cls.round_col(Activities.__tablename__ + '.avg_cadence', 'avg_rpms'),
            cls.round_col(Activities.__tablename__ + '.max_cadence', 'max_rpms'),
            cls.round_col(Activities.__tablename__ + '.avg_speed', 'avg_speed'),
            Activities.training_effect.label('training_effect'),
            Activities.anaerobic_training_effect.label('anaerobic_training_effect')
        ]
