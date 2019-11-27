"""Class that manages Garmin Connect download config."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import platform
import subprocess
from utilities import JsonConfig


class GarminConnectConfigManager(JsonConfig):
    """Class that manages Garmin Connect downloads."""

    config_filename = 'GarminConnectConfig.json'

    def __init__(self):
        """Return a new GarminConnectConfigManager instance."""
        try:
            super().__init__(self.config_filename)
        except Exception as e:
            print(str(e))
            print("Missing config: copy GarminConnectConfig.json.example to GarminConnectConfig.json and edit GarminConnectConfig.json to "
                  "add your Garmin Connect username and password.")
            sys.exit(-1)

    def get_secure_password(self):
        """Return the Garmin Connect password from secure storage. On MacOS that si the KeyChain."""
        system = platform.system()
        if system == 'Darwin':
            password = subprocess.check_output(["security", "find-internet-password", "-s", "sso.garmin.com", "-w"])
            if password:
                return password.rstrip()

    def get_user(self):
        """Return the Garmin Connect username."""
        return self.config['credentials']['user']

    def get_password(self):
        """Return the Garmin Connect password."""
        password = self.config['credentials']['password']
        if not password:
            password = self.get_secure_password()
        return password

    def latest_activity_count(self):
        """Return the number of activities to download when getting the latest."""
        return self.config['data']['download_latest_activities']

    def all_activity_count(self):
        """Return the number of activities to download when getting all activities."""
        return self.config['data']['download_all_activities']

    def stat_start_date(self, stat_type):
        """Return a tuple containing the start date and the number of days to fetch stats from."""
        date = self.config['data'][stat_type + '_start_date']
        days = self.config['data']['download_days']
        return (date, days)

    def device_mount_dir(self):
        """Return the directory where the Garmin USB device is mounted."""
        return self.config['copy']['mount_dir']

    def download_days_overlap(self):
        """Return the number of days to overlap previously downloaded data when downloading."""
        return self.config['data']['download_days_overlap']
