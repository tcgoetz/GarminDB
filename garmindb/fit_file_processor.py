"""Class that takes a parsed FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import traceback

import fitfile

from .garmindb import GarminDb, File, Device, DeviceInfo, Stress, Attributes


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class FitFileProcessor():
    """Class that takes a parsed FIT file object and imports it into a database."""

    def __init__(self, db_params, plugin_manager=None, debug=0):
        """
        Return a new FitFileProcessor instance.

        Paramters:
        db_params (dict): database access configuration
        debug (Boolean): if True, debug logging is enabled
        """
        root_logger.info("Debug: %s", debug)
        self.plugin_manager = plugin_manager
        self.db_params = db_params
        self.debug = debug
        self.garmin_db = GarminDb(db_params, debug - 1)

    def _plugin_dispatch(self, plugins, handler_name, *args, **kwargs):
        result = {}
        for plugin in plugins:
            function = getattr(plugin, handler_name, None)
            if function:
                result.update(function(*args, **kwargs))
        return result

    def __write_generic(self, fit_file, message_type, messages):
        """Write all messages of a given message type to the database."""
        handler_name = '_write_' + message_type.name + '_entry'
        function = getattr(self, handler_name, None)
        if function is not None:
            for message in messages:
                try:
                    function(fit_file, message.fields)
                except Exception as e:
                    logger.error("Failed to write message %r type %r: %s", message_type, message, e)
                    root_logger.error("Failed to write message %r type %r: %s", message_type, message, traceback.format_exc())
        elif isinstance(message_type, fitfile.UnknownMessageType) or message_type.is_unknown():
            root_logger.debug("No entry handler %s for message type %r (%d) from %s: %s",
                              handler_name, message_type, len(messages), fit_file.filename, messages[0])
        else:
            root_logger.info("No entry handler %s for known message type %r (%d) from %s: %s",
                             handler_name, message_type, len(messages), fit_file.filename, messages[0])

    def _write_file_id(self, fit_file, message_type, messages):
        """Write all file id messages to the database."""
        self.serial_number = None
        self.manufacturer = None
        self.product = None
        for message in messages:
            self._write_file_id_entry(fit_file, message.fields)

    def __write_message_type(self, fit_file, message_type):
        messages = fit_file[message_type]
        function = getattr(self, '_write_' + message_type.name, self.__write_generic)
        function(fit_file, message_type, messages)
        root_logger.debug("Processed %d %r entries for %s", len(messages), message_type, fit_file.filename)

    def _write_message_types(self, fit_file, message_types):
        """Write all messages from the FIT file to the database ordered by message type."""
        root_logger.info("Importing %s (%s) [%s] with message types: %s", fit_file.filename, fit_file.time_created_local, fit_file.type, message_types)
        #
        # Some ordering is important: 1. create new file entries 2. create new device entries
        #
        priority_message_types = [fitfile.MessageType.file_id, fitfile.MessageType.device_info]
        for message_type in priority_message_types:
            self.__write_message_type(fit_file, message_type)
        for message_type in message_types:
            if message_type not in priority_message_types:
                self.__write_message_type(fit_file, message_type)

    def write_file(self, fit_file):
        """Write all data from the FIT file to database files."""
        with self.garmin_db.managed_session() as self.garmin_db_session:
            self._write_message_types(fit_file, fit_file.message_types)

    #
    # Message type handlers
    #
    def _write_file_id_entry(self, fit_file, message_fields):
        root_logger.debug("file_id fields: %r", message_fields)
        self.serial_number = message_fields.serial_number
        _manufacturer = Device.Manufacturer.convert(message_fields.manufacturer)
        if _manufacturer is not None:
            self.manufacturer = _manufacturer
        self.product = message_fields.product
        device_type = fitfile.MainDeviceType.derive_device_type(self.manufacturer, self.product)
        if self.serial_number:
            device = {
                'serial_number' : self.serial_number,
                'timestamp'     : fit_file.utc_datetime_to_local(message_fields.time_created),
                'device_type'   : fitfile.field_enums.name_for_enum(device_type),
                'manufacturer'  : self.manufacturer,
                'product'       : fitfile.field_enums.name_for_enum(self.product),
            }
            Device.s_insert_or_update(self.garmin_db_session, device)
        (file_id, file_name) = File.name_and_id_from_path(fit_file.filename)
        file = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : File.FileType.convert(message_fields.type),
            'serial_number' : self.serial_number
        }
        File.s_insert_or_update(self.garmin_db_session, file)

    def _write_device_info_entry(self, fit_file, message_fields):
        timestamp = fit_file.utc_datetime_to_local(message_fields.timestamp)
        device_type = message_fields.get('device_type', fitfile.MainDeviceType.fitness_tracker)
        serial_number = message_fields.serial_number
        source_type = message_fields.source_type
        # local devices are part of the main device. Base missing fields off of the main device.
        if source_type is fitfile.field_enums.SourceType.local:
            if serial_number is None and self.serial_number is not None and device_type is not None:
                serial_number = Device.local_device_serial_number(self.serial_number, device_type)
        if serial_number is not None:
            manufacturer = Device.Manufacturer.convert(message_fields.manufacturer)
            device = {
                'serial_number'     : serial_number,
                'timestamp'         : timestamp,
                'device_type'       : fitfile.field_enums.name_for_enum(device_type),
                'manufacturer'      : manufacturer or self.manufacturer,
                'product'           : fitfile.field_enums.name_for_enum(message_fields.product or self.product),
                'hardware_version'  : message_fields.hardware_version
            }
            Device.s_insert_or_update(self.garmin_db_session, device, ignore_none=True)
            device_info = {
                'file_id'               : File.s_get_id(self.garmin_db_session, fit_file.filename),
                'serial_number'         : serial_number,
                'timestamp'             : timestamp,
                'cum_operating_time'    : message_fields.cum_operating_time,
                'battery_status'        : message_fields.battery_status,
                'battery_voltage'       : message_fields.battery_voltage,
                'software_version'      : message_fields.software_version
            }
            DeviceInfo.s_insert_or_update(self.garmin_db_session, device_info, ignore_none=True)
            return serial_number

    def _write_stress_level_entry(self, fit_file, message_fields):
        stress = {
            'timestamp' : message_fields.local_timestamp,
            'stress'    : message_fields.stress_level
        }
        Stress.s_insert_or_update(self.garmin_db_session, stress)

    def _write_event_entry(self, fit_file, message_fields):
        root_logger.debug("event message: %r", message_fields)

    def _write_hrv_entry(self, fit_file, message_fields):
        root_logger.debug("hrv message: %r", message_fields)

    def _write_ohr_settings_entry(self, fit_file, message_fields):
        root_logger.debug("ohr_settings message: %r", message_fields)

    def _write_software_entry(self, fit_file, message_fields):
        root_logger.debug("software message: %r", message_fields)

    def _write_file_creator_entry(self, fit_file, message_fields):
        root_logger.debug("file creator message: %r", message_fields)

    def _write_sport_entry(self, fit_file, message_fields):
        root_logger.debug("sport message: %r", message_fields)

    def _write_sensor_entry(self, fit_file, message_fields):
        root_logger.debug("sensor message: %r", message_fields)

    def _write_source_entry(self, fit_file, message_fields):
        root_logger.debug("source message: %r", message_fields)

    def _write_training_file_entry(self, fit_file, message_fields):
        root_logger.debug("Training file entry: %r", message_fields)

    def _write_attribute(self, timestamp, message_fields, attribute_name, db_attribute_name=None):
        attribute = message_fields.get(attribute_name)
        if attribute is not None:
            if db_attribute_name is None:
                db_attribute_name = attribute_name
            root_logger.info("Writing attribute: %r -> %r at %r", attribute, db_attribute_name, timestamp)
            Attributes.s_set_newer(self.garmin_db_session, db_attribute_name, attribute, timestamp)

    def _write_attributes(self, timestamp, message_fields, attribute_names):
        for attribute_name in attribute_names:
            self._write_attribute(timestamp, message_fields, attribute_name)

    def _write_measurement_sytem_attributes(self, timestamp, message_fields):
        for attribute_name in ['dist_setting', 'speed_setting', 'height_setting', 'temperature_setting']:
            self._write_attribute(timestamp, message_fields, attribute_name, 'measurement_system')

    def _write_device_settings_entry(self, fit_file, message_fields):
        root_logger.debug("device settings message: %r", message_fields)
        timestamp = fit_file.time_created_local
        self._write_attributes(timestamp, message_fields, ['active_time_zone', 'date_mode'])
        self._write_measurement_sytem_attributes(timestamp, message_fields)
        self._write_attribute(timestamp, message_fields, 'active_time_zone', 'time_zone')
        self._write_attribute(timestamp, message_fields, 'date_mode', 'date_format')

    def _write_battery_entry(self, fit_file, message_fields):
        root_logger.debug("battery message: %r", message_fields)

    def _write_user_profile_entry(self, fit_file, message_fields):
        root_logger.info("user profile message: %r", message_fields)
        timestamp = fit_file.time_created_local
        attribute_names = [
            'gender', 'height', 'weight', 'age', 'year_of_birth', 'language', 'dist_setting', 'weight_setting', 'position_setting', 'elev_setting', 'sleep_time', 'wake_time',
            'speed_setting'
        ]
        self._write_attributes(timestamp, message_fields, attribute_names)
        self._write_measurement_sytem_attributes(timestamp, message_fields)

    def _write_activity_entry(self, fit_file, message_fields):
        root_logger.debug("activity message: %r", message_fields)

    def _write_zones_target_entry(self, fit_file, message_fields):
        root_logger.debug("zones target message: %r", message_fields)

    def _write_dev_data_id_entry(self, fit_file, message_fields):
        root_logger.debug("dev_data_id message: %r", message_fields)

    def _write_field_description_entry(self, fit_file, message_fields):
        root_logger.debug("field_description message: %r", message_fields)

    def _write_length_entry(self, fit_file, message_fields):
        root_logger.debug("length message: %r", message_fields)

    def _write_set_entry(self, fit_file, message_fields):
        root_logger.debug("set message: %r", message_fields)

    def _write_watchface_settings_entry(self, fit_file, message_fields):
        root_logger.debug("watchface settings message: %r", message_fields)

    def _write_personal_record_entry(self, fit_file, message_fields):
        logger.info("personal record message: %r", message_fields)
