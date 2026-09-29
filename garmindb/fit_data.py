"""Class for importing monitoring FIT files into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
import traceback

import fitfile
from idbutils import FileProcessor

from .progress import progress


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class FitData():
    """Class for importing FIT files into a database."""

    _progress_label = 'Processing FIT files'

    def __init__(self, input_dir, debug, latest=False, recursive=False, fit_types=None, measurement_system=fitfile.MeasurementSystem.metric, simple_output=False):
        """
        Return an instance of FitData.

        Parameters:
        input_dir (string): directory (full path) to check for monitoring data files
        debug (Boolean): enable debug logging
        latest (Boolean): check for latest files only
        fit_types (Fit.field_enums.FileType): check for this file type only
        measurement_system (enum): which measurement system to use when importing the files
        simple_output (Boolean): print progress as lines instead of a progress bar

        """
        logger.info("Processing %s FIT data from %s", fit_types, input_dir)
        self.measurement_system = measurement_system
        self.debug = debug
        self.simple_output = simple_output
        self.fit_types = fit_types
        self.file_names = sorted(FileProcessor.dir_to_files(input_dir, fitfile.file.name_regex, latest, recursive))

    def file_count(self):
        """Return the number of files that will be processed."""
        return len(self.file_names)

    def process_files(self, fit_file_processor):
        """Import FIT files into the database."""
        for file_name in progress(self.file_names, self._progress_label, unit='files', simple_output=self.simple_output):
            try:
                fit_file = fitfile.file.File(file_name, self.measurement_system)
                if self.fit_types is None or fit_file.type in self.fit_types:
                    fit_file_processor.write_file(fit_file)
                    root_logger.debug("Wrote %s to the database", fit_file)
                else:
                    root_logger.debug("skipping non-matching %s", fit_file)
            except Exception as e:
                logger.error("Failed to parse %s: %s", file_name, e)
                root_logger.error("Failed to parse %s: %s - %s", file_name, e, traceback.format_exc())
