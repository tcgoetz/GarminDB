"""Functions for managing the application config."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import logging
import tempfile

from garmin_db_config import GarminDBConfig


logger = logging.getLogger(__name__)


def get_db_type():
    """Return the type (SQLite, MySQL, etc) of database that is configured."""
    return GarminDBConfig.db['type']


def get_db_user():
    """Return the configured username of the database."""
    return GarminDBConfig.db['user']


def get_db_password():
    """Return the configured password of the database."""
    return GarminDBConfig.db['password']


def get_db_host():
    """Return the configured hostname of the database."""
    return GarminDBConfig.db['host']


def _create_dir_if_needed(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def get_base_dir():
    """Return the configured directory of where the data files will be stored."""
    base = GarminDBConfig.directories['base_dir']
    if GarminDBConfig.directories['relative_to_home']:
        homedir = os.path.expanduser('~')
        return homedir + os.sep + base
    return base


def get_fit_files_dir():
    """Return the configured directory of where the FIT files will be stored."""
    return get_base_dir() + os.sep + GarminDBConfig.directories['fit_file_dir']


def get_or_create_fit_files_dir():
    """Return the configured directory of where the FIT files will be stored creating it if needed."""
    return _create_dir_if_needed(get_fit_files_dir())


def get_monitoring_base_dir():
    """Return the configured directory of where the all monitoring files will be stored."""
    return get_fit_files_dir() + os.sep + GarminDBConfig.directories['monitoring_file_dir']


def get_or_create_monitoring_base_dir():
    """Return the configured directory of where the monitoring files will be stored creating it if needed."""
    return _create_dir_if_needed(get_monitoring_base_dir())


def get_monitoring_dir(year):
    """Return the configured directory of where the new monitoring files will be stored."""
    return get_monitoring_base_dir() + os.sep + str(year)


def get_or_create_monitoring_dir(year):
    """Return the configured directory of where the monitoring files will be stored creating it if needed."""
    return _create_dir_if_needed(get_monitoring_dir(year))


def get_activities_dir():
    """Return the configured directory of where the activities files will be stored."""
    return get_fit_files_dir() + os.sep + GarminDBConfig.directories['activities_file_dir']


def get_or_create_activities_dir():
    """Return the configured directory of where the activities files will be stored creating it if needed."""
    return _create_dir_if_needed(get_activities_dir())


def get_sleep_dir():
    """Return the configured directory of where the sleep files will be stored."""
    return get_base_dir() + os.sep + GarminDBConfig.directories['sleep_files_dir']


def get_or_create_sleep_dir():
    """Return the configured directory of where the sleep files will be stored creating it if needed."""
    return _create_dir_if_needed(get_sleep_dir())


def get_weight_dir():
    """Return the configured directory of where the weight files will be stored."""
    return get_base_dir() + os.sep + GarminDBConfig.directories['weight_files_dir']


def get_or_create_weight_dir():
    """Return the configured directory of where the weight files will be stored creating it if needed."""
    return _create_dir_if_needed(get_weight_dir())


def get_rhr_dir():
    """Return the configured directory of where the resting heart rate files will be stored."""
    return get_base_dir() + os.sep + GarminDBConfig.directories['rhr_files_dir']


def get_or_create_rhr_dir():
    """Return the configured directory of where the resting heart rate files will be stored creating it if needed."""
    return _create_dir_if_needed(get_rhr_dir())


def get_fitbit_dir():
    """Return the configured directory of where the FitBit will be stored."""
    return get_base_dir() + os.sep + GarminDBConfig.directories['fitbit_file_dir']


def get_or_create_fitbit_dir():
    """Return the configured directory of where the FitBit files will be stored creating it if needed."""
    return _create_dir_if_needed(get_fitbit_dir())


def get_mshealth_dir():
    """Return the configured directory of where the Microsoft Health will be stored."""
    return get_base_dir() + os.sep + GarminDBConfig.directories['mshealth_file_dir']


def get_or_create_mshealth_dir():
    """Return the configured directory of where the Microsoft Health files will be stored creating it if needed."""
    return _create_dir_if_needed(get_mshealth_dir())


def get_db_dir(test_db=False):
    """Return the configured directory of where the database will be stored."""
    if test_db:
        base = tempfile.mkdtemp()
    else:
        base = get_base_dir()
    return _create_dir_if_needed(base + os.sep + GarminDBConfig.directories['db_dir'])


def get_db_params(test_db=False):
    """Return the database configuration."""
    db_type = get_db_type()
    db_params_dict = {
        'db_type' : db_type
    }
    if db_type == 'sqlite':
        db_params_dict['db_path'] = get_db_dir(test_db)
    elif db_type == "mysql":
        db_params_dict['db_type'] = 'mysql'
        db_params_dict['db_username'] = get_db_user()
        db_params_dict['db_password'] = get_db_password()
        db_params_dict['db_host'] = get_db_host()
    return db_params_dict


def get_metric():
    """Return the unit system (metric, statute) that is configured."""
    return GarminDBConfig.config['metric']


def is_stat_enabled(stat_name):
    """Return whether a particular statistic is enabled or not."""
    return GarminDBConfig.enabled_stats[stat_name]


def device_monitoring_dir(mount_dir):
    """Return the full path to the monitoring files on a mounted device."""
    return mount_dir + os.sep + GarminDBConfig.device_directories['base'] + os.sep + GarminDBConfig.device_directories['monitoring']


def device_activities_dir(mount_dir):
    """Return the full path to the activities files on a mounted device."""
    return mount_dir + os.sep + GarminDBConfig.device_directories['base'] + os.sep + GarminDBConfig.device_directories['activities']


def graphs_activity(activity):
    """Return a dictionary of graph config items for a given activity."""
    return GarminDBConfig.graphs.get(activity)


def graphs_activity_config(activity, key):
    """Return a config value for the graphing capability given it's key name."""
    activity = graphs_activity(activity)
    if activity is not None:
        return activity.get(key)


def checkup(item):
    """Return an item from the checkup config."""
    return GarminDBConfig.checkup.get(item)
