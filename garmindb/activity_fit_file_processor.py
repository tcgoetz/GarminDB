"""Class that takes a parsed activity FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
from datetime import timedelta

import fitfile

from .garmindb import File, ActivitiesDb, Activities, ActivityRecords, ActivityLaps, ActivitySplits, ActivitiesDevices, StepsActivities, \
    CycleActivities, ClimbingActivities, PaddleActivities
from .fit_file_processor import FitFileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class ActivityFitFileProcessor(FitFileProcessor):
    """Class that takes a parsed activity FIT file object and imports it into a database."""

    def write_file(self, fit_file):
        """Given a Fit File object, write all of its messages to the DB."""
        self.activity_fit_file_plugins = [plugin for plugin in self.plugin_manager.get_file_processors('ActivityFit', fit_file).values()]
        if len(self.activity_fit_file_plugins):
            root_logger.info("Loaded %d activity plugins %r for file %s", len(self.activity_fit_file_plugins), self.activity_fit_file_plugins, fit_file)
        # Create the db after setting up the plugins so that plugin tables are handled properly
        self.garmin_act_db = ActivitiesDb(self.db_params, self.debug - 1)
        self._session_num = 0
        # Multi-sport files have >1 session; all child sessions get a suffixed activity_id.
        self._is_multi_sport_file = len(fit_file.session) > 1
        if self._is_multi_sport_file:
            self._build_multi_sport_index(fit_file)
        with self.garmin_db.managed_session() as self.garmin_db_session, self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self._write_message_types(fit_file, fit_file.message_types)

    def _build_multi_sport_index(self, fit_file):
        """Pre-compute per-session activity_ids, lap ranges, and time windows for multi-sport partitioning."""
        base_id = File.id_from_path(fit_file.filename)
        self._session_activity_ids = [f"{base_id}_{i + 1}" for i in range(len(fit_file.session))]
        # Map global lap index -> (activity_id, lap_in_session)
        self._lap_session_map = []
        for session_idx, session in enumerate(fit_file.session):
            nlaps = session.fields.get('num_laps') or 0
            for lap_in_session in range(nlaps):
                self._lap_session_map.append((self._session_activity_ids[session_idx], lap_in_session))
        # Per-session time windows (UTC, end = start + total_elapsed_time) for record partitioning.
        self._session_time_windows = []
        for session in fit_file.session:
            start_utc = session.fields.start_time
            elapsed = session.fields.total_elapsed_time
            end_utc = start_utc + timedelta(
                hours=elapsed.hour, minutes=elapsed.minute,
                seconds=elapsed.second, microseconds=elapsed.microsecond)
            self._session_time_windows.append((start_utc, end_utc))
        self._record_counts_per_session = [0] * len(fit_file.session)

    def _session_for_timestamp(self, timestamp_utc):
        """Return the session index that contains the given UTC timestamp, or None if outside all windows."""
        for idx, (start, end) in enumerate(self._session_time_windows):
            if start <= timestamp_utc <= end:
                return idx
        return None

    def _plugin_dispatch(self, handler_name, *args, **kwargs):
        return super()._plugin_dispatch(self.activity_fit_file_plugins, handler_name, *args, **kwargs)

    def _write_device_info_entry(self, fit_file, message_fields):
        device_serial_number = super()._write_device_info_entry(fit_file, message_fields)
        if device_serial_number:
            if self._is_multi_sport_file:
                activity_ids = self._session_activity_ids
            else:
                activity_ids = [File.id_from_path(fit_file.filename)]
            for activity_id in activity_ids:
                entry = {'activity_id' : activity_id, 'device_serial_number' : device_serial_number}
                if not ActivitiesDevices.s_exists(self.garmin_act_db_session, entry):
                    root_logger.debug("_write_device_info_entry activity_id %s, device serial number %s doesn't exist", activity_id, device_serial_number)
                    self.garmin_act_db_session.add(ActivitiesDevices(**entry))

    def _write_lap(self, fit_file, message_type, messages):
        """Write all lap messages to the database, partitioned by session for multi-sport files."""
        if self._is_multi_sport_file:
            for global_lap_num, message in enumerate(messages):
                if global_lap_num >= len(self._lap_session_map):
                    # Stray lap beyond session num_laps — skip to avoid collisions.
                    root_logger.warning("Skipping lap %d beyond session num_laps sum for %s", global_lap_num, fit_file.filename)
                    continue
                activity_id, lap_in_session = self._lap_session_map[global_lap_num]
                self._write_lap_entry(fit_file, message.fields, lap_in_session, override_activity_id=activity_id)
        else:
            for lap_num, message in enumerate(messages):
                self._write_lap_entry(fit_file, message.fields, lap_num)

    def _write_split(self, fit_file, message_type, messages):
        """Write all split messages to the database."""
        for split_num, message in enumerate(messages):
            self._write_split_entry(fit_file, message.fields, split_num)

    def _write_record(self, fit_file, message_type, messages):
        """Write all record messages to the database, partitioned by session for multi-sport files."""
        if self._is_multi_sport_file:
            for message in messages:
                session_idx = self._session_for_timestamp(message.fields.timestamp)
                if session_idx is None:
                    continue
                activity_id = self._session_activity_ids[session_idx]
                record_num = self._record_counts_per_session[session_idx]
                self._record_counts_per_session[session_idx] += 1
                self._write_record_entry(fit_file, message.fields, record_num, override_activity_id=activity_id)
        else:
            for record_num, message in enumerate(messages):
                self._write_record_entry(fit_file, message.fields, record_num)

    def _write_record_entry(self, fit_file, message_fields, record_num, override_activity_id=None):
        # We don't get record data from multiple sources so we don't need to coellesce data in the DB.
        # It's fastest to just write the new data out if it doesn't currently exist.
        activity_id = override_activity_id or File.id_from_path(fit_file.filename)
        plugin_record = self._plugin_dispatch('write_record_entry', self.garmin_act_db_session, fit_file, activity_id, message_fields, record_num)
        if not ActivityRecords.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'record' : record_num}):
            record = {
                'activity_id'                       : activity_id,
                'record'                            : record_num,
                'timestamp'                         : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'position_lat'                      : message_fields.get('position_lat'),
                'position_long'                     : message_fields.get('position_long'),
                'distance'                          : message_fields.get('distance'),
                'cadence'                           : message_fields.get('cadence'),
                'hr'                                : message_fields.get('heart_rate'),
                'rr'                                : message_fields.get('respiration_rate'),
                'altitude'                          : message_fields.get('altitude'),
                'speed'                             : message_fields.get('speed'),
                'temperature'                       : message_fields.get('temperature'),
            }
            record.update(plugin_record)
            root_logger.debug("_write_record_entry activity_id %s, record %s doesn't exist", activity_id, record_num)
            self.garmin_act_db_session.add(ActivityRecords(**record))

    def _write_lap_entry(self, fit_file, message_fields, lap_num, override_activity_id=None):
        # Use insert_or_update so we coalesce with rows created by hr_zones_timer processed earlier.
        activity_id = override_activity_id or File.id_from_path(fit_file.filename)
        plugin_lap = self._plugin_dispatch('write_lap_entry', self.garmin_act_db_session, fit_file, activity_id, message_fields, lap_num)
        # For multi-sport children Garmin sets lap `timestamp` to the parent's start_time, so compute
        # the real lap end from start_time + total_elapsed_time (same workaround as sessions).
        start_time_utc = message_fields.start_time
        if self._is_multi_sport_file:
            elapsed = message_fields.get('total_elapsed_time')
            stop_time_utc = start_time_utc + timedelta(
                hours=elapsed.hour, minutes=elapsed.minute,
                seconds=elapsed.second, microseconds=elapsed.microsecond) if elapsed else message_fields.timestamp
        else:
            stop_time_utc = message_fields.timestamp
        lap = {
            'activity_id'                       : activity_id,
            'lap'                               : lap_num,
            'start_time'                        : fit_file.utc_datetime_to_local(start_time_utc),
            'stop_time'                         : fit_file.utc_datetime_to_local(stop_time_utc),
            'elapsed_time'                      : message_fields.get('total_elapsed_time'),
            'moving_time'                       : message_fields.get('total_timer_time'),
            'start_lat'                         : message_fields.get('start_position_lat'),
            'start_long'                        : message_fields.get('start_position_long'),
            'stop_lat'                          : message_fields.get('end_position_lat'),
            'stop_long'                         : message_fields.get('end_position_long'),
            'distance'                          : message_fields.get('total_distance'),
            'cycles'                            : message_fields.get('total_cycles'),
            'avg_hr'                            : message_fields.get('avg_heart_rate'),
            'max_hr'                            : message_fields.get('max_heart_rate'),
            'avg_rr'                            : message_fields.get('avg_respiration_rate'),
            'max_rr'                            : message_fields.get('max_respiration_rate'),
            'calories'                          : message_fields.get('total_calories'),
            'avg_cadence'                       : message_fields.get('avg_cadence'),
            'max_cadence'                       : message_fields.get('max_cadence'),
            'avg_speed'                         : message_fields.get('avg_speed'),
            'max_speed'                         : message_fields.get('max_speed'),
            'ascent'                            : message_fields.get('total_ascent'),
            'descent'                           : message_fields.get('total_descent'),
            'max_temperature'                   : message_fields.get('max_temperature'),
            'avg_temperature'                   : message_fields.get('avg_temperature'),
        }
        lap.update(plugin_lap)
        root_logger.debug("writing lap %r for %s", lap, fit_file.filename)
        ActivityLaps.s_insert_or_update(self.garmin_act_db_session, lap, ignore_none=True, ignore_zero=True)

    def _write_split_entry(self, fit_file, message_fields, split_num):
        # we don't get splits data from multiple sources so we don't need to coellesce data in the DB.
        # It's fastest to just write new data out if the it doesn't currently exist.
        activity_id = File.id_from_path(fit_file.filename)
        plugin_split = self._plugin_dispatch('write_split_entry', self.garmin_act_db_session, fit_file, activity_id, message_fields, split_num)

        if not ActivitySplits.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'split' : split_num}):
            split = {
                'activity_id'                       : File.id_from_path(fit_file.filename),
                'split'                             : split_num,
                'start_time'                        : fit_file.utc_datetime_to_local(message_fields.start_time),
                'stop_time'                         : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'elapsed_time'                      : message_fields.get('total_elapsed_time'),
                'moving_time'                       : message_fields.get('total_timer_time'),
                'avg_hr'                            : message_fields.get('avg_heart_rate'),
                'max_hr'                            : message_fields.get('max_heart_rate'),
                'calories'                          : message_fields.get('total_calories'),
                'ascent'                            : message_fields.get('total_ascent'),
                'descent'                           : message_fields.get('total_descent'),
                'avg_speed'                         : message_fields.get('avg_vertical_speed'),
            }
            bouldering_font_grade = {
                0: '1',
                1: '2',
                2: '3',
                3: '4',
                4: '4+',
                5: '5',
                6: '5+',
                7: '6A',
                8: '6A+',
                9: '6B',
                10: '6B+',
                11: '6C',
                12: '6C+',
                13: '7A',
                14: '7A+',
                15: '7B',
                16: '7B+',
                17: '7C',
                18: '7C+',
                19: '8A',
                20: '8A+',
                21: '8B',
                22: '8B+',
                23: '8C',
                24: '8C+',
                25: '9A',
            }
            indoor_font_grade = {
                0: '1',
                1: '2',
                2: '3',
                3: '4a',
                4: '4b',
                5: '4c',
                6: '5a',
                7: '5b',
                8: '5c',
                9: '6a',
                10: '6a+',
                11: '6b',
                12: '6b+',
                13: '6c',
                14: '6c+',
                15: '7a',
                16: '7a+',
                17: '7b',
                18: '7b+',
                19: '7c',
                20: '7c+',
                21: '8a',
                22: '8a+',
                23: '8b',
                24: '8b+',
                25: '8c',
                26: '8c+',
                27: '9a',
                28: '9a+',
                29: '9b',
            }

            route = {
                'activity_id'   : activity_id,
                'grade'         : message_fields.get('grade'),
                'completed'     : message_fields.get('completed'),
                'falls'         : message_fields.get('falls'),
            }

            if 'grade' in route and route.get('grade') is not None:
                if fitfile.SubSport.bouldering == fit_file.sub_sport_type:
                    route['grade'] = bouldering_font_grade[int(route['grade'])]
                elif fitfile.SubSport.indoor_climbing == fit_file.sub_sport_type:
                    route['grade'] = indoor_font_grade[int(route['grade'])]

            split.update(plugin_split)
            split.update(route)

            # there are some empty splits we want to filter out
            if route.get('grade') is not None and route.get('completed') is not None:
                root_logger.debug("writing split %r for %s", split, fit_file.filename)
                self.garmin_act_db_session.add(ActivitySplits(**split))

    def _write_steps_entry(self, fit_file, activity_id, sub_sport, message_fields):
        steps = {
            'activity_id'                       : activity_id,
            'steps'                             : message_fields.get('total_steps'),
            'avg_pace'                          : fitfile.conversions.perhour_speed_to_pace(message_fields.avg_speed),
            'max_pace'                          : fitfile.conversions.perhour_speed_to_pace(message_fields.max_speed),
            'avg_steps_per_min'                 : message_fields.get('avg_steps_per_min'),
            'max_steps_per_min'                 : message_fields.get('max_steps_per_min'),
            'avg_step_length'                   : message_fields.get('avg_step_length'),
            'avg_vertical_ratio'                : message_fields.get('avg_vertical_ratio'),
            'avg_vertical_oscillation'          : message_fields.get('avg_vertical_oscillation'),
            'avg_gct_balance'                   : message_fields.get('avg_stance_time_balance'),
            'avg_ground_contact_time'           : message_fields.get('avg_stance_time'),
            'avg_stance_time_percent'           : message_fields.get('avg_stance_time_percent'),
        }
        steps.update(self._plugin_dispatch('write_steps_entry', self.garmin_act_db_session, fit_file, activity_id, sub_sport, message_fields))
        root_logger.debug("_write_steps_entry: %r", steps)
        StepsActivities.s_insert_or_update(self.garmin_act_db_session, steps, ignore_none=True, ignore_zero=True)

    def _write_running_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_walking_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_hiking_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_cycling_entry(self, fit_file, activity_id, sub_sport, message_fields):
        ride = {
            'activity_id'   : activity_id,
            'strokes'       : message_fields.get('total_strokes'),
        }
        ride.update(self._plugin_dispatch('write_cycle_entry', self.garmin_act_db_session, fit_file, activity_id, sub_sport, message_fields))
        CycleActivities.s_insert_or_update(self.garmin_act_db_session, ride, ignore_none=True, ignore_zero=True)

    def _write_rock_climbing_entry(self, fit_file, activity_id, sub_sport, message_fields):
        entry = {
            'activity_id'   : activity_id,
            'total_routes': len([s for s in fit_file.split if s.fields.get('grade')]),
        }
        entry.update(self._plugin_dispatch('write_rock_climbing_entry', self.garmin_act_db_session, fit_file, activity_id, sub_sport, message_fields))
        ClimbingActivities.s_insert_or_update(self.garmin_act_db_session, entry, ignore_none=True, ignore_zero=True)

    def _write_stand_up_paddleboarding_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("sup sport entry: %r", message_fields)
        paddle = {
            'activity_id'           : activity_id,
            'strokes'               : message_fields.get('total_strokes'),
            'avg_stroke_distance'   : message_fields.get('avg_stroke_distance'),
        }
        paddle.update(self._plugin_dispatch('write_paddle_entry', self.garmin_act_db_session, fit_file, activity_id, sub_sport, message_fields))
        PaddleActivities.s_insert_or_update(self.garmin_act_db_session, paddle, ignore_none=True, ignore_zero=True)

    def _write_rowing_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("row sport entry: %r", message_fields)
        return self._write_stand_up_paddleboarding_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_boating_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("boating sport entry: %r", message_fields)

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
        sport = fitfile.Sport.strict_from_string(current_sport)
        sub_sport = fitfile.SubSport.strict_from_string(current_sub_sport)
        if new_sport is not None and (sport is None or (not sport.preferred() and new_sport.preferred())):
            sport = new_sport
        if new_sub_sport is not None and (sub_sport is None or (not sub_sport.preferred() and new_sub_sport.preferred())):
            sub_sport = new_sub_sport
        return {'sport' : fitfile.field_enums.name_for_enum(sport), 'sub_sport' : fitfile.field_enums.name_for_enum(sub_sport)}

    def _write_session_entry(self, fit_file, message_fields):
        self._session_num += 1
        base_activity_id = File.id_from_path(fit_file.filename)
        sport = message_fields.sport
        sub_sport = message_fields.sub_sport
        is_multi_sport = self._is_multi_sport_file
        if is_multi_sport:
            activity_id = f"{base_activity_id}_{self._session_num}"
        else:
            activity_id = base_activity_id
        # For multi-sport children Garmin sets `timestamp` to the parent's start_time, so compute
        # the real session end from start_time + total_elapsed_time.
        start_time_utc = message_fields.start_time
        if is_multi_sport:
            elapsed = message_fields.total_elapsed_time
            stop_time_utc = start_time_utc + timedelta(
                hours=elapsed.hour, minutes=elapsed.minute,
                seconds=elapsed.second, microseconds=elapsed.microsecond)
        else:
            stop_time_utc = message_fields.timestamp
        activity = {
            'activity_id'                       : activity_id,
            'start_time'                        : fit_file.utc_datetime_to_local(start_time_utc),
            'stop_time'                         : fit_file.utc_datetime_to_local(stop_time_utc),
            'elapsed_time'                      : message_fields.total_elapsed_time,
            'moving_time'                       : message_fields.get('total_timer_time'),
            'start_lat'                         : message_fields.get('start_position_lat'),
            'start_long'                        : message_fields.get('start_position_long'),
            'stop_lat'                          : message_fields.get('end_position_lat'),
            'stop_long'                         : message_fields.get('end_position_long'),
            'distance'                          : message_fields.get('total_distance'),
            'cycles'                            : message_fields.get('total_cycles'),
            'laps'                              : message_fields.get('num_laps'),
            'avg_hr'                            : message_fields.get('avg_heart_rate'),
            'max_hr'                            : message_fields.get('max_heart_rate'),
            'avg_rr'                            : message_fields.get('avg_respiration_rate'),
            'max_rr'                            : message_fields.get('max_respiration_rate'),
            'calories'                          : message_fields.get('total_calories'),
            'avg_cadence'                       : message_fields.get('avg_cadence'),
            'max_cadence'                       : message_fields.get('max_cadence'),
            'avg_speed'                         : message_fields.get('avg_speed'),
            'max_speed'                         : message_fields.get('max_speed'),
            'ascent'                            : message_fields.get('total_ascent'),
            'descent'                           : message_fields.get('total_descent'),
            'max_temperature'                   : message_fields.get('max_temperature'),
            'avg_temperature'                   : message_fields.get('avg_temperature'),
            'training_effect'                   : message_fields.get('total_training_effect'),
            'anaerobic_training_effect'         : message_fields.get('total_anaerobic_training_effect')
        }
        activity.update(self._plugin_dispatch('write_session_entry', self.garmin_act_db_session, fit_file, activity_id, message_fields))
        if is_multi_sport:
            # Multi-sport child session: create a new activity entry with the correct sport
            activity.update({'sport': sport.name if sport else 'unknown', 'sub_sport': sub_sport.name if sub_sport else 'unknown'})
            current = Activities.s_get(self.garmin_act_db_session, activity_id)
            if current:
                current.update_from_dict(activity, ignore_none=True, ignore_zero=True)
            else:
                self.garmin_act_db_session.add(Activities(**activity))
        else:
            # Single-session file: original behavior, coalesce with JSON-imported data
            current = Activities.s_get(self.garmin_act_db_session, activity_id)
            if current:
                activity.update(self.__choose_sport(current.sport, current.sub_sport, sport, sub_sport))
                root_logger.debug("Updating with %r", activity)
                current.update_from_dict(activity, ignore_none=True, ignore_zero=True)
            else:
                activity.update({'sport': sport.name, 'sub_sport': sub_sport.name})
                root_logger.debug("Adding %r", activity)
                self.garmin_act_db_session.add(Activities(**activity))
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

    def _write_hr_zones_timer_entry(self, fit_file, message_fields):
        """Write hz zones message to the database."""
        root_logger.info("writing hr zone data for %s", fit_file.filename)
        hr_zones_type = message_fields.get('hr_zones_timer_type')
        if hr_zones_type is fitfile.field_enums.HeartRateZonesTimerType.lap:
            self._write_hr_zones_timer_lap_entry(fit_file, message_fields)
        elif hr_zones_type is fitfile.field_enums.HeartRateZonesTimerType.session:
            self._write_hr_zones_timer_session_entry(fit_file, message_fields)

    def __hr_zone_data(self, message_fields):
        hr_zones_time = message_fields.get('hr_zones_time')
        zone_data = {
            'hr_zones_method'   : message_fields.get('hr_zones_method'),
            'hrz_1_time'        : hr_zones_time[1],
            'hrz_2_time'        : hr_zones_time[2],
            'hrz_3_time'        : hr_zones_time[3],
            'hrz_4_time'        : hr_zones_time[4],
            'hrz_5_time'        : hr_zones_time[5]
        }
        hr_zones = message_fields.get('hr_zones')
        if hr_zones:
            zone_data.update({
                'hrz_1_hr'      : hr_zones[0],
                'hrz_2_hr'      : hr_zones[1],
                'hrz_3_hr'      : hr_zones[2],
                'hrz_4_hr'      : hr_zones[3],
                'hrz_5_hr'      : hr_zones[4],
            })
        return zone_data

    def _write_hr_zones_timer_lap_entry(self, fit_file, message_fields):
        """Write lap hz zones message to the database."""
        root_logger.info("writing lap hr zone data %r for %s", message_fields, fit_file.filename)
        activity_id = File.id_from_path(fit_file.filename)
        global_lap = message_fields.get('record_num')
        if self._is_multi_sport_file and global_lap is not None and global_lap < len(self._lap_session_map):
            activity_id, lap_num = self._lap_session_map[global_lap]
        else:
            lap_num = global_lap
        lap = {
            'activity_id'   : activity_id,
            'lap'           : lap_num,
        }
        lap.update(self.__hr_zone_data(message_fields))
        root_logger.info("writing lap hr zone data %r for %s", lap, fit_file.filename)
        ActivityLaps.s_insert_or_update(self.garmin_act_db_session, lap, ignore_none=True, ignore_zero=True)

    def _write_hr_zones_timer_session_entry(self, fit_file, message_fields):
        """Write session hz zones message to the database."""
        root_logger.info("writing session hr zone data %r for %s", message_fields, fit_file.filename)
        activity_id = File.id_from_path(fit_file.filename)
        if self._is_multi_sport_file:
            # record_num is the 0-indexed session number, matching the suffix used in _write_session_entry.
            activity_id = f"{activity_id}_{message_fields.get('record_num') + 1}"
        session = {
            'activity_id'   : activity_id,
        }
        session.update(self.__hr_zone_data(message_fields))
        root_logger.debug("writing session hr zone data %r for %s", session, fit_file.filename)
        Activities.s_insert_or_update(self.garmin_act_db_session, session, ignore_none=True, ignore_zero=True)
