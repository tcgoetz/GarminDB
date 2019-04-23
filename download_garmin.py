#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, logging, datetime, time, tempfile, zipfile, json
import dateutil.parser
import requests

import GarminDB
from Fit import Conversions


logging.basicConfig(level=logging.INFO)
root_logger = logging.getLogger()
logger = logging.getLogger()


class Download():

    garmin_connect_base_url = "https://connect.garmin.com"
    garmin_connect_enus_url = garmin_connect_base_url + "/en-US"

    garmin_sso_base_url = 'https://sso.garmin.com/sso'
    garmin_connect_sso_login_url = garmin_sso_base_url + '/signin'

    garmin_connect_login_url = garmin_connect_enus_url + "/signin"

    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

    garmin_connect_privacy_url = "//connect.garmin.com/en-U/privacy"

    garmin_connect_modern_url = garmin_connect_base_url + "/modern"
    garmin_connect_activities_url = garmin_connect_modern_url + "/activities"

    garmin_connect_modern_proxy_url = garmin_connect_modern_url + '/proxy'
    garmin_connect_download_url = garmin_connect_modern_proxy_url + "/download-service/files"
    garmin_connect_download_activity_url = garmin_connect_download_url + "/activity/"

    garmin_connect_download_daily_url = garmin_connect_download_url + "/wellness"
    garmin_connect_user_profile_url = garmin_connect_modern_proxy_url + "/userprofile-service/userprofile"
    garmin_connect_personal_info_url = garmin_connect_user_profile_url + "/personal-information"
    garmin_connect_wellness_url = garmin_connect_modern_proxy_url + "/wellness-service/wellness"
    garmin_connect_hr_daily_url = garmin_connect_wellness_url + "/dailyHeartRate"
    garmin_connect_stress_daily_url = garmin_connect_wellness_url + "/dailyStress"
    garmin_connect_sleep_daily_url = garmin_connect_wellness_url + "/dailySleepData"

    garmin_connect_rhr_url = garmin_connect_modern_proxy_url + "/userstats-service/wellness/daily"
    garmin_connect_weight_url = garmin_connect_modern_proxy_url + "/weight-service/weight/dateRange"

    garmin_connect_biometric_url = garmin_connect_modern_proxy_url + "/biometric-service/biometric"
    garmin_connect_weight_by_date_url = garmin_connect_biometric_url + "/weightByDate"

    garmin_connect_activity_types_url = garmin_connect_modern_proxy_url + "/activity-service/activity/activityTypes"
    garmin_connect_activity_search_url = garmin_connect_modern_proxy_url + "/activitylist-service/activities/search/activities"

    garmin_connect_course_url = garmin_connect_modern_proxy_url + "/course-service/course"

    agents = {
        'Chrome_Linux'  : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1337 Safari/537.36',
        'Firefox_MacOS' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    agent = agents['Firefox_MacOS']

    default_headers = {
        'User-Agent'    : agent,
        'Accept'        : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        logger.debug("__init__: temp_dir= " + self.temp_dir)
        self.session = requests.session()

    def get_activity_details_url(self, activity_id):
        return self.garmin_connect_modern_proxy_url + '/activity-service/activity/%s' % str(activity_id)

    def get(self, url, aaditional_headers={}, params={}):
        total_headers = self.default_headers.copy()
        total_headers.update(aaditional_headers)
        response = self.session.get(url, headers=total_headers, params=params)
        logger.debug("get: %s (%d)", response.url, response.status_code)
        return response

    def post(self, url, aaditional_headers, params, data):
        total_headers = self.default_headers.copy()
        total_headers.update(aaditional_headers)
        response = self.session.post(url, headers=total_headers, params=params, data=data)
        logger.debug("post: %s (%d)", response.url, response.status_code)
        return response

    def get_json(self, page_html, key):
        found = re.search(key + r" = JSON.parse\(\"(.*)\"\);", page_html, re.M)
        if found:
            json_text = found.group(1).replace('\\"', '"')
            return json.loads(json_text)

    def login(self, username, password, profile_dir=None):
        logger.debug("login: %s %s", username, password)
        get_headers = {
            'Referer'                           : self.garmin_connect_login_url
        }
        params = {
            'service'                           : self.garmin_connect_modern_url,
            'webhost'                           : self.garmin_connect_base_url,
            'source'                            : self.garmin_connect_login_url,
            'redirectAfterAccountLoginUrl'      : self.garmin_connect_modern_url,
            'redirectAfterAccountCreationUrl'   : self.garmin_connect_modern_url,
            'gauthHost'                         : self.garmin_sso_base_url,
            'locale'                            : 'en_US',
            'id'                                : 'gauth-widget',
            'cssUrl'                            : self.garmin_connect_css_url,
            'privacyStatementUrl'               : '//connect.garmin.com/en-US/privacy/',
            'clientId'                          : 'GarminConnect',
            'rememberMeShown'                   : 'true',
            'rememberMeChecked'                 : 'false',
            # 'customerId'                        : '',
            'createAccountShown'                : 'true',
            'openCreateAccount'                 : 'false',
            'displayNameShown'                  : 'false',
            'consumeServiceTicket'              : 'false',
            'initialFocus'                      : 'true',
            'embedWidget'                       : 'false',
            'generateExtraServiceTicket'        : 'true',
            'generateTwoExtraServiceTickets'    : 'false',
            'generateNoServiceTicket'           : 'false',
            'globalOptInShown'                  : 'true',
            'globalOptInChecked'                : 'false',
            'mobile'                            : 'false',
            'connectLegalTerms'                 : 'true',
            'locationPromptShown'               : 'true',
            'showPassword'                      : 'true'
        }
        response = self.get(self.garmin_connect_sso_login_url, get_headers, params)
        if response.status_code != 200:
            logger.error("Login get failed (%d).", response.status_code)
            self.save_binary_file('login_get.html', response)
            return False
        found = re.search(r"name=\"_csrf\" value=\"(\w*)", response.text, re.M)
        if not found:
            logger.error("_csrf not found.", response.status_code)
            self.save_binary_file('login_get.html', response)
            return False
        logger.debug("_csrf found (%s).", found.group(1))
        data = {
            'username': username,
            'password': password,
            'embed': 'false',
            '_csrf' : found.group(1)
        }

        post_headers = {
            'Referer'                           : response.url,
            'Content-Type'                      : 'application/x-www-form-urlencoded'
        }
        response = self.post(self.garmin_connect_sso_login_url, post_headers, params, data)
        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        if not found:
            logger.error("Login ticket not found (%d).", response.status_code)
            self.save_binary_file('login_post.html', response)
            return False
        params = {
            'ticket' : found.group(1)
        }

        response = self.get(self.garmin_connect_modern_url, params=params)
        if response.status_code != 200:
            logger.error("Login get homepage failed (%d).", response.status_code)
            self.save_binary_file('login_home.html', response)
            return False
        self.user_prefs = self.get_json(response.text, 'VIEWER_USERPREFERENCES')
        if profile_dir:
            self.save_json_file(profile_dir + "/profile", self.user_prefs)
        self.display_name = self.user_prefs['displayName']
        self.english_units = (self.user_prefs['measurementSystem'] == 'statute_us')
        self.social_profile = self.get_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.full_name = self.social_profile['fullName']
        logger.info("login: %s (%s) english units: %s", self.full_name, self.display_name, str(self.english_units))
        return True

    def save_binary_file(self, filename, response):
        with open(filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)

    def convert_to_json(self, object):
        return object.__str__()

    def save_json_file(self, json_full_filname, json_data):
        with open(json_full_filname, 'w') as file:
            logger.info("save_json_file: %s", json_full_filname)
            file.write(json.dumps(json_data, default=self.convert_to_json))

    def download_json_file(self, job_name, url, params, json_filename, overwite):
        json_full_filname = json_filename + '.json'
        if not os.path.isfile(json_full_filname) or overwite:
            response = self.get(url, params=params)
            if response.status_code == 200:
                self.save_json_file(json_full_filname, response.json())
            else:
                logger.error("%s: %s failed (%d): %s", job_name, response.url, response.status_code, response.text)
                return False
        return True

    def unzip_files(self, outdir):
        logger.info("unzip_files: " + outdir)
        for filename in os.listdir(self.temp_dir):
            match = re.search('.*\.zip', filename)
            if match:
                files_zip = zipfile.ZipFile(self.temp_dir + "/" + filename, 'r')
                files_zip.extractall(outdir)
                files_zip.close()

    def get_monitoring_day(self, date):
        logger.info("get_monitoring_day: %s", str(date))
        response = self.get(self.garmin_connect_download_daily_url + '/' + date.strftime("%Y-%m-%d"))
        if response and response.status_code == 200:
            self.save_binary_file(self.temp_dir + '/' + str(date) + '.zip', response)

    def get_monitoring(self, date, days):
        logger.info("get_monitoring: %s : %d", str(date), days)
        for day in xrange(0, days):
            day_date = date + datetime.timedelta(day)
            self.get_monitoring_day(day_date)
            # pause for a second between every page access
            time.sleep(1)

    def get_weight_day(self, directory, day, overwite=False):
        date_str = day.strftime('%Y-%m-%d')
        params = {
            'startDate' : date_str,
            'endDate'   : date_str,
            '_'         : str(Conversions.dt_to_epoch_ms(day))
        }
        return self.download_json_file('get_weight_day', self.garmin_connect_weight_url, params, directory + '/weight_' + date_str, overwite)

    def get_weight(self, directory, date, days):
        day = date - datetime.timedelta(days)
        logger.info("get_weight: %s - %s", day, date)
        while self.get_weight_day(directory, day):
            day = day + datetime.timedelta(1)
            if day > date:
                break
            # pause for a second between every page access
            time.sleep(1)

    def get_activity_summaries(self, start, count):
        logger.info("get_activity_summaries")
        params = {
            'start' : str(start),
            "limit" : str(count)
        }
        response = self.get(self.garmin_connect_activity_search_url, params=params)
        if response.status_code == 200:
            return response.json()

    def save_activity_details(self, directory, activity_id_str, overwite):
        logger.debug("save_activity_details")
        json_filename = directory + '/activity_details_' + activity_id_str
        return self.download_json_file('save_activity_details', self.get_activity_details_url(activity_id_str), None, json_filename, overwite)

    def save_activity_file(self, activity_id_str):
        logger.debug("save_activity_file: " + activity_id_str)
        response = self.get(self.garmin_connect_download_activity_url + activity_id_str)
        if response.status_code == 200:
            self.save_binary_file(self.temp_dir + '/activity_' + activity_id_str + '.zip', response)
        else:
            logger.error("save_activity_file: %s failed (%d): %s", response.url, response.status_code, response.text)

    def get_activities(self, directory, count, overwite=False):
        logger.info("get_activities: '%s' (%d)", directory, count)
        activities = self.get_activity_summaries(0, count)
        for activity in activities:
            activity_id_str = str(activity['activityId'])
            activity_name_str = Conversions.printable(activity['activityName'])
            logger.info("get_activities: %s (%s)" % (activity_name_str, activity_id_str))
            json_filename = directory + '/activity_' + activity_id_str + '.json'
            if not os.path.isfile(json_filename) or overwite:
                logger.debug("get_activities: %s <- %s" % (json_filename, repr(activity)))
                self.save_activity_details(directory, activity_id_str, overwite)
                self.save_json_file(json_filename, activity)
                if not os.path.isfile(directory + '/' + activity_id_str + '.fit') or overwite:
                    self.save_activity_file(activity_id_str)
                # pause for a second between every page access
                time.sleep(1)

    def get_activity_types(self, directory, overwite):
        logger.info("get_activity_types: '%s'", directory)
        return self.download_json_file('get_activity_types', self.garmin_connect_activity_types_url, None, directory + '/activity_types', overwite)

    def get_sleep_day(self, directory, date, overwite=False):
        json_filename = directory + '/sleep_' + str(date)
        params = {
            'date' : date.strftime("%Y-%m-%d")
        }
        return self.download_json_file('get_sleep_day', self.garmin_connect_sleep_daily_url + '/' + self.display_name, params, json_filename, overwite)

    def get_sleep(self, directory, date, days):
        logger.info("get_sleep: %s : %d" % (str(date), days))
        for day in xrange(0, days):
            day_date = date + datetime.timedelta(day)
            self.get_sleep_day(directory, day_date)
            # pause for a second between every page access
            time.sleep(1)

    def get_rhr_day(self, directory, day, overwite=False):
        date_str = day.strftime('%Y-%m-%d')
        json_filename = directory + '/rhr_' + date_str
        params = {
            'fromDate'  : date_str,
            'untilDate' : date_str,
            'metricId'  : 60
        }
        return self.download_json_file('get_rhr_day', self.garmin_connect_rhr_url + '/' + self.display_name, params, json_filename, overwite)

    def get_rhr(self, directory, date, days):
        day = date - datetime.timedelta(days)
        logger.info("get_rhr: %s - %s", day, date)
        while self.get_rhr_day(directory, day):
            day = day + datetime.timedelta(1)
            if day > date:
                break
            # pause for a second between every page access
            time.sleep(1)


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
    profile = None
    activities = None
    activity_count = 1000
    activity_types = False
    monitoring = None
    overwite = False
    weight = None
    rhr = None
    sleep = None
    debug = 0

    try:
        opts, args = getopt.getopt(argv,"a:c:d:n:lm:oP:p:r:S:s:t:u:w:",
            ["activities=", "activity_count=", "date=", "days=", "username=", "password=", "profile=", "latest", "monitoring=", "mysql=",
             "overwrite", "rhr=", "sqlite=", "sleep=", "trace=", "weight="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-a", "--activities"):
            logger.debug("Activities: " + arg)
            activities = arg
        elif opt in ("-c", "--activity_count"):
            logger.debug("Activity count: " + arg)
            activity_count = int(arg)
        elif opt in ("-t", "--trace"):
            debug = int(arg)
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
        elif opt in ("-P", "--profile"):
            logger.info("Profile: " + arg)
            profile = arg
        elif opt in ("-m", "--monitoring"):
            logger.debug("Monitoring: " + arg)
            monitoring = arg
        elif opt in ("-o", "--overwite"):
            overwite = True
        elif opt in ("-S", "--sleep"):
            logger.debug("Sleep: " + arg)
            sleep = arg
        elif opt in ("-w", "--weight"):
            logger.debug("Weight")
            weight = arg
        elif opt in ("-r", "--rhr"):
            logger.debug("Resting heart rate")
            rhr = arg
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

    if debug > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    if ((not date or not days) and not latest) and (monitoring or sleep):
        print "Missing arguments: specify date and days or latest when downloading monitoring or sleep data"
        usage(sys.argv[0])
    if not username or not password:
        print "Missing arguments: need username and password"
        usage(sys.argv[0])
    if len(db_params_dict) == 0 and monitoring and latest:
        print "Missing arguments: must specify <db params> with --sqlite or --mysql"
        usage(sys.argv[0])

    download = Download()
    if not download.login(username, password, profile):
        sys.exit()

    if activities and activity_count > 0:
        logger.info("Fetching %d activities" % activity_count)
        download.get_activity_types(activities, overwite)
        download.get_activities(activities, activity_count, overwite)
        download.unzip_files(activities)

    if latest and monitoring:
        mondb = GarminDB.MonitoringDB(db_params_dict)
        last_ts = GarminDB.Monitoring.latest_time(mondb)
        if last_ts is None:
            days = 31
            date = datetime.datetime.now().date() - datetime.timedelta(days)
            logger.info("Automatic date not found, using: " + str(date))
        else:
            # start from the day after the last day in the DB
            logger.info("Automatically downloading monitoring data from: " + str(last_ts))
            date = last_ts.date() + datetime.timedelta(1)
            days = (datetime.datetime.now().date() - date).days

    if latest and sleep:
        garmindb = GarminDB.GarminDB(db_params_dict)
        last_ts = GarminDB.Sleep.latest_time(garmindb)
        if last_ts is None:
            days = 31
            date = datetime.datetime.now().date() - datetime.timedelta(days)
            logger.info("Automatic date not found, using: " + str(date))
        else:
            # start from the day after the last day in the DB
            logger.info("Automatically downloading sleep data from: " + str(last_ts))
            date = last_ts + datetime.timedelta(1)
            days = (datetime.datetime.now().date() - date).days

    if latest and weight:
        garmindb = GarminDB.GarminDB(db_params_dict)
        last_ts = GarminDB.Weight.latest_time(garmindb)
        date = datetime.datetime.now()
        if last_ts is None:
            days = 31
            logger.info("Automatic date not found, using: " + str(date))
        else:
            # start from the day after the last day in the DB
            logger.info("Automatically downloading weight data from: " + str(last_ts))
            days = (date - last_ts).days

    if latest and rhr:
        garmindb = GarminDB.GarminDB(db_params_dict)
        last_ts = GarminDB.RestingHeartRate.latest_time(garmindb)
        date = datetime.datetime.now().date()
        if last_ts is None:
            days = 31
            logger.info("Automatic date not found, using: " + str(date))
        else:
            # start from the day after the last day in the DB
            logger.info("Automatically downloading rhr data from: " + str(last_ts))
            days = (date - last_ts).days

    if monitoring and days > 0:
        logger.info("Date range to update: %s (%d)" % (str(date), days))
        download.get_monitoring(date, days)
        download.unzip_files(monitoring)
        logger.info("Saved monitoring files for %s (%d) to %s for processing" % (str(date), days, monitoring))

    if sleep and days > 0:
        logger.info("Date range to update: %s (%d)" % (str(date), days))
        download.get_sleep(sleep, date, days)
        logger.info("Saved sleep files for %s (%d) to %s for processing" % (str(date), days, sleep))

    if weight and days > 0:
       download.get_weight(weight, date, days)

    if rhr and days > 0:
        download.get_rhr(rhr, date, days)


if __name__ == "__main__":
    main(sys.argv[1:])


