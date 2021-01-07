"""Base classes for plugins."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging

import GarminDB
import utilities


logger = logging.getLogger(__file__)


class GarminDbPlugin(utilities.Plugin):
    """Base class for all GarminDb plugins."""

    def __init__(self):
        """Base class for all GarminDb plugins."""
        super().__init__(utilities.DynamicDb, GarminDB.ActivitiesDB)

    @classmethod
    def _load_custom_db(cls, db_name, db_version):
        return utilities.DynamicDb.Create(db_name, db_version)

    @classmethod
    def _load_custom_table(cls, db, table_name, table_version, table_pk, table_cols):
        return utilities.DynamicDb.CreateTable(table_name, db, table_version, table_pk, table_cols)

    def write_message_type(self, fit_file, message_type, message):
        handler_name = '_write_' + message_type.name + '_entry'
        function = getattr(self, handler_name, None)
        if function:
            function(fit_file, message.fields)

    @classmethod
    def _pre_message_handler(cls):
        pass

    @classmethod
    def _post_message_handler(cls):
        pass


class GarminDbPluginManager(utilities.PluginManager):
    """Loads python file based plugins that extend GarminDb."""

    def __init__(self, plugin_dir, db_params):
        """Load python file based plugins from plugin_dir."""
        logger.info("Loading GarminDb plugins from %s", plugin_dir)
        super().__init__(plugin_dir, GarminDbPlugin, {'db_params': db_params})

    def get_activity_processors(self, fit_file):
        """Return a dict of all plugins that handle FIT file messages."""
        result = {}
        for plugin_name, plugin in self.plugins.items():
            if plugin.matches_activity(fit_file):
                result[plugin_name] = plugin
        return result
