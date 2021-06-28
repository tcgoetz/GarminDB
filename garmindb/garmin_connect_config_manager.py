"""Class that manages Garmin Connect download config."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import sys
import platform
import subprocess
import datetime

from idbutils import JsonConfig

from .statistics import Statistics
from .config_manager import ConfigManager


class GarminConnectConfigManager(JsonConfig):
    """Class that manages Garmin Connect downloads."""

    def __init__(self):
        """Return a new GarminConnectConfigManager instance."""
        self.enabled_statistics = None
        config_file = ConfigManager.get_config_file()
        try:
            super().__init__(config_file)
        except Exception as e:
            print(str(e))
            print(f"Missing config: copy GarminConnectConfig.json.example from {os.path.dirname(os.path.abspath(__file__))} to {config_file} and edit it to "
                  "add your Garmin Connect username and password.")
            sys.exit(-1)

    def __get_node_value(self, node, leaf):
        node = self.config.get(node)
        if node is not None:
            return node.get(leaf)

    def __get_node_value_default(self, node, leaf, default):
        node = self.config.get(node)
        if node is not None:
            return node.get(leaf, default)
        return default

    def get_secure_password(self):
        """Return the Garmin Connect password from secure storage. On MacOS that si the KeyChain."""
        system = platform.system()
        if system == 'Darwin':
            password = subprocess.check_output(["security", "find-internet-password", "-s", "sso.garmin.com", "-w"])
            if password:
                return password.rstrip()

    def get_user(self):
        """Return the Garmin Connect username."""
        return self.__get_node_value('credentials', 'user')

    def get_password(self):
        """Return the Garmin Connect password."""
        password = self.__get_node_value('credentials', 'password')
        if not password:
            password = self.get_secure_password()
        return password

    def latest_activity_count(self):
        """Return the number of activities to download when getting the latest."""
        return self.__get_node_value('data', 'download_latest_activities')

    def all_activity_count(self):
        """Return the number of activities to download when getting all activities."""
        return self.__get_node_value('data', 'download_all_activities')

    def stat_start_date(self, stat_type):
        """Return a tuple containing the start date and the number of days to fetch stats from."""
        date = self.__get_node_value('data', stat_type + '_start_date')
        days = (datetime.datetime.now().date() - date).days
        return (date, days)

    def device_mount_dir(self):
        """Return the directory where the Garmin USB device is mounted."""
        return self.__get_node_value('copy', 'mount_dir')

    def download_days_overlap(self):
        """Return the number of days to overlap previously downloaded data when downloading."""
        return self.__get_node_value('data', 'download_days_overlap')

    def course_views(self, type):
        """Return a list of course ids to create views for for the given activitiy type."""
        return self.__get_node_value('course_views', type)

    def is_stat_enabled(self, statistic):
        """Return whether a particular statistic is enabled or not."""
        return statistic in self.enabled_stats()

    def enabled_stats(self):
        """Return all enabled statistics as a list of string names."""
        if not self.enabled_statistics:
            json_enabled_stats_dict = self.config.get('enabled_stats', {stat_name: True for stat_name in list(Statistics)})
            self.enabled_statistics = [Statistics.from_string(stat_name) for stat_name, stat_enabled in json_enabled_stats_dict.items() if stat_enabled]
        return self.enabled_statistics
