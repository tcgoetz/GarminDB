#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, logging, datetime, time, tempfile, zipfile, json
import dateutil.parser
import requests
import progressbar

from GarminConnectConfigManager import GarminConnectConfigManager
import GarminDBConfigManager
import GarminDB
from Fit import Conversions


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class RESTClient(object):

    agents = {
        'Chrome_Linux'  : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1337 Safari/537.36',
        'Firefox_MacOS' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    agent = agents['Firefox_MacOS']

    default_headers = {
        'User-Agent'    : agent,
        'Accept'        : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    def __init__(self, session, base_route):
        self.session = session
        self.base_route = base_route

    @classmethod
    def inherit(cls, rest_client, route):
        return RESTClient(rest_client.session, '%s/%s' % (rest_client.base_route, route))

    def build_url(self, leaf_route):
        return '%s/%s' % (self.base_route, leaf_route)

    def get(self, leaf_route, aditional_headers={}, params={}):
        total_headers = self.default_headers.copy()
        total_headers.update(aditional_headers)
        response = self.session.get(self.build_url(leaf_route), headers=total_headers, params=params)
        root_logger.info("get: %s (%d)", response.url, response.status_code)
        return response

    def post(self, leaf_route, aditional_headers, params, data):
        total_headers = self.default_headers.copy()
        total_headers.update(aditional_headers)
        response = self.session.post(self.build_url(leaf_route), headers=total_headers, params=params, data=data)
        root_logger.info("post: %s (%d)", response.url, response.status_code)
        return response

    def convert_to_json(self, object):
        return object.__str__()

    def save_json_to_file(self, json_full_filename, json_data):
        with open(json_full_filename, 'w') as file:
            root_logger.info("save_json_to_file: %s", json_full_filename)
            file.write(json.dumps(json_data, default=self.convert_to_json))

    def download_json_file(self, url, params, json_filename, overwite):
        json_full_filname = json_filename + '.json'
        exists = os.path.isfile(json_full_filname)
        if not exists or overwite:
            root_logger.info("%s %s", 'Overwriting' if exists else 'Downloading', json_filename)
            response = self.get(url, params=params)
            if response.status_code != 200:
                logger.error("GET %s failed (%d): %s", response.url, response.status_code, response.text)
                return False
            self.save_json_to_file(json_full_filname, response.json())
        else:
            root_logger.info("Ignoring %s (exists)", json_filename)
        return True


class Download(object):

    garmin_connect_base_url = "https://connect.garmin.com"
    garmin_connect_enus_url = garmin_connect_base_url + "/en-US"

    garmin_sso_base_url = 'https://sso.garmin.com/sso'
    garmin_connect_sso_login = 'signin'

    garmin_connect_login_url = garmin_connect_enus_url + "/signin"

    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

    garmin_connect_privacy_url = "//connect.garmin.com/en-U/privacy"

    garmin_connect_modern_url = garmin_connect_base_url + "/modern"

    garmin_connect_modern_proxy = 'proxy'
    garmin_connect_download_service = garmin_connect_modern_proxy + "/download-service/files"

    garmin_connect_user_profile_url = garmin_connect_modern_proxy + "/userprofile-service/userprofile"
    garmin_connect_wellness_url = garmin_connect_modern_proxy + "/wellness-service/wellness"
    garmin_connect_sleep_daily_url = garmin_connect_wellness_url + "/dailySleepData"
    garmin_connect_rhr = garmin_connect_modern_proxy + "/userstats-service/wellness/daily"
    garmin_connect_weight_url = garmin_connect_modern_proxy + "/weight-service/weight/dateRange"

    garmin_connect_activity_service = garmin_connect_modern_proxy + "/activity-service/activity"
    garmin_connect_activity_search_url = garmin_connect_modern_proxy + "/activitylist-service/activities/search/activities"

    garmin_connect_usersummary_url = garmin_connect_modern_proxy + "/usersummary-service/usersummary"
    garmin_connect_daily_summary_url = garmin_connect_usersummary_url + "/daily/"


    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        logger.debug("__init__: temp_dir= " + self.temp_dir)
        self.session = requests.session()
        self.sso_rest_client = RESTClient(self.session, self.garmin_sso_base_url)
        self.rest_client = RESTClient(self.session, self.garmin_connect_modern_url)
        self.activity_service_rest_client = RESTClient.inherit(self.rest_client, self.garmin_connect_activity_service)
        self.download_service_rest_client = RESTClient.inherit(self.rest_client, self.garmin_connect_download_service)
        self.gc_gonfig = GarminConnectConfigManager()
        self.download_days_overlap = self.gc_gonfig.download_days_overlap()

    def get_json(self, page_html, key):
        found = re.search(key + r" = JSON.parse\(\"(.*)\"\);", page_html, re.M)
        if found:
            json_text = found.group(1).replace('\\"', '"')
            return json.loads(json_text)

    def login(self):
        profile_dir = GarminDBConfigManager.get_or_create_fit_files_dir()
        username = self.gc_gonfig.get_user()
        password = self.gc_gonfig.get_password()
        if not username or not password:
            print "Missing config: need username and password. Edit GarminConnectConfig.json."
            return

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
        response = self.sso_rest_client.get(self.garmin_connect_sso_login, get_headers, params)
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
            'username'  : username,
            'password'  : password,
            'embed'     : 'false',
            '_csrf'     : found.group(1)
        }
        post_headers = {
            'Referer'       : response.url,
            'Content-Type'  : 'application/x-www-form-urlencoded'
        }
        response = self.sso_rest_client.post(self.garmin_connect_sso_login, post_headers, params, data)
        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        if not found:
            logger.error("Login ticket not found (%d).", response.status_code)
            self.save_binary_file('login_post.html', response)
            return False

        params = {
            'ticket' : found.group(1)
        }
        response = self.rest_client.get('', params=params)
        if response.status_code != 200:
            logger.error("Login get homepage failed (%d).", response.status_code)
            self.save_binary_file('login_home.html', response)
            return False
        self.user_prefs = self.get_json(response.text, 'VIEWER_USERPREFERENCES')
        if profile_dir:
            self.rest_client.save_json_to_file(profile_dir + "/profile.json", self.user_prefs)
        self.display_name = self.user_prefs['displayName']
        self.social_profile = self.get_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.full_name = self.social_profile['fullName']
        root_logger.info("login: %s (%s)", self.full_name, self.display_name)
        return True

    def save_binary_file(self, filename, response):
        with open(filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)

    def unzip_files(self, outdir):
        logger.info("unzip_files: " + outdir)
        for filename in os.listdir(self.temp_dir):
            match = re.search('.*\.zip', filename)
            if match:
                files_zip = zipfile.ZipFile(self.temp_dir + "/" + filename, 'r')
                files_zip.extractall(outdir)
                files_zip.close()

    def get_stat(self, stat_function, directory, date, days, overwite):
        for day in progressbar.progressbar(xrange(0, days + 1)):
            download_date = date + datetime.timedelta(days=day)
            # always overight for yesterday and today since the last download may have been a partial result
            delta = datetime.datetime.now().date() - download_date
            if not stat_function(directory, download_date, overwite or delta.days <= self.download_days_overlap):
                break
            # pause for a second between every page access
            time.sleep(1)

    def get_summary_day(self, directory, date, overwite=False):
        root_logger.info("get_summary_day: %s", date)
        date_str = date.strftime('%Y-%m-%d')
        params = {
            'calendarDate' : date_str,
            '_'         : str(Conversions.dt_to_epoch_ms(Conversions.date_to_dt(date)))
        }
        url = self.garmin_connect_daily_summary_url + self.display_name
        return self.rest_client.download_json_file(url, params, directory + '/daily_summary_' + date_str, overwite)

    def get_daily_summaries(self, directory, date, days, overwite):
        root_logger.info("Geting daily summaries: %s (%d)", date, days)
        self.get_stat(self.get_summary_day, directory, date, days, overwite)

    def get_monitoring_day(self, date):
        root_logger.info("get_monitoring_day: %s", date)
        response = self.download_service_rest_client.get('wellness/' + date.strftime("%Y-%m-%d"))
        if response and response.status_code == 200:
            self.save_binary_file(self.temp_dir + '/' + str(date) + '.zip', response)

    def get_monitoring(self, date, days):
        root_logger.info("Geting monitoring: %s (%d)", date, days)
        for day in progressbar.progressbar(xrange(0, days + 1)):
            day_date = date + datetime.timedelta(day)
            self.get_monitoring_day(day_date)
            # pause for a second between every page access
            time.sleep(1)

    def get_weight_day(self, directory, day, overwite=False):
        root_logger.info("Checking weight: %s overwite %r", day, overwite)
        date_str = day.strftime('%Y-%m-%d')
        params = {
            'startDate' : date_str,
            'endDate'   : date_str,
            '_'         : str(Conversions.dt_to_epoch_ms(Conversions.date_to_dt(day)))
        }
        return self.rest_client.download_json_file(self.garmin_connect_weight_url, params, directory + '/weight_' + date_str, overwite)

    def get_weight(self, directory, date, days, overwite):
        root_logger.info("Geting weight: %s (%d)", date, days)
        self.get_stat(self.get_weight_day, directory, date, days, overwite)

    def get_activity_summaries(self, start, count):
        root_logger.info("get_activity_summaries")
        params = {
            'start' : str(start),
            "limit" : str(count)
        }
        response = self.rest_client.get(self.garmin_connect_activity_search_url, params=params)
        if response.status_code == 200:
            return response.json()

    def save_activity_details(self, directory, activity_id_str, overwite):
        root_logger.debug("save_activity_details")
        json_filename = directory + '/activity_details_' + activity_id_str
        return self.activity_service_rest_client.download_json_file(activity_id_str, None, json_filename, overwite)

    def save_activity_file(self, activity_id_str):
        root_logger.debug("save_activity_file: " + activity_id_str)
        response = self.download_service_rest_client.get('activity/' + activity_id_str)
        if response.status_code == 200:
            self.save_binary_file(self.temp_dir + '/activity_' + activity_id_str + '.zip', response)
        else:
            root_logger.error("save_activity_file: %s failed (%d): %s", response.url, response.status_code, response.text)

    def get_activities(self, directory, count, overwite=False):
        logger.info("Geting activities: '%s' (%d)", directory, count)
        activities = self.get_activity_summaries(0, count)
        for activity in progressbar.progressbar(activities):
            activity_id_str = str(activity['activityId'])
            activity_name_str = Conversions.printable(activity['activityName'])
            root_logger.info("get_activities: %s (%s)" % (activity_name_str, activity_id_str))
            json_filename = directory + '/activity_' + activity_id_str + '.json'
            if not os.path.isfile(json_filename) or overwite:
                root_logger.info("get_activities: %s <- %r" % (json_filename, activity))
                self.save_activity_details(directory, activity_id_str, overwite)
                self.rest_client.save_json_to_file(json_filename, activity)
                if not os.path.isfile(directory + '/' + activity_id_str + '.fit') or overwite:
                    self.save_activity_file(activity_id_str)
                # pause for a second between every page access
                time.sleep(1)

    def get_activity_types(self, directory, overwite):
        root_logger.info("get_activity_types: '%s'", directory)
        return self.activity_service_rest_client.download_json_file('activityTypes', None, directory + '/activity_types', overwite)

    def get_sleep_day(self, directory, date, overwite=False):
        json_filename = directory + '/sleep_' + str(date)
        params = {
            'date' : date.strftime("%Y-%m-%d")
        }
        return self.rest_client.download_json_file(self.garmin_connect_sleep_daily_url + '/' + self.display_name, params, json_filename, overwite)

    def get_sleep(self, directory, date, days, overwite):
        root_logger.info("Geting sleep: %s (%d)", date, days)
        self.get_stat(self.get_sleep_day, directory, date, days, overwite)

    def get_rhr_day(self, directory, day, overwite=False):
        date_str = day.strftime('%Y-%m-%d')
        json_filename = directory + '/rhr_' + date_str
        params = {
            'fromDate'  : date_str,
            'untilDate' : date_str,
            'metricId'  : 60
        }
        return self.rest_client.download_json_file(self.garmin_connect_rhr + '/' + self.display_name, params, json_filename, overwite)

    def get_rhr(self, directory, date, days, overwite):
        root_logger.info("Geting rhr: %s (%d)", date, days)
        self.get_stat(self.get_rhr_day, directory, date, days, overwite)
