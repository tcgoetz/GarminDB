#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, sys, datetime, traceback

import Fit
import GarminDB


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class FitFileProcessor():

    def __init__(self, db_params_dict, debug):
        root_logger.info("Debug: %s", debug)
        self.db_params_dict = db_params_dict
        self.debug = debug

        self.garmin_db = GarminDB.GarminDB(db_params_dict, debug - 1)
        self.garmin_mon_db = GarminDB.MonitoringDB(self.db_params_dict, self.debug - 1)
        self.garmin_act_db = GarminDB.ActivitiesDB(self.db_params_dict, self.debug - 1)

    def write_generic(self, fit_file, message_type, messages):
        for message in messages:
            handler_name = 'write_' + message_type.name + '_entry'
            function = getattr(self, handler_name, None)
            if function is not None:
                # parse the message with lower case field names
                message_dict = message.to_lower_dict()
                function(fit_file, message_dict)
            else:
                root_logger.debug("No entry handler %s for message type %r (%d) from %s: %s",
                    handler_name, message_type, len(messages), fit_file.filename, messages[0])

    def write_message_type(self, fit_file, message_type):
        messages = fit_file[message_type]
        function = getattr(self, 'write_' + message_type.name, self.write_generic)
        function(fit_file, message_type, messages)
        root_logger.debug("Processed %d %r entries for %s", len(messages), message_type, fit_file.filename)

    def write_message_types(self, fit_file, message_types):
        root_logger.info("Importing %s (%s) [%s] with message types: %s", fit_file.filename, fit_file.time_created(), fit_file.type(), message_types)
        #
        # Some ordering is import: 1. create new file entries 2. create new device entries
        #
        priority_message_types = [Fit.MessageType.file_id, Fit.MessageType.device_info]
        for message_type in priority_message_types:
            self.write_message_type(fit_file, message_type)
        for message_type in message_types:
            if message_type not in priority_message_types:
                self.write_message_type(fit_file, message_type)

    def write_file(self, fit_file):
        self.lap = 1
        self.record = 1
        self.serial_number = None
        self.manufacturer = None
        self.product = None
        with self.garmin_db.managed_session() as self.garmin_db_session:
            with self.garmin_mon_db.managed_session() as self.garmin_mon_db_session:
                with self.garmin_act_db.managed_session() as self.garmin_act_db_session:
                    self.write_message_types(fit_file, fit_file.message_types())
                    # Now write a file's worth of data to the DB
                    self.garmin_act_db_session.commit()
                self.garmin_mon_db_session.commit()
            self.garmin_db_session.commit()


    #
    # Message type handlers
    #
    def write_file_id_entry(self, fit_file, message_dict):
        root_logger.info("file_id message: %r", message_dict)
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
                'product'       : Fit.FieldEnums.name_for_enum(self.product),
            }
            GarminDB.Device._find_or_create(self.garmin_db_session, device)
        (file_id, file_name) = GarminDB.File.name_and_id_from_path(fit_file.filename)
        file = {
            'id'            : file_id,
            'name'          : file_name,
            'type'          : GarminDB.File.FileType.convert(message_dict['type']),
            'serial_number' : self.serial_number,
        }
        GarminDB.File._find_or_create(self.garmin_db_session, file)

    def write_stress_level_entry(self, fit_file, stress_message_dict):
        stress = {
            'timestamp' : stress_message_dict['stress_level_time'],
            'stress'    : stress_message_dict['stress_level_value'],
        }
        GarminDB.Stress._find_or_create(self.garmin_db_session, stress)

    def write_event_entry(self, fit_file, event_message_dict):
        root_logger.debug("event message: %r", event_message_dict)

    def write_software_entry(self, fit_file, software_message_dict):
        root_logger.debug("software message: %r", software_message_dict)

    def write_file_creator_entry(self, fit_file, file_creator_message_dict):
        root_logger.debug("file creator message: %r", file_creator_message_dict)

    def write_sport_entry(self, fit_file, sport_message_dict):
        root_logger.debug("sport message: %r", sport_message_dict)

    def write_sensor_entry(self, fit_file, sensor_message_dict):
        root_logger.debug("sensor message: %r", sensor_message_dict)

    def write_source_entry(self, fit_file, source_message_dict):
        root_logger.debug("source message: %r", source_message_dict)

    def get_field_value(self, message_dict, field_name):
        # developer fields take precedence over regular fields
        return message_dict.get('dev_' + field_name, message_dict.get(field_name))

    def get_field_list_value(self, message_dict, field_name_list):
        for field_name in field_name_list:
            value = self.get_field_value(message_dict, field_name)
            if value is not None:
                return value

    def write_running_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("run entry: %r", message_dict)
        run = {
            'activity_id'                       : activity_id,
            'steps'                             : self.get_field_value(message_dict, 'total_steps'),
            'avg_pace'                          : Fit.Conversions.speed_to_pace(message_dict.get('avg_speed')),
            'max_pace'                          : Fit.Conversions.speed_to_pace(message_dict.get('max_speed')),
            'avg_steps_per_min'                 : message_dict.get('avg_cadence', 0) * 2,
            'max_steps_per_min'                 : message_dict.get('max_cadence', 0) * 2,
            'avg_step_length'                   : self.get_field_value(message_dict, 'avg_step_length'),
            'avg_vertical_ratio'                : self.get_field_value(message_dict, 'avg_vertical_ratio'),
            'avg_vertical_oscillation'          : self.get_field_value(message_dict, 'avg_vertical_oscillation'),
            'avg_gct_balance'                   : self.get_field_value(message_dict, 'avg_stance_time_balance'),
            'avg_ground_contact_time'           : self.get_field_value(message_dict, 'avg_stance_time'),
            'avg_stance_time_percent'           : self.get_field_value(message_dict, 'avg_stance_time_percent'),
        }
        GarminDB.RunActivities._create_or_update_not_none(self.garmin_act_db_session, run)

    def write_walking_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("walk entry: %r", message_dict)
        walk = {
            'activity_id'                       : activity_id,
            'steps'                             : self.get_field_value(message_dict, 'total_steps'),
            'avg_pace'                          : Fit.Conversions.speed_to_pace(message_dict.get('avg_speed')),
            'max_pace'                          : Fit.Conversions.speed_to_pace(message_dict.get('max_speed')),
        }
        GarminDB.WalkActivities._create_or_update_not_none(self.garmin_act_db_session, walk)

    def write_hiking_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("hike entry: %r", message_dict)
        return self.write_walking_entry(fit_file, activity_id, sub_sport, message_dict)

    def write_cycling_entry(self, fit_file, activity_id, sub_sport, message_dict):
        ride = {
            'activity_id'                        : activity_id,
            'strokes'                            : self.get_field_value(message_dict, 'total_strokes'),
        }
        root_logger.debug("ride entry: %r writing %r", message_dict, ride)
        GarminDB.CycleActivities._create_or_update_not_none(self.garmin_act_db_session, ride)

    def write_stand_up_paddleboarding_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("sup entry: %r", message_dict)
        paddle = {
            'activity_id'                       : activity_id,
            'strokes'                           : self.get_field_value(message_dict, 'total_strokes'),
            'avg_stroke_distance'               : self.get_field_value(message_dict, 'avg_stroke_distance'),
        }
        GarminDB.PaddleActivities._create_or_update_not_none(self.garmin_act_db_session, paddle)

    def write_rowing_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("row entry: %r", message_dict)
        return self.write_stand_up_paddleboarding_entry(fit_file, activity_id, sub_sport, message_dict)

    def write_elliptical_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("elliptical entry: %r", message_dict)
        workout = {
            'activity_id'                       : activity_id,
            'steps'                             : message_dict.get('dev_steps', message_dict.get('total_steps')),
            'elliptical_distance'               : message_dict.get('dev_user_distance', message_dict.get('dev_distance', message_dict.get('distance'))),
        }
        GarminDB.EllipticalActivities._create_or_update_not_none(self.garmin_act_db_session, workout)

    def write_fitness_equipment_entry(self, fit_file, activity_id, sub_sport, message_dict):
        try:
            function = getattr(self, 'write_' + sub_sport.name + '_entry')
            function(fit_file, activity_id, sub_sport, message_dict)
        except AttributeError:
            root_logger.info("No sub sport handler type %s from %s: %s", sub_sport, fit_file.filename, message_dict)

    def write_alpine_skiing_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("Skiing entry: %r", message_dict)

    def write_training_entry(self, fit_file, activity_id, sub_sport, message_dict):
        root_logger.debug("Training entry: %r", message_dict)

    def write_session_entry(self, fit_file, message_dict):
        root_logger.debug("session message: %r", message_dict)
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        sport = message_dict['sport']
        sub_sport = message_dict['sub_sport']
        activity = {
            'activity_id'                       : activity_id,
            'start_time'                        : message_dict['start_time'],
            'stop_time'                         : message_dict['timestamp'],
            'elapsed_time'                      : message_dict['total_elapsed_time'],
            'moving_time'                       : self.get_field_value(message_dict, 'total_timer_time'),
            'start_lat'                         : self.get_field_value(message_dict, 'start_position_lat'),
            'start_long'                        : self.get_field_value(message_dict, 'start_position_long'),
            'stop_lat'                          : self.get_field_value(message_dict, 'end_position_lat'),
            'stop_long'                         : self.get_field_value(message_dict, 'end_position_long'),
            'distance'                          : self.get_field_list_value(message_dict, ['user_distance', 'total_distance']),
            'cycles'                            : self.get_field_value(message_dict, 'total_cycles'),
            'laps'                              : self.get_field_value(message_dict, 'num_laps'),
            'avg_hr'                            : self.get_field_value(message_dict, 'avg_heart_rate'),
            'max_hr'                            : self.get_field_value(message_dict, 'max_heart_rate'),
            'calories'                          : self.get_field_value(message_dict, 'total_calories'),
            'avg_cadence'                       : self.get_field_value(message_dict, 'avg_cadence'),
            'max_cadence'                       : self.get_field_value(message_dict, 'max_cadence'),
            'avg_speed'                         : self.get_field_value(message_dict, 'avg_speed'),
            'max_speed'                         : self.get_field_value(message_dict, 'max_speed'),
            'ascent'                            : self.get_field_value(message_dict, 'total_ascent'),
            'descent'                           : self.get_field_value(message_dict, 'total_descent'),
            'max_temperature'                   : self.get_field_value(message_dict, 'max_temperature'),
            'avg_temperature'                   : self.get_field_value(message_dict, 'avg_temperature'),
            'training_effect'                   : self.get_field_value(message_dict, 'total_training_effect'),
            'anaerobic_training_effect'         : self.get_field_value(message_dict, 'total_anaerobic_training_effect')
        }
        # json metadata gives better values for sport and subsport, so use existing value if set
        current = GarminDB.Activities.get(self.garmin_act_db, activity_id)
        if current:
            if current.sport is None:
                activity['sport'] = sport.name
            if current.sub_sport is None:
                activity['sub_sport'] = sub_sport.name
        GarminDB.Activities._create_or_update_not_none(self.garmin_act_db_session, activity)
        try:
            function = getattr(self, 'write_' + sport.name + '_entry')
            function(fit_file, activity_id, sub_sport, message_dict)
        except AttributeError:
            root_logger.info("No sport handler for type %s from %s: %s", sport, fit_file.filename, message_dict)

    def write_device_settings_entry(self, fit_file, device_settings_message_dict):
        root_logger.debug("device settings message: %r", device_settings_message_dict)

    def write_lap_entry(self, fit_file, message_dict):
        root_logger.debug("lap message: %r", message_dict)
        lap = {
            'activity_id'                       : GarminDB.File.id_from_path(fit_file.filename),
            'lap'                               : self.lap,
            'start_time'                        : self.get_field_value(message_dict, 'start_time'),
            'stop_time'                         : self.get_field_value(message_dict, 'timestamp'),
            'elapsed_time'                      : self.get_field_value(message_dict, 'total_elapsed_time'),
            'moving_time'                       : self.get_field_value(message_dict, 'total_timer_time'),
            'start_lat'                         : self.get_field_value(message_dict, 'start_position_lat'),
            'start_long'                        : self.get_field_value(message_dict, 'start_position_long'),
            'stop_lat'                          : self.get_field_value(message_dict, 'end_position_lat'),
            'stop_long'                         : self.get_field_value(message_dict, 'end_position_long'),
            'distance'                          : self.get_field_list_value(message_dict, ['user_distance', 'total_distance']),
            'cycles'                            : self.get_field_value(message_dict, 'total_cycles'),
            'avg_hr'                            : self.get_field_value(message_dict, 'avg_heart_rate'),
            'max_hr'                            : self.get_field_value(message_dict, 'max_heart_rate'),
            'calories'                          : self.get_field_value(message_dict, 'total_calories'),
            'avg_cadence'                       : self.get_field_value(message_dict, 'avg_cadence'),
            'max_cadence'                       : self.get_field_value(message_dict, 'max_cadence'),
            'avg_speed'                         : self.get_field_value(message_dict, 'avg_speed'),
            'max_speed'                         : self.get_field_value(message_dict, 'max_speed'),
            'ascent'                            : self.get_field_value(message_dict, 'total_ascent'),
            'descent'                           : self.get_field_value(message_dict, 'total_descent'),
            'max_temperature'                   : self.get_field_value(message_dict, 'max_temperature'),
            'avg_temperature'                   : self.get_field_value(message_dict, 'avg_temperature'),
        }
        GarminDB.ActivityLaps._create_or_update_not_none(self.garmin_act_db_session, lap)
        self.lap += 1

    def write_battery_entry(self, fit_file, battery_message_dict):
        root_logger.debug("battery message: %r", battery_message_dict)

    def write_attribute(self, timestamp, parsed_message, attribute_name):
        attribute = parsed_message.get(attribute_name)
        if attribute is not None:
            GarminDB.Attributes._set_newer(self.garmin_db_session, attribute_name, attribute, timestamp)

    def write_user_profile_entry(self, fit_file, message_dict):
        root_logger.debug("user profile message: %r", message_dict)
        timestamp = fit_file.time_created()
        for attribute_name in [
                'gender', 'height', 'weight', 'language', 'dist_setting', 'weight_setting', 'position_setting', 'elev_setting', 'sleep_time', 'wake_time'
            ]:
            self.write_attribute(timestamp, message_dict, attribute_name)

    def write_activity_entry(self, fit_file, activity_message_dict):
        root_logger.debug("activity message: %r", activity_message_dict)

    def write_zones_target_entry(self, fit_file, zones_target_message_dict):
        root_logger.debug("zones target message: %r", zones_target_message_dict)

    def write_record_entry(self, fit_file, message_dict):
        root_logger.debug("record message: %r", message_dict)
        record = {
            'activity_id'                       : GarminDB.File.id_from_path(fit_file.filename),
            'record'                            : self.record,
            'timestamp'                         : self.get_field_value(message_dict, 'timestamp'),
            'position_lat'                      : self.get_field_value(message_dict, 'position_lat'),
            'position_long'                     : self.get_field_value(message_dict, 'position_long'),
            'distance'                          : self.get_field_value(message_dict, 'distance'),
            'cadence'                           : self.get_field_value(message_dict, 'cadence'),
            'hr'                                : self.get_field_value(message_dict, 'heart_rate'),
            'alititude'                         : self.get_field_value(message_dict, 'altitude'),
            'speed'                             : self.get_field_value(message_dict, 'speed'),
            'temperature'                       : self.get_field_value(message_dict, 'temperature'),
        }
        GarminDB.ActivityRecords._create_or_update_not_none(self.garmin_act_db_session, record)
        self.record += 1

    def write_dev_data_id_entry(self, fit_file, dev_data_id_message_dict):
        root_logger.debug("dev_data_id message: %r", dev_data_id_message_dict)

    def write_field_description_entry(self, fit_file, field_description_message_dict):
        root_logger.debug("field_description message: %r", field_description_message_dict)

    def write_monitoring_info_entry(self, fit_file, message_dict):
        activity_types = message_dict['activity_type']
        if isinstance(activity_types, list):
            for index, activity_type in enumerate(activity_types):
                entry = {
                    'file_id'                   : GarminDB.File._get_id(self.garmin_db_session, fit_file.filename),
                    'timestamp'                 : message_dict['local_timestamp'],
                    'activity_type'             : activity_type,
                    'resting_metabolic_rate'    : self.get_field_value(message_dict, 'resting_metabolic_rate'),
                    'cycles_to_distance'        : message_dict['cycles_to_distance'][index],
                    'cycles_to_calories'        : message_dict['cycles_to_calories'][index]
                }
                GarminDB.MonitoringInfo._find_or_create(self.garmin_mon_db_session, entry)

    def write_monitoring_entry(self, fit_file, message_dict):
        # Only include not None values so that we match and update only if a table's columns if it has values.
        entry = {key : value for key, value in message_dict.iteritems() if value is not None}
        try:
            intersection = GarminDB.MonitoringHeartRate.intersection(entry)
            if len(intersection) > 1 and intersection['heart_rate'] > 0:
                GarminDB.MonitoringHeartRate._create_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.MonitoringIntensity.intersection(entry)
            if len(intersection) > 1:
                GarminDB.MonitoringIntensity._create_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.MonitoringClimb.intersection(entry)
            if len(intersection) > 1:
                GarminDB.MonitoringClimb._create_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.Monitoring.intersection(entry)
            if len(intersection) > 1:
                GarminDB.Monitoring._create_or_update(self.garmin_mon_db_session, intersection)
        except ValueError as e:
            logger.error("write_monitoring_entry: ValueError for %r: %s", entry, traceback.format_exc())
        except Exception as e:
            logger.error("Exception on monitoring entry: %r: %s", entry, traceback.format_exc())

    def write_device_info_entry(self, fit_file, device_info_message_dict):
        try:
            device_type = device_info_message_dict.get('device_type')
            serial_number = device_info_message_dict.get('serial_number')
            manufacturer = GarminDB.Device.Manufacturer.convert(device_info_message_dict.get('manufacturer'))
            product = device_info_message_dict.get('product')
            source_type = device_info_message_dict.get('source_type')
            # local devices are part of the main device. Base missing fields off of the main device.
            if source_type is Fit.FieldEnums.SourceType.local:
                if serial_number is None and self.serial_number is not None and device_type is not None:
                    serial_number = GarminDB.Device.local_device_serial_number(self.serial_number, device_type)
                if manufacturer is None and self.manufacturer is not None:
                    manufacturer = self.manufacturer
                if product is None and self.product is not None:
                    product = self.product
        except Exception as e:
            logger.warning("Unrecognized device: %r - %s", device_info_message_dict, e)

        if serial_number is not None:
            device = {
                'serial_number'     : serial_number,
                'timestamp'         : device_info_message_dict['timestamp'],
                'manufacturer'      : manufacturer,
                'product'           : Fit.FieldEnums.name_for_enum(product),
                'hardware_version'  : device_info_message_dict.get('hardware_version'),
            }
            try:
                GarminDB.Device._create_or_update_not_none(self.garmin_db_session, device)
            except Exception as e:
                logger.error("Device not written: %r - %s", device_info_message_dict, e)
            device_info = {
                'file_id'               : GarminDB.File._get_id(self.garmin_db_session, fit_file.filename),
                'serial_number'         : serial_number,
                'device_type'           : Fit.FieldEnums.name_for_enum(device_type),
                'timestamp'             : device_info_message_dict['timestamp'],
                'cum_operating_time'    : device_info_message_dict.get('cum_operating_time'),
                'battery_voltage'       : device_info_message_dict.get('battery_voltage'),
                'software_version'      : device_info_message_dict['software_version'],
            }
            try:
                GarminDB.DeviceInfo._create_or_update_not_none(self.garmin_db_session, device_info)
            except Exception as e:
                logger.warning("device_info not written: %r - %s", device_info_message_dict, e)
