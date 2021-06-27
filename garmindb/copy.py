"""Class for copying data from a USB mounted Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import sys
import shutil
from tqdm import tqdm
import logging

import fitfile
from idbutils import FileProcessor

from .config_manager import ConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class Copy(object):
    """Class for copying data from a USB mounted Garmin device."""

    def __init__(self, device_mount_dir):
        """Create a Copy object given the directory where the Garmin USB device is mounted."""
        self.device_mount_dir = device_mount_dir
        if not os.path.exists(self.device_mount_dir):
            raise RuntimeError(f'Device mount directory {self.device_mount_dir} not found')
        if not os.path.isdir(self.device_mount_dir):
            raise RuntimeError(f'Device mount directory {self.device_mount_dir} not a directory')

    def __copy(self, src_dir, dest_dir, latest=False):
        """Copy FIT files from a USB mounted Garmin device to the given directory."""
        file_names = FileProcessor.dir_to_files(src_dir, fitfile.file.name_regex, latest)
        logger.info("Copying files from %s to %s", src_dir, dest_dir)
        for file in tqdm(file_names, unit='files'):
            shutil.copy(file, dest_dir)

    def copy_activities(self, activities_dir, latest=False):
        """Copy activites data FIT files from a USB mounted Garmin device to the given directory."""
        device_activities_dir = ConfigManager.device_activities_dir(self.device_mount_dir)
        self.__copy(device_activities_dir, activities_dir, latest)

    def copy_monitoring(self, monitoring_dir, latest=False):
        """Copy daily monitoring data FIT files from a USB mounted Garmin device to the given directory."""
        device_monitoring_dir = ConfigManager.device_monitoring_dir(self.device_mount_dir)
        self.__copy(device_monitoring_dir, monitoring_dir, latest)

    def copy_sleep(self, monitoring_dir, latest=False):
        """Copy daily sleep data FIT files from a USB mounted Garmin device to the given directory."""
        device_sleep_dir = ConfigManager.device_sleep_dir(self.device_mount_dir)
        self.__copy(device_sleep_dir, monitoring_dir, latest)

    def copy_settings(self, settings_dir):
        """Copy settings FIT files from a USB mounted Garmin device to the given directory."""
        device_settings_dir = ConfigManager.device_settings_dir(self.device_mount_dir)
        self.__copy(device_settings_dir, settings_dir)
