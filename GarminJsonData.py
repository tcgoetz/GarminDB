#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, json

import FileProcessor


logger = logging.getLogger(__file__)


class GarminJsonData():

    def __init__(self, input_file, input_dir, file_regex, latest, english_units, debug):
        self.english_units = english_units
        self.debug = debug
        logger.info("Debug: %s", str(debug))
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, file_regex)
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, file_regex, latest)

    def file_count(self):
        return len(self.file_names)

    def get_garmin_json_data(self, json, fieldname, format_func=str):
        try:
            data = json[fieldname]
            if data is not None:
                return format_func(data)
        except KeyError as e:
            logger.error("JSON %s not found in %s: %s", fieldname, repr(json), str(e))

    def process_files(self):
        for file_name in self.file_names:
            logger.info("Processing: %s", file_name)
            json_data = json.load(open(file_name))
            self.process_json(json_data)
