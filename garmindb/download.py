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
from garth import Client as GarthClient
from tqdm import tqdm

import fitfile.conversions as conversions
from idbutils import RestClient, RestException, RestResponseException

from .garmin_connect_config_manager import GarminConnectConfigManager
from .config_manager import ConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class Download():
    """Class for downloading health data from Garmin Connect."""

    garmin_connect_base_url = "https://connect.garmin.com"
    garmin_connect_enus_url = garmin_connect_base_url + "/en-US"

    garmin_connect_sso_login = 'signin'
    garmin_connect_mfa_login = 'verifyMFA/loginEnterMfaCode'

    garmin_connect_login_url = garmin_connect_enus_url + "/signin"

    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

    garmin_connect_privacy_url = "//connect.garmin.com/en-U/privacy"

    garmin_connect_user_profile_url = "userprofile-service/userprofile"
    garmin_connect_wellness_url = "wellness-service/wellness"
    garmin_connect_sleep_daily_url = garmin_connect_wellness_url + "/dailySleepData"
    garmin_connect_rhr = "userstats-service/wellness/daily"
    garmin_connect_weight_url = "weight-service/weight/dateRange"

    garmin_connect_activity_search_url = "activitylist-service/activities/search/activities"

    garmin_connect_usersummary_url = "/usersummary-service/usersummary"
    garmin_connect_daily_summary_url = garmin_connect_usersummary_url + "/daily"
    garmin_connect_daily_hydration_url = garmin_connect_usersummary_url + "/hydration/allData"

    # https://connect.garmin.com/modern/proxy/usersummary-service/usersummary/hydration/allData/2019-11-29

    garmin_headers = {'NK': 'NT'}

    def __init__(self):
        """Create a new Download class instance."""
        logger.debug("__init__")
        self.session = cloudscraper.CloudScraper()
        self.garth = GarthClient(session=self.session)

    def __get_json(self, page_html, key):
        found = re.search(key + r" = (\{.*\});", page_html, re.M)
        if found:
            json_text = found.group(1).replace('\\"', '"')
            return json.loads(json_text)

    def login(self):
        """Login to Garmin Connect."""
        profile_dir = ConfigManager.get_or_create_fit_files_dir()
        self.gc_config = GarminConnectConfigManager()
        username = self.gc_config.get_user()
        password = self.gc_config.get_password()
        if not username or not password:
            print("Missing config: need username and password. Edit GarminConnectConfig.json.")
            return

        logger.debug("login: %s %s", username, password)
        self.garth.login(username, password)

        self.user_prefs = self.garth.profile

        self.garmin_headers['Authorization'] = str(self.garth.oauth2_token)

        self.modern_rest_client = RestClient(self.session, 'connectapi.garmin.com', '', aditional_headers=self.garmin_headers)
        self.activity_service_rest_client = RestClient.inherit(self.modern_rest_client, "activity-service/activity")
        self.download_service_rest_client = RestClient.inherit(self.modern_rest_client, "download-service/files")
        self.download_days_overlap = 3  # Existing donloaded data will be redownloaded and overwritten if it is within this number of days of now.

        if profile_dir:
            self.modern_rest_client.save_json_to_file(f'{profile_dir}/profile.json', self.user_prefs)
        self.display_name = self.user_prefs['displayName']
        self.social_profile = self.garth.profile
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

    @classmethod
    def __convert_to_json(cls, object):
        return object.__str__()

    @classmethod
    def save_json_to_file(cls, filename, json_data):
        """Save JSON formatted data to a file."""
        root_logger.info("Writing daily summary: %s with %s", filename, json_data)
        with open(filename, 'w') as file:
            file.write(json.dumps(json_data, default=cls.__convert_to_json))

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
        json_filename = f'{directory_func(date.year)}/daily_summary_{date_str}.json'
        try:
            self.save_json_to_file(json_filename, self.garth.download(url, params=params))
        except RestException as e:
            root_logger.error("Exception getting daily summary: %s", e)

    def get_daily_summaries(self, directory_func, date, days, overwite):
        """Download the daily summary data from Garmin Connect and save to a JSON file."""
        root_logger.info("Getting daily summaries: %s (%d)", date, days)
        self.__get_stat(self.__get_summary_day, directory_func, date, days, overwite)

    def __get_monitoring_day(self, date):
        root_logger.info("get_monitoring_day: %s to %s", date, self.temp_dir)
        zip_filename = f'{self.temp_dir}/{date}.zip'
        url = f'wellness/{date.strftime("%Y-%m-%d")}'
        try:
            self.download_service_rest_client.download_binary_file(url, zip_filename)
        except RestException as e:
            root_logger.error("Exception getting daily summary: %s", e)

    def get_monitoring(self, directory_func, date, days):
        """Download the daily monitoring data from Garmin Connect, unzip and save the raw files."""
        root_logger.info("Getting monitoring: %s (%d)", date, days)
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
            root_logger.error("Exception getting daily summary: %s", e)

    def get_weight(self, directory, date, days, overwite):
        """Download the sleep data from Garmin Connect and save to a JSON file."""
        root_logger.info("Getting weight: %s (%d)", date, days)
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
            root_logger.error("Exception getting activity summary: %s", e)

    def __save_activity_details(self, directory, activity_id_str, overwite):
        root_logger.debug("save_activity_details")
        json_filename = f'{directory}/activity_details_{activity_id_str}'
        try:
            self.activity_service_rest_client.download_json_file(activity_id_str, json_filename, overwite)
        except RestException as e:
            root_logger.error("Exception getting daily summary %s", e)

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
        logger.info("Getting activities: '%s' (%d) temp %s", directory, count, self.temp_dir)
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
            root_logger.error("Exception getting activity types: %s", e)

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
            root_logger.error("Exception getting daily summary: %s", e)

    def get_sleep(self, directory, date, days, overwite):
        """Download the sleep data from Garmin Connect and save to a JSON file."""
        root_logger.info("Getting sleep: %s (%d)", date, days)
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
            root_logger.error("Exception getting daily summary %s", e)

    def get_rhr(self, directory, date, days, overwite):
        """Download the resting heart rate data from Garmin Connect and save to a JSON file."""
        root_logger.info("Getting rhr: %s (%d)", date, days)
        self.__get_stat(self.__get_rhr_day, directory, date, days, overwite)

    def __get_hydration_day(self, directory_func, day, overwite=False):
        date_str = day.strftime('%Y-%m-%d')
        json_filename = f'{directory_func(day.year)}/hydration_{date_str}'
        url = f'{self.garmin_connect_daily_hydration_url}/{date_str}'
        try:
            self.modern_rest_client.download_json_file(url, json_filename, overwite)
        except RestException as e:
            root_logger.error("Exception getting hydration: %s", e)

    def get_hydration(self, directory_func, date, days, overwite):
        """Download the hydration data from Garmin Connect and save to a JSON file."""
        root_logger.info("Getting hydration: %s (%d)", date, days)
        self.__get_stat(self.__get_hydration_day, directory_func, date, days, overwite)
