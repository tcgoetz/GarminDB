"""Class for importing Garmin activity from FIT files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import fitfile

from .fit_data import FitData


class GarminActivitiesFitData(FitData):
    """Class for importing Garmin activity data from FIT files."""

    _progress_label = 'Processing activity FIT files'

    def __init__(self, input_dir, latest, measurement_system, debug, simple_output=False):
        """
        Return an instance of GarminActivitiesFitData.

        Parameters:
        ----------
        db_params (dict): configuration data for accessing the database
        input_dir (string): directory (full path) to check for data files
        latest (Boolean): check for latest files only
        measurement_system (enum): which measurement system to use when importing the files
        debug (Boolean): enable debug logging
        simple_output (Boolean): print progress as lines instead of a progress bar

        """
        super().__init__(input_dir, debug, latest, False, [fitfile.FileType.activity], measurement_system, simple_output=simple_output)
