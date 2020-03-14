"""Class that takes a parsed FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import traceback
import datetime

import Fit
import GarminDB
import utilities


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class FitFileProcessor(object):
    """Class that takes a parsed FIT file object and imports it into a database."""

    def __init__(self, db_params, ignore_dev_fields, debug):
        """
        Return a new FitFileProcessor instance.

        Paramters:
        db_params (dict): database access configuration
        ignore_dev_fields (Boolean): If True, then ignore develoepr fields in Fit files
        debug (Boolean): if True, debug logging is enabled
        """
        root_logger.info("Ignore dev fields: %s Debug: %s", ignore_dev_fields, debug)
        self.debug = debug
        self.garmin_db = GarminDB.GarminDB(db_params, debug - 1)
        self.garmin_mon_db = GarminDB.MonitoringDB(db_params, self.debug - 1)
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params, self.debug - 1)
        self.ignore_dev_fields = ignore_dev_fields
        if not self.ignore_dev_fields:
            self.field_prefixes = ['dev_', '']
        else:
            self.field_prefixes = ['']

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
                    root_logger.error("Failed to write message %r type %r: %s", message_type, message, e)
        elif isinstance(message_type, Fit.UnknownMessageType) or message_type.is_unknown():
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

    def _write_lap(self, fit_file, message_type, messages):
        """Write all lap messages to the database."""
        for lap_num, message in enumerate(messages):
            self._write_lap_entry(fit_file, message.fields, lap_num)

    def _write_record(self, fit_file, message_type, messages):
        """Write all record messages to the database."""
        for record_num, message in enumerate(messages):
            self._write_record_entry(fit_file, message.fields, record_num)

    def __write_message_type(self, fit_file, message_type):
        messages = fit_file[message_type]
        function = getattr(self, '_write_' + message_type.name, self.__write_generic)
        function(fit_file, message_type, messages)
        root_logger.debug("Processed %d %r entries for %s", len(messages), message_type, fit_file.filename)

    def __write_message_types(self, fit_file, message_types):
        """Write all messages from the FIT file to the database ordered by message type."""
        root_logger.info("Importing %s (%s) [%s] with message types: %s",
                         fit_file.filename, fit_file.time_created_local, fit_file.type, message_types)
        #
        # Some ordering is important: 1. create new file entries 2. create new device entries
        #
        priority_message_types = [Fit.MessageType.file_id, Fit.MessageType.device_info]
        for message_type in priority_message_types:
            self.__write_message_type(fit_file, message_type)
        for message_type in message_types:
            if message_type not in priority_message_types:
                self.__write_message_type(fit_file, message_type)

    def write_file(self, fit_file):
        """Given a Fit File object, write all of its messages to the DB."""
        with self.garmin_db.managed_session() as self.garmin_db_session, self.garmin_mon_db.managed_session() as self.garmin_mon_db_session, \
                self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self.__write_message_types(fit_file, fit_file.message_types)
            # Now write a file's worth of data to the DB
            self.garmin_act_db_session.commit()
            self.garmin_mon_db_session.commit()
            self.garmin_db_session.commit()

    def __get_field_value(self, message_fields, field_name):
        for prefix in self.field_prefixes:
            prefixed_field_name = prefix + field_name
            if prefixed_field_name in message_fields:
                return message_fields[prefixed_field_name]

    def __get_field_list_value(self, message_fields, dev_field_name_list, field_name_list):
        if not self.ignore_dev_fields:
            for field_name in dev_field_name_list:
                dev_field_name = 'dev_' + field_name
                if dev_field_name in message_fields:
                    return message_fields[dev_field_name]
        for field_name in field_name_list:
            value = self.__get_field_value(message_fields, field_name)
            if value is not None:
                return value

    def __get_total_steps(self, message_fields):
        return self.__get_field_list_value(message_fields, ['tStps', 'Stps', 'ts', 'totalsteps'], ['total_steps'])

    def __get_total_distance(self, message_fields):
        return self.__get_field_list_value(message_fields, ['user_distance'], ['total_distance'])

    #
    # Message type handlers
    #
    def _write_file_id_entry(self, fit_file, message_fields):
        root_logger.debug("file_id fields: %r", message_fields)
        self.serial_number = message_fields.serial_number
        _manufacturer = GarminDB.Device.Manufacturer.convert(message_fields.manufacturer)
        if _manufacturer is not None:
            self.manufacturer = _manufacturer
        self.product = message_fields.product
        device_type = Fit.MainDeviceType.derive_device_type(self.manufacturer, self.product)
        if self.serial_number:
            device = {
                'serial_number' : self.serial_number,
                'timestamp'     : fit_file.utc_datetime_to_local(message_fields.time_created),
                'device_type'   : Fit.field_enums.name_for_enum(device_type),
                'manufacturer'  : self.manufacturer,
                'product'       : Fit.field_enums.name_for_enum(self.product),
            }
            GarminDB.Device.s_insert_or_update(self.garmin_db_session, device)
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(fit_file.filename)
        file = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : GarminDB.File.FileType.convert(message_fields.type),
            'serial_number' : self.serial_number,
        }
        GarminDB.File.s_insert_or_update(self.garmin_db_session, file)

    def _write_device_info_entry(self, fit_file, message_fields):
        timestamp = fit_file.utc_datetime_to_local(message_fields.timestamp)
        device_type = message_fields.get('device_type', Fit.MainDeviceType.fitness_tracker)
        serial_number = message_fields.serial_number
        manufacturer = GarminDB.Device.Manufacturer.convert(message_fields.manufacturer)
        product = message_fields.product
        source_type = message_fields.source_type
        # local devices are part of the main device. Base missing fields off of the main device.
        if source_type is Fit.field_enums.SourceType.local:
            if serial_number is None and self.serial_number is not None and device_type is not None:
                serial_number = GarminDB.Device.local_device_serial_number(self.serial_number, device_type)
            if manufacturer is None:
                manufacturer = self.manufacturer
            if product is None:
                product = self.product
        if serial_number is not None:
            device = {
                'serial_number'     : serial_number,
                'timestamp'         : timestamp,
                'device_type'       : Fit.field_enums.name_for_enum(device_type),
                'manufacturer'      : manufacturer,
                'product'           : Fit.field_enums.name_for_enum(product),
                'hardware_version'  : message_fields.hardware_version,
            }
            GarminDB.Device.s_insert_or_update(self.garmin_db_session, device, ignore_none=True)
            device_info = {
                'file_id'               : GarminDB.File.s_get_id(self.garmin_db_session, fit_file.filename),
                'serial_number'         : serial_number,
                'timestamp'             : timestamp,
                'cum_operating_time'    : message_fields.cum_operating_time,
                'battery_status'        : message_fields.battery_status,
                'battery_voltage'       : message_fields.battery_voltage,
                'software_version'      : message_fields.software_version,
            }
            GarminDB.DeviceInfo.s_insert_or_update(self.garmin_db_session, device_info, ignore_none=True)

    def _write_stress_level_entry(self, fit_file, message_fields):
        stress = {
            'timestamp' : message_fields.local_timestamp,
            'stress'    : message_fields.stress_level,
        }
        GarminDB.Stress.s_insert_or_update(self.garmin_db_session, stress)

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

    def _write_steps_entry(self, fit_file, activity_id, sub_sport, message_fields):
        steps = {
            'activity_id'                       : activity_id,
            'steps'                             : self.__get_total_steps(message_fields),
            'avg_pace'                          : Fit.conversions.perhour_speed_to_pace(message_fields.avg_speed),
            'max_pace'                          : Fit.conversions.perhour_speed_to_pace(message_fields.max_speed),
            'avg_steps_per_min'                 : self.__get_field_value(message_fields, 'avg_steps_per_min'),
            'max_steps_per_min'                 : self.__get_field_value(message_fields, 'max_steps_per_min'),
            'avg_step_length'                   : self.__get_field_value(message_fields, 'avg_step_length'),
            'avg_vertical_ratio'                : self.__get_field_value(message_fields, 'avg_vertical_ratio'),
            'avg_vertical_oscillation'          : self.__get_field_value(message_fields, 'avg_vertical_oscillation'),
            'avg_gct_balance'                   : self.__get_field_value(message_fields, 'avg_stance_time_balance'),
            'avg_ground_contact_time'           : self.__get_field_value(message_fields, 'avg_stance_time'),
            'avg_stance_time_percent'           : self.__get_field_value(message_fields, 'avg_stance_time_percent'),
        }
        root_logger.info("steps: %r", steps)
        GarminDB.StepsActivities.s_insert_or_update(self.garmin_act_db_session, steps, ignore_none=True, ignore_zero=True)

    def _write_running_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_walking_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_hiking_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_cycling_entry(self, fit_file, activity_id, sub_sport, message_fields):
        ride = {
            'activity_id'   : activity_id,
            'strokes'       : self.__get_field_value(message_fields, 'total_strokes'),
        }
        GarminDB.CycleActivities.s_insert_or_update(self.garmin_act_db_session, ride, ignore_none=True, ignore_zero=True)

    def _write_stand_up_paddleboarding_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("sup sport entry: %r", message_fields)
        paddle = {
            'activity_id'           : activity_id,
            'strokes'               : self.__get_field_value(message_fields, 'total_strokes'),
            'avg_stroke_distance'   : self.__get_field_value(message_fields, 'avg_stroke_distance'),
        }
        GarminDB.PaddleActivities.s_insert_or_update(self.garmin_act_db_session, paddle, ignore_none=True, ignore_zero=True)

    def _write_rowing_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("row sport entry: %r", message_fields)
        return self._write_stand_up_paddleboarding_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_boating_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("boating sport entry: %r", message_fields)

    def _write_elliptical_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("elliptical entry: %r", message_fields)
        workout = {
            'activity_id'           : activity_id,
            'steps'                 : self.__get_total_steps(message_fields),
            'elliptical_distance'   : self.__get_total_distance(message_fields),
        }
        GarminDB.EllipticalActivities.s_insert_or_update(self.garmin_act_db_session, workout, ignore_none=True, ignore_zero=True)

    def _write_fitness_equipment_entry(self, fit_file, activity_id, sub_sport, message_fields):
        try:
            function = getattr(self, '_write_' + sub_sport.name + '_entry')
            function(fit_file, activity_id, sub_sport, message_fields)
        except AttributeError:
            root_logger.info("No sub sport handler type %s from %s: %s", sub_sport, fit_file.filename, message_fields)

    def _write_alpine_skiing_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Skiing sport entry: %r", message_fields)

    def _write_swimming_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Swimming sport entry: %r", message_fields)

    def _write_training_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Training sport entry: %r", message_fields)

    def _write_transition_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Transition sport entry: %r", message_fields)

    def _write_generic_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Generic sport entry: %r", message_fields)

    def __choose_sport(self, current_sport, current_sub_sport, new_sport, new_sub_sport):
        sport = Fit.Sport.strict_from_string(current_sport)
        sub_sport = Fit.SubSport.strict_from_string(current_sub_sport)
        if new_sport is not None and (sport is None or (not sport.preferred() and new_sport.preferred())):
            sport = new_sport
        if new_sub_sport is not None and (sub_sport is None or (not sub_sport.preferred() and new_sub_sport.preferred())):
            sub_sport = new_sub_sport
        return {'sport' : Fit.field_enums.name_for_enum(sport), 'sub_sport' : Fit.field_enums.name_for_enum(sub_sport)}

    def _write_session_entry(self, fit_file, message_fields):
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        sport = message_fields.sport
        sub_sport = message_fields.sub_sport
        activity = {
            'activity_id'                       : activity_id,
            'start_time'                        : fit_file.utc_datetime_to_local(message_fields.start_time),
            'stop_time'                         : fit_file.utc_datetime_to_local(message_fields.timestamp),
            'elapsed_time'                      : message_fields.total_elapsed_time,
            'moving_time'                       : self.__get_field_value(message_fields, 'total_timer_time'),
            'start_lat'                         : self.__get_field_value(message_fields, 'start_position_lat'),
            'start_long'                        : self.__get_field_value(message_fields, 'start_position_long'),
            'stop_lat'                          : self.__get_field_value(message_fields, 'end_position_lat'),
            'stop_long'                         : self.__get_field_value(message_fields, 'end_position_long'),
            'distance'                          : self.__get_total_distance(message_fields),
            'cycles'                            : self.__get_field_value(message_fields, 'total_cycles'),
            'laps'                              : self.__get_field_value(message_fields, 'num_laps'),
            'avg_hr'                            : self.__get_field_value(message_fields, 'avg_heart_rate'),
            'max_hr'                            : self.__get_field_value(message_fields, 'max_heart_rate'),
            'avg_rr'                            : self.__get_field_value(message_fields, 'avg_respiration_rate'),
            'max_rr'                            : self.__get_field_value(message_fields, 'max_respiration_rate'),
            'calories'                          : self.__get_field_value(message_fields, 'total_calories'),
            'avg_cadence'                       : self.__get_field_value(message_fields, 'avg_cadence'),
            'max_cadence'                       : self.__get_field_value(message_fields, 'max_cadence'),
            'avg_speed'                         : self.__get_field_value(message_fields, 'avg_speed'),
            'max_speed'                         : self.__get_field_value(message_fields, 'max_speed'),
            'ascent'                            : self.__get_field_value(message_fields, 'total_ascent'),
            'descent'                           : self.__get_field_value(message_fields, 'total_descent'),
            'max_temperature'                   : self.__get_field_value(message_fields, 'max_temperature'),
            'avg_temperature'                   : self.__get_field_value(message_fields, 'avg_temperature'),
            'training_effect'                   : self.__get_field_value(message_fields, 'total_training_effect'),
            'anaerobic_training_effect'         : self.__get_field_value(message_fields, 'total_anaerobic_training_effect')
        }
        # json metadata gives better values for sport and subsport, so use existing value if set
        current = GarminDB.Activities.s_get(self.garmin_act_db_session, activity_id)
        if current:
            activity.update(self.__choose_sport(current.sport, current.sub_sport, sport, sub_sport))
            root_logger.debug("Updating with %r", activity)
            current.update_from_dict(activity, ignore_none=True, ignore_zero=True)
        else:
            activity.update({'sport': sport.name, 'sub_sport': sub_sport.name})
            root_logger.debug("Adding %r", activity)
            self.garmin_act_db_session.add(GarminDB.Activities(**activity))
        if sport is not None:
            function_name = '_write_' + sport.name + '_entry'
            try:
                function = getattr(self, function_name, None)
                if function is not None:
                    function(fit_file, activity_id, sub_sport, message_fields)
                else:
                    root_logger.warning("No sport handler for type %s from %s: %s", sport, fit_file.filename, message_fields)
            except Exception as e:
                root_logger.error("Exception in %s from %s: %s", function_name, fit_file.filename, e)

    def _write_attribute(self, timestamp, message_fields, attribute_name, db_attribute_name=None):
        attribute = message_fields.get(attribute_name)
        if attribute is not None:
            if db_attribute_name is None:
                db_attribute_name = attribute_name
            GarminDB.Attributes.s_set_newer(self.garmin_db_session, db_attribute_name, attribute, timestamp)

    def _write_attributes(self, timestamp, message_fields, attribute_names):
        for attribute_name in attribute_names:
            self._write_attribute(timestamp, message_fields, attribute_name)

    def _write_device_settings_entry(self, fit_file, message_fields):
        root_logger.debug("device settings message: %r", message_fields)
        timestamp = fit_file.time_created_local
        attribute_names = [
            'active_time_zone', 'date_mode'
        ]
        self._write_attributes(timestamp, message_fields, attribute_names)
        self._write_attribute(timestamp, message_fields, 'active_time_zone', 'time_zone')
        self._write_attribute(timestamp, message_fields, 'date_mode', 'date_format')

    def _write_lap_entry(self, fit_file, message_fields, lap_num):
        # we don't get laps data from multiple sources so we don't need to coellesce data in the DB.
        # It's fastest to just write new data out if the it doesn't currently exist.
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        if not GarminDB.ActivityLaps.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'lap' : lap_num}):
            lap = {
                'activity_id'                       : GarminDB.File.id_from_path(fit_file.filename),
                'lap'                               : lap_num,
                'start_time'                        : fit_file.utc_datetime_to_local(message_fields.start_time),
                'stop_time'                         : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'elapsed_time'                      : self.__get_field_value(message_fields, 'total_elapsed_time'),
                'moving_time'                       : self.__get_field_value(message_fields, 'total_timer_time'),
                'start_lat'                         : self.__get_field_value(message_fields, 'start_position_lat'),
                'start_long'                        : self.__get_field_value(message_fields, 'start_position_long'),
                'stop_lat'                          : self.__get_field_value(message_fields, 'end_position_lat'),
                'stop_long'                         : self.__get_field_value(message_fields, 'end_position_long'),
                'distance'                          : self.__get_total_distance(message_fields),
                'cycles'                            : self.__get_field_value(message_fields, 'total_cycles'),
                'avg_hr'                            : self.__get_field_value(message_fields, 'avg_heart_rate'),
                'max_hr'                            : self.__get_field_value(message_fields, 'max_heart_rate'),
                'avg_rr'                            : self.__get_field_value(message_fields, 'avg_respiration_rate'),
                'max_rr'                            : self.__get_field_value(message_fields, 'max_respiration_rate'),
                'calories'                          : self.__get_field_value(message_fields, 'total_calories'),
                'avg_cadence'                       : self.__get_field_value(message_fields, 'avg_cadence'),
                'max_cadence'                       : self.__get_field_value(message_fields, 'max_cadence'),
                'avg_speed'                         : self.__get_field_value(message_fields, 'avg_speed'),
                'max_speed'                         : self.__get_field_value(message_fields, 'max_speed'),
                'ascent'                            : self.__get_field_value(message_fields, 'total_ascent'),
                'descent'                           : self.__get_field_value(message_fields, 'total_descent'),
                'max_temperature'                   : self.__get_field_value(message_fields, 'max_temperature'),
                'avg_temperature'                   : self.__get_field_value(message_fields, 'avg_temperature'),
            }
            self.garmin_act_db_session.add(GarminDB.ActivityLaps(**lap))

    def _write_battery_entry(self, fit_file, message_fields):
        root_logger.debug("battery message: %r", message_fields)

    def _write_user_profile_entry(self, fit_file, message_fields):
        root_logger.debug("user profile message: %r", message_fields)
        timestamp = fit_file.time_created_local
        attribute_names = [
            'gender', 'height', 'weight', 'language', 'dist_setting', 'weight_setting', 'position_setting', 'elev_setting', 'sleep_time', 'wake_time',
            'speed_setting'
        ]
        self._write_attributes(timestamp, message_fields, attribute_names)
        self._write_attribute(timestamp, message_fields, 'dist_setting', 'measurement_system')

    def _write_activity_entry(self, fit_file, message_fields):
        root_logger.debug("activity message: %r", message_fields)

    def _write_zones_target_entry(self, fit_file, message_fields):
        root_logger.debug("zones target message: %r", message_fields)

    def _write_record_entry(self, fit_file, message_fields, record_num):
        # We don't get record data from multiple sources so we don't need to coellesce data in the DB.
        # It's fastest to just write the new data out if it doesn't currently exist.
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        if not GarminDB.ActivityRecords.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'record' : record_num}):
            record = {
                'activity_id'                       : activity_id,
                'record'                            : record_num,
                'timestamp'                         : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'position_lat'                      : self.__get_field_value(message_fields, 'position_lat'),
                'position_long'                     : self.__get_field_value(message_fields, 'position_long'),
                'distance'                          : self.__get_field_value(message_fields, 'distance'),
                'cadence'                           : self.__get_field_value(message_fields, 'cadence'),
                'hr'                                : self.__get_field_value(message_fields, 'heart_rate'),
                'rr'                                : self.__get_field_value(message_fields, 'respiration_rate'),
                'altitude'                          : self.__get_field_value(message_fields, 'altitude'),
                'speed'                             : self.__get_field_value(message_fields, 'speed'),
                'temperature'                       : self.__get_field_value(message_fields, 'temperature'),
            }
            self.garmin_act_db_session.add(GarminDB.ActivityRecords(**record))

    def _write_dev_data_id_entry(self, fit_file, message_fields):
        root_logger.debug("dev_data_id message: %r", message_fields)

    def _write_field_description_entry(self, fit_file, message_fields):
        root_logger.debug("field_description message: %r", message_fields)

    def _write_length_entry(self, fit_file, message_fields):
        root_logger.debug("length message: %r", message_fields)

    def _write_monitoring_info_entry(self, fit_file, message_fields):
        activity_types = message_fields.activity_type
        if isinstance(activity_types, list):
            for index, activity_type in enumerate(activity_types):
                entry = {
                    'file_id'                   : GarminDB.File.s_get_id(self.garmin_db_session, fit_file.filename),
                    'timestamp'                 : message_fields.local_timestamp,
                    'activity_type'             : activity_type,
                    'resting_metabolic_rate'    : self.__get_field_value(message_fields, 'resting_metabolic_rate'),
                    'cycles_to_distance'        : message_fields.cycles_to_distance[index],
                    'cycles_to_calories'        : message_fields.cycles_to_calories[index]
                }
                GarminDB.MonitoringInfo.s_insert_or_update(self.garmin_mon_db_session, entry)

    def _write_monitoring_entry(self, fit_file, message_fields):
        # Only include not None values so that we match and update only if a table's columns if it has values.
        entry = utilities.list_and_dict.dict_filter_none_values(message_fields)
        timestamp = fit_file.utc_datetime_to_local(message_fields.timestamp)
        # Hack: daily monitoring summaries appear at 00:00:00 localtime for the PREVIOUS day. Subtract a second so they appear int he previous day.
        if timestamp.time() == datetime.time.min:
            timestamp = timestamp - datetime.timedelta(seconds=1)
        entry['timestamp'] = timestamp
        logger.debug("monitoring entry: %r", entry)
        try:
            intersection = GarminDB.MonitoringHeartRate.intersection(entry)
            if len(intersection) > 1 and intersection['heart_rate'] > 0:
                GarminDB.MonitoringHeartRate.s_insert_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.MonitoringIntensity.intersection(entry)
            if len(intersection) > 1:
                GarminDB.MonitoringIntensity.s_insert_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.MonitoringClimb.intersection(entry)
            if len(intersection) > 1:
                GarminDB.MonitoringClimb.s_insert_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.Monitoring.intersection(entry)
            if len(intersection) > 1:
                GarminDB.Monitoring.s_insert_or_update(self.garmin_mon_db_session, intersection)
        except ValueError:
            logger.error("write_monitoring_entry: ValueError for %r: %s", entry, traceback.format_exc())
        except Exception:
            logger.error("Exception on monitoring entry: %r: %s", entry, traceback.format_exc())

    def _write_respiration_entry(self, fit_file, message_fields):
        logger.debug("respiration message: %r", message_fields)
        rr = self.__get_field_value(message_fields, 'respiration_rate')
        if rr > 0:
            respiration = {
                'timestamp' : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'rr'        : rr,
            }
            if fit_file.type is Fit.FileType.monitoring_b:
                GarminDB.MonitoringRespirationRate.s_insert_or_update(self.garmin_mon_db_session, respiration)
            else:
                raise(ValueError(f'Unexpected file type {repr(fit_file.type)} for respiration message'))

    def _write_pulse_ox_entry(self, fit_file, message_fields):
        logger.debug("pulse_ox message: %r", message_fields)
        if fit_file.type is Fit.FileType.monitoring_b:
            pulse_ox = self.__get_field_value(message_fields, 'pulse_ox')
            if pulse_ox is not None:
                pulse_ox_entry = {
                    'timestamp': fit_file.utc_datetime_to_local(message_fields.timestamp),
                    'pulse_ox': pulse_ox,
                }
                GarminDB.MonitoringPulseOx.s_insert_or_update(self.garmin_mon_db_session, pulse_ox_entry)
        else:
            raise(ValueError(f'Unexpected file type {repr(fit_file.type)} for pulse ox'))

    def _write_set_entry(self, fit_file, message_fields):
        root_logger.debug("set message: %r", message_fields)

    def _write_watchface_settings_entry(self, fit_file, message_fields):
        root_logger.debug("watchface settings message: %r", message_fields)

    def _write_personal_record_entry(self, fit_file, message_fields):
        logger.info("personal record message: %r", message_fields)
