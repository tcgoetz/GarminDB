"""Base class for GarminDb plugins."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging

from .plugin_base import PluginBase


logger = logging.getLogger(__file__)


class ActivityFitPluginBase(PluginBase):
    """Base class for GarminDb activity FIT file plugins that handle data based on ids of applications or developer fields, sport or sub-sport ids, etc."""

    _type = 'ActivityFit'

    @classmethod
    def matches_activity_file(cls, fit_file):
        """Return if the file matches this plugin."""
        if hasattr(cls, '_application_id'):
            return cls._application_id in fit_file.dev_application_ids
        if hasattr(cls, '_sport') and (fit_file.sport_type is None or fit_file.sport_type.value is not cls._sport):
            return False
        if hasattr(cls, '_sub_sport') and (fit_file.sub_sport_type is None or fit_file.sub_sport_type.value is not cls._sub_sport):
            return False
        if hasattr(cls, '_dev_fields'):
            for dev_field in cls._dev_fields:
                if dev_field not in fit_file.dev_fields:
                    return False
        return True

    @classmethod
    def init_activity(cls, act_db_class, activities_table):
        """Initialize an instance of the plugin as an activity FIT file plugin."""
        logger.info("Initializing tables for activity plugin %s with activities table %s", cls.__name__, activities_table)
        if hasattr(cls, '_records_tablename') and 'record' not in cls._tables:
            cls._tables['record'] = activities_table.create(cls._records_tablename, act_db_class, cls._records_version, cls._records_pk, cls._records_cols)
        if hasattr(cls, '_laps_tablename') and 'lap' not in cls._tables:
            cls._tables['lap'] = activities_table.create(cls._laps_tablename, act_db_class, cls._laps_version, cls._laps_pk, cls._laps_cols)
        if hasattr(cls, '_sessions_tablename') and 'session' not in cls._tables:
            cls._tables['session'] = activities_table.create(cls._sessions_tablename, act_db_class, cls._sessions_version, cols=cls._sessions_cols,
                                                             create_view=cls._views['activity_view'], vars={'activities_table': activities_table})
