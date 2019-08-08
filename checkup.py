"""Class running a checkup against the DB data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import logging
import getopt
from datetime import datetime, timedelta

import GarminDB
import garmin_db_config_manager as GarminDBConfigManager
from version import version

logging.basicConfig(filename='graphs.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class CheckUp(object):
    """Class running a checkup against the DB data."""

    def __init__(self, debug):
        """Return an instance of the CheckUp class."""
        self.db_params_dict = GarminDBConfigManager.get_db_params()
        self.debug = debug

    def goals(self):
        """Do a checkup of th euser's goals."""
        garmin_db = GarminDB.GarminDB(self.db_params_dict, self.debug)
        look_back_days = GarminDBConfigManager.checkup('look_back_days')
        end_ts = datetime.now()
        start_ts = end_ts - timedelta(days=look_back_days)
        results = GarminDB.DailySummary.get_for_period(garmin_db, start_ts, end_ts)
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
        logger.info('Steps: on goal %d of %d days', step_goal_days, look_back_days)
        logger.info('Floors: on goal %d of %d days', floors_goal_days, look_back_days)
        logger.info('Intensity mins: on goal %d of %d weeks', intensity_goal_weeks, intensity_weeks)

    def __activity_string(self, activity_db, activity):
        if activity.is_steps_activity():
            steps_activity = GarminDB.StepsActivities.get(activity_db, activity.activity_id)
            return ('%s: "%s" %s in %s (%s [%s])' %
                    (activity.start_time, activity.name, activity.distance, activity.elapsed_time, steps_activity.avg_pace, activity.avg_speed))
        return '%s: "%s" %s in %s (%s)' % (activity.start_time, activity.name, activity.distance, activity.elapsed_time, activity.avg_speed)

    def activity_course(self, course_id):
        """Run a checkup on all activities matcing the course_id."""
        activity_db = GarminDB.ActivitiesDB(self.db_params_dict, self.debug)
        activities = GarminDB.Activities.get_by_course_id(activity_db, course_id)
        activities_count = len(activities)
        fastest_activity = GarminDB.Activities.get_fastest_by_course_id(activity_db, course_id)
        slowest_activity = GarminDB.Activities.get_slowest_by_course_id(activity_db, course_id)
        logger.info('Matching Activities: %d', activities_count)
        logger.info('  first: %s', self.__activity_string(activity_db, activities[0]))
        logger.info('  lastest: %s', self.__activity_string(activity_db, activities[-1]))
        logger.info('  fastest: %s', self.__activity_string(activity_db, fastest_activity))
        logger.info('  slowest: %s', self.__activity_string(activity_db, slowest_activity))


def __print_usage(program, error=None):
    if error is not None:
        print error
        print
    print '%s [--goals]' % program
    print '    --goals        : run a checkup on the user\'s goals.'
    sys.exit()


def __print_version(program):
    print '%s' % version


def main(argv):
    """Run a data checkup of the user's choice."""
    debug = 0
    goals = False
    course = None

    try:
        opts, args = getopt.getopt(argv, "c:gt:v", ["goals", 'course=', "trace=", "version"])
    except getopt.GetoptError as e:
        __print_usage(sys.argv[0], str(e))

    for opt, arg in opts:
        if opt == '-h':
            __print_usage(sys.argv[0])
        elif opt in ("-v", "--version"):
            __print_version(sys.argv[0])
        elif opt in ("-g", "--goals"):
            logging.debug("Goals: %s", arg)
            goals = True
        elif opt in ("-c", "--course"):
            logging.debug("Course: %s", arg)
            course = arg
        elif opt in ("-t", "--trace"):
            debug = int(arg)

    checkup = CheckUp(debug)
    if goals:
        checkup.goals()
    if course:
        checkup.activity_course(course)


if __name__ == "__main__":
    main(sys.argv[1:])
