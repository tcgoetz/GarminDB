"""Functions for managing the application config."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import logging
import tempfile

from garmin_db_config import GarminDBConfig
from garmin_db_schema import GarminDbSchema
from garmin_db_mappings import GarminDBMappings
from utilities import DbParams, DynamicDb


logger = logging.getLogger(__name__)


class GarminDBConfigManager(GarminDBConfig, GarminDbSchema, GarminDBMappings):
    """Provides accessors to the base class config."""

    temp_dir = tempfile.mkdtemp()

    @classmethod
    def get_db_type(cls):
        """Return the type (SQLite, MySQL, etc) of database that is configured."""
        return cls.db['type']

    @classmethod
    def get_db_user(cls):
        """Return the configured username of the database."""
        return cls.db['user']

    @classmethod
    def get_db_password(cls):
        """Return the configured password of the database."""
        return cls.db['password']

    @classmethod
    def get_db_host(cls):
        """Return the configured hostname of the database."""
        return cls.db['host']

    @classmethod
    def create_dev_db(cls):
        """Create a developer fields database according to the mapping provided in the config."""
        dev_db_name = 'garmin_dev'
        dev_db_version = cls.dev_db_config.get('version')
        logger.info("Creating dev db %s version %s", dev_db_name, dev_db_version)
        cls.dev_db = DynamicDb.Create(dev_db_name, dev_db_version)
        tables = cls.dev_db_config.get('tables')
        cls.dev_tables = {}
        for dev_table_name, dev_table_config in tables.items():
            dev_table_version = dev_table_config.get('version')
            logger.info("Creating dev db table %s version %s", dev_table_name, dev_table_version)
            dev_table = DynamicDb.CreateTable(dev_table_name, cls.dev_db, dev_table_version, dev_table_config.get('pk'), dev_table_config.get('cols'))
            cls.dev_tables[dev_table_name] = dev_table

    @classmethod
    def get_dev_db(cls, db_params_dict, debug_level=0):
        """Return a instantiated developer field database object."""
        return cls.dev_db(db_params_dict, debug_level)

    @classmethod
    def get_dev_table(cls, dev_table_name):
        """Return a developer field database table class object."""
        return cls.dev_tables.get(dev_table_name)

    @classmethod
    def _create_dir_if_needed(cls, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)
        return dir

    @classmethod
    def get_base_dir(cls, test_dir=False):
        """Return the configured directory of where the data files will be stored."""
        base = cls.directories['base_dir']
        if test_dir:
            return cls.temp_dir + os.sep + base
        if cls.directories['relative_to_home']:
            homedir = os.path.expanduser('~')
            return homedir + os.sep + base
        return base

    @classmethod
    def get_fit_files_dir(cls, test_dir=False):
        """Return the configured directory of where the FIT files will be stored."""
        return cls.get_base_dir(test_dir) + os.sep + cls.directories['fit_file_dir']

    @classmethod
    def get_or_create_fit_files_dir(cls, test_dir=False):
        """Return the configured directory of where the FIT files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_fit_files_dir(test_dir))

    @classmethod
    def get_monitoring_base_dir(cls, test_dir=False):
        """Return the configured directory of where the all monitoring files will be stored."""
        return cls.get_fit_files_dir(test_dir) + os.sep + cls.directories['monitoring_file_dir']

    @classmethod
    def get_or_create_monitoring_base_dir(cls, test_dir=False):
        """Return the configured directory of where the monitoring files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_monitoring_base_dir(test_dir))

    @classmethod
    def get_monitoring_dir(cls, year, test_dir=False):
        """Return the configured directory of where the new monitoring files will be stored."""
        return cls.get_monitoring_base_dir(test_dir) + os.sep + str(year)

    @classmethod
    def get_or_create_monitoring_dir(cls, year, test_dir=False):
        """Return the configured directory of where the monitoring files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_monitoring_dir(year, test_dir))

    @classmethod
    def get_activities_dir(cls, test_dir=False):
        """Return the configured directory of where the activities files will be stored."""
        return cls.get_fit_files_dir(test_dir) + os.sep + cls.directories['activities_file_dir']

    @classmethod
    def get_or_create_activities_dir(cls, test_dir=False):
        """Return the configured directory of where the activities files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_activities_dir(test_dir))

    @classmethod
    def get_sleep_dir(cls, test_dir=False):
        """Return the configured directory of where the sleep files will be stored."""
        return cls.get_base_dir(test_dir) + os.sep + cls.directories['sleep_files_dir']

    @classmethod
    def get_or_create_sleep_dir(cls, test_dir=False):
        """Return the configured directory of where the sleep files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_sleep_dir(test_dir))

    @classmethod
    def get_weight_dir(cls, test_dir=False):
        """Return the configured directory of where the weight files will be stored."""
        return cls.get_base_dir() + os.sep + cls.directories['weight_files_dir']

    @classmethod
    def get_or_create_weight_dir(cls, test_dir=False):
        """Return the configured directory of where the weight files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_weight_dir(test_dir))

    @classmethod
    def get_rhr_dir(cls, test_dir=False):
        """Return the configured directory of where the resting heart rate files will be stored."""
        return cls.get_base_dir(test_dir) + os.sep + cls.directories['rhr_files_dir']

    @classmethod
    def get_or_create_rhr_dir(cls, test_dir=False):
        """Return the configured directory of where the resting heart rate files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_rhr_dir(test_dir))

    @classmethod
    def get_fitbit_dir(cls, test_dir=False):
        """Return the configured directory of where the FitBit will be stored."""
        return cls.get_base_dir(test_dir) + os.sep + cls.directories['fitbit_file_dir']

    @classmethod
    def get_or_create_fitbit_dir(cls, test_dir=False):
        """Return the configured directory of where the FitBit files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_fitbit_dir(test_dir))

    @classmethod
    def get_mshealth_dir(cls, test_dir=False):
        """Return the configured directory of where the Microsoft Health will be stored."""
        return cls.get_base_dir(test_dir) + os.sep + cls.directories['mshealth_file_dir']

    @classmethod
    def get_or_create_mshealth_dir(cls, test_dir=False):
        """Return the configured directory of where the Microsoft Health files will be stored creating it if needed."""
        return cls._create_dir_if_needed(cls.get_mshealth_dir(test_dir))

    @classmethod
    def get_db_dir(cls, test_db=False):
        """Return the configured directory of where the database will be stored."""
        if test_db:
            base = cls.temp_dir
        else:
            base = cls.get_base_dir()
        return cls._create_dir_if_needed(base + os.sep + cls.directories['db_dir'])

    @classmethod
    def get_db_params(cls, test_db=False):
        """Return the database configuration."""
        db_type = cls.get_db_type()
        db_params = {
            'db_type' : db_type
        }
        if db_type == 'sqlite':
            db_params['db_path'] = cls.get_db_dir(test_db)
        elif db_type == "mysql":
            db_params['db_type'] = 'mysql'
            db_params['db_username'] = cls.get_db_user()
            db_params['db_password'] = cls.get_db_password()
            db_params['db_host'] = cls.get_db_host()
        return DbParams(**db_params)

    @classmethod
    def get_metric(cls):
        """Return the unit system (metric, statute) that is configured."""
        return cls.config['metric']

    @classmethod
    def device_settings_dir(cls, mount_dir):
        """Return the full path to the settings file on a mounted device."""
        return mount_dir + os.sep + cls.device_directories['base'] + os.sep + cls.device_directories['settings']

    @classmethod
    def device_monitoring_dir(cls, mount_dir):
        """Return the full path to the monitoring files on a mounted device."""
        return mount_dir + os.sep + cls.device_directories['base'] + os.sep + cls.device_directories['monitoring']

    @classmethod
    def device_sleep_dir(cls, mount_dir):
        """Return the full path to the sleep files on a mounted device."""
        return mount_dir + os.sep + cls.device_directories['base'] + os.sep + cls.device_directories['sleep']

    @classmethod
    def device_activities_dir(cls, mount_dir):
        """Return the full path to the activities files on a mounted device."""
        return mount_dir + os.sep + cls.device_directories['base'] + os.sep + cls.device_directories['activities']

    @classmethod
    def graphs_activity_config(cls, activity, key):
        """Return a config value for the graphing capability given it's key name."""
        activity = cls.graphs.get(activity)
        if activity is not None:
            return activity.get(key)