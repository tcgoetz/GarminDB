"""Class for downloading health data from Garmin Connect."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import sys
import re
import logging
import datetime
import time
import tempfile
import zipfile
import json
import cloudscraper
from tqdm import tqdm

import fitfile.conversions as conversions
from idbutils import RestClient, RestException, RestResponseException

from .garmin_connect_config_manager import GarminConnectConfigManager
from .config_manager import ConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class Download(object):
    """Class for downloading health data from Garmin Connect."""

    garmin_connect_base_url = "https://connect.garmin.com"
    garmin_connect_enus_url = garmin_connect_base_url + "/en-US"

    garmin_connect_sso_login = 'signin'

    garmin_connect_login_url = garmin_connect_enus_url + "/signin"

    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

    garmin_connect_privacy_url = "//connect.garmin.com/en-U/privacy"

    garmin_connect_user_profile_url = "proxy/userprofile-service/userprofile"
    garmin_connect_wellness_url = "proxy/wellness-service/wellness"
    garmin_connect_sleep_daily_url = garmin_connect_wellness_url + "/dailySleepData"
    garmin_connect_rhr = "proxy/userstats-service/wellness/daily"
    garmin_connect_weight_url = "proxy/weight-service/weight/dateRange"

    garmin_connect_activity_search_url = "proxy/activitylist-service/activities/search/activities"

    garmin_connect_usersummary_url = "proxy/usersummary-service/usersummary"
    garmin_connect_daily_summary_url = garmin_connect_usersummary_url + "/daily"
    garmin_connect_daily_hydration_url = garmin_connect_usersummary_url + "/hydration/allData"

    # https://connect.garmin.com/modern/proxy/usersummary-service/usersummary/hydration/allData/2019-11-29

    garmin_headers = {'NK': 'NT'}

    def __init__(self):
        """Create a new Download class instance."""
        logger.debug("__init__")
        self.session = cloudscraper.CloudScraper()
        self.sso_rest_client = RestClient(self.session, 'sso.garmin.com', 'sso', aditional_headers=self.garmin_headers)
        self.modern_rest_client = RestClient(self.session, 'connect.garmin.com', 'modern', aditional_headers=self.garmin_headers)
        self.activity_service_rest_client = RestClient.inherit(self.modern_rest_client, "proxy/activity-service/activity")
        self.download_service_rest_client = RestClient.inherit(self.modern_rest_client, "proxy/download-service/files")
        self.gc_config = GarminConnectConfigManager()
        self.download_days_overlap = 3  # Existing donloaded data will be redownloaded and overwritten if it is within this number of days of now.

    def __get_json(self, page_html, key):
        found = re.search(key + r" = (\{.*\});", page_html, re.M)
        if found:
            json_text = found.group(1).replace('\\"', '"')
            return json.loads(json_text)

    def login(self):
        """Login to Garmin Connect."""
        profile_dir = ConfigManager.get_or_create_fit_files_dir()
        username = self.gc_config.get_user()
        password = self.gc_config.get_password()
        if not username or not password:
            print("Missing config: need username and password. Edit GarminConnectConfig.json.")
            return

        logger.debug("login: %s %s", username, password)
        get_headers = {
            'Referer'                           : self.garmin_connect_login_url
        }
        params = {
            'service'                           : self.modern_rest_client.url(),
            'webhost'                           : self.garmin_connect_base_url,
            'source'                            : self.garmin_connect_login_url,
            'redirectAfterAccountLoginUrl'      : self.modern_rest_client.url(),
            'redirectAfterAccountCreationUrl'   : self.modern_rest_client.url(),
            'gauthHost'                         : self.sso_rest_client.url(),
            'locale'                            : 'en_US',
            'id'                                : 'gauth-widget',
            'cssUrl'                            : self.garmin_connect_css_url,
            'privacyStatementUrl'               : '//connect.garmin.com/en-US/privacy/',
            'clientId'                          : 'GarminConnect',
            'rememberMeShown'                   : 'true',
            'rememberMeChecked'                 : 'false',
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
        try:
            response = self.sso_rest_client.get(self.garmin_connect_sso_login, get_headers, params)
        except RestResponseException as e:
            root_logger.error("Exception during login get: %s", e)
            RestClient.save_binary_file('login_get.html', e.response)
            return False
        found = re.search(r"name=\"_csrf\" value=\"(\w*)", response.text, re.M)
        if not found:
            logger.error("_csrf not found: %s", response.status_code)
            RestClient.save_binary_file('login_get.html', response)
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
        try:
            response = self.sso_rest_client.post(self.garmin_connect_sso_login, post_headers, params, data)
        except RestException as e:
            root_logger.error("Exception during login post: %s", e)
            return False
        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        if not found:
            logger.error("Login ticket not found (%d).", response.status_code)
            RestClient.save_binary_file('login_post.html', response)
            return False
        params = {
            'ticket' : found.group(1)
        }
        try:
            response = self.modern_rest_client.get('', params=params)
        except RestException:
            logger.error("Login get homepage failed (%d).", response.status_code)
            RestClient.save_binary_file('login_home.html', response)
            return False
        self.user_prefs = self.__get_json(response.text, 'VIEWER_USERPREFERENCES')
        if profile_dir:
            self.modern_rest_client.save_json_to_file(f'{profile_dir}/profile.json', self.user_prefs)
        self.display_name = self.user_prefs['displayName']
        self.social_profile = self.__get_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.full_name = self.social_profile['fullName']
        root_logger.info("login: %s (%s)", self.full_name, self.display_name)
        return True

    def __unzip_files(self, outdir):
        """Unzip and downloaded zipped files into the directory supplied."""
        root_logger.info("unzip_files: from %s to %s", self.temp_dir, outdir)
        for filename in os.listdir(self.temp_dir):
            match = re.search(r'.*\.zip', filename)
            if match:
                full_pathname = f'{self.temp_dir}/{filename}'
                with zipfile.ZipFile(full_pathname, 'r') as files_zip:
                    try:
                        files_zip.extractall(outdir)
                    except Exception as e:
                        logger.error('Failed to unzip %s to %s: %s', full_pathname, outdir, e)

    def __get_stat(self, stat_function, directory, date, days, overwite):
        for day in tqdm(range(0, days), unit='days'):
            download_date = date + datetime.timedelta(days=day)
            # always overwrite for yesterday and today since the last download may have been a partial result
            delta = datetime.datetime.now().date() - download_date
            stat_function(directory, download_date, overwite or delta.days <= self.download_days_overlap)
            # pause for a second between every page access
            time.sleep(1)

    def __get_summary_day(self, directory_func, date, overwite=False):
        root_logger.info("get_summary_day: %s", date)
        date_str = date.strftime('%Y-%m-%d')
        params = {
            'calendarDate': date_str,
            '_': str(conversions.dt_to_epoch_ms(conversions.date_to_dt(date)))
        }
        url = f'{self.garmin_connect_daily_summary_url}/{self.display_name}'
        json_filename = f'{directory_func(date.year)}/daily_summary_{date_str}'
        try:
            self.modern_rest_client.download_json_file(url, json_filename, overwite, params)
        except RestException as e:
            root_logger.error("Exception geting daily summary: %s", e)

    def get_daily_summaries(self, directory_func, date, days, overwite):
        """Download the daily summary data from Garmin Connect and save to a JSON file."""
        root_logger.info("Geting daily summaries: %s (%d)", date, days)
        self.__get_stat(self.__get_summary_day, directory_func, date, days, overwite)

    def __get_monitoring_day(self, date):
        root_logger.info("get_monitoring_day: %s to %s", date, self.temp_dir)
        zip_filename = f'{self.temp_dir}/{date}.zip'
        url = f'wellness/{date.strftime("%Y-%m-%d")}'
        try:
            self.download_service_rest_client.download_binary_file(url, zip_filename)
        except RestException as e:
            root_logger.error("Exception geting daily summary: %s", e)

    def get_monitoring(self, directory_func, date, days):
        """Download the daily monitoring data from Garmin Connect, unzip and save the raw files."""
        root_logger.info("Geting monitoring: %s (%d)", date, days)
        for day in tqdm(range(0, days + 1), unit='days'):
            day_date = date + datetime.timedelta(day)
            self.temp_dir = tempfile.mkdtemp()
            self.__get_monitoring_day(day_date)
            self.__unzip_files(directory_func(day_date.year))
            # pause for a second between every page access
            time.sleep(1)

    def __get_weight_day(self, directory, day, overwite=False):
        root_logger.info("Checking weight: %s overwite %r", day, overwite)
        date_str = day.strftime('%Y-%m-%d')
        params = {
            'startDate' : date_str,
            'endDate'   : date_str,
            '_'         : str(conversions.dt_to_epoch_ms(conversions.date_to_dt(day)))
        }
        json_filename = f'{directory}/weight_{date_str}'
        try:
            self.modern_rest_client.download_json_file(self.garmin_connect_weight_url, json_filename, overwite, params)
        except RestException as e:
            root_logger.error("Exception geting daily summary: %s", e)

    def get_weight(self, directory, date, days, overwite):
        """Download the sleep data from Garmin Connect and save to a JSON file."""
        root_logger.info("Geting weight: %s (%d)", date, days)
        self.__get_stat(self.__get_weight_day, directory, date, days, overwite)

    def __get_activity_summaries(self, start, count):
        root_logger.info("get_activity_summaries")
        params = {
            'start' : str(start),
            "limit" : str(count)
        }
        try:
            response = self.modern_rest_client.get(self.garmin_connect_activity_search_url, params=params)
            return response.json()
        except RestException as e:
            root_logger.error("Exception geting activity summary: %s", e)

    def __save_activity_details(self, directory, activity_id_str, overwite):
        root_logger.debug("save_activity_details")
        json_filename = f'{directory}/activity_details_{activity_id_str}'
        try:
            self.activity_service_rest_client.download_json_file(activity_id_str, json_filename, overwite)
        except RestException as e:
            root_logger.error("Exception geting daily summary %s", e)

    def __save_activity_file(self, activity_id_str):
        root_logger.debug("save_activity_file: %s", activity_id_str)
        zip_filename = f'{self.temp_dir}/activity_{activity_id_str}.zip'
        url = f'activity/{activity_id_str}'
        try:
            self.download_service_rest_client.download_binary_file(url, zip_filename)
        except RestException as e:
            root_logger.error("Exception downloading activity file: %s", e)

    def get_activities(self, directory, count, overwite=False):
        """Download activities files from Garmin Connect and save the raw files."""
        self.temp_dir = tempfile.mkdtemp()
        logger.info("Geting activities: '%s' (%d) temp %s", directory, count, self.temp_dir)
        activities = self.__get_activity_summaries(0, count)
        for activity in tqdm(activities or [], unit='activities'):
            activity_id_str = str(activity['activityId'])
            activity_name_str = conversions.printable(activity['activityName'])
            root_logger.info("get_activities: %s (%s)", activity_name_str, activity_id_str)
            json_filename = f'{directory}/activity_{activity_id_str}.json'
            if not os.path.isfile(json_filename) or overwite:
                root_logger.info("get_activities: %s <- %r", json_filename, activity)
                self.__save_activity_details(directory, activity_id_str, overwite)
                self.modern_rest_client.save_json_to_file(json_filename, activity)
                if not os.path.isfile(f'{directory}/{activity_id_str}.fit') or overwite:
                    self.__save_activity_file(activity_id_str)
                # pause for a second between every page access
                time.sleep(1)
        self.__unzip_files(directory)

    def get_activity_types(self, directory, overwite):
        """Download the activity types from Garmin Connect and save to a JSON file."""
        root_logger.info("get_activity_types: '%s'", directory)
        json_filename = f'{directory}/activity_types'
        try:
            self.activity_service_rest_client.download_json_file('activityTypes', json_filename, overwite)
        except RestException as e:
            root_logger.error("Exception geting activity types: %s", e)

    def __get_sleep_day(self, directory, date, overwite=False):
        json_filename = f'{directory}/sleep_{date}'
        params = {
            'date'                  : date.strftime("%Y-%m-%d"),
            'nonSleepBufferMinutes' : 60
        }
        url = f'{self.garmin_connect_sleep_daily_url}/{self.display_name}'
        try:
            self.modern_rest_client.download_json_file(url, json_filename, overwite, params)
        except RestException as e:
            root_logger.error("Exception geting daily summary: %s", e)

    def get_sleep(self, directory, date, days, overwite):
        """Download the sleep data from Garmin Connect and save to a JSON file."""
        root_logger.info("Geting sleep: %s (%d)", date, days)
        self.__get_stat(self.__get_sleep_day, directory, date, days, overwite)

    def __get_rhr_day(self, directory, day, overwite=False):
        date_str = day.strftime('%Y-%m-%d')
        json_filename = f'{directory}/rhr_{date_str}'
        params = {
            'fromDate'  : date_str,
            'untilDate' : date_str,
            'metricId'  : 60
        }
        url = f'{self.garmin_connect_rhr}/{self.display_name}'
        try:
            self.modern_rest_client.download_json_file(url, json_filename, overwite, params)
        except RestException as e:
            root_logger.error("Exception geting daily summary %s", e)

    def get_rhr(self, directory, date, days, overwite):
        """Download the resting heart rate data from Garmin Connect and save to a JSON file."""
        root_logger.info("Geting rhr: %s (%d)", date, days)
        self.__get_stat(self.__get_rhr_day, directory, date, days, overwite)

    def __get_hydration_day(self, directory_func, day, overwite=False):
        date_str = day.strftime('%Y-%m-%d')
        json_filename = f'{directory_func(day.year)}/hydration_{date_str}'
        url = f'{self.garmin_connect_daily_hydration_url}/{date_str}'
        try:
            self.modern_rest_client.download_json_file(url, json_filename, overwite)
        except RestException as e:
            root_logger.error("Exception geting hydration: %s", e)

    def get_hydration(self, directory_func, date, days, overwite):
        """Download the hydration data from Garmin Connect and save to a JSON file."""
        root_logger.info("Geting hydration: %s (%d)", date, days)
        self.__get_stat(self.__get_hydration_day, directory_func, date, days, overwite)
