#!/usr/bin/env python3

"""Class running a checkup against the DB data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import logging
import argparse
from datetime import datetime, timedelta

import Fit
import GarminDB
import garmin_db_config_manager as GarminDBConfigManager
from version import format_version


logging.basicConfig(filename='graphs.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class CheckUp(object):
    """Class running a checkup against the DB data."""

    def __init__(self, debug):
        """Return an instance of the CheckUp class."""
        self.db_params = GarminDBConfigManager.get_db_params()
        self.debug = debug
        self.garmin_db = GarminDB.GarminDB(self.db_params)
        self.measurement_system = GarminDB.Attributes.measurements_type(self.garmin_db)
        self.unit_strings = Fit.units.unit_strings[self.measurement_system]

    def goals(self):
        """Do a checkup of th euser's goals."""
        look_back_days = GarminDBConfigManager.checkup('look_back_days')
        end_ts = datetime.now()
        start_ts = end_ts - timedelta(days=look_back_days)
        results = GarminDB.DailySummary.get_for_period(self.garmin_db, start_ts, end_ts)
        step_goal_days = 0
        floors_goal_days = 0
        intensity_days = 0
        intensity_weeks = 0
        intensity_time_goal_percent = 0
        intensity_goal_weeks = 0
        for result in results:
            if result.steps_goal_percent >= 100:
                step_goal_days += 1
            if result.floors_goal_percent >= 100:
                floors_goal_days += 1
            if result.day.weekday() == 0:
                intensity_days = 0
            intensity_time_goal_percent += result.intensity_time_goal_percent
            intensity_days += 1
            if result.day.weekday() == 6:
                if intensity_days == 7:
                    intensity_weeks += 1
                    if intensity_time_goal_percent >= 100:
                        intensity_goal_weeks += 1
        logger.info('Steps: met goal %d of last %d days', step_goal_days, look_back_days)
        logger.info('Floors: met goal %d of last %d days', floors_goal_days, look_back_days)
        logger.info('Intensity mins: met goal %d of last %d weeks', intensity_goal_weeks, intensity_weeks)

    def __activity_string(self, activity_db, activity):
        if activity.is_steps_activity():
            steps_activity = GarminDB.StepsActivities.get(activity_db, activity.activity_id)
            return ('%s: "%s" %.2f %s in %s pace: %s %s speed: %.2f %s' %
                    (activity.start_time, activity.name, activity.distance, self.unit_strings[Fit.units.UnitTypes.distance_long], activity.elapsed_time,
                     steps_activity.avg_pace, self.unit_strings[Fit.units.UnitTypes.pace], activity.avg_speed,
                     self.unit_strings[Fit.units.UnitTypes.speed]))
        return '%s: "%s" %s in %s (%s)' % (activity.start_time, activity.name, activity.distance, activity.elapsed_time, activity.avg_speed)

    def activity_course(self, course_id):
        """Run a checkup on all activities matcing the course_id."""
        activity_db = GarminDB.ActivitiesDB(self.db_params, self.debug)
        activities = GarminDB.Activities.get_by_course_id(activity_db, course_id)
        activities_count = len(activities)
        fastest_activity = GarminDB.Activities.get_fastest_by_course_id(activity_db, course_id)
        slowest_activity = GarminDB.Activities.get_slowest_by_course_id(activity_db, course_id)
        logger.info('Matching Activities: %d', activities_count)
        logger.info('  first: %s', self.__activity_string(activity_db, activities[0]))
        logger.info('  lastest: %s', self.__activity_string(activity_db, activities[-1]))
        logger.info('  fastest: %s', self.__activity_string(activity_db, fastest_activity))
        logger.info('  slowest: %s', self.__activity_string(activity_db, slowest_activity))


def main(argv):
    """Run a data checkup of the user's choice."""
    debug = 0
    goals = False
    course = None

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="print the program's version", action='version', version=format_version(sys.argv[0]))
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    parser.add_argument("-g", "--goals", help="Run a checkup on the user\'s goals.", action="store_true", default=False)
    parser.add_argument("-c", "--course", help="Show statistics over all workouts for a single course.", type=int, default=None)
    args = parser.parse_args()

    checkup = CheckUp(debug)
    if args.goals:
        checkup.goals()
    if args.course:
        checkup.activity_course(args.course)


if __name__ == "__main__":
    main(sys.argv[1:])
