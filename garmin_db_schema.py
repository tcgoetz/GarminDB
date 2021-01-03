"""Class that encapsulates config data for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


from sqlalchemy import Integer, Date, DateTime, Time, Float, String, Enum


class GarminDbSchema(object):
    """Class that describes the database layout for dynamic tables."""

    dev_db_config = {
        'version': 1,
        'tables': {
            'dev_table': {
                'version': 1,
                'pk': 'id',
                'cols': {
                    'id': Integer,
                    'hr': Integer
                }
            }
        }
    }
