#!/usr/bin/env python3

"""
A script that imports and analyzes Garmin health device data into a database.

The data is either copied from a USB mounted Garmin device or downloaded from Garmin Connect.
"""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import getopt
import datetime

from version import print_version, python_version_check, log_version
from download_garmin import Download
from copy_garmin import Copy
from import_garmin import GarminProfile, GarminWeightData, GarminSummaryData, GarminMonitoringExtraData, GarminMonitoringFitData, GarminSleepData, GarminRhrData
from import_garmin_activities import GarminJsonSummaryData, GarminJsonDetailsData, GarminActivitiesExtraData, GarminTcxData, GarminActivitiesFitData
from analyze_garmin import Analyze
from export_activities import ActivityExporter

import HealthDB
import GarminDB
import garmin_db_config_manager as GarminDBConfigManager
from garmin_connect_config_manager import GarminConnectConfigManager


logging.basicConfig(filename='garmin.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()

gc_gonfig = GarminConnectConfigManager()


def __get_date_and_days(db, latest, table, col, stat_name):
    if latest:
        last_ts = table.latest_time(db, col)
        if last_ts is None:
            date, days = gc_gonfig.stat_start_date(stat_name)
            logger.info("Automatic date not found, using: %s : %s for %s", date, days, stat_name)
        else:
            # start from the day after the last day in the DB
            logger.info("Automatically downloading %s data from: %s", stat_name, last_ts)
            if stat_name == 'monitoring':
                date = last_ts.date()
                days = (datetime.datetime.now() - last_ts).days
            else:
                date = last_ts
                days = (datetime.date.today() - last_ts).days
    else:
        date, days = gc_gonfig.stat_start_date(stat_name)
        max_days = (datetime.date.today() - date).days
        if days > max_days:
            days = max_days
    if date is None or days is None:
        print("Missing config: need %s_start_date and download_days. Edit GarminConnectConfig.py." % stat_name)
        sys.exit()
    return (date, days)


def copy_data(overwite, latest, weight, monitoring, sleep, rhr, activities):
    """Copy data from a mounted Garmin USB device to files."""
    copy = Copy(gc_gonfig.device_mount_dir())

    if activities:
        activities_dir = GarminDBConfigManager.get_or_create_activities_dir()
        root_logger.info("Copying activities to %s", activities_dir)
        copy.copy_activities(activities_dir, latest)

    if monitoring:
        monitoring_dir = GarminDBConfigManager.get_or_create_monitoring_dir(datetime.datetime.now().year)
        root_logger.info("Copying monitoring to %s", monitoring_dir)
        copy.copy_monitoring(monitoring_dir, latest)


def download_data(overwite, latest, weight, monitoring, sleep, rhr, activities):
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously downloaded data if indicated."""
    db_params_dict = GarminDBConfigManager.get_db_params()

    download = Download()
    if not download.login():
        logger.error("Failed to login!")
        sys.exit()

    if activities:
        if latest:
            activity_count = gc_gonfig.latest_activity_count()
        else:
            activity_count = gc_gonfig.all_activity_count()
        activities_dir = GarminDBConfigManager.get_or_create_activities_dir()
        root_logger.info("Fetching %d activities to %s", activity_count, activities_dir)
        download.get_activity_types(activities_dir, overwite)
        download.get_activities(activities_dir, activity_count, overwite)
        download.unzip_files(activities_dir)

    if monitoring:
        date, days = __get_date_and_days(GarminDB.MonitoringDB(db_params_dict), latest, GarminDB.MonitoringHeartRate, GarminDB.MonitoringHeartRate.heart_rate, 'monitoring')
        if days > 0:
            monitoring_dir = GarminDBConfigManager.get_or_create_monitoring_dir(date.year)
            root_logger.info("Date range to update: %s (%d) to %s", date, days, monitoring_dir)
            download.get_daily_summaries(monitoring_dir, date, days, overwite)
            download.get_monitoring(date, days)
            download.unzip_files(monitoring_dir)
            root_logger.info("Saved monitoring files for %s (%d) to %s for processing", date, days, monitoring_dir)

    if sleep:
        date, days = __get_date_and_days(GarminDB.GarminDB(db_params_dict), latest, GarminDB.Sleep, GarminDB.Sleep.total_sleep, 'sleep')
        if days > 0:
            sleep_dir = GarminDBConfigManager.get_or_create_sleep_dir()
            root_logger.info("Date range to update: %s (%d) to %s", date, days, sleep_dir)
            download.get_sleep(sleep_dir, date, days, overwite)
            root_logger.info("Saved sleep files for %s (%d) to %s for processing", date, days, sleep_dir)

    if weight:
        date, days = __get_date_and_days(GarminDB.GarminDB(db_params_dict), latest, GarminDB.Weight, GarminDB.Weight.weight, 'weight')
        if days > 0:
            weight_dir = GarminDBConfigManager.get_or_create_weight_dir()
            root_logger.info("Date range to update: %s (%d) to %s", date, days, weight_dir)
            download.get_weight(weight_dir, date, days, overwite)
            root_logger.info("Saved weight files for %s (%d) to %s for processing", date, days, weight_dir)

    if rhr:
        date, days = __get_date_and_days(GarminDB.GarminDB(db_params_dict), latest, GarminDB.RestingHeartRate, GarminDB.RestingHeartRate.resting_heart_rate, 'rhr')
        if days > 0:
            rhr_dir = GarminDBConfigManager.get_or_create_rhr_dir()
            root_logger.info("Date range to update: %s (%d) to %s", date, days, rhr_dir)
            download.get_rhr(rhr_dir, date, days, overwite)
            root_logger.info("Saved rhr files for %s (%d) to %s for processing", date, days, rhr_dir)


def import_data(debug, test, latest, weight, monitoring, sleep, rhr, activities):
    """Import previously downloaded Garmin data into the database."""
    db_params_dict = GarminDBConfigManager.get_db_params(test_db=test)

    gp = GarminProfile(db_params_dict, GarminDBConfigManager.get_fit_files_dir(), debug)
    if gp.file_count() > 0:
        gp.process()

    garmindb = GarminDB.GarminDB(db_params_dict)
    measurement_system = GarminDB.Attributes.measurements_type(garmindb)

    if weight:
        weight_dir = GarminDBConfigManager.get_weight_dir()
        gwd = GarminWeightData(db_params_dict, weight_dir, latest, measurement_system, debug)
        if gwd.file_count() > 0:
            gwd.process()

    if monitoring:
        monitoring_dir = GarminDBConfigManager.get_monitoring_base_dir()
        gsd = GarminSummaryData(db_params_dict, monitoring_dir, latest, measurement_system, debug)
        if gsd.file_count() > 0:
            gsd.process()
        ged = GarminMonitoringExtraData(db_params_dict, monitoring_dir, latest, debug)
        if ged.file_count() > 0:
            ged.process()
        gfd = GarminMonitoringFitData(monitoring_dir, latest, measurement_system, debug)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)

    if sleep:
        sleep_dir = GarminDBConfigManager.get_sleep_dir()
        gsd = GarminSleepData(db_params_dict, sleep_dir, latest, debug)
        if gsd.file_count() > 0:
            gsd.process()

    if rhr:
        rhr_dir = GarminDBConfigManager.get_rhr_dir()
        grhrd = GarminRhrData(db_params_dict, rhr_dir, latest, debug)
        if grhrd.file_count() > 0:
            grhrd.process()

    if activities:
        activities_dir = GarminDBConfigManager.get_activities_dir()
        gjsd = GarminJsonSummaryData(db_params_dict, activities_dir, latest, measurement_system, debug)
        if gjsd.file_count() > 0:
            gjsd.process()

        gdjd = GarminJsonDetailsData(db_params_dict, activities_dir, latest, measurement_system, debug)
        if gdjd.file_count() > 0:
            gdjd.process()

        ged = GarminActivitiesExtraData(db_params_dict, activities_dir, latest, debug)
        if ged.file_count() > 0:
            ged.process()

        gtd = GarminTcxData(activities_dir, latest, measurement_system, debug)
        if gtd.file_count() > 0:
            gtd.process_files(db_params_dict)

        gfd = GarminActivitiesFitData(activities_dir, latest, measurement_system, debug)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)


def analyze_data(debug):
    """Analyze the downloaded and imported Garmin data and create summary tables."""
    db_params_dict = GarminDBConfigManager.get_db_params()
    analyze = Analyze(db_params_dict, debug - 1)
    analyze.get_stats()
    analyze.summary()


def delete_dbs(debug):
    """Delete all GarminDB database files."""
    db_params_dict = GarminDBConfigManager.get_db_params()
    GarminDB.GarminDB.delete_db(db_params_dict)
    GarminDB.MonitoringDB.delete_db(db_params_dict)
    GarminDB.ActivitiesDB.delete_db(db_params_dict)
    GarminDB.GarminSummaryDB.delete_db(db_params_dict)
    HealthDB.SummaryDB.delete_db(db_params_dict)


def export_activity(debug, export_activity_id):
    """Export an activity given its databse id."""
    db_params_dict = GarminDBConfigManager.get_db_params()
    garmindb = GarminDB.GarminDB(db_params_dict)
    measurement_system = GarminDB.Attributes.measurements_type(garmindb)
    ae = ActivityExporter(export_activity_id, measurement_system, debug)
    ae.process(db_params_dict)
    ae.write('activity_%s.tcx' % export_activity_id)


def print_usage(program, error=None):
    """Print usage information for the script."""
    if error is not None:
        print(error)
        print
    print('%s [--all | --activities | --monitoring | --rhr | --sleep | --weight] [--download | --copy | --import | --analyze] [--latest]' % program)
    print('    --all        : Download and/or import data for all enabled stats.')
    print('    --activities : Download and/or import activities data.')
    print('    --monitoring : Download and/or import monitoring data.')
    print('    --rhr        : Download and/or import resting heart rate data.')
    print('    --sleep      : Download and/or import sleep data.')
    print('    --weight     : Download and/or import weight data.')
    print('    --download   : Download data from Garmin Connect for the chosen stats.')
    print('    --copy       : Copy data from a USB mounted Garmin device for the chosen stats.')
    print('    --import     : Import data for the chosen stats.')
    print('    --analyze    : Analyze data in the db and create summary and derived tables.')
    print('    --latest     : Only download and/or import the latest data.')
    print('    --overwrite  : Overwite existing files when downloading. The default is to only download missing files.')
    print('    --delete_db  : Delete Garmin DB db files.')
    print('    --trace      : Turn on debug tracing. Extra logging will be written to log file.')
    print('    ')
    sys.exit()


def main(argv):
    """Manage Garmin device data."""
    _download_data = False
    _copy_data = False
    _import_data = False
    _analyze_data = False
    _delete_db = False
    activities = False
    debug = 0
    test = False
    monitoring = False
    overwite = False
    weight = False
    rhr = False
    sleep = False
    latest = False
    export_activity_id = None

    python_version_check(sys.argv[0])

    try:
        opts, args = getopt.getopt(argv, "acAde:imolrstT:vw",
                                   ["all", "activities", "analyze", "copy", "delete_db", "download", "export-activity=", "import", "trace=", "test",
                                    "monitoring", "overwrite", "latest", "rhr", "sleep", "weight", "version"])
    except getopt.GetoptError as e:
        print_usage(sys.argv[0], str(e))

    for opt, arg in opts:
        if opt == '-h':
            print_usage(sys.argv[0])
        elif opt in ("-v", "--version"):
            print_version(sys.argv[0])
        elif opt in ("-A", "--all"):
            logger.debug("All: " + arg)
            monitoring = GarminDBConfigManager.is_stat_enabled('monitoring')
            sleep = GarminDBConfigManager.is_stat_enabled('sleep')
            weight = GarminDBConfigManager.is_stat_enabled('weight')
            rhr = GarminDBConfigManager.is_stat_enabled('rhr')
            activities = GarminDBConfigManager.is_stat_enabled('activities')
        elif opt in ("-a", "--activities"):
            logging.debug("activities")
            activities = True
        elif opt in ("-c", "--copy"):
            logging.debug("Copy")
            _copy_data = True
        elif opt in ("--delete_db"):
            logging.debug("Delete DB")
            _delete_db = True
        elif opt in ("-d", "--download"):
            logging.debug("Download")
            _download_data = True
        elif opt in ("-i", "--import"):
            logging.debug("Import")
            _import_data = True
        elif opt in ("--analyze"):
            logging.debug("analyze: True")
            _analyze_data = True
        elif opt in ("-t", "--trace"):
            debug = int(arg)
        elif opt in ("-T", "--test"):
            test = True
        elif opt in ("-m", "--monitoring"):
            logging.debug("Monitoring")
            monitoring = True
        elif opt in ("-o", "--overwrite"):
            overwite = True
        elif opt in ("-l", "--latest"):
            latest = True
        elif opt in ("-r", "--rhr"):
            logging.debug("RHR")
            rhr = True
        elif opt in ("-s", "--sleep"):
            logging.debug("Sleep")
            sleep = True
        elif opt in ("-w", "--weight"):
            logging.debug("Weight")
            weight = True
        elif opt in ("-e", "--export-activity"):
            export_activity_id = arg
            logging.debug("Export activity %s", export_activity_id)

    log_version(sys.argv[0])

    if debug > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    if _delete_db:
        delete_dbs(debug)
        sys.exit()

    if _copy_data:
        copy_data(overwite, latest, weight, monitoring, sleep, rhr, activities)

    if _download_data:
        download_data(overwite, latest, weight, monitoring, sleep, rhr, activities)

    if _import_data:
        import_data(debug, test, latest, weight, monitoring, sleep, rhr, activities)

    if _analyze_data:
        analyze_data(debug)

    if export_activity_id:
        export_activity(debug, export_activity_id)

if __name__ == "__main__":
    main(sys.argv[1:])
