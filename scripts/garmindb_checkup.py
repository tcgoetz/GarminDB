#!/usr/bin/env python3

"""Class running a checkup against the DB data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import logging
import argparse
from datetime import datetime, time, timedelta

import fitfile

from garmindb.garmindb import GarminDb, Attributes, Device, DeviceInfo, DailySummary, ActivitiesDb, Activities, StepsActivities
from garmindb import ConfigManager, format_version


logging.basicConfig(filename='checkup.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class CheckUp(object):
    """Class running a checkup against the DB data."""

    def __init__(self, debug):
        """Return an instance of the CheckUp class."""
        self.db_params = ConfigManager.get_db_params()
        self.debug = debug
        self.garmin_db = GarminDb(self.db_params)
        self.measurement_system = Attributes.measurements_type(self.garmin_db)
        self.unit_strings = fitfile.units.unit_strings[self.measurement_system]

    def goals(self):
        """Do a checkup of th euser's goals."""
        look_back_days = ConfigManager.checkup.get('look_back_days')
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
                logger.debug('Steps: goal not met on %s', result.day)
            if result.floors_goal_percent >= 100:
                floors_goal_days += 1
                floor_goal_days_in_week += 1
            else:
                logger.debug('Floors: goal not met on %s', result.day)
            intensity_time = fitfile.conversions.add_time(intensity_time, result.intensity_time)
            intensity_time_goal = fitfile.conversions.add_time(intensity_time_goal, result.intensity_time_goal)
            if result.day.weekday() == 6:
                if days_in_week == 7:
                    intensity_weeks += 1
                    if step_goal_days_in_week < days_in_week:
                        logger.info('Steps: goal not met %d days for week ending in %s', days_in_week - step_goal_days_in_week, result.day)
                    if floor_goal_days_in_week < days_in_week:
                        logger.info('Floors: goal not met %d days for week ending in %s', days_in_week - floor_goal_days_in_week, result.day)
                    if intensity_time >= intensity_time_goal:
                        intensity_goal_weeks += 1
                    else:
                        logger.info('Intensity mins: goal not met for week ending in %s', result.day)
        logger.info('Summary:')
        logger.info('Steps: met goal %d of last %d days', step_goal_days, look_back_days)
        logger.info('Floors: met goal %d of last %d days', floors_goal_days, look_back_days)
        logger.info('Intensity mins: met goal %d of last %d weeks', intensity_goal_weeks, intensity_weeks)

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
        logger.info('Matching Activities: %d', activities_count)
        logger.info('  first: %s', self.__activity_string(activity_db, activities[0]))
        logger.info('  lastest: %s', self.__activity_string(activity_db, activities[-1]))
        logger.info('  fastest: %s', self.__activity_string(activity_db, fastest_activity))
        logger.info('  slowest: %s', self.__activity_string(activity_db, slowest_activity))

    def battery_status(self):
        """Check for devices with low battery status."""
        devices = Device.get_all(self.garmin_db)
        for device in devices:
            battery_level = DeviceInfo.get_col_latest_where(self.garmin_db, DeviceInfo.battery_status,
                                                            [DeviceInfo.serial_number == device.serial_number, DeviceInfo.battery_status != fitfile.field_enums.BatteryStatus.invalid])
            if battery_level is fitfile.field_enums.BatteryStatus.low:
                logger.info("Device %s %s (%s) has a low battery", device.manufacturer, device.product, device.serial_number)


def main(argv):
    """Run a data checkup of the user's choice."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="print the program's version", action='version', version=format_version(sys.argv[0]))
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    checks_group = parser.add_argument_group('Checks')
    checks_group.add_argument("-b", "--battery", help="Check for low battery levels.", action="store_true", default=False)
    checks_group.add_argument("-c", "--course", help="Show statistics from all workouts for a single course.", type=int, default=None)
    checks_group.add_argument("-g", "--goals", help="Run a checkup on the user\'s goals.", action="store_true", default=False)
    checks_group.add_argument("-a", "--all", help="Run a checkup on all of the the user\'s stats.", action="store_true", default=False)
    args = parser.parse_args()

    checkup = CheckUp(args.trace)
    if args.all or args.battery:
        checkup.battery_status()
    if args.course:
        checkup.activity_course(args.course)
    if args.all or args.goals:
        checkup.goals()


if __name__ == "__main__":
    main(sys.argv[1:])
