"""Class for importing monitoring FIT files into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
import progressbar

import Fit
from utilities import FileProcessor
from fit_file_processor import FitFileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class FitData(object):
    """Class for importing FIT files into a database."""

    def __init__(self, input_dir, debug, latest=False, fit_type=None, measurement_system=Fit.field_enums.DisplayMeasure.metric):
        """
        Return an instance of FitData.

        Parameters:
        input_dir (string): directory (full path) to check for monitoring data files
        debug (Boolean): enable debug logging
        latest (Boolean): check for latest files only
        fit_type (Fit.field_enums.FileType): check for this file type only
        measurement_system (enum): which measurement system to use when importing the files

        """
        logger.info("Processing %s FIT data", fit_type)
        self.measurement_system = measurement_system
        self.debug = debug
        self.fit_type = fit_type
        if input_dir:
            self.file_names = FileProcessor.dir_to_files(input_dir, Fit.file.name_regex, latest, True)

    def file_count(self):
        """Return the number of files that will be processed."""
        return len(self.file_names)

    def process_files(self, db_params_dict):
        """Import FIT files into the database."""
        fp = FitFileProcessor(db_params_dict, self.debug)
        for file_name in progressbar.progressbar(self.file_names):
            try:
                fit_file = Fit.file.File(file_name, self.measurement_system)
                if self.fit_type is None or fit_file.type() == self.fit_type:
                    fp.write_file(fit_file)
                else:
                    root_logger.info("skipping non %s file %s type %r message types %r",
                                     self.fit_type, file_name, fit_file.type(), fit_file.message_types())
            except Fit.exceptions.FitFileError as e:
                logger.error("Failed to parse %s: %s", file_name, e)
