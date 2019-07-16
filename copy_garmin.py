#
# copyright Tom Goetz
#

import os
import sys
import shutil
import progressbar
import logging

import Fit
from FileProcessor import FileProcessor
import GarminDBConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class Copy(object):

    def __init__(self, device_mount_dir):
        self.device_mount_dir = device_mount_dir
        if not os.path.exists(self.device_mount_dir):
            raise RuntimeError('%s not found' % self.device_mount_dir)
        if not os.path.isdir(self.device_mount_dir):
            raise RuntimeError('%s not a directory' % self.device_mount_dir)

    def copy_activities(self, activities_dir, latest):
        device_activities_dir = GarminDBConfigManager.device_activities_dir(self.device_mount_dir)
        logger.info("Copying activities files from %s to %s", device_activities_dir, activities_dir)
        file_names = FileProcessor.dir_to_files(device_activities_dir, Fit.File.name_regex, latest)
        for file in progressbar.progressbar(file_names):
            shutil.copy(file, activities_dir)

    def copy_monitoring(self, monitoring_dir, latest):
        device_monitoring_dir = GarminDBConfigManager.device_monitoring_dir(self.device_mount_dir)
        logger.info("Copying monitoring files from %s to %s", device_monitoring_dir, monitoring_dir)
        file_names = FileProcessor.dir_to_files(device_monitoring_dir, Fit.File.name_regex, latest)
        for file in progressbar.progressbar(file_names):
            shutil.copy(file, monitoring_dir)
