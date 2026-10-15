"""Objects for importing Garmin data from Garmin Connect downloads and FIT files."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging

from idbutils import JsonFileProcessor

from .garmindb import GarminDb, LifestyleLogging


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class GarminConnectLifestyleLogging(JsonFileProcessor):
    """Class for importing JSON formatted Garmin Connect lifestyle logging data into a database."""

    _progress_label = 'Processing lifestyle logging JSON files'

    def __init__(self, db_params, input_dir, latest, debug, simple_output=False):
        """
        Return an instance of GarminConnectLifestyleLogging.

        Parameters:
        ----------
        db_params (object): configuration data for accessing the database
        input_dir (string): directory (full path) to check for resting heart rate data files
        latest (Boolean): check for latest files only
        debug (Boolean): enable debug logging
        simple_output (Boolean): print progress as lines instead of a progress bar

        """
        logger.info("Processing lifesyle logging")
        super().__init__(r'lifestyle_logging_\d{4}-\d{2}-\d{2}\.json', input_dir=input_dir, latest=latest, debug=debug, simple_output=simple_output)
        self.garmin_db = GarminDb(db_params)
        self.conversions = {'calendarDate': self._parse_date}

    def _process_json(self, json_data):
        report_list = json_data.get('dailyLogsReport')
        if report_list and len(report_list) > 0:
            for report in report_list:
                logged = report.get('logStatus')
                if logged:
                    entry = {
                        'day': json_data['calendarDate'],
                        'name': report['name'],
                    }
                    details = report.get('details')
                    if details:
                        for detail in details:
                            entry.update({
                                'subtype_name': detail['subTypeName'],
                                'amount': detail['amount']
                            })
                            LifestyleLogging.insert_or_update(self.garmin_db, entry, ignore_none=True)
                    else:
                        entry.update({
                            'subtype_name': "",
                            'amount': 1
                        })
                        LifestyleLogging.insert_or_update(self.garmin_db, entry, ignore_none=True)
                    return len(report_list)
        return 0
