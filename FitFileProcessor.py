#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, sys, datetime

import Fit
import GarminDB


logger = logging.getLogger(__file__)


class FitFileProcessor():

    def __init__(self, db_params_dict, english_units, debug):
        self.db_params_dict = db_params_dict
        self.english_units = english_units
        self.debug = debug

        self.garmin_db = GarminDB.GarminDB(db_params_dict, debug - 1)
        self.garmin_mon_db = GarminDB.MonitoringDB(self.db_params_dict, self.debug - 1)
        self.garmin_act_db = GarminDB.ActivitiesDB(self.db_params_dict, self.debug - 1)

        if english_units:
            GarminDB.Attributes.set_newer(self.garmin_db, 'dist_setting', 'statute')
        else:
            GarminDB.Attributes.set_newer(self.garmin_db, 'dist_setting', 'metric')
        logger.info("Debug: %s English units: %s" % (str(debug), str(english_units)))

    def write_generic(self, fit_file, message_type, messages):
        for message in messages:
            try:
                function = getattr(self, 'write_' + message_type + '_entry')
                function(fit_file, message)
            except AttributeError:
                logger.debug("No entry handler for message type %s (%d) from %s: %s" % (message_type, len(messages), fit_file.filename, str(messages[0])))

    def write_message_type(self, fit_file, message_type):
        messages = fit_file[message_type]
        function = getattr(self, 'write_' + message_type, self.write_generic)
        function(fit_file, message_type, messages)
        logger.debug("Processed %d %s entries for %s" % (len(messages), message_type, fit_file.filename))

    def write_message_types(self, fit_file, message_types):
        logger.info("%s (%s) [%s] message types: %s" % (fit_file.filename, fit_file.time_created(), fit_file.type(), message_types))
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
        self.lap = 1
        self.record = 1
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
        logger.debug("sport message: " + repr(sport_message.to_dict()))

    def write_sensor_entry(self, fit_file, sensor_message):
        logger.debug("sensor message: " + repr(sensor_message.to_dict()))

    def write_source_entry(self, fit_file, source_message):
        logger.debug("source message: " + repr(source_message.to_dict()))

    def get_field_value(self, message_dict, field_name):
        return message_dict.get('dev_' + field_name, message_dict.get(field_name, None))

    def write_running_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("run entry: " + repr(message_dict))
        run = {
            'activity_id'                       : activity_id,
            'steps'                             : self.get_field_value(message_dict, 'total_steps'),
            'avg_pace'                          : (datetime.datetime.min +  datetime.timedelta(0, 3600 / message_dict['avg_speed'])).time(),
            'max_pace'                          : (datetime.datetime.min +  datetime.timedelta(0, 3600 / message_dict['max_speed'])).time(),
            'avg_steps_per_min'                 : self.get_field_value(message_dict, 'avg_cadence') * 2,
            'max_steps_per_min'                 : self.get_field_value(message_dict, 'max_cadence') * 2,
            'avg_step_length'                   : self.get_field_value(message_dict, 'avg_step_length'),
            'avg_vertical_ratio'                : self.get_field_value(message_dict, 'avg_vertical_ratio'),
            'avg_vertical_oscillation'          : self.get_field_value(message_dict, 'avg_vertical_oscillation'),
            'avg_gct_balance'                   : self.get_field_value(message_dict, 'avg_stance_time_balance'),
            'avg_ground_contact_time'           : self.get_field_value(message_dict, 'avg_stance_time'),
            'avg_stance_time_percent'           : self.get_field_value(message_dict, 'avg_stance_time_percent'),
        }
        GarminDB.RunActivities.create_or_update_not_none(self.garmin_act_db, run)

    def write_walking_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("walk entry: " + repr(message_dict))
        walk = {
            'activity_id'                       : activity_id,
            'steps'                             : self.get_field_value(message_dict, 'total_steps'),
            'avg_pace'                          : (datetime.datetime.min +  datetime.timedelta(0, 3600 / message_dict['avg_speed'])).time(),
            'max_pace'                          : (datetime.datetime.min +  datetime.timedelta(0, 3600 / message_dict['max_speed'])).time(),
        }
        GarminDB.WalkActivities.create_or_update_not_none(self.garmin_act_db, walk)

    def write_hiking_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("hike entry: " + repr(message_dict))
        return self.write_walking_entry(fit_file, activity_id, sub_sport, message_dict)

    def write_cycling_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("ride entry: " + repr(message_dict))
        ride = {
            'activity_id'                        : activity_id,
            'strokes'                            : self.get_field_value(message_dict, 'total_strokes'),
        }
        GarminDB.CycleActivities.create_or_update_not_none(self.garmin_act_db, ride)

    def write_stand_up_paddleboarding_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("sup entry: " + repr(message_dict))
        paddle = {
            'activity_id'                       : activity_id,
            'strokes'                           : self.get_field_value(message_dict, 'total_strokes'),
            'avg_stroke_distance'               : self.get_field_value(message_dict, 'avg_stroke_distance'),
        }
        GarminDB.PaddleActivities.create_or_update_not_none(self.garmin_act_db, paddle)

    def write_rowing_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("row entry: " + repr(message_dict))
        return self.write_stand_up_paddleboarding_entry(fit_file, activity_id, sub_sport, message_dict)

    def write_elliptical_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("elliptical entry: " + repr(message_dict))
        workout = {
            'activity_id'                       : activity_id,
            'steps'                             : message_dict.get('dev_Steps', message_dict.get('total_steps', None)),
            'elliptical_distance'               : message_dict.get('dev_User_distance', message_dict.get('dev_distance', message_dict.get('distance', None))),
        }
        GarminDB.EllipticalActivities.create_or_update_not_none(self.garmin_act_db, workout)

    def write_fitness_equipment_entry(self, fit_file, activity_id, sub_sport, message_dict):
        try:
            function = getattr(self, 'write_' + sub_sport + '_entry')
            function(fit_file, activity_id, sub_sport, message_dict)
        except AttributeError:
            logger.info("No sub sport handler type %s from %s: %s" % (sub_sport, fit_file.filename, str(message_dict)))

    def write_alpine_skiing_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("Skiing entry: " + repr(message_dict))

    def write_training_entry(self, fit_file, activity_id, sub_sport, message_dict):
        logger.debug("Training entry: " + repr(message_dict))

    def write_session_entry(self, fit_file, message):
        logger.debug("session message: " + repr(message.to_dict()))
        message_dict = message.to_dict()
        activity_id = GarminDB.File.get(self.garmin_db, fit_file.filename)
        sport = message_dict['sport']
        sub_sport = message_dict['sub_sport']
        activity = {
            'activity_id'                       : activity_id,
            'start_time'                        : message_dict['start_time'],
            'stop_time'                         : message_dict['timestamp'],
            'elapsed_time'                      : message_dict['total_elapsed_time'],
            'moving_time'                       : message_dict.get('total_timer_time', None),
            'start_lat'                         : message_dict.get('start_position_lat', None),
            'start_long'                        : message_dict.get('start_position_long', None),
            'stop_lat'                          : message_dict.get('end_position_lat', None),
            'stop_long'                         : message_dict.get('end_position_long', None),
            'distance'                          : message_dict.get('dev_User_distance', message_dict.get('total_distance', None)),
            'sport'                             : sport,
            'sub_sport'                         : sub_sport,
            'cycles'                            : self.get_field_value(message_dict, 'total_cycles'),
            'laps'                              : self.get_field_value(message_dict, 'num_laps'),
            'avg_hr'                            : self.get_field_value(message_dict, 'avg_heart_rate'),
            'max_hr'                            : self.get_field_value(message_dict, 'max_heart_rate'),
            'calories'                          : self.get_field_value(message_dict, 'total_calories'),
            'avg_cadence'                       : self.get_field_value(message_dict, 'avg_cadence'),
            'max_cadence'                       : self.get_field_value(message_dict, 'max_cadence'),
            'avg_speed'                         : message_dict['avg_speed'],
            'max_speed'                         : message_dict['max_speed'],
            'ascent'                            : message_dict['total_ascent'],
            'descent'                           : message_dict['total_descent'],
            'max_temperature'                   : message_dict.get('max_temperature', None),
            'avg_temperature'                   : message_dict.get('avg_temperature', None),
            'training_effect'                   : message_dict.get('total_training_effect', None),
            'anaerobic_training_effect'         : message_dict.get('total_anaerobic_training_effect', None)
        }
        GarminDB.Activities.create_or_update_not_none(self.garmin_act_db, activity)
        try:
            function = getattr(self, 'write_' + sport + '_entry')
            function(fit_file, activity_id, sub_sport, message_dict)
        except AttributeError:
            logger.info("No sport handler for type %s from %s: %s" % (sport, fit_file.filename, str(message_dict)))

    def write_device_settings_entry(self, fit_file, device_settings_message):
        logger.debug("device settings message: " + repr(device_settings_message.to_dict()))

    def write_lap_entry(self, fit_file, lap_message):
        message_dict = lap_message.to_dict()
        logger.debug("lap message: " + repr(message_dict))
        activity_id = GarminDB.File.get(self.garmin_db, fit_file.filename)
        lap = {
            'activity_id'                       : activity_id,
            'lap'                               : self.lap,
            'start_time'                        : message_dict['start_time'],
            'stop_time'                         : message_dict['timestamp'],
            'elapsed_time'                      : message_dict['total_elapsed_time'],
            'moving_time'                       : message_dict.get('total_timer_time', None),
            'start_lat'                         : message_dict.get('start_position_lat', None),
            'start_long'                        : message_dict.get('start_position_long', None),
            'stop_lat'                          : message_dict.get('end_position_lat', None),
            'stop_long'                         : message_dict.get('end_position_long', None),
            'distance'                          : message_dict.get('dev_User_distance', message_dict.get('total_distance', None)),
            'cycles'                            : self.get_field_value(message_dict, 'total_cycles'),
            'avg_hr'                            : self.get_field_value(message_dict, 'avg_heart_rate'),
            'max_hr'                            : self.get_field_value(message_dict, 'max_heart_rate'),
            'calories'                          : self.get_field_value(message_dict, 'total_calories'),
            'avg_cadence'                       : self.get_field_value(message_dict, 'avg_cadence'),
            'max_cadence'                       : self.get_field_value(message_dict, 'max_cadence'),
            'avg_speed'                         : message_dict['avg_speed'],
            'max_speed'                         : message_dict['max_speed'],
            'ascent'                            : message_dict['total_ascent'],
            'descent'                           : message_dict['total_descent'],
            'max_temperature'                   : message_dict.get('max_temperature', None),
            'avg_temperature'                   : message_dict.get('avg_temperature', None),
        }
        GarminDB.ActivityLaps.create_or_update_not_none(self.garmin_act_db, lap)
        self.lap += 1

    def write_battery_entry(self, fit_file, battery_message):
        logger.debug("battery message: " + repr(battery_message.to_dict()))

    def write_attribute(self, timestamp, parsed_message, attribute_name):
        attribute = parsed_message.get(attribute_name, None)
        if attribute is not None:
            GarminDB.Attributes.set_newer(self.garmin_db, attribute_name, attribute, timestamp)

    def write_user_profile_entry(self, fit_file, message):
        logger.debug("user profile message: " + repr(message.to_dict()))
        parsed_message = message.to_dict()
        timestamp = fit_file.time_created()
        for attribute_name in [
                'Gender', 'height', 'Weight', 'Language', 'dist_setting', 'weight_setting', 'position_setting', 'elev_setting', 'sleep_time', 'wake_time'
            ]:
            self.write_attribute(timestamp, parsed_message, attribute_name)

    def write_activity_entry(self, fit_file, activity_message):
        logger.debug("activity message: " + repr(activity_message.to_dict()))

    def write_zones_target_entry(self, fit_file, zones_target_message):
        logger.debug("zones target message: " + repr(zones_target_message.to_dict()))

    def write_record_entry(self, fit_file, record_message):
        message_dict = record_message.to_dict()
        logger.debug("record message: " + repr(message_dict))
        activity_id = GarminDB.File.get(self.garmin_db, fit_file.filename)
        record = {
            'activity_id'                       : activity_id,
            'record'                            : self.record,
            'timestamp'                         : message_dict['timestamp'],
            'position_lat'                      : message_dict.get('position_lat', None),
            'position_long'                     : message_dict.get('position_long', None),
            'distance'                          : message_dict.get('distance', None),
            'cadence'                           : self.get_field_value(message_dict, 'cadence'),
            'hr'                                : self.get_field_value(message_dict, 'heart_rate'),
            'alititude'                         : message_dict.get('altitude', None),
            'speed'                             : message_dict.get('speed', None),
            'temperature'                       : message_dict.get('temperature', None),
        }
        GarminDB.ActivityRecords.create_or_update_not_none(self.garmin_act_db, record)
        self.record += 1

    def write_dev_data_id_entry(self, fit_file, dev_data_id_message):
        logger.debug("dev_data_id message: " + repr(dev_data_id_message.to_dict()))

    def write_field_description_entry(self, fit_file, field_description_message):
        logger.debug("field_description message: " + repr(field_description_message.to_dict()))

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
                GarminDB.MonitoringHeartRate.create_or_update_not_none(self.garmin_mon_db, entry)
            elif GarminDB.MonitoringIntensity.matches(entry):
                GarminDB.MonitoringIntensity.create_or_update_not_none(self.garmin_mon_db, entry)
            elif GarminDB.MonitoringClimb.matches(entry):
                GarminDB.MonitoringClimb.create_or_update_not_none(self.garmin_mon_db, entry)
            else:
                GarminDB.Monitoring.create_or_update_not_none(self.garmin_mon_db, entry)
        except ValueError as e:
            logger.info("ValueError: %s" % str(e))
        except Exception as e:
            logger.info("Exception on monitoring entry: %s: %s" % (repr(entry), str(e)))

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
                GarminDB.Device.create_or_update_not_none(self.garmin_db, device)
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
                GarminDB.DeviceInfo.create_or_update_not_none(self.garmin_db, device_info)
            except Exception as e:
                logger.warning("Device info message not written: " + repr(parsed_message))
