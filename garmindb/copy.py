"""Class for copying data from a USB mounted Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import sys
import shutil
from tqdm import tqdm
import logging
from datetime import datetime

import fitfile
from idbutils import FileProcessor

from .garmin_connect_config_manager import GarminConnectConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class Copy():
    """Class for copying data from a USB mounted Garmin device."""

    def __init__(self):
        """Create a Copy object given the directory where the Garmin USB device is mounted."""
        self.gc_config = GarminConnectConfigManager()
        device_mount_dir = self.gc_config.device_mount_dir()
        if not os.path.exists(device_mount_dir):
            raise RuntimeError(f'Device mount directory {device_mount_dir} not found')
        if not os.path.isdir(device_mount_dir):
            raise RuntimeError(f'Device mount directory {device_mount_dir} not a directory')

    def __copy(self, src_dir, dest_dir, latest=False, parse_as_ts=False, fn_suffix='WELLNESS'):
        """Copy FIT files from a USB mounted Garmin device to the given directory."""
        file_names = FileProcessor.dir_to_files(src_dir, fitfile.file.name_regex, latest)
        logger.info("Copying files from %s to %s", src_dir, dest_dir)
        for file in tqdm(file_names, unit='files'):
            dest = dest_dir
            if parse_as_ts:
                dt = os.path.basename(file).split('.fit')[0]
                ts = datetime.strptime(dt, '%Y-%m-%d-%H-%M-%S').timestamp()
                dest = os.path.join(dest_dir, f'{ts:.0f}') + fn_suffix + '.fit'
            shutil.copy(file, dest)

    def copy_activities(self, activities_dir, latest=False):
        """Copy activites data FIT files from a USB mounted Garmin device to the given directory."""
        device_activities_dir = self.gc_config.device_activities_dir()
        self.__copy(device_activities_dir, activities_dir, latest, True, '_activities')

    def copy_monitoring(self, monitoring_dir, latest=False):
        """Copy daily monitoring data FIT files from a USB mounted Garmin device to the given directory."""
        device_monitoring_dir = self.gc_config.device_monitoring_dir()
        self.__copy(device_monitoring_dir, monitoring_dir, latest)

    def copy_sleep(self, monitoring_dir, latest=False):
        """Copy daily sleep data FIT files from a USB mounted Garmin device to the given directory."""
        device_sleep_dir = self.gc_config.device_sleep_dir()
        self.__copy(device_sleep_dir, monitoring_dir, latest)

    def copy_settings(self, settings_dir):
        """Copy settings FIT files from a USB mounted Garmin device to the given directory."""
        device_settings_dir = self.gc_config.device_settings_dir()
        self.__copy(device_settings_dir, settings_dir)
