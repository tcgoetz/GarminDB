#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, sys, getopt, datetime, dateutil.parser

from download_garmin import Download
from import_garmin import GarminProfile, GarminWeightData, GarminSummaryData, GarminExtraData, GarminFitData, GarminSleepData, GarminRhrData
from import_garmin_activities import GarminJsonSummaryData, GarminJsonDetailsData, GarminExtraData, GarminTcxData, GarminFitData
from analyze_garmin import Analyze

import HealthDB
import GarminDB
import GarminDBConfigManager

try:
    import GarminConnectConfig
except ImportError:
    print "Missing config: copy GarminConnectConfig.py.orig to GarminConnectConfig.py and edit GarminConnectConfig.py to " + \
     "add your Garmin Connect username and password."
    sys.exit(-1)


logging.basicConfig(filename='garmin.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def config_start_date(type):
    date = dateutil.parser.parse(GarminConnectConfig.data[type + '_start_date']).date()
    days = GarminConnectConfig.data['download_days']
    return (date, days)

def get_date_and_days(latest, db, table, stat_name):
    if latest:
        last_ts = table.latest_time(db)
        if last_ts is None:
            date, days = config_start_date(stat_name)
            logger.info("Automatic date not found, using: %s : %s for %s", str(date), str(days), stat_name)
        else:
            # start from the day after the last day in the DB
            logger.info("Automatically downloading %s data from: %s", stat_name, str(last_ts))
            if stat_name == 'monitoring':
                date = last_ts.date()
                days = (datetime.datetime.now() - last_ts).days
            else:
                date = last_ts
                days = (datetime.date.today() - last_ts).days
    else:
        date, days = config_start_date(stat_name)
    if date is None or days is None:
        print "Missing config: need %s_start_date and download_days. Edit GarminConnectConfig.py." % stat_name
        sys.exit()
    return (date, days)

def download_data(overwite, latest, weight, monitoring, sleep, rhr, activities):
    db_params_dict = GarminDBConfigManager.get_db_params()

    download = Download()
    if not download.login():
        logger.error("Failed to login!")
        sys.exit()

    if activities:
        if latest:
            activity_count = GarminConnectConfig.data['download_latest_activities']
        else:
            activity_count = GarminConnectConfig.data['download_all_activities']
        activities_dir = GarminDBConfigManager.get_or_create_activities_dir()
        root_logger.info("Fetching %d activities to %s", activity_count, activities_dir)
        download.get_activity_types(activities_dir, overwite)
        download.get_activities(activities_dir, activity_count, overwite)
        download.unzip_files(activities_dir)

    if monitoring:
        date, days = get_date_and_days(latest, GarminDB.MonitoringDB(db_params_dict), GarminDB.Monitoring, 'monitoring')
        if days > 0:
            monitoring_dir = GarminDBConfigManager.get_or_create_monitoring_dir(date.year)
            root_logger.info("Date range to update: %s (%d) to %s", str(date), days, monitoring_dir)
            download.get_daily_summaries(monitoring_dir, date, days, overwite)
            download.get_monitoring(date, days)
            download.unzip_files(monitoring_dir)
            root_logger.info("Saved monitoring files for %s (%d) to %s for processing", str(date), days, monitoring_dir)

    if sleep:
        date, days = get_date_and_days(latest, GarminDB.GarminDB(db_params_dict), GarminDB.Sleep, 'sleep')
        if days > 0:
            sleep_dir = GarminDBConfigManager.get_or_create_sleep_dir()
            root_logger.info("Date range to update: %s (%d) to %s", str(date), days, sleep_dir)
            download.get_sleep(sleep_dir, date, days, overwite)
            root_logger.info("Saved sleep files for %s (%d) to %s for processing", str(date), days, sleep_dir)

    if weight:
        date, days = get_date_and_days(latest, GarminDB.GarminDB(db_params_dict), GarminDB.Weight, 'weight')
        if days > 0:
            weight_dir = GarminDBConfigManager.get_or_create_weight_dir()
            root_logger.info("Date range to update: %s (%d) to %s", str(date), days, weight_dir)
            download.get_weight(weight_dir, date, days, overwite)
            root_logger.info("Saved weight files for %s (%d) to %s for processing", str(date), days, weight_dir)

    if rhr:
        date, days = get_date_and_days(latest, GarminDB.GarminDB(db_params_dict), GarminDB.RestingHeartRate, 'rhr')
        if days > 0:
            rhr_dir = GarminDBConfigManager.get_or_create_rhr_dir()
            root_logger.info("Date range to update: %s (%d) to %s", str(date), days, rhr_dir)
            download.get_rhr(rhr_dir, date, days, overwite)
            root_logger.info("Saved rhr files for %s (%d) to %s for processing", str(date), days, rhr_dir)


def import_data(debug, test, latest, weight, monitoring, sleep, rhr, activities):
    db_params_dict = GarminDBConfigManager.get_db_params(test_db=test)

    gp = GarminProfile(db_params_dict, GarminDBConfigManager.get_fit_files_dir(), debug)
    if gp.file_count() > 0:
        gp.process()

    garmindb = GarminDB.GarminDB(db_params_dict)
    english_units = GarminDB.Attributes.measurements_type_metric(garmindb) == False

    if weight:
        weight_dir = GarminDBConfigManager.get_weight_dir()
        gwd = GarminWeightData(db_params_dict, None, weight_dir, latest, english_units, debug)
        if gwd.file_count() > 0:
            gwd.process()

    if monitoring:
        monitoring_dir = GarminDBConfigManager.get_monitoring_base_dir()
        gsd = GarminSummaryData(db_params_dict, None, monitoring_dir, latest, english_units, debug)
        if gsd.file_count() > 0:
            gsd.process()
        ged = GarminExtraData(db_params_dict, None, monitoring_dir, latest, debug)
        if ged.file_count() > 0:
            ged.process()
        gfd = GarminFitData(None, monitoring_dir, latest, english_units, debug)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)

    if sleep:
        sleep_dir = GarminDBConfigManager.get_sleep_dir()
        gsd = GarminSleepData(db_params_dict, None, sleep_dir, latest, debug)
        if gsd.file_count() > 0:
            gsd.process()

    if rhr:
        rhr_dir = GarminDBConfigManager.get_rhr_dir()
        grhrd = GarminRhrData(db_params_dict, None, rhr_dir, latest, debug)
        if grhrd.file_count() > 0:
            grhrd.process()

    if activities:
        activities_dir = GarminDBConfigManager.get_activities_dir()
        gjsd = GarminJsonSummaryData(db_params_dict, None, activities_dir, latest, english_units, debug)
        if gjsd.file_count() > 0:
            gjsd.process()

        gdjd = GarminJsonDetailsData(db_params_dict, None, activities_dir, latest, english_units, debug)
        if gdjd.file_count() > 0:
            gdjd.process()

        ged = GarminExtraData(db_params_dict, None, activities_dir, latest, debug)
        if ged.file_count() > 0:
            ged.process()

        gtd = GarminTcxData(None, activities_dir, latest, english_units, debug)
        if gtd.file_count() > 0:
            gtd.process_files(db_params_dict)

        gfd = GarminFitData(None, activities_dir, latest, english_units, debug)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)

def analyze_data(debug):
    db_params_dict = GarminDBConfigManager.get_db_params()
    analyze = Analyze(db_params_dict, debug - 1)
    analyze.get_stats()
    analyze.summary()


def delete_db(debug):
    db_params_dict = GarminDBConfigManager.get_db_params()
    GarminDB.GarminDB(db_params_dict, debug - 1).delete_db()
    GarminDB.MonitoringDB(db_params_dict, debug - 1).delete_db()
    GarminDB.ActivitiesDB(db_params_dict, debug - 1).delete_db()
    GarminDB.GarminSummaryDB(db_params_dict, debug - 1).delete_db()
    HealthDB.SummaryDB(db_params_dict, debug - 1).delete_db()


def usage(program):
    print '%s [--monitoring | --rhr | --sleep | --weight] ...' % program
    print '    --monitoring : import monitoring data'
    print '    --rhr        : import resting heart rate data'
    print '    --sleep      : import sleep data'
    print '    --weight     : import weight data'
    print '    --trace      : turn on debug tracing'
    print '    '
    sys.exit()

def main(argv):
    _download_data = False
    _import_data = False
    _analyze_data = False
    _delete_db = False
    activities = False
    debug = 0
    test = False
    profile_dir = None
    monitoring = False
    overwite = False
    weight = False
    rhr = False
    sleep = False
    latest = False

    try:
        opts, args = getopt.getopt(argv,"aAdimlrstT:w",
            ["all", "activities", "analyze", "delete_db", "download", "import", "trace=", "test", "monitoring", "latest", "rhr", "sleep", "weight"])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
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
        elif opt in ("-o", "--overwite"):
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

    if debug > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    if _delete_db:
        delete_db(debug)
        sys.exit()

    if _download_data:
        download_data(overwite, latest, weight, monitoring, sleep, rhr, activities)

    if _import_data:
        import_data(debug, test, latest, weight, monitoring, sleep, rhr, activities)

    if _analyze_data:
        analyze_data(debug)


if __name__ == "__main__":
    main(sys.argv[1:])
