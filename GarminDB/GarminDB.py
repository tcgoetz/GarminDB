#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *
from ExtraData import *
from Fit import FieldEnums


logger = logging.getLogger(__name__)


class GarminDB(DB):
    Base = declarative_base()
    db_name = 'garmin'
    db_version = 13

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        super(GarminDB, self).__init__(db_params_dict, debug)
        GarminDB.Base.metadata.create_all(self.engine)
        version = GarminDB.DbVersion()
        version.version_check(self, self.db_version)
        self.tables = [Attributes, Device, DeviceInfo, File, Weight, Stress, Sleep, SleepEvents, RestingHeartRate, DailySummary, DailyExtraData]
        for table in self.tables:
            version.table_version_check(self, table)
            if not version.view_version_check(self, table):
                table.delete_view(self)
        DeviceInfo.create_view(self)
        File.create_view(self)


class Attributes(GarminDB.Base, KeyValueObject):
    __tablename__ = 'attributes'
    table_version = 1

    @classmethod
    def measurements_type(cls, db):
        return FieldEnums.DisplayMeasure.from_string(cls.get(db, 'measurement_system'))

    @classmethod
    def measurements_type_metric(cls, db):
        return (cls.measurements_type(db) == FieldEnums.DisplayMeasure.metric)


class Device(GarminDB.Base, DBObject):
    __tablename__ = 'devices'
    table_version = 3
    unknown_device_serial_number = 9999999999

    Manufacturer = derived_enum('Manufacturer', FieldEnums.Manufacturer, {'Microsoft' : 100001, 'Unknown': 100000})

    serial_number = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    manufacturer = Column(Enum(Manufacturer))
    product = Column(String)
    hardware_version = Column(String)

    time_col_name = 'timestamp'
    match_col_names = ['serial_number']

    @property
    def product_as_enum(self):
        return FieldEnums.product_enum(self.manufacturer, self.product)

    @classmethod
    def get(cls, db, serial_number):
        return cls.find_one(db, {'serial_number' : serial_number})

    @classmethod
    def local_device_serial_number(cls, serial_number, device_type):
        return '%s%06d' % (serial_number, device_type.value)


class DeviceInfo(GarminDB.Base, DBObject):
    __tablename__ = 'device_info'
    table_version = 2
    view_version = 4

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    file_id = Column(String, ForeignKey('files.id'))
    serial_number = Column(Integer, ForeignKey('devices.serial_number'), nullable=False)
    device_type = Column(String)
    software_version = Column(String)
    cum_operating_time = Column(Time, nullable=False, default=datetime.time.min)
    battery_voltage = Column(Float)

    time_col_name = 'timestamp'
    match_col_names = ['timestamp', 'serial_number', 'device_type']

    @classmethod
    def create_view(cls, db):
        cls.create_join_view(db, cls.get_default_view_name(),
            [
                cls.timestamp.label('timestamp'),
                cls.file_id.label('file_id'),
                cls.serial_number.label('serial_number'),
                cls.device_type.label('device_type'),
                cls.software_version.label('software_version'),
                Device.manufacturer.label('manufacturer'),
                Device.product.label('product'),
                Device.hardware_version.label('hardware_version')
            ],
            Device, cls.timestamp.desc())


class File(GarminDB.Base, DBObject):
    __tablename__ = 'files'
    table_version = 3
    view_version = 4

    fit_file_types_prefix = 'fit_'
    FileType = derived_enum('FileType', FieldEnums.FileType, {'tcx' : 100001, 'gpx' : 100002}, fit_file_types_prefix)

    id = Column(String, primary_key=True)
    name = Column(String, unique=True)
    type = Column(Enum(FileType), nullable=False)
    serial_number = Column(Integer, ForeignKey('devices.serial_number'))

    match_col_names = ['name']

    @classmethod
    def _get_id(cls, session, pathname):
        return cls._find_id(session, {'name' : os.path.basename(pathname)})

    @classmethod
    def get_id(cls, db, pathname):
        return cls.find_id(db, {'name' : os.path.basename(pathname)})

    @classmethod
    def create_view(cls, db):
        cls.create_multi_join_view(db, cls.get_default_view_name(),
            [
                DeviceInfo.timestamp.label('timestamp'),
                cls.id.label('activity_id'),
                cls.name.label('name'),
                cls.type.label('type'),
                Device.manufacturer.label('manufacturer'),
                Device.product.label('product'),
                Device.serial_number.label('serial_number')
            ],
            [(Device, File.serial_number==Device.serial_number), (DeviceInfo, File.id==DeviceInfo.file_id)],
            DeviceInfo.timestamp.desc())

    @classmethod
    def name_and_id_from_path(cls, pathname):
        name = os.path.basename(pathname)
        id = name.split('.')[0]
        return (id, name)

    @classmethod
    def id_from_path(cls, pathname):
        return os.path.basename(pathname).split('.')[0]


class Weight(GarminDB.Base, DBObject):
    __tablename__ = 'weight'
    table_version = 1

    day = Column(Date, primary_key=True)
    weight = Column(Float, nullable=False)

    time_col_name = 'day'

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        stats = {
            'weight_avg' : cls._get_col_avg(session, cls.weight, start_ts, end_ts, True),
            'weight_min' : cls._get_col_min(session, cls.weight, start_ts, end_ts, True),
            'weight_max' : cls._get_col_max(session, cls.weight, start_ts, end_ts),
        }
        return stats


class Stress(GarminDB.Base, DBObject):
    __tablename__ = 'stress'
    table_version = 1

    timestamp = Column(DateTime, primary_key=True, unique=True)
    stress = Column(Integer, nullable=False)

    time_col_name = 'timestamp'

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        stats = {
            'stress_avg' : cls._get_col_avg(session, cls.stress, start_ts, end_ts, True),
        }
        return stats


class Sleep(GarminDB.Base, DBObject):
    __tablename__ = 'sleep'
    table_version = 1

    day = Column(Date, primary_key=True)
    start = Column(DateTime)
    end = Column(DateTime)
    total_sleep = Column(Time, nullable=False, default=datetime.time.min)
    deep_sleep = Column(Time, nullable=False, default=datetime.time.min)
    light_sleep = Column(Time, nullable=False, default=datetime.time.min)
    rem_sleep = Column(Time, nullable=False, default=datetime.time.min)
    awake = Column(Time, nullable=False, default=datetime.time.min)

    time_col_name = 'day'

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        return {
            'sleep_avg'     : cls._get_time_col_avg(session, cls.total_sleep, start_ts, end_ts),
            'sleep_min'     : cls._get_time_col_min(session, cls.total_sleep, start_ts, end_ts),
            'sleep_max'     : cls._get_time_col_max(session, cls.total_sleep, start_ts, end_ts),
            'rem_sleep_avg' : cls._get_time_col_avg(session, cls.rem_sleep, start_ts, end_ts),
            'rem_sleep_min' : cls._get_time_col_min(session, cls.rem_sleep, start_ts, end_ts),
            'rem_sleep_max' : cls._get_time_col_max(session, cls.rem_sleep, start_ts, end_ts),
        }


class SleepEvents(GarminDB.Base, DBObject):
    __tablename__ = 'sleep_events'
    table_version = 1

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, unique=True)
    event = Column(String)
    duration = Column(Time, nullable=False, default=datetime.time.min)

    time_col_name = 'timestamp'

    @classmethod
    def get_wake_time(cls, db, day_date):
        day_start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        day_stop_ts = datetime.datetime.combine(day_date, datetime.time.max)
        values = cls.get_col_values(db, cls.timestamp, cls.event, 'wake_time', day_start_ts, day_stop_ts)
        if len(values) > 0:
            return values[0][0]


class RestingHeartRate(GarminDB.Base, DBObject):
    __tablename__ = 'resting_hr'
    table_version = 1

    day = Column(Date, primary_key=True)
    resting_heart_rate = Column(Float)

    time_col_name = 'day'

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        stats = {
            'rhr_avg' : cls._get_col_avg(session, cls.resting_heart_rate, start_ts, end_ts, True),
            'rhr_min' : cls._get_col_min(session, cls.resting_heart_rate, start_ts, end_ts, True),
            'rhr_max' : cls._get_col_max(session, cls.resting_heart_rate, start_ts, end_ts),
        }
        return stats


class DailySummary(GarminDB.Base, DBObject):
    __tablename__ = 'daily_summary'
    table_version = 1

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
    description = Column(String)

    time_col_name = 'day'

    @hybrid_property
    def intensity_time(self):
        return Conversions.add_time(self.moderate_activity_time, self.vigorous_activity_time, 2)

    @intensity_time.expression
    def intensity_time(cls):
        return cls.time_from_secs(2 * cls.secs_from_time(cls.vigorous_activity_time) + cls.secs_from_time(cls.moderate_activity_time))

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        return  {
            'rhr_avg'                   : cls._get_col_avg(session, cls.rhr, start_ts, end_ts),
            'rhr_min'                   : cls._get_col_min(session, cls.rhr, start_ts, end_ts),
            'rhr_max'                   : cls._get_col_max(session, cls.rhr, start_ts, end_ts),
            'stress_avg'                : cls._get_col_avg(session, cls.stress_avg, start_ts, end_ts),
            'steps'                     : cls._get_col_sum(session, cls.steps, start_ts, end_ts),
            'steps_goal'                : cls._get_col_sum(session, cls.step_goal, start_ts, end_ts),
            'floors'                    : cls._get_col_sum(session, cls.floors_up, start_ts, end_ts),
            'floors_goal'               : cls._get_col_sum(session, cls.floors_goal, start_ts, end_ts),
            'calories_goal'             : cls._get_col_avg(session, cls.calories_goal, start_ts, end_ts),
            'intensity_time'            : cls._get_time_col_sum(session, cls.intensity_time, start_ts, end_ts),
            'moderate_activity_time'    : cls._get_time_col_sum(session, cls.moderate_activity_time, start_ts, end_ts),
            'vigorous_activity_time'    : cls._get_time_col_sum(session, cls.vigorous_activity_time, start_ts, end_ts),
            'intensity_time_goal'       : cls._get_time_col_sum(session, cls.intensity_time_goal, start_ts, end_ts),
            'calories_avg'              : cls._get_col_avg(session, cls.calories_total, start_ts, end_ts),
            'calories_bmr_avg'          : cls._get_col_avg(session, cls.calories_bmr, start_ts, end_ts),
            'calories_active_avg'       : cls._get_col_avg(session, cls.calories_active, start_ts, end_ts),
        }

    @classmethod
    def get_monthly_stats(cls, session, first_day_ts, last_day_ts):
        stats = cls.get_stats(session, first_day_ts, last_day_ts)
        # intensity time is a weekly goal, so sum up the weekly average values
        first_week_end = first_day_ts + datetime.timedelta(7)
        second_week_end = first_day_ts + datetime.timedelta(14)
        third_week_end = first_day_ts + datetime.timedelta(21)
        fourth_week_end = first_day_ts + datetime.timedelta(28)
        stats['intensity_time_goal'] = Conversions.add_time(
            Conversions.add_time(
                cls._get_time_col_avg(session, cls.intensity_time_goal, first_day_ts, first_week_end),
                cls._get_time_col_avg(session, cls.intensity_time_goal, first_week_end, second_week_end)
            ),
            Conversions.add_time(
                cls._get_time_col_avg(session, cls.intensity_time_goal, second_week_end, third_week_end),
                cls._get_time_col_avg(session, cls.intensity_time_goal, third_week_end, fourth_week_end)
            )
        )
        stats['first_day'] = first_day_ts
        return stats


class DailyExtraData(GarminDB.Base, ExtraData):
    __tablename__ = 'daily_extra_data'
    table_version = 1

    day = Column(Date, primary_key=True)

    time_col_name = 'day'

