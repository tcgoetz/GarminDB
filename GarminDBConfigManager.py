#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, logging, tempfile

import GarminDBConfig


logger = logging.getLogger(__name__)


def get_db_type():
    return GarminDBConfig.db['type']

def get_db_user():
    return GarminDBConfig.db['user']

def get_db_password():
    return GarminDBConfig.db['password']

def get_db_host():
    return GarminDBConfig.db['host']

def _create_dir_if_needed(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def get_base_dir():
    base = GarminDBConfig.directories['base_dir']
    if GarminDBConfig.directories['relative_to_home']:
        homedir = os.path.expanduser('~')
        return homedir + os.sep + base
    return base

def get_fit_files_dir():
    return get_base_dir() + os.sep + GarminDBConfig.directories['fit_file_dir']

def get_or_create_fit_files_dir():
    return _create_dir_if_needed(get_fit_files_dir())

def get_monitoring_base_dir():
    return get_fit_files_dir() + os.sep + GarminDBConfig.directories['monitoring_file_dir']

def get_monitoring_dir(year):
    return get_monitoring_base_dir() + os.sep + str(year)

def get_or_create_monitoring_dir(year):
    return _create_dir_if_needed(get_monitoring_dir(year))

def get_activities_dir():
    return get_fit_files_dir() + os.sep + GarminDBConfig.directories['activities_file_dir']

def get_or_create_activities_dir():
    return _create_dir_if_needed(get_activities_dir())

def get_sleep_dir():
    return get_base_dir() + os.sep + GarminDBConfig.directories['sleep_files_dir']

def get_or_create_sleep_dir():
    return _create_dir_if_needed(get_sleep_dir())

def get_weight_dir():
    return get_base_dir() + os.sep + GarminDBConfig.directories['weight_files_dir']

def get_or_create_weight_dir():
    return _create_dir_if_needed(get_weight_dir())

def get_rhr_dir():
    return get_base_dir() + os.sep + GarminDBConfig.directories['rhr_files_dir']

def get_or_create_rhr_dir():
    return _create_dir_if_needed(get_rhr_dir())

def get_fitbit_dir():
    return get_base_dir() + os.sep + GarminDBConfig.directories['fitbit_file_dir']

def get_or_create_fitbit_dir():
    return _create_dir_if_needed(get_fitbit_dir())

def get_mshealth_dir():
    return get_base_dir() + os.sep + GarminDBConfig.directories['mshealth_file_dir']

def get_or_create_mshealth_dir():
    return _create_dir_if_needed(get_mshealth_dir())

def get_db_dir(test_db=False):
    if test_db:
        base = tempfile.mkdtemp()
    else:
        base = get_base_dir()
    return _create_dir_if_needed(base + os.sep + GarminDBConfig.directories['db_dir'])

def get_db_params(test_db=False):
    db_type = get_db_type()
    db_params_dict = {
        'db_type' : db_type
    }
    if db_type == 'sqlite':
        db_path = get_db_dir(test_db)
        db_params_dict['db_path'] = db_path
    elif opt in ("--mysql"):
        db_args = arg.split(',')
        db_params_dict['db_type'] = 'mysql'
        db_params_dict['db_username'] = get_db_user()
        db_params_dict['db_password'] = get_db_password()
        db_params_dict['db_host'] = get_db_host()
    return db_params_dict

def get_metric():
    return GarminDBConfig.config['metric']

def is_stat_enabled(stat_name):
    return GarminDBConfig.enabled_stats[stat_name]

