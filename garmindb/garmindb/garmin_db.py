"""Objects representing a database and database objects for storing health data from a Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import datetime
import logging
import re
from sqlalchemy import Column, Integer, Date, DateTime, Time, Float, String, Enum, ForeignKey, func, PrimaryKeyConstraint
from sqlalchemy.ext.hybrid import hybrid_property

import fitfile
import idbutils


logger = logging.getLogger(__name__)


class GarminDbError(Exception):
    """Base exception for GarminDb exceptions"""


class GarminDbError_IdNotFound(GarminDbError):
    """File id not found"""


GarminDb = idbutils.DB.create('garmin', 14, "Database for storing health data from a Garmin device.")


class Attributes(GarminDb.Base, idbutils.KeyValueObject):
    """Object representing generic key-value data from a Garmin device."""

    __tablename__ = 'attributes'

    db = GarminDb
    table_version = 1

    @classmethod
    def measurements_type(cls, db, default=None):
        """Return the database units type (metric, statute, etc)."""
        return fitfile.field_enums.DisplayMeasure.from_string(cls.get_string(db, 'measurement_system', default))

    @classmethod
    def measurements_type_metric(cls, db):
        """Return True if the database units are metric."""
        return (cls.measurements_type(db) == fitfile.field_enums.DisplayMeasure.metric)


class Device(GarminDb.Base, idbutils.DbObject):
    """Class representing a Garmin device."""

    __tablename__ = 'devices'

    db = GarminDb
    table_version = 4
    unknown_device_serial_number = 9999999999

    Manufacturer = idbutils.derived_enum.derive('Manufacturer', fitfile.Manufacturer, {'Microsoft' : 100001, 'Unknown': 100000})

    serial_number = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    device_type = Column(String)
    manufacturer = Column(Enum(Manufacturer))
    product = Column(String)
    hardware_version = Column(String)

    @property
    def product_as_enum(self):
        """Convert the product attribute from a string to an enum and return it."""
        return fitfile.product_enum(self.manufacturer, self.product)

    @classmethod
    def local_device_serial_number(cls, serial_number, device_type):
        """Return a synthetic serial number for a sub device composed of the parent's serial number and the sub device type."""
        return '%s%06d' % (serial_number, device_type.value)


class DeviceInfo(GarminDb.Base, idbutils.DbObject):
    """Class representing a Garmin device info message from a FIT file."""

    __tablename__ = 'device_info'

    db = GarminDb
    table_version = 4
    view_version = 6

    timestamp = Column(DateTime, nullable=False)
    file_id = Column(String, ForeignKey('files.id'))
    serial_number = Column(Integer, ForeignKey('devices.serial_number'), nullable=False)
    software_version = Column(String)
    cum_operating_time = Column(Time, nullable=False, default=datetime.time.min)
    battery_status = Column(Enum(fitfile.field_enums.BatteryStatus))
    battery_voltage = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint('timestamp', 'serial_number'),
    )

    @classmethod
    def s_get_from_dict(cls, session, values_dict):
        """Return a single DeviceInfo instance for the given id."""
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp']).filter(cls.serial_number == values_dict['serial_number']).one_or_none()

    @classmethod
    def create_view(cls, db):
        """Create a database view that presents the device info data in a more user friendly way."""
        cols = [
            cls.timestamp.label('timestamp'),
            cls.file_id.label('file_id'),
            cls.serial_number.label('serial_number'),
            Device.device_type.label('device_type'),
            cls.software_version.label('software_version'),
            Device.manufacturer.label('manufacturer'),
            Device.product.label('product'),
            Device.hardware_version.label('hardware_version'),
            cls.battery_status.label('battery_status')
        ]
        cls.create_join_view(db, cls._get_default_view_name(), cols, Device, order_by=cls.timestamp.desc())


class File(GarminDb.Base, idbutils.DbObject):
    """Class representing a data file."""

    __tablename__ = 'files'

    db = GarminDb
    table_version = 3
    view_version = 4

    fit_file_types_prefix = 'fit_'
    FileType = idbutils.derived_enum.derive('FileType', fitfile.FileType, {'tcx' : 100001, 'gpx' : 100002}, fit_file_types_prefix)

    id = Column(String, primary_key=True)
    name = Column(String, unique=True)
    type = Column(Enum(FileType), nullable=False)
    serial_number = Column(Integer, ForeignKey('devices.serial_number'))

    @classmethod
    def s_get_id(cls, session, pathname):
        """Return the id of a file given it's pathname."""
        return cls.s_find_id(session, {File.name: os.path.basename(pathname)})

    @classmethod
    def create_view(cls, db):
        """Create a databse view that presents the file data in a more user friendly way."""
        cols = [
            DeviceInfo.timestamp.label('timestamp'),
            cls.id.label('activity_id'),
            cls.name.label('name'),
            cls.type.label('type'),
            Device.manufacturer.label('manufacturer'),
            Device.product.label('product'),
            Device.serial_number.label('serial_number')
        ]
        cls.create_multi_join_view(db, cls._get_default_view_name(), cols,
                                   [(Device, File.serial_number == Device.serial_number), (DeviceInfo, File.id == DeviceInfo.file_id)],
                                   DeviceInfo.timestamp.desc())

    @classmethod
    def name_and_id_from_path(cls, pathname):
        """Return the name and id of a file given it's pathname."""
        filename = os.path.basename(pathname)
        # first check for file name formats like 123456789_ACTIVITY.fit and 123456789.fit from Garmin Connect
        found = re.match(r"(\d+).*\.\w+", filename)
        if found:
            return (found.group(1), filename)
        # Check for files from a watch with names like SBK82515.FIT
        found = re.match(r"(.+)\.\w+", filename)
        if found:
            return (found.group(1), filename)
        raise GarminDbError_IdNotFound()

    @classmethod
    def id_from_path(cls, pathname):
        """Return the id of a file given it's pathname."""
        id, _ = cls.name_and_id_from_path(pathname)
        return id


class Weight(GarminDb.Base, idbutils.DbObject):
    """Class representing a weight entry."""

    __tablename__ = 'weight'

    db = GarminDb
    table_version = 1

    day = Column(Date, primary_key=True)
    weight = Column(Float, nullable=False)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'weight_avg': cls.s_get_col_avg(session, cls.weight, start_ts, end_ts, True),
            'weight_min': cls.s_get_col_min(session, cls.weight, start_ts, end_ts, True),
            'weight_max': cls.s_get_col_max(session, cls.weight, start_ts, end_ts)
        }


class Stress(GarminDb.Base, idbutils.DbObject):
    """Class representing a stress reading."""

    __tablename__ = 'stress'

    db = GarminDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True, unique=True)
    stress = Column(Integer, nullable=False)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'stress_avg': cls.s_get_col_avg(session, cls.stress, start_ts, end_ts, True),
        }


class Sleep(GarminDb.Base, idbutils.DbObject):
    """Class representing a sleep session."""

    __tablename__ = 'sleep'

    db = GarminDb
    table_version = 1

    day = Column(Date, primary_key=True)
    start = Column(DateTime)
    end = Column(DateTime)
    total_sleep = Column(Time, nullable=False, default=datetime.time.min)
    deep_sleep = Column(Time, nullable=False, default=datetime.time.min)
    light_sleep = Column(Time, nullable=False, default=datetime.time.min)
    rem_sleep = Column(Time, nullable=False, default=datetime.time.min)
    awake = Column(Time, nullable=False, default=datetime.time.min)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'sleep_avg'     : cls.s_get_time_col_avg(session, cls.total_sleep, start_ts, end_ts),
            'sleep_min'     : cls.s_get_time_col_min(session, cls.total_sleep, start_ts, end_ts),
            'sleep_max'     : cls.s_get_time_col_max(session, cls.total_sleep, start_ts, end_ts),
            'rem_sleep_avg' : cls.s_get_time_col_avg(session, cls.rem_sleep, start_ts, end_ts),
            'rem_sleep_min' : cls.s_get_time_col_min(session, cls.rem_sleep, start_ts, end_ts),
            'rem_sleep_max' : cls.s_get_time_col_max(session, cls.rem_sleep, start_ts, end_ts),
        }


class SleepEvents(GarminDb.Base, idbutils.DbObject):
    """Table that stores events recorded druing sleep."""

    __tablename__ = 'sleep_events'

    db = GarminDb
    table_version = 2

    timestamp = Column(DateTime, primary_key=True)
    event = Column(String)
    duration = Column(Time, nullable=False, default=datetime.time.min)

    @classmethod
    def get_wake_time(cls, db, day_date):
        """Return the wake time for a given date."""
        day_start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        day_stop_ts = datetime.datetime.combine(day_date, datetime.time.max)
        values = cls.get_col_values(db, cls.timestamp, cls.event, 'wake_time', day_start_ts, day_stop_ts)
        if len(values) > 0:
            return values[0][0]


class RestingHeartRate(GarminDb.Base, idbutils.DbObject):
    """Class representing a daily resting heart rate reading."""

    __tablename__ = 'resting_hr'

    db = GarminDb
    table_version = 1
    _col_units = {'resting_heart_rate': 'bpm'}

    day = Column(Date, primary_key=True)
    resting_heart_rate = Column(Float)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'rhr_avg': cls.s_get_col_avg(session, cls.resting_heart_rate, start_ts, end_ts, ignore_le_zero=True),
            'rhr_min': cls.s_get_col_min(session, cls.resting_heart_rate, start_ts, end_ts, ignore_le_zero=True),
            'rhr_max': cls.s_get_col_max(session, cls.resting_heart_rate, start_ts, end_ts),
        }


class DailySummary(GarminDb.Base, idbutils.DbObject):
    """Class representing a Garmin daily summary."""

    __tablename__ = 'daily_summary'

    db = GarminDb
    table_version = 4
    _col_units = {'hr_min': 'bpm', 'hr_max': 'bpm', 'rhr': 'bpm'}

    day = Column(Date, primary_key=True)
    hr_min = Column(Integer)
    hr_max = Column(Integer)
    rhr = Column(Integer)
    stress_avg = Column(Integer)
    step_goal = Column(Integer)
    steps = Column(Integer)
    moderate_activity_time = Column(Time, nullable=False, default=datetime.time.min)
    vigorous_activity_time = Column(Time, nullable=False, default=datetime.time.min)
    intensity_time_goal = Column(Time, nullable=False, default=datetime.time.min)
    floors_up = Column(Float)
    floors_down = Column(Float)
    floors_goal = Column(Float)
    distance = Column(Float)
    calories_goal = Column(Integer)
    calories_total = Column(Integer)
    calories_bmr = Column(Integer)
    calories_active = Column(Integer)
    calories_consumed = Column(Integer)
    hydration_goal = Column(Integer)
    hydration_intake = Column(Integer)
    sweat_loss = Column(Integer)
    spo2_avg = Column(Float)
    spo2_min = Column(Float)
    rr_waking_avg = Column(Float)
    rr_max = Column(Float)
    rr_min = Column(Float)
    bb_charged = Column(Integer)
    bb_max = Column(Integer)
    bb_min = Column(Integer)
    description = Column(String)

    @hybrid_property
    def intensity_time(self):
        """Return intensity_time computed from moderate_activity_time and vigorous_activity_time."""
        return fitfile.conversions.add_time(self.moderate_activity_time, self.vigorous_activity_time, 2)

    @intensity_time.expression
    def intensity_time(cls):
        """Return intensity_time computed from moderate_activity_time and vigorous_activity_time."""
        return cls._time_from_secs(2 * cls._secs_from_time(cls.vigorous_activity_time) + cls._secs_from_time(cls.moderate_activity_time))

    @hybrid_property
    def intensity_time_goal_percent(self):
        """Return the percentage of intensity time goal achieved."""
        if self.intensity_time is not None and self.intensity_time_goal is not None:
            return (fitfile.conversions.time_to_secs(self.intensity_time) * 100) / fitfile.conversions.time_to_secs(self.intensity_time_goal)
        return 0.0

    @intensity_time_goal_percent.expression
    def intensity_time_goal_percent(cls):
        """Return the percentage of intensity time goal achieved."""
        return func.round((cls._secs_from_time(cls.intensity_time) * 100) / cls._secs_from_time(cls.intensity_time_goal))

    @hybrid_property
    def steps_goal_percent(self):
        """Return the percentage of steps goal achieved."""
        if self.steps is not None and self.step_goal is not None:
            return (self.steps * 100) / self.step_goal
        return 0.0

    @steps_goal_percent.expression
    def steps_goal_percent(cls):
        """Return the percentage of steps goal achieved."""
        return func.round((cls.steps * 100) / cls.step_goal)

    @hybrid_property
    def floors_goal_percent(self):
        """Return the percentage of floors goal achieved."""
        if self.floors_up is not None and self.floors_goal is not None:
            return (self.floors_up * 100) / self.floors_goal
        return 0.0

    @floors_goal_percent.expression
    def floors_goal_percent(cls):
        """Return the percentage of floors goal achieved."""
        return func.round((cls.floors_up * 100) / cls.floors_goal)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'rhr_avg'                   : cls.s_get_col_avg(session, cls.rhr, start_ts, end_ts),
            'rhr_min'                   : cls.s_get_col_min(session, cls.rhr, start_ts, end_ts),
            'rhr_max'                   : cls.s_get_col_max(session, cls.rhr, start_ts, end_ts),
            'stress_avg'                : cls.s_get_col_avg(session, cls.stress_avg, start_ts, end_ts),
            'steps'                     : cls.s_get_col_sum(session, cls.steps, start_ts, end_ts),
            'steps_goal'                : cls.s_get_col_sum(session, cls.step_goal, start_ts, end_ts),
            'floors'                    : cls.s_get_col_sum(session, cls.floors_up, start_ts, end_ts),
            'floors_goal'               : cls.s_get_col_sum(session, cls.floors_goal, start_ts, end_ts),
            'intensity_time'            : cls.s_get_time_col_avg(session, cls.intensity_time, start_ts, end_ts),
            'moderate_activity_time'    : cls.s_get_time_col_avg(session, cls.moderate_activity_time, start_ts, end_ts),
            'vigorous_activity_time'    : cls.s_get_time_col_sum(session, cls.vigorous_activity_time, start_ts, end_ts),
            'intensity_time_goal'       : cls.s_get_time_col_avg(session, cls.intensity_time_goal, start_ts, end_ts),
            'calories_goal'             : cls.s_get_col_sum(session, cls.calories_goal, start_ts, end_ts),
            'calories_avg'              : cls.s_get_col_avg(session, cls.calories_total, start_ts, end_ts),
            'calories_bmr_avg'          : cls.s_get_col_avg(session, cls.calories_bmr, start_ts, end_ts),
            'calories_active_avg'       : cls.s_get_col_avg(session, cls.calories_active, start_ts, end_ts),
            'calories_consumed_avg'     : cls.s_get_col_avg(session, cls.calories_consumed, start_ts, end_ts),
            'hydration_goal'            : cls.s_get_col_sum(session, cls.hydration_goal, start_ts, end_ts),
            'hydration_avg'             : cls.s_get_col_avg(session, cls.hydration_intake, start_ts, end_ts),
            'hydration_intake'          : cls.s_get_col_sum(session, cls.hydration_intake, start_ts, end_ts),
            'sweat_loss_avg'            : cls.s_get_col_avg(session, cls.sweat_loss, start_ts, end_ts),
            'sweat_loss'                : cls.s_get_col_sum(session, cls.sweat_loss, start_ts, end_ts),
            'spo2_avg'                  : cls.s_get_col_avg(session, cls.spo2_avg, start_ts, end_ts),
            'spo2_min'                  : cls.s_get_col_min(session, cls.spo2_min, start_ts, end_ts),
            'rr_waking_avg'             : cls.s_get_col_avg(session, cls.rr_waking_avg, start_ts, end_ts),
            'rr_max'                    : cls.s_get_col_max(session, cls.rr_max, start_ts, end_ts),
            'rr_min'                    : cls.s_get_col_min(session, cls.rr_min, start_ts, end_ts),
            'bb_max'                    : cls.s_get_col_avg(session, cls.bb_max, start_ts, end_ts),
            'bb_min'                    : cls.s_get_col_avg(session, cls.bb_min, start_ts, end_ts),
        }

    @classmethod
    def get_daily_stats(cls, session, day_ts):
        """Return a dictionary of aggregate statistics for the given day."""
        stats = cls.get_stats(session, day_ts, day_ts + datetime.timedelta(1))
        # intensity_time_goal is a weekly goal, so the daily value is 1/7 of the weekly goal
        stats['intensity_time_goal'] = cls._time_from_secs(cls._secs_from_time(stats['intensity_time_goal']) / 7)
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, session, first_day_ts, last_day_ts):
        """Return a dictionary of aggregate statistics for the given month."""
        stats = cls.get_stats(session, first_day_ts, last_day_ts)
        # intensity time is a weekly goal, so sum up the weekly average values
        first_week_end = first_day_ts + datetime.timedelta(7)
        second_week_end = first_day_ts + datetime.timedelta(14)
        third_week_end = first_day_ts + datetime.timedelta(21)
        fourth_week_end = first_day_ts + datetime.timedelta(28)
        stats['intensity_time_goal'] = fitfile.conversions.add_time(
            fitfile.conversions.add_time(
                cls.s_get_time_col_avg(session, cls.intensity_time_goal, first_day_ts, first_week_end),
                cls.s_get_time_col_avg(session, cls.intensity_time_goal, first_week_end, second_week_end)
            ),
            fitfile.conversions.add_time(
                cls.s_get_time_col_avg(session, cls.intensity_time_goal, second_week_end, third_week_end),
                cls.s_get_time_col_avg(session, cls.intensity_time_goal, third_week_end, fourth_week_end)
            )
        )
        stats['first_day'] = first_day_ts
        return stats
