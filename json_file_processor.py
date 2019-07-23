"""Class for parsing JSON formatted health data into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import json
import logging
import traceback
import sys
import progressbar

from file_processor import FileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class JsonFileProcessor(object):
    """Class for parsing JSON formatted health data into a database."""

    def __init__(self, input_file, input_dir, file_regex, latest, debug, recursive=False):
        """
        Return an instance of JsonFileProcessor.

        Parameters:
            input_file (string): file (full path) to check for data
            input_dir (string): directory (full path) to check for data files
            latest (Boolean): check for latest files only
            debug (Boolean): enable debug logging
            recursive (Boolean): check the search directory recursively

        """
        self.debug = debug
        root_logger.info("Debug: %s", debug)
        if input_file:
            self.file_names = FileProcessor.match_file(input_file, file_regex)
            root_logger.info("Found %d json files for %s in %s", self.file_count(), file_regex, input_file)
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, file_regex, latest, recursive)
            root_logger.info("Found %d json files for %s in %s", self.file_count(), file_regex, input_dir)

    def file_count(self):
        """Return the number of files that will be proccessed."""
        return len(self.file_names)

    def __parse_file(self, filename):
        def parser(entry):
            for (conversion_key, conversion_func) in self.conversions.iteritems():
                entry_value = entry.get(conversion_key)
                if entry_value is not None:
                    entry[conversion_key] = conversion_func(entry_value)
            return entry
        return json.load(open(filename), object_hook=parser)

    def _get_field(self, json, fieldname, format_func=str):
        try:
            data = json[fieldname]
            if data is not None:
                return format_func(data)
        except KeyError as e:
            root_logger.debug("JSON %s not found in %r: %s", fieldname, json, e)

    def _get_field_obj(self, json, fieldname, format_func):
        try:
            data = json[fieldname]
            return format_func(data)
        except KeyError as e:
            root_logger.debug("JSON %s not found in %r: %s", fieldname, json, e)

    def __convert_to_json(self, object):
        return object.__str__()

    def _save_json_file(self, json_full_filname, json_data):
        with open(json_full_filname, 'w') as file:
            root_logger.info("_save_json_file: %s", json_full_filname)
            file.write(json.dumps(json_data, default=self.__convert_to_json))

    def _process_json(self, json_data):
        pass

    def _commit(self):
        pass

    def call_process_func(self, name, id, json_data):
        """Call a JSON data processor function given it's base name."""
        process_function = '_process_' + name
        try:
            function = getattr(self, process_function, None)
            if function is not None:
                function(id, json_data)
            else:
                root_logger.warning("No handler %s from %s %s", process_function, id, self.__class__.__name__)
        except Exception as e:
            root_logger.error("Exception in %s from %s %s: %s", process_function, id, self.__class__.__name__, e)

    def _process_files(self):
        root_logger.info("Processing %d json files", self.file_count())
        for file_name in progressbar.progressbar(self.file_names):
            try:
                json_data = self.__parse_file(file_name)
                updates = self._process_json(json_data)
                if updates > 0:
                    root_logger.info("DB updated with %d entries from %s", updates, file_name)
                else:
                    root_logger.info("No data saved for %s", file_name)
            except Exception:
                root_logger.error("Failed to parse %s: %s", file_name, traceback.format_exc())
            self._commit()
        root_logger.info("DB updated with %d entries.", self.file_count())

    def process(self):
        """Import files into the databse."""
        self._process_files()
