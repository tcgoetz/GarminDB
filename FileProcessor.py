#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, sys, os, re, datetime


logger = logging.getLogger(__file__)


class FileProcessor():

    @classmethod
    def regex_matches_file(cls, file, file_regex):
        return re.search(file_regex, file)

    @classmethod
    def match_file(cls, input_file, file_regex):
        logger.info("Reading file: " + input_file)
        if cls.regex_matches_file(input_file, file_regex):
            return [input_file]
        return []

    @classmethod
    def file_newer_than(cls, file, timestamp):
        return datetime.datetime.fromtimestamp(os.stat(file).st_ctime) > timestamp

    @classmethod
    def dir_to_files(cls, input_dir, file_regex, latest=False):
        logger.info("Reading directory: " + input_dir)
        file_names = []
        timestamp = datetime.datetime.now() - datetime.timedelta(1)
        for file in os.listdir(input_dir):
            file_with_path = input_dir + "/" + file
            if cls.regex_matches_file(file, file_regex) and (not latest or cls.file_newer_than(file_with_path, timestamp)):
                file_names.append(file_with_path)
        return file_names
