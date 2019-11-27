"""Class for copying data from a USB mounted Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import sys
import shutil
import progressbar
import logging

import Fit
from utilities import FileProcessor
import garmin_db_config_manager as GarminDBConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class Copy(object):
    """Class for copying data from a USB mounted Garmin device."""

    def __init__(self, device_mount_dir):
        """Create a Copy object given the directory where the Garmin USB device is mounted."""
        self.device_mount_dir = device_mount_dir
        if not os.path.exists(self.device_mount_dir):
            raise RuntimeError('%s not found' % self.device_mount_dir)
        if not os.path.isdir(self.device_mount_dir):
            raise RuntimeError('%s not a directory' % self.device_mount_dir)

    def __copy(self, src_dir, dest_dir, latest=False):
        """Copy FIT files from a USB mounted Garmin device to the given directory."""
        file_names = FileProcessor.dir_to_files(src_dir, Fit.file.name_regex, latest)
        logger.info("Copying files from %s to %s", src_dir, dest_dir)
        for file in progressbar.progressbar(file_names):
            shutil.copy(file, dest_dir)

    def copy_activities(self, activities_dir, latest):
        """Copy activites data FIT files from a USB mounted Garmin device to the given directory."""
        device_activities_dir = GarminDBConfigManager.device_activities_dir(self.device_mount_dir)
        self.__copy(device_activities_dir, activities_dir, latest)

    def copy_monitoring(self, monitoring_dir, latest):
        """Copy daily monitoring data FIT files from a USB mounted Garmin device to the given directory."""
        device_monitoring_dir = GarminDBConfigManager.device_monitoring_dir(self.device_mount_dir)
        self.__copy(device_monitoring_dir, monitoring_dir, latest)

    def copy_settings(self, settings_dir):
        """Copy settings FIT files from a USB mounted Garmin device to the given directory."""
        device_settings_dir = GarminDBConfigManager.device_settings_dir(self.device_mount_dir)
        self.__copy(device_settings_dir, settings_dir)
