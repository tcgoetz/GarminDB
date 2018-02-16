#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, sys

import Fit
import GarminDB

logger = logging.getLogger(__file__)

class FitFileProcessor():

    def __init__(self, db_params_dict, english_units, debug):
        self.db_params_dict = db_params_dict
        self.english_units = english_units
        self.debug = debug

        self.garmin_db = GarminDB.GarminDB(db_params_dict, debug)
        self.garmin_mon_db = GarminDB.MonitoringDB(self.db_params_dict, self.debug)
        self.garmin_act_db = GarminDB.ActivitiesDB(self.db_params_dict, self.debug)

        if english_units:
            GarminDB.Attributes.set_newer(self.garmin_db, 'units', 'english')
        else:
            GarminDB.Attributes.set_newer(self.garmin_db, 'units', 'metric')
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))

    def write_generic(self, fit_file, message_type, messages):
        for message in messages:
            try:
                function = getattr(self, 'write_' + message_type + "_entry")
                function(fit_file, messages)
            except AttributeError:
                logger.debug("No entry handler for message type %s (%d) from %s: %s" % (message_type, len(messages), fit_file.filename, str(messages[0])))

    def write_message_type(self, fit_file, message_type):
        messages = fit_file[message_type]
        function = getattr(self, 'write_' + message_type, self.write_generic)
        function(fit_file, message_type, messages)
        logger.debug("Processed %d %s entries for %s" % (len(messages), message_type, fit_file.filename))

    def write_message_types(self, fit_file, message_types):
        logger.info("%s [%s] message types: %s" % (fit_file.filename, fit_file.type(), message_types))
        #
        # Some ordering is import: 1. create new file entries 2. create new device entries
        #
        priority_message_types = ['file_id', 'device_info']
        for message_type in priority_message_types:
            self.write_message_type(fit_file, message_type)
        for message_type in message_types:
            if message_type not in priority_message_types:
                self.write_message_type(fit_file, message_type)

    def write_file(self, fit_file):
        self.write_message_types(fit_file, fit_file.message_types())

    #
    # Message type handlers
    #
    def write_file_id_entry(self, fit_file, message):
        parsed_message = message.to_dict()
        if parsed_message['serial_number'] is not None:
            device = {
                'serial_number' : parsed_message['serial_number'],
                'timestamp'     : parsed_message['time_created'],
                'manufacturer'  : parsed_message['manufacturer'],
                'product'       : parsed_message['product'],
            }
            GarminDB.Device.find_or_create(self.garmin_db, device)
        file = {
            'name'          : fit_file.filename,
            'type'          : parsed_message['type'],
            'serial_number' : parsed_message['serial_number'],
        }
        GarminDB.File.find_or_create(self.garmin_db, file)

    def write_stress_level_entry(self, fit_file, stress_message):
        parsed_message = stress_message.to_dict()
        stress = {
            'timestamp' : parsed_message['stress_level_time'],
            'stress'    : parsed_message['stress_level_value'],
        }
        GarminDB.Stress.find_or_create(self.garmin_db, stress)

    def write_event_entry(self, fit_file, event_message):
        logger.debug("event message: " + repr(event_message.to_dict()))

    def write_software_entry(self, fit_file, software_message):
        logger.debug("software message: " + repr(software_message.to_dict()))

    def write_file_creator_entry(self, fit_file, file_creator_message):
        logger.debug("file creator message: " + repr(file_creator_message.to_dict()))

    def write_sport_entry(self, fit_file, sport_message):
        logger.info("sport message: " + repr(sport_message.to_dict()))

    def write_sensor_entry(self, fit_file, sensor_message):
        logger.debug("sensor message: " + repr(sensor_message.to_dict()))

    def write_source_entry(self, fit_file, source_message):
        logger.info("source message: " + repr(source_message.to_dict()))

    def write_session_entry(self, fit_file, message):
        logger.info("session message: " + repr(message.to_dict()))
        parsed_message = message.to_dict()
        activity = {
            'id'                                : GarminDB.File.get(self.garmin_db, fit_file.filename),
            'start_time'                        : parsed_message['start_time'],
            'stop_time'                         : parsed_message['timestamp'],
            'time'                              : parsed_message['total_elapsed_time'],
            'moving_time'                       : parsed_message.get('total_timer_time', None),
            'start_lat'                         : parsed_message.get('start_position_lat', None),
            'start_long'                        : parsed_message.get('start_position_long', None),
            'stop_lat'                          : parsed_message.get('end_position_lat', None),
            'stop_long'                         : parsed_message.get('end_position_long', None),
            'distance'                          : parsed_message.get('total_distance', None),
            'sport'                             : parsed_message['sport'],
            'sub_sport'                         : parsed_message['sub_sport'],
            'cycles'                            : parsed_message.get('total_cycles', None),
            'laps'                              : parsed_message['num_laps'],
            'avg_hr'                            : parsed_message['avg_heart_rate'],
            'max_hr'                            : parsed_message['max_heart_rate'],
            'calories'                          : parsed_message['total_calories'],
            'avg_cadence'                       : parsed_message['avg_cadence'],
            'max_cadence'                       : parsed_message['max_cadence'],
            'avg_speed'                         : parsed_message['avg_speed'],
            'max_speed'                         : parsed_message['max_speed'],
            'ascent'                            : parsed_message['total_ascent'],
            'descent'                           : parsed_message['total_descent'],
            'max_tempature'                     : parsed_message.get('max_temperature', None),
            'avg_tempature'                     : parsed_message.get('avg_temperature', None),
            'training_effect'                   : parsed_message.get('total_training_effect', None),
            'anaerobic_training_effect'         : parsed_message.get('total_anaerobic_training_effect', None)
        }
        GarminDB.Activities.find_or_create(self.garmin_act_db, activity)

    def write_device_settings_entry(self, fit_file, device_settings_message):
        logger.debug("device settings message: " + repr(device_settings_message.to_dict()))

    def write_lap_entry(self, fit_file, lap_message):
        logger.info("lap message: " + repr(lap_message.to_dict()))

    def write_battery_entry(self, fit_file, battery_message):
        logger.info("battery message: " + repr(battery_message.to_dict()))

    def write_attribute(self, timestamp, parsed_message, attribute_name):
        attribute = parsed_message.get(attribute_name, None)
        if attribute is not None:
            GarminDB.Attributes.set_newer(self.garmin_db, attribute_name, attribute, timestamp)

    def write_user_profile_entry(self, fit_file, message):
        logger.info("user profile message: " + repr(message.to_dict()))
        parsed_message = message.to_dict()
        timestamp = fit_file.time_created()
        for attribute_name in [
                'Gender', 'Height', 'Weight', 'Language', 'dist_setting', 'weight_setting', 'position_setting', 'elev_setting', 'sleep_time', 'wake_time'
            ]:
            self.write_attribute(timestamp, parsed_message, attribute_name)

    def write_activity_entry(self, fit_file, activity_message):
        logger.info("activity message: " + repr(activity_message.to_dict()))

    def write_zones_target_entry(self, fit_file, zones_target_message):
        logger.info("zones target message: " + repr(zones_target_message.to_dict()))

    def write_record_entry(self, fit_file, record_message):
        logger.debug("record message: " + repr(record_message.to_dict()))

    def write_dev_data_id_entry(self, fit_file, dev_data_id_message):
        logger.debug("dev_data_id message: " + repr(dev_data_id_message.to_dict()))

    def write_monitoring_info_entry(self, fit_file, message):
        parsed_message = message.to_dict()
        activity_type = parsed_message['activity_type']
        if isinstance(activity_type, list):
            for index, type in enumerate(activity_type):
                entry = {
                    'file_id'                   : GarminDB.File.get(self.garmin_db, fit_file.filename),
                    'timestamp'                 : parsed_message['local_timestamp'],
                    'activity_type'             : type,
                    'resting_metabolic_rate'    : parsed_message['resting_metabolic_rate'],
                    'cycles_to_distance'        : parsed_message['cycles_to_distance'][index],
                    'cycles_to_calories'        : parsed_message['cycles_to_calories'][index]
                }
                GarminDB.MonitoringInfo.find_or_create(self.garmin_mon_db, entry)

    def write_monitoring_entry(self, fit_file, message):
        entry = message.to_dict()
        try:
            if GarminDB.MonitoringHeartRate.matches(entry):
                GarminDB.MonitoringHeartRate.find_or_create(self.garmin_mon_db, entry)
            elif GarminDB.MonitoringIntensityMins.matches(entry):
                GarminDB.MonitoringIntensityMins.find_or_create(self.garmin_mon_db, entry)
            elif GarminDB.MonitoringClimb.matches(entry):
                GarminDB.MonitoringClimb.find_or_create(self.garmin_mon_db, entry)
            else:
                GarminDB.Monitoring.find_or_create(self.garmin_mon_db, entry)
        except ValueError as e:
            logger.info("ValueError on entry: %s" % repr(entry))
        except Exception as e:
            logger.info("Exception on entry: %s" % repr(entry))
            raise

    def write_device_info_entry(self, fit_file, device_info_message):
        parsed_message = device_info_message.to_dict()
        if parsed_message['serial_number'] is not None:
            device = {
                'serial_number'     : parsed_message['serial_number'],
                'timestamp'         : parsed_message['timestamp'],
                'manufacturer'      : parsed_message['manufacturer'],
                'product'           : parsed_message['product'],
                'hardware_version'  : parsed_message.get('hardware_version', None),
            }
            try:
                GarminDB.Device.create_or_update(self.garmin_db, device)
            except ValueError:
                logger.debug("Message not written: " + repr(parsed_message))
            device_info = {
                'file_id'               : GarminDB.File.get(self.garmin_db, fit_file.filename),
                'serial_number'         : parsed_message['serial_number'],
                'timestamp'             : parsed_message['timestamp'],
                'cum_operating_time'    : parsed_message.get('cum_operating_time', None),
                'battery_voltage'       : parsed_message.get('battery_voltage', None),
                'software_version'      : parsed_message['software_version'],
            }
            try:
                GarminDB.DeviceInfo.find_or_create(self.garmin_db, device_info)
            except Exception as e:
                logger.warning("Device info message not written: " + repr(parsed_message))
