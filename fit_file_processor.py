"""Class that takes a parsed FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import traceback

import Fit
import GarminDB
import utilities


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class FitFileProcessor(object):
    """Class that takes a parsed FIT file object and imports it into a database."""

    def __init__(self, db_params, debug):
        """
        Return a new FitFileProcessor instance.

        Paramters:
        db_params (dict): database access configuration
        debug (Boolean): if True, debug logging is enabled
        """
        root_logger.info("Debug: %s", debug)
        self.debug = debug
        self.garmin_db = GarminDB.GarminDB(db_params, debug - 1)
        self.garmin_mon_db = GarminDB.MonitoringDB(db_params, self.debug - 1)
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params, self.debug - 1)

    def __write_generic(self, fit_file, message_type, messages):
        """Write all messages of a given message type to the databse."""
        for message in messages:
            handler_name = '_write_' + message_type.name + '_entry'
            function = getattr(self, handler_name, None)
            if function is not None:
                # parse the message with lower case field names
                message_dict = message.to_lower_dict()
                function(fit_file, message_dict)
            elif isinstance(message_type, Fit.UnknownMessageType) or message_type.is_unknown():
                root_logger.debug("No entry handler %s for message type %r (%d) from %s: %s",
                                  handler_name, message_type, len(messages), fit_file.filename, messages[0])
            else:
                root_logger.info("No entry handler %s for known message type %r (%d) from %s: %s",
                                 handler_name, message_type, len(messages), fit_file.filename, messages[0])

    def __write_message_type(self, fit_file, message_type):
        messages = fit_file[message_type]
        function = getattr(self, '_write_' + message_type.name, self.__write_generic)
        function(fit_file, message_type, messages)
        root_logger.debug("Processed %d %r entries for %s", len(messages), message_type, fit_file.filename)

    def __write_message_types(self, fit_file, message_types):
        """Write all messages from the FIT file to the database ordered by message type."""
        root_logger.debug("Importing %s (%s) [%s] with message types: %s", fit_file.filename, fit_file.time_created(), fit_file.type(), message_types)
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
        self.lap = 1
        self.record = 1
        self.serial_number = None
        self.manufacturer = None
        self.product = None
        with self.garmin_db.managed_session() as self.garmin_db_session:
            with self.garmin_mon_db.managed_session() as self.garmin_mon_db_session:
                with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
                    self.__write_message_types(fit_file, fit_file.message_types())
                    # Now write a file's worth of data to the DB
                    self.garmin_act_db_session.commit()
                self.garmin_mon_db_session.commit()
            self.garmin_db_session.commit()

    def __get_field_value(self, message_dict, field_name):
        prefixes = ['dev_', 'enhanced_', '']
        for prefix in prefixes:
            value = message_dict.get(prefix + field_name)
            if value is not None:
                return value

    def __get_field_list_value(self, message_dict, dev_field_name_list, field_name_list):
        for field_name in dev_field_name_list:
            value = message_dict.get('dev_' + field_name)
            if value is not None:
                return value
        for field_name in field_name_list:
            value = self.__get_field_value(message_dict, field_name)
            if value is not None:
                return value

    def __get_total_steps(self, message_dict):
        return self.__get_field_list_value(message_dict, ['tStps', 'Stps', 'ts'], ['total_steps'])

    def __get_total_distance(self, message_dict):
        return self.__get_field_list_value(message_dict, ['user_distance'], ['total_distance'])

    #
    # Message type handlers
    #
    def _write_file_id_entry(self, fit_file, message_dict):
        root_logger.debug("file_id message: %r", message_dict)
        self.serial_number = message_dict.get('serial_number')
        _manufacturer = GarminDB.Device.Manufacturer.convert(message_dict.get('manufacturer'))
        if _manufacturer is not None:
            self.manufacturer = _manufacturer
        self.product = message_dict.get('product')
        if self.serial_number:
            device = {
                'serial_number' : self.serial_number,
                'timestamp'     : message_dict['time_created'],
                'manufacturer'  : self.manufacturer,
                'product'       : Fit.field_enums.name_for_enum(self.product),
            }
            GarminDB.Device.s_find_or_create(self.garmin_db_session, device)
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(fit_file.filename)
        file = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : GarminDB.File.FileType.convert(message_dict['type']),
            'serial_number' : self.serial_number,
        }
        GarminDB.File.s_find_or_create(self.garmin_db_session, file)

    def _write_stress_level_entry(self, fit_file, stress_message_dict):
        stress = {
            'timestamp' : stress_message_dict['stress_level_time'],
            'stress'    : stress_message_dict['stress_level_value'],
        }
        GarminDB.Stress.s_find_or_create(self.garmin_db_session, stress)

    def _write_event_entry(self, fit_file, event_message_dict):
        root_logger.debug("event message: %r", event_message_dict)

    def _write_hrv_entry(self, fit_file, hrv_message_dict):
        root_logger.debug("hrv message: %r", hrv_message_dict)

    def _write_ohr_settings_entry(self, fit_file, message_dict):
        root_logger.debug("ohr_settings message: %r", message_dict)

    def _write_software_entry(self, fit_file, software_message_dict):
        root_logger.debug("software message: %r", software_message_dict)

    def _write_file_creator_entry(self, fit_file, file_creator_message_dict):
        root_logger.debug("file creator message: %r", file_creator_message_dict)

    def _write_sport_entry(self, fit_file, sport_message_dict):
        root_logger.debug("sport message: %r", sport_message_dict)

    def _write_sensor_entry(self, fit_file, sensor_message_dict):
        root_logger.debug("sensor message: %r", sensor_message_dict)

    def _write_source_entry(self, fit_file, source_message_dict):
        root_logger.debug("source message: %r", source_message_dict)

    def _write_training_file_entry(self, fit_file, message_dict):
        root_logger.debug("Training file entry: %r", message_dict)

    def _write_steps_entry(self, fit_file, activity_id, sub_sport, message_dict):
        steps = {
            'activity_id'                       : activity_id,
            'steps'                             : self.__get_total_steps(message_dict),
            'avg_pace'                          : Fit.conversions.speed_to_pace(message_dict.get('avg_speed')),
            'max_pace'                          : Fit.conversions.speed_to_pace(message_dict.get('max_speed')),
            'avg_steps_per_min'                 : Fit.Cadence.from_cycles(self.__get_field_value(message_dict, 'avg_cadence')).to_spm(),
            'max_steps_per_min'                 : Fit.Cadence.from_cycles(self.__get_field_value(message_dict, 'max_cadence')).to_spm(),
            'avg_step_length'                   : self.__get_field_value(message_dict, 'avg_step_length'),
            'avg_vertical_ratio'                : self.__get_field_value(message_dict, 'avg_vertical_ratio'),
            'avg_vertical_oscillation'          : self.__get_field_value(message_dict, 'avg_vertical_oscillation'),
            'avg_gct_balance'                   : self.__get_field_value(message_dict, 'avg_stance_time_balance'),
            'avg_ground_contact_time'           : self.__get_field_value(message_dict, 'avg_stance_time'),
            'avg_stance_time_percent'           : self.__get_field_value(message_dict, 'avg_stance_time_percent'),
        }
        root_logger.info("steps: %r", steps)
        GarminDB.StepsActivities.s_create_or_update(self.garmin_act_db_session, steps, ignore_none=True, ignore_zero=True)

    def _write_running_entry(self, fit_file, activity_id, sub_sport, message_dict):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_dict)

    def _write_walking_entry(self, fit_file, activity_id, sub_sport, message_dict):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_dict)

    def _write_hiking_entry(self, fit_file, activity_id, sub_sport, message_dict):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_dict)

    def _write_cycling_entry(self, fit_file, activity_id, sub_sport, message_dict):
        ride = {
            'activity_id'                        : activity_id,
            'strokes'                            : self.__get_field_value(message_dict, 'total_strokes'),
        }
        GarminDB.CycleActivities.s_create_or_update(self.garmin_act_db_session, ride, ignore_none=True, ignore_zero=True)

    def _write_stand_up_paddleboarding_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("sup sport entry: %r", message_dict)
        paddle = {
            'activity_id'                       : activity_id,
            'strokes'                           : self.__get_field_value(message_dict, 'total_strokes'),
            'avg_stroke_distance'               : self.__get_field_value(message_dict, 'avg_stroke_distance'),
        }
        GarminDB.PaddleActivities.s_create_or_update(self.garmin_act_db_session, paddle, ignore_none=True, ignore_zero=True)

    def _write_rowing_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("row sport entry: %r", message_dict)
        return self._write_stand_up_paddleboarding_entry(fit_file, activity_id, sub_sport, message_dict)

    def _write_boating_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("boating sport entry: %r", message_dict)

    def _write_elliptical_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("elliptical entry: %r", message_dict)
        workout = {
            'activity_id'                       : activity_id,
            'steps'                             : self.__get_total_steps(message_dict),
            'elliptical_distance'               : self.__get_total_distance(message_dict),
        }
        GarminDB.EllipticalActivities.s_create_or_update(self.garmin_act_db_session, workout, ignore_none=True, ignore_zero=True)

    def _write_fitness_equipment_entry(self, fit_file, activity_id, sub_sport, message_dict):
        try:
            function = getattr(self, '_write_' + sub_sport.name + '_entry')
            function(fit_file, activity_id, sub_sport, message_dict)
        except AttributeError:
            root_logger.info("No sub sport handler type %s from %s: %s", sub_sport, fit_file.filename, message_dict)

    def _write_alpine_skiing_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("Skiing sport entry: %r", message_dict)

    def _write_swimming_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("Swimming sport entry: %r", message_dict)

    def _write_training_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("Training sport entry: %r", message_dict)

    def _write_transition_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("Transition sport entry: %r", message_dict)

    def _write_generic_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("Generic sport entry: %r", message_dict)

    def __choose_sport(self, current_sport, current_sub_sport, new_sport, new_sub_sport):
        sport = Fit.field_enums.Sport.strict_from_string(current_sport)
        sub_sport = Fit.field_enums.SubSport.strict_from_string(current_sub_sport)
        if (sport is None and new_sport is not None) or (not sport.preferred() and new_sport.preferred()):
            sport = new_sport
        if (sub_sport is None and new_sub_sport is not None) or (not sub_sport.preferred() and new_sub_sport.preferred()):
            sub_sport = new_sub_sport
        return {'sport' : sport.name, 'sub_sport' : sub_sport.name}

    def _write_session_entry(self, fit_file, message_dict):
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        sport = message_dict['sport']
        sub_sport = message_dict['sub_sport']
        activity = {
            'activity_id'                       : activity_id,
            'start_time'                        : message_dict['start_time'],
            'stop_time'                         : message_dict['timestamp'],
            'elapsed_time'                      : message_dict['total_elapsed_time'],
            'moving_time'                       : self.__get_field_value(message_dict, 'total_timer_time'),
            'start_lat'                         : self.__get_field_value(message_dict, 'start_position_lat'),
            'start_long'                        : self.__get_field_value(message_dict, 'start_position_long'),
            'stop_lat'                          : self.__get_field_value(message_dict, 'end_position_lat'),
            'stop_long'                         : self.__get_field_value(message_dict, 'end_position_long'),
            'distance'                          : self.__get_total_distance(message_dict),
            'cycles'                            : self.__get_field_value(message_dict, 'total_cycles'),
            'laps'                              : self.__get_field_value(message_dict, 'num_laps'),
            'avg_hr'                            : self.__get_field_value(message_dict, 'avg_heart_rate'),
            'max_hr'                            : self.__get_field_value(message_dict, 'max_heart_rate'),
            'calories'                          : self.__get_field_value(message_dict, 'total_calories'),
            'avg_cadence'                       : self.__get_field_value(message_dict, 'avg_cadence'),
            'max_cadence'                       : self.__get_field_value(message_dict, 'max_cadence'),
            'avg_speed'                         : self.__get_field_value(message_dict, 'avg_speed'),
            'max_speed'                         : self.__get_field_value(message_dict, 'max_speed'),
            'ascent'                            : self.__get_field_value(message_dict, 'total_ascent'),
            'descent'                           : self.__get_field_value(message_dict, 'total_descent'),
            'max_temperature'                   : self.__get_field_value(message_dict, 'max_temperature'),
            'avg_temperature'                   : self.__get_field_value(message_dict, 'avg_temperature'),
            'training_effect'                   : self.__get_field_value(message_dict, 'total_training_effect'),
            'anaerobic_training_effect'         : self.__get_field_value(message_dict, 'total_anaerobic_training_effect')
        }
        # json metadata gives better values for sport and subsport, so use existing value if set
        current = GarminDB.Activities.s_get(self.garmin_act_db_session, activity_id)
        if current:
            activity.update(self.__choose_sport(current.sport, current.sub_sport, sport, sub_sport))
            root_logger.debug("Updating with %r", activity)
            current.update_from_dict(activity, ignore_none=True, ignore_zero=True)
        else:
            activity.update({'sport' : sport.name, 'sub_sport' : sub_sport.name})
            root_logger.debug("Adding %r", activity)
            self.garmin_act_db_session.add(GarminDB.Activities(**activity))
        function_name = '_write_' + sport.name + '_entry'
        try:
            function = getattr(self, function_name, None)
            if function is not None:
                function(fit_file, activity_id, sub_sport, message_dict)
            else:
                root_logger.warning("No sport handler for type %s from %s: %s", sport, fit_file.filename, message_dict)
        except Exception as e:
            root_logger.error("Exception in %s from %s: %s", function_name, fit_file.filename, e)

    def _write_attribute(self, timestamp, parsed_message, attribute_name, db_attribute_name=None):
        attribute = parsed_message.get(attribute_name)
        if attribute is not None:
            if db_attribute_name is None:
                db_attribute_name = attribute_name
            GarminDB.Attributes.s_set_newer(self.garmin_db_session, db_attribute_name, attribute, timestamp)

    def _write_attributes(self, timestamp, parsed_message, attribute_names):
        for attribute_name in attribute_names:
            self._write_attribute(timestamp, parsed_message, attribute_name)

    def _write_device_settings_entry(self, fit_file, device_settings_message_dict):
        root_logger.debug("device settings message: %r", device_settings_message_dict)
        timestamp = fit_file.time_created()
        attribute_names = [
            'active_time_zone', 'date_mode'
        ]
        self._write_attributes(timestamp, device_settings_message_dict, attribute_names)
        self._write_attribute(timestamp, device_settings_message_dict, 'active_time_zone', 'time_zone')
        self._write_attribute(timestamp, device_settings_message_dict, 'date_mode', 'date_format')

    def _write_lap_entry(self, fit_file, message_dict):
        # we don't get laps data from multiple sources so we don't need to coellesce data in the DB.
        # It's fastest to just write new data out if the it doesn't currently exist.
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        if not GarminDB.ActivityLaps.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'lap' : self.lap}):
            lap = {
                'activity_id'                       : GarminDB.File.id_from_path(fit_file.filename),
                'lap'                               : self.lap,
                'start_time'                        : self.__get_field_value(message_dict, 'start_time'),
                'stop_time'                         : self.__get_field_value(message_dict, 'timestamp'),
                'elapsed_time'                      : self.__get_field_value(message_dict, 'total_elapsed_time'),
                'moving_time'                       : self.__get_field_value(message_dict, 'total_timer_time'),
                'start_lat'                         : self.__get_field_value(message_dict, 'start_position_lat'),
                'start_long'                        : self.__get_field_value(message_dict, 'start_position_long'),
                'stop_lat'                          : self.__get_field_value(message_dict, 'end_position_lat'),
                'stop_long'                         : self.__get_field_value(message_dict, 'end_position_long'),
                'distance'                          : self.__get_total_distance(message_dict),
                'cycles'                            : self.__get_field_value(message_dict, 'total_cycles'),
                'avg_hr'                            : self.__get_field_value(message_dict, 'avg_heart_rate'),
                'max_hr'                            : self.__get_field_value(message_dict, 'max_heart_rate'),
                'calories'                          : self.__get_field_value(message_dict, 'total_calories'),
                'avg_cadence'                       : self.__get_field_value(message_dict, 'avg_cadence'),
                'max_cadence'                       : self.__get_field_value(message_dict, 'max_cadence'),
                'avg_speed'                         : self.__get_field_value(message_dict, 'avg_speed'),
                'max_speed'                         : self.__get_field_value(message_dict, 'max_speed'),
                'ascent'                            : self.__get_field_value(message_dict, 'total_ascent'),
                'descent'                           : self.__get_field_value(message_dict, 'total_descent'),
                'max_temperature'                   : self.__get_field_value(message_dict, 'max_temperature'),
                'avg_temperature'                   : self.__get_field_value(message_dict, 'avg_temperature'),
            }
            self.garmin_act_db_session.add(GarminDB.ActivityLaps(**lap))
            self.lap += 1

    def _write_battery_entry(self, fit_file, battery_message_dict):
        root_logger.debug("battery message: %r", battery_message_dict)

    def _write_user_profile_entry(self, fit_file, message_dict):
        root_logger.debug("user profile message: %r", message_dict)
        timestamp = fit_file.time_created()
        attribute_names = [
            'gender', 'height', 'weight', 'language', 'dist_setting', 'weight_setting', 'position_setting', 'elev_setting', 'sleep_time', 'wake_time',
            'speed_setting'
        ]
        self._write_attributes(timestamp, message_dict, attribute_names)
        self._write_attribute(timestamp, message_dict, 'dist_setting', 'measurement_system')

    def _write_activity_entry(self, fit_file, activity_message_dict):
        root_logger.debug("activity message: %r", activity_message_dict)

    def _write_zones_target_entry(self, fit_file, zones_target_message_dict):
        root_logger.debug("zones target message: %r", zones_target_message_dict)

    def _write_record_entry(self, fit_file, message_dict):
        # We don't get record data from multiple sources so we don't need to coellesce data in the DB.
        # It's fastest to just write the new data out if it doesn't currently exist.
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        if not GarminDB.ActivityRecords.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'record' : self.record}):
            record = {
                'activity_id'                       : activity_id,
                'record'                            : self.record,
                'timestamp'                         : self.__get_field_value(message_dict, 'timestamp'),
                'position_lat'                      : self.__get_field_value(message_dict, 'position_lat'),
                'position_long'                     : self.__get_field_value(message_dict, 'position_long'),
                'distance'                          : self.__get_field_value(message_dict, 'distance'),
                'cadence'                           : self.__get_field_value(message_dict, 'cadence'),
                'hr'                                : self.__get_field_value(message_dict, 'heart_rate'),
                'altitude'                          : self.__get_field_value(message_dict, 'altitude'),
                'speed'                             : self.__get_field_value(message_dict, 'speed'),
                'temperature'                       : self.__get_field_value(message_dict, 'temperature'),
            }
            self.garmin_act_db_session.add(GarminDB.ActivityRecords(**record))
            self.record += 1

    def _write_dev_data_id_entry(self, fit_file, dev_data_id_message_dict):
        root_logger.debug("dev_data_id message: %r", dev_data_id_message_dict)

    def _write_field_description_entry(self, fit_file, field_description_message_dict):
        root_logger.debug("field_description message: %r", field_description_message_dict)

    def _write_length_entry(self, fit_file, length_message_dict):
        root_logger.debug("length message: %r", length_message_dict)

    def _write_monitoring_info_entry(self, fit_file, message_dict):
        activity_types = message_dict['activity_type']
        if isinstance(activity_types, list):
            for index, activity_type in enumerate(activity_types):
                entry = {
                    'file_id'                   : GarminDB.File.s_get_id(self.garmin_db_session, fit_file.filename),
                    'timestamp'                 : message_dict['local_timestamp'],
                    'activity_type'             : activity_type,
                    'resting_metabolic_rate'    : self.__get_field_value(message_dict, 'resting_metabolic_rate'),
                    'cycles_to_distance'        : message_dict['cycles_to_distance'][index],
                    'cycles_to_calories'        : message_dict['cycles_to_calories'][index]
                }
                GarminDB.MonitoringInfo.s_find_or_create(self.garmin_mon_db_session, entry)

    def _write_monitoring_entry(self, fit_file, message_dict):
        # Only include not None values so that we match and update only if a table's columns if it has values.
        entry = utilities.list_and_dict.dict_filter_none_values(message_dict)
        try:
            intersection = GarminDB.MonitoringHeartRate.intersection(entry)
            if len(intersection) > 1 and intersection['heart_rate'] > 0:
                GarminDB.MonitoringHeartRate.s_create_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.MonitoringIntensity.intersection(entry)
            if len(intersection) > 1:
                GarminDB.MonitoringIntensity.s_create_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.MonitoringClimb.intersection(entry)
            if len(intersection) > 1:
                GarminDB.MonitoringClimb.s_create_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.Monitoring.intersection(entry)
            if len(intersection) > 1:
                GarminDB.Monitoring.s_create_or_update(self.garmin_mon_db_session, intersection)
        except ValueError:
            logger.error("write_monitoring_entry: ValueError for %r: %s", entry, traceback.format_exc())
        except Exception:
            logger.error("Exception on monitoring entry: %r: %s", entry, traceback.format_exc())

    def _write_set_entry(self, fit_file, set_message_dict):
        root_logger.debug("set message: %r", set_message_dict)

    def _write_device_info_entry(self, fit_file, device_info_message_dict):
        try:
            device_type = device_info_message_dict.get('device_type')
            serial_number = device_info_message_dict.get('serial_number')
            manufacturer = GarminDB.Device.Manufacturer.convert(device_info_message_dict.get('manufacturer'))
            product = device_info_message_dict.get('product')
            source_type = device_info_message_dict.get('source_type')
            # local devices are part of the main device. Base missing fields off of the main device.
            if source_type is Fit.field_enums.SourceType.local:
                if serial_number is None and self.serial_number is not None and device_type is not None:
                    serial_number = GarminDB.Device.local_device_serial_number(self.serial_number, device_type)
                if manufacturer is None and self.manufacturer is not None:
                    manufacturer = self.manufacturer
                if product is None and self.product is not None:
                    product = self.product
        except Exception as e:
            logger.warning("Unrecognized device in %s: %r - %s", fit_file.filename, device_info_message_dict, e)

        if serial_number is not None:
            device = {
                'serial_number'     : serial_number,
                'timestamp'         : device_info_message_dict['timestamp'],
                'manufacturer'      : manufacturer,
                'product'           : Fit.field_enums.name_for_enum(product),
                'hardware_version'  : device_info_message_dict.get('hardware_version'),
            }
            try:
                GarminDB.Device.s_create_or_update(self.garmin_db_session, device, ignore_none=True)
            except Exception as e:
                logger.error("Device not written: %r - %s", device_info_message_dict, e)
            device_info = {
                'file_id'               : GarminDB.File.s_get_id(self.garmin_db_session, fit_file.filename),
                'serial_number'         : serial_number,
                'device_type'           : Fit.field_enums.name_for_enum(device_type),
                'timestamp'             : device_info_message_dict['timestamp'],
                'cum_operating_time'    : device_info_message_dict.get('cum_operating_time'),
                'battery_voltage'       : device_info_message_dict.get('battery_voltage'),
                'software_version'      : device_info_message_dict['software_version'],
            }
            try:
                GarminDB.DeviceInfo.s_create_or_update(self.garmin_db_session, device_info, ignore_none=True)
            except Exception as e:
                logger.warning("device_info not written: %r - %s", device_info_message_dict, e)
