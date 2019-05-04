#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *
from Fit import FieldEnums


logger = logging.getLogger(__name__)


class GarminDB(DB):
    Base = declarative_base()
    db_name = 'garmin'
    db_version = 7
    view_version = 3

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("GarminDB: %s debug: %s ", repr(db_params_dict), str(debug))
        super(GarminDB, self).__init__(db_params_dict, debug)
        GarminDB.Base.metadata.create_all(self.engine)
        version = GarminDB.DbVersion()
        version.version_check(self, self.db_version)
        db_view_version = version.version_check_key(self, 'view_version', self.view_version)
        if db_view_version != self.view_version:
            DeviceInfo.delete_view(self)
            File.delete_view(self)
            version.update_version(self, 'view_version', self.view_version)
        DeviceInfo.create_view(self)
        File.create_view(self)


class Attributes(GarminDB.Base, KeyValueObject):
    __tablename__ = 'attributes'

    @classmethod
    def measurements_type_metric(cls, db):
        return (cls.get(db, 'measurement_system') == str(FieldEnums.DisplayMeasure.metric))


class Device(GarminDB.Base, DBObject):
    __tablename__ = 'devices'
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
    def local_device_serial_number(cls, db, serial_number, device_type):
        return '%s%06d' % (serial_number, device_type.value)


class DeviceInfo(GarminDB.Base, DBObject):
    __tablename__ = 'device_info'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    file_id = Column(Integer, ForeignKey('files.id'))
    serial_number = Column(Integer, ForeignKey('devices.serial_number'), nullable=False)
    device_type = Column(String)
    software_version = Column(String)
    cum_operating_time = Column(Time, nullable=False, default=datetime.time.min)
    battery_voltage = Column(Float)

    time_col_name = 'timestamp'
    match_col_names = ['timestamp', 'serial_number', 'device_type']

    @classmethod
    def create_view(cls, db):
        view_name = cls.get_default_view_name()
        query_str = (
            'SELECT ' +
                'device_info.timestamp AS timestamp, ' +
                'device_info.file_id AS file_id, ' +
                'device_info.serial_number AS serial_number, ' +
                'device_info.device_type AS device_type, ' +
                'device_info.software_version AS software_version, ' +
                'devices.manufacturer AS devices_manufacturer, ' +
                'devices.product AS devices_product, ' +
                'devices.hardware_version AS devices_hardware_version ' +
            'FROM device_info JOIN devices ON devices.serial_number = device_info.serial_number ' +
            'ORDER BY device_info.timestamp DESC'
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)


class File(GarminDB.Base, DBObject):
    __tablename__ = 'files'

    fit_file_types_prefix = 'fit_'
    FileType = derived_enum('FileType', FieldEnums.FileType, {'tcx' : 100001, 'gpx' : 100002}, fit_file_types_prefix)

    id = Column(Integer, primary_key=True)
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
        view_name = cls.get_default_view_name()
        query_str = (
            'SELECT ' +
                'device_info.timestamp AS timestamp, ' +
                'files.id AS activity_id, ' +
                'files.name AS name, ' +
                'files.type AS type, ' +
                'devices.serial_number AS device_serial_number, ' +
                'devices.manufacturer AS device_manufacturer, ' +
                'devices.product AS device_product ' +
            'FROM files JOIN devices ON devices.serial_number = files.serial_number JOIN device_info ON device_info.file_id = files.id ' +
            'ORDER BY device_info.timestamp DESC'
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)

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

    timestamp = Column(DateTime, primary_key=True, unique=True)
    weight = Column(Float, nullable=False)

    time_col_name = 'timestamp'

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'weight_avg' : cls.get_col_avg(db, cls.weight, start_ts, end_ts, True),
            'weight_min' : cls.get_col_min(db, cls.weight, start_ts, end_ts, True),
            'weight_max' : cls.get_col_max(db, cls.weight, start_ts, end_ts),
        }
        return stats


class Stress(GarminDB.Base, DBObject):
    __tablename__ = 'stress'

    timestamp = Column(DateTime, primary_key=True, unique=True)
    stress = Column(Integer, nullable=False)

    time_col_name = 'timestamp'

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'stress_avg' : cls.get_col_avg(db, cls.stress, start_ts, end_ts, True),
        }
        return stats


class Sleep(GarminDB.Base, DBObject):
    __tablename__ = 'sleep'

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
    def get_stats(cls, db, start_ts, end_ts):
        return {
            'sleep_avg'     : cls.get_time_col_avg(db, cls.total_sleep, start_ts, end_ts),
            'sleep_min'     : cls.get_time_col_min(db, cls.total_sleep, start_ts, end_ts),
            'sleep_max'     : cls.get_time_col_max(db, cls.total_sleep, start_ts, end_ts),
            'rem_sleep_avg' : cls.get_time_col_avg(db, cls.rem_sleep, start_ts, end_ts),
            'rem_sleep_min' : cls.get_time_col_min(db, cls.rem_sleep, start_ts, end_ts),
            'rem_sleep_max' : cls.get_time_col_max(db, cls.rem_sleep, start_ts, end_ts),
        }


class SleepEvents(GarminDB.Base, DBObject):
    __tablename__ = 'sleep_events'

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

    day = Column(Date, primary_key=True)
    resting_heart_rate = Column(Float)

    time_col_name = 'day'

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'rhr_avg' : cls.get_col_avg(db, cls.resting_heart_rate, start_ts, end_ts, True),
            'rhr_min' : cls.get_col_min(db, cls.resting_heart_rate, start_ts, end_ts, True),
            'rhr_max' : cls.get_col_max(db, cls.resting_heart_rate, start_ts, end_ts),
        }
        return stats

