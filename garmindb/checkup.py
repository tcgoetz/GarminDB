#!/usr/bin/env python3

"""Class running a checkup against the DB data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import logging
from datetime import datetime, time, timedelta

import fitfile

from garmindb.garmindb import GarminDb, Attributes, Device, DeviceInfo, DailySummary, ActivitiesDb, Activities, StepsActivities
from garmindb import GarminConnectConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class Checkup():
    """Class running a checkup against the DB data."""

    def __init__(self, paragraph_func=logger.info, heading_func=logger.info, debug=False):
        """Return an instance of the CheckUp class."""
        self.gc_config = GarminConnectConfigManager()
        self.db_params = self.gc_config.get_db_params()
        self.paragraph_func = paragraph_func
        self.heading_func = heading_func
        self.debug = debug
        self.garmin_db = GarminDb(self.db_params)
        self.measurement_system = Attributes.measurements_type(self.garmin_db)
        self.unit_strings = fitfile.units.unit_strings[self.measurement_system]

    def goals(self):
        """Do a checkup of the user's goals."""
        look_back_days = self.gc_config.get_node_value_default('checkup', 'look_back_days', 90)
        end_ts = datetime.now()
        start_ts = end_ts - timedelta(days=look_back_days)
        results = DailySummary.get_for_period(self.garmin_db, start_ts, end_ts)
        step_goal_days = 0
        step_goal_days_in_week = 0
        floors_goal_days = 0
        floor_goal_days_in_week = 0
        days_in_week = 0
        intensity_time = time.min
        intensity_time_goal = time.min
        intensity_weeks = 0
        intensity_goal_weeks = 0
        for result in results:
            if result.day.weekday() == 0:
                days_in_week = 0
                step_goal_days_in_week = 0
                floor_goal_days_in_week = 0
                intensity_time = time.min
                intensity_time_goal = time.min
            days_in_week += 1
            if result.steps_goal_percent >= 100:
                step_goal_days += 1
                step_goal_days_in_week += 1
            else:
                self.paragraph_func(f'Steps: goal not met on {result.day}')
            if result.floors_goal_percent >= 100:
                floors_goal_days += 1
                floor_goal_days_in_week += 1
            else:
                self.paragraph_func(f'Floors: goal not met on {result.day}')
            intensity_time = fitfile.conversions.add_time(intensity_time, result.intensity_time)
            intensity_time_goal = fitfile.conversions.add_time(intensity_time_goal, result.intensity_time_goal)
            if result.day.weekday() == 6:
                if days_in_week == 7:
                    intensity_weeks += 1
                    if step_goal_days_in_week < days_in_week:
                        self.paragraph_func(f'Steps: goal not met {days_in_week - step_goal_days_in_week} days for week ending in {result.day}')
                    if floor_goal_days_in_week < days_in_week:
                        self.paragraph_func(f'Floors: goal not met {days_in_week - floor_goal_days_in_week} days for week ending in {result.day}')
                    if intensity_time >= intensity_time_goal:
                        intensity_goal_weeks += 1
                    else:
                        self.paragraph_func(f'Intensity mins: goal not met for week ending in {result.day}')
        self.heading_func('Summary:')
        self.paragraph_func(f'Steps: met goal {step_goal_days} of last {look_back_days} days')
        self.paragraph_func(f'Floors: met goal {floors_goal_days} of last {look_back_days} days')
        self.paragraph_func(f'Intensity mins: met goal {intensity_goal_weeks} of last {intensity_weeks} weeks')

    def __activity_string(self, activity_db, activity):
        if activity.is_steps_activity():
            steps_activity = StepsActivities.get(activity_db, activity.activity_id)
            return ('%s: "%s" %.2f %s in %s pace: %s %s speed: %.2f %s' %
                    (activity.start_time, activity.name, activity.distance, self.unit_strings[fitfile.units.UnitTypes.distance_long], activity.elapsed_time,
                     steps_activity.avg_pace, self.unit_strings[fitfile.units.UnitTypes.pace], activity.avg_speed,
                     self.unit_strings[fitfile.units.UnitTypes.speed]))
        return '%s: "%s" %s in %s (%s)' % (activity.start_time, activity.name, activity.distance, activity.elapsed_time, activity.avg_speed)

    def activity_course(self, course_id):
        """Run a checkup on all activities matching the course_id."""
        activity_db = ActivitiesDb(self.db_params, self.debug)
        activities = Activities.get_by_course_id(activity_db, course_id)
        activities_count = len(activities)
        fastest_activity = Activities.get_fastest_by_course_id(activity_db, course_id)
        slowest_activity = Activities.get_slowest_by_course_id(activity_db, course_id)
        self.paragraph_func(f'Matching Activities: {activities_count}')
        self.paragraph_func(f'  first: {self.__activity_string(activity_db, activities[0])}')
        self.paragraph_func(f'  lastest: {self.__activity_string(activity_db, activities[-1])}')
        self.paragraph_func(f'  fastest: {self.__activity_string(activity_db, fastest_activity)}')
        self.paragraph_func(f'  slowest: {self.__activity_string(activity_db, slowest_activity)}')

    def battery_status(self):
        """Check for devices with low battery status."""
        devices = Device.get_all(self.garmin_db)
        for device in devices:
            battery_level = DeviceInfo.get_col_latest_where(self.garmin_db, DeviceInfo.battery_status,
                                                            [DeviceInfo.serial_number == device.serial_number,
                                                             DeviceInfo.battery_status != fitfile.field_enums.BatteryStatus.invalid])
            if battery_level is fitfile.field_enums.BatteryStatus.low:
                self.paragraph_func(f"Device {device.manufacturer} {device.product} ({device.serial_number}) has a low battery")
