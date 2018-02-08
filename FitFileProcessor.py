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
            GarminDB.Attributes.set(self.garmin_db, 'units', 'english')
        else:
            GarminDB.Attributes.set(self.garmin_db, 'units', 'metric')
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))

    def write_message_type(self, fit_file, message_type):
        messages = fit_file[message_type]
        try:
            function = getattr(self, 'write_' + message_type)
            function(fit_file, messages)
            logger.debug("Processed %d %s entries for %s" % (len(messages), message_type, fit_file.filename))
        except AttributeError:
            logger.warning("No handler for message type %s (%d) from %s" % (message_type, len(messages), fit_file.filename))

    def write_message_types(self, fit_file, message_types):
        logger.info("%s message types: %s" % (fit_file.filename, message_types))
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
    # Message type handler
    #
    def write_file_id_entry(self, fit_file, message):
        parsed_message = message.parsed()
        device = {
            'serial_number' : parsed_message['serial_number'],
            'timestamp' : parsed_message['time_created'],
            'manufacturer' : parsed_message['manufacturer'],
            'product' : parsed_message['product'],
        }
        GarminDB.Device.find_or_create(self.garmin_db, device)
        file = {
            'name' : fit_file.filename,
            'type' : parsed_message['type'],
            'serial_number' : parsed_message['serial_number'],
        }
        GarminDB.File.find_or_create(self.garmin_db, file)

    def write_file_id(self, fit_file, file_id_messages):
        for message in file_id_messages:
            self.write_file_id_entry(fit_file, message)

    def write_stress(self, fit_file, stress_messages):
        for fit_file in self.fitfiles:
            GarminDB.File.find_or_create(self.garmin_db, {'name' : fit_file.filename, 'type' : fit_file.type()})
            stress_messages = fit_file['stress_level']
            if stress_messages:
                for stress_message in stress_messages:
                    timestamp = stress_message['stress_level_time'].value()
                    stress = stress_message['stress_level_value'].value()
                    GarminDB.Stress.find_or_create(self.garmin_db, {'timestamp' : timestamp, 'stress' : stress})

    def write_event(self, fit_file, event_messages):
        for message in event_messages:
            logger.info("event message: " + repr(message.parsed()))

    def write_software(self, fit_file, software_messages):
        for message in software_messages:
            logger.debug("software message: " + repr(message.parsed()))

    def write_file_creator(self, fit_file, file_creator_messages):
        for message in file_creator_messages:
            logger.debug("file creator message: " + repr(message.parsed()))

    def write_sport(self, fit_file, sport_messages):
        for message in sport_messages:
            logger.info("sport message: " + repr(message.parsed()))

    def write_sensor(self, fit_file, sensor_messages):
        for message in sensor_messages:
            logger.debug("sensor message: " + repr(message.parsed()))

    def write_source(self, fit_file, source_messages):
        for message in source_messages:
            logger.info("source message: " + repr(message.parsed()))

    def write_session_entry(self, fit_file, message):
        parsed_message = message.parsed()
        activity = {
            'start_time'                        : parsed_message['start_time'],
            'stop_time'                         : parsed_message['timestamp'],
            'sport_type'                        : parsed_message['sport'],
            'cycles'                            : parsed_message['cycles'],
            'laps'                              : parsed_message['num_laps'],
            'avg_hr'                            : parsed_message['avg_heart_rate'],
            'max_hr'                            : parsed_message['max_heart_rate'],
            'calories'                          : parsed_message['total_calories'],
            'avg_cadence'                       : parsed_message['avg_cadence'],
            'avg_speed'                         : parsed_message['avg_speed'],
            'max_speed'                         : parsed_message['max_speed'],
            'ascent'                            : parsed_message['total_ascent'],
            'descent'                           : parsed_message['total_descent'],
            'training_effect'                   : parsed_message['total_training_effect'],
            'anaerobic_training_effect'         : parsed_message['total_anaerobic_training_effect'],
        }
        GarminDB.Activities.find_or_create(self.garmin_act_db, activity)

    def write_session(self, fit_file, session_messages):
        for message in session_messages:
            logger.info("session message: " + repr(message.parsed()))
            self.write_session_entry(fit_file, message)

    def write_device_settings(self, fit_file, device_settings_messages):
        for message in device_settings_messages:
            logger.debug("device settings message: " + repr(message.parsed()))

    def write_lap(self, fit_file, lap_messages):
        for message in lap_messages:
            logger.info("lap message: " + repr(message.parsed()))

    def write_battery(self, fit_file, battery_messages):
        for message in battery_messages:
            logger.info("battery message: " + repr(message.parsed()))

    def write_user_profile(self, fit_file, user_profile_messages):
        for message in user_profile_messages:
            logger.info("user profile message: " + repr(message.parsed()))

    def write_activity(self, fit_file, activity_messages):
        for message in activity_messages:
            logger.debug("activity message: " + repr(message.parsed()))

    def write_zones_target(self, fit_file, zones_target_messages):
        for message in zones_target_messages:
            logger.info("zones target message: " + repr(message.parsed()))

    def write_record(self, fit_file, record_messages):
        for message in record_messages:
            logger.debug("record message: " + repr(message.parsed()))

    def write_monitoring_info_entry(self, fit_file, message):
        parsed_message = message.parsed()
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

    def write_monitoring_info(self, fit_file, monitoring_info_messages):
        for message in monitoring_info_messages:
            self.write_monitoring_info_entry(fit_file, message)

    def write_monitoring_entry(self, entry):
        if GarminDB.MonitoringHeartRate.matches(entry):
            GarminDB.MonitoringHeartRate.find_or_create(self.garmin_mon_db, entry)
        elif GarminDB.MonitoringIntensityMins.matches(entry):
            GarminDB.MonitoringIntensityMins.find_or_create(self.garmin_mon_db, entry)
        elif GarminDB.MonitoringClimb.matches(entry):
            GarminDB.MonitoringClimb.find_or_create(self.garmin_mon_db, entry)
        else:
            GarminDB.Monitoring.find_or_create(self.garmin_mon_db, entry)

    def write_monitoring(self, fit_file, monitoring_messages):
        for message in monitoring_messages:
            entry = message.parsed()
            try:
                self.write_monitoring_entry(entry)
            except ValueError as e:
                logger.info("ValueError on entry: %s" % repr(entry))
            except Exception as e:
                logger.info("Exception on entry: %s" % repr(entry))
                raise

    def write_device_info_entry(self, fit_file, device_info_message):
        parsed_message = device_info_message.parsed()
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
        GarminDB.DeviceInfo.find_or_create(self.garmin_db, device_info)


    def write_device_info(self, fit_file, device_info_messages):
        for message in device_info_messages:
            self.write_device_info_entry(fit_file, message)
