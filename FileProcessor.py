"""Class for finding matching files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import os
import re
import datetime


logger = logging.getLogger(__file__)


class FileProcessor(object):
    """Class for finding matching files."""

    @classmethod
    def __regex_matches_file(cls, file, file_regex):
        return re.search(file_regex, file)

    @classmethod
    def match_file(cls, input_file, file_regex):
        """Test if a file matches a regex."""
        logger.info("Matching file: " + input_file)
        if cls.__regex_matches_file(input_file, file_regex):
            return [input_file]
        return []

    @classmethod
    def __file_newer_than(cls, file, timestamp):
        return datetime.datetime.fromtimestamp(os.stat(file).st_ctime) > timestamp

    @classmethod
    def dir_to_files(cls, input_dir, file_regex, latest=False, recursive=False):
        """Search a directory, p[ossibly recursively, and return a list of all files matching a regex."""
        logger.debug("Reading directory: %s looking for %s", input_dir, file_regex)
        file_names = []
        timestamp = datetime.datetime.now() - datetime.timedelta(1)
        for file in os.listdir(input_dir):
            file_with_path = input_dir + "/" + file
            if recursive and os.path.isdir(file_with_path):
                file_names = file_names + cls.dir_to_files(file_with_path, file_regex, latest)
            elif cls.__regex_matches_file(file, file_regex) and (not latest or cls.__file_newer_than(file_with_path, timestamp)):
                file_names.append(file_with_path)
        return file_names
