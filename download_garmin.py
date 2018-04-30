#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, logging, datetime, time, tempfile, zipfile, json, dateutil.parser
import requests

import GarminDB
from Fit import Conversions


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class Download():

    garmin_connect_base_url = "https://connect.garmin.com"

    garmin_connect_sso_url = 'https://sso.garmin.com/sso'
    garmin_connect_sso_login_url = garmin_connect_sso_url + '/login'

    garmin_connect_login_url = garmin_connect_base_url + "/en-US/signin"
    garmin_connect_post_login_url = garmin_connect_base_url + "/post-auth/login"

    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

    garmin_connect_modern_url = garmin_connect_base_url + "/modern"
    garmin_connect_daily_url = garmin_connect_modern_url + "/dailySummary/timeline"
    garmin_connect_daily_user_base_url = garmin_connect_modern_url + "/daily-summary"
    garmin_connect_weight_base_url = garmin_connect_modern_url + "/weight"
    garmin_connect_activities_url = garmin_connect_modern_url + "/activities"

    garmin_connect_modern_proxy_url = garmin_connect_modern_url + '/proxy'
    garmin_connect_download_daily_url = garmin_connect_modern_proxy_url + "/download-service/files/wellness"
    garmin_connect_user_profile_url = garmin_connect_modern_proxy_url + "/userprofile-service/userprofile"
    garmin_connect_personal_info_url = garmin_connect_user_profile_url + "/personal-information"
    garmin_connect_wellness_url = garmin_connect_modern_proxy_url + "/wellness-service/wellness"
    garmin_connect_hr_daily_url = garmin_connect_wellness_url + "/dailyHeartRate"
    garmin_connect_stress_daily_url = garmin_connect_wellness_url + "/dailyStress"
    garmin_connect_stress_daily_url = garmin_connect_wellness_url + "/dailySleepData"

    garmin_connect_weight_url = garmin_connect_modern_proxy_url + "/userprofile-service/userprofile/personal-information/weightWithOutbound/filterByDay"

    agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1337 Safari/537.36'

    # timeout is seconds
    initial_page_load_timeout = 30
    page_reload_timeout = 15

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        logger.debug("__init__: temp_dir= " + self.temp_dir)
        self.session = requests.session()

    def get(self, url, params={}):
        logger.debug("get: " + url)
        headers = {
            'User-Agent': self.agent
        }
        try:
            response = self.session.get(url, headers=headers, params=params)
            logger.debug("get: %s (%d)" % (response.url, response.status_code))
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error("get exception: " + str(e))

    def post(self, url, params, data):
        logger.debug("post: " + url)
        headers = {
            'User-Agent': self.agent
        }
        try:
            response = self.session.post(url, headers=headers, params=params, data=data)
            logger.debug("post: %s (%d)" % (response.url, response.status_code))
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error("post exception: " + str(e))

    def build_login_url(self):
        return 'https://sso.garmin.com/sso/login?'

    def login(self, username, password):
        logger.debug("login: %s %s" % (username, password))
        params = {
            'service': self.garmin_connect_post_login_url,
            'webhost': self.garmin_connect_base_url,
            'source': self.garmin_connect_login_url,
            'redirectAfterAccountLoginUrl': self.garmin_connect_post_login_url,
            'redirectAfterAccountCreationUrl': self.garmin_connect_post_login_url,
            'gauthHost': self.garmin_connect_sso_url,
            'locale': 'en_US',
            'id': 'gauth-widget',
            'cssUrl': self.garmin_connect_css_url,
            'clientId': 'GarminConnect',
            'rememberMeShown': 'true',
            'rememberMeChecked': 'false',
            'createAccountShown': 'true',
            'openCreateAccount': 'false',
            'usernameShown': 'false',
            'displayNameShown': 'false',
            'consumeServiceTicket': 'false',
            'initialFocus': 'true',
            'embedWidget': 'false',
            'generateExtraServiceTicket': 'false'
        }
        self.get(self.garmin_connect_sso_login_url, params)
        data = {
            'username': username,
            'password': password,
            'embed': 'true',
            'lt': 'e1s1',
            '_eventId': 'submit',
            'displayNameRequired': 'false'
        }
        response = self.post(self.garmin_connect_sso_login_url, params, data)
        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        if not found:
            logger.error("Login failed: " + response.text)
            return False
        print found.group(1)
        params = {
            'ticket' : found.group(1)
        }
        self.get(self.garmin_connect_activities_url, params)
        return True

    def save_file(self, filename, response):
        with open(filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)

    def get_monitoring_day(self, date):
        logger.info("get_monitoring_day: %s" % str(date))
        response = self.get(self.garmin_connect_download_daily_url + '/' + date.strftime("%Y-%m-%d"))
        self.save_file(self.temp_dir + '/' + str(date) + '.zip', response)

    def get_monitoring(self, date, days):
        logger.info("get_monitoring: %s : %d" % (str(date), days))
        for day in xrange(0, days):
            day_date = date + datetime.timedelta(day)
            self.get_monitoring_day(day_date)

    def unzip_monitoring(self, outdir):
        logger.info("unzip_monitoring: " + outdir)
        for filename in os.listdir(self.temp_dir):
            monitoring_files_zip = zipfile.ZipFile(self.temp_dir + "/" + filename, 'r')
            monitoring_files_zip.extractall(outdir)
            monitoring_files_zip.close()

    def get_weight_chunk(self, start, end):
        logger.info("get_weight_chunk: %d - %d" % (start, end))
        response = self.get(self.garmin_connect_weight_url + '?from=' + str(start) + "&until=" + str(end))
        return response.json()

    def get_weight(self):
        logger.info("get_weight")
        data = []
        chunk_size = int((86400 * 365) * 1000)
        end = Conversions.dt_to_epoch_ms(datetime.datetime.now())
        while True:
            start = end - chunk_size
            chunk_data = self.get_weight_chunk(start, end)
            if len(chunk_data) <= 1:
                break
            data.extend(chunk_data)
            end -= chunk_size
        return data


def convert_to_json(object):
    return object.__str__()


def usage(program):
    print '%s -d [<date> -n <days> | -l <path to dbs>] -u <username> -p <password> [-m <outdir> | -w ]' % program
    print '  -d <date ex: 01/21/2018> -n <days> fetch n days of monitoring data starting at date'
    print '  -l check the garmin DB and find out what the most recent date is and fetch monitoring data from that date on'
    print '  -m <outdir> fetches the daily monitoring FIT files for each day specified, unzips them, and puts them in outdit'
    print '  -w <outdit> fetches the daily weight data for each day specified and puts them in the DB'
    sys.exit()

def main(argv):
    date = None
    days = None
    latest = False
    db_params_dict = {}
    username = None
    password = None
    monitoring = None
    weight = None
    debug = False

    try:
        opts, args = getopt.getopt(argv,"d:n:lm:p:s:tu:w:",
            ["debug", "date=", "days=", "username=", "password=", "latest", "monitoring=", "mysql=", "sqlite=", "weight="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--debug"):
            debug = True
        elif opt in ("-d", "--date"):
            logger.debug("Date: " + arg)
            date = dateutil.parser.parse(arg).date()
        elif opt in ("-n", "--days"):
            logger.debug("Days: " + arg)
            days = int(arg)
        elif opt in ("-l", "--latest"):
            logger.debug("Latest" )
            latest = True
        elif opt in ("-u", "--username"):
            logger.debug("Username: " + arg)
            username = arg
        elif opt in ("-p", "--password"):
            logger.debug("Password: " + arg)
            password = arg
        elif opt in ("-m", "--monitoring"):
            logger.debug("Monitoring: " + arg)
            monitoring = arg
        elif opt in ("-w", "--weight"):
            logger.debug("Weight")
            weight = arg
        elif opt in ("-s", "--sqlite"):
            logging.debug("Sqlite DB path: %s" % arg)
            db_params_dict['db_type'] = 'sqlite'
            db_params_dict['db_path'] = arg
        elif opt in ("--mysql"):
            logging.debug("Mysql DB string: %s" % arg)
            db_args = arg.split(',')
            db_params_dict['db_type'] = 'mysql'
            db_params_dict['db_username'] = db_args[0]
            db_params_dict['db_password'] = db_args[1]
            db_params_dict['db_host'] = db_args[2]

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if ((not date or not days) and not latest) and monitoring:
        print "Missing arguments: specify date and days or latest when scraping monitoring data"
        usage(sys.argv[0])
    if not username or not password:
        print "Missing arguments: need username and password"
        usage(sys.argv[0])
    if len(db_params_dict) == 0 and monitoring and latest:
        print "Missing arguments: must specify <db params> with --sqlite or --mysql"
        usage(sys.argv[0])

    garmindb = GarminDB.GarminDB(db_params_dict)
    english_units = (GarminDB.Attributes.get(garmindb, 'dist_setting') == 'statute')

    if latest and monitoring:
        mondb = GarminDB.MonitoringDB(db_params_dict)
        last_ts = GarminDB.Monitoring.latest_time(mondb)
        if last_ts is None:
            days = 365
            date = datetime.datetime.now().date() - datetime.timedelta(days)
            logger.info("Automatic date not found, using: " + str(date))
        else:
            # start from the day after the last day in the DB
            logger.info("Automatically downloading monitoring data from: " + str(last_ts))
            date = last_ts.date() + datetime.timedelta(1)
            days = (datetime.datetime.now().date() - date).days

    if monitoring and days > 0:
        logger.info("Date range to update: %s (%d)" % (str(date), days))
        download = Download()
        download.login(username, password)
        download.get_monitoring(date, days)
        download.unzip_monitoring(monitoring)
        logger.info("Saved monitoring files for %s (%d) to %s for processing" % (str(date), days, monitoring))

    if weight:
        download = Download()
        download.login(username, password)
        weight_data = download.get_weight()

        # dump weight data to file as json
        json_filename = weight + '/weight_' + str(int(time.time())) + '.json'
        save_file = open(json_filename, 'w')
        save_file.write(json.dumps(weight_data, default=convert_to_json))
        save_file.close()

        for entry in weight_data:
            weight = entry['weight'] / 1000.0
            if english_units:
                weight *= 2.204623
            point = {
                'timestamp' : Conversions.epoch_ms_to_dt(entry['date']),
                'weight' : weight
            }
            logger.debug("Inserting: " + repr(point))
            GarminDB.Weight.create_or_update(garmindb, point)
        logger.info("DB updated with weight %d entries" % len(weight_data))



if __name__ == "__main__":
    main(sys.argv[1:])


