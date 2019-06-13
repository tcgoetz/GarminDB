#!/usr/bin/env python

#
# copyright Tom Goetz
#

import json, logging, traceback, sys
import dateutil.parser
import progressbar

import FileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class JsonFileProcessor(object):

    def __init__(self, input_file, input_dir, file_regex, latest, debug, recursive=False):
        self.debug = debug
        root_logger.info("Debug: %s", debug)
        if input_file:
            self.file_names = FileProcessor.FileProcessor.match_file(input_file, file_regex)
            root_logger.info("Found %d json files for %s in %s", self.file_count(), file_regex, input_file)
        if input_dir:
            self.file_names = FileProcessor.FileProcessor.dir_to_files(input_dir, file_regex, latest, recursive)
            root_logger.info("Found %d json files for %s in %s", self.file_count(), file_regex, input_dir)

    def file_count(self):
        return len(self.file_names)

    def parse_file(self, filename):
        def parser(entry):
            for (conversion_key, conversion_func) in self.conversions.iteritems():
                entry_value = entry.get(conversion_key)
                if entry_value is not None:
                    entry[conversion_key] = conversion_func(entry_value)
            return entry
        return json.load(open(filename), object_hook=parser)

    def get_field(self, json, fieldname, format_func=str):
        try:
            data = json[fieldname]
            if data is not None:
                return format_func(data)
        except KeyError as e:
            root_logger.debug("JSON %s not found in %r: %s", fieldname, json, e)

    def get_field_obj(self, json, fieldname, format_func):
        try:
            data = json[fieldname]
            return format_func(data)
        except KeyError as e:
            root_logger.debug("JSON %s not found in %r: %s", fieldname, json, e)

    def convert_to_json(self, object):
        return object.__str__()

    def save_json_file(self, json_full_filname, json_data):
        with open(json_full_filname, 'w') as file:
            root_logger.info("save_json_file: %s", json_full_filname)
            file.write(json.dumps(json_data, default=self.convert_to_json))

    def process_json(self, json_data):
        pass

    def commit(self):
        pass

    def process_files(self):
        root_logger.info("Processing %d json files", self.file_count())
        for file_name in progressbar.progressbar(self.file_names):
            try:
                json_data = self.parse_file(file_name)
                updates = self.process_json(json_data)
                if updates > 0:
                    root_logger.info("DB updated with %d entries from %s", updates, file_name)
                else:
                    root_logger.info("No data saved for %s", file_name)
            except Exception as e:
                root_logger.error("Failed to parse %s: %s", file_name, traceback.format_exc())
            self.commit()
        root_logger.info("DB updated with %d entries.", self.file_count())

    def process(self):
        self.process_files()
