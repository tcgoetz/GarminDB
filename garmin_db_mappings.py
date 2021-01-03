"""Class that encapsulates config data for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


class GarminDBMappings(object):
    """Class that encapsilates config data for the application."""

    dev_field_mapping = {
        'message_type': {
            'db': 'dev_data',
            'table': 'dev_table',
            'field_to_col': {
                'message_field1': 'id'
            }
        }
    }
