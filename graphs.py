#!/usr/bin/env python3

"""A script that generated graphs for health data in a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import getopt
import datetime
import matplotlib.pyplot as plt
import enum

import HealthDB
import garmin_db_config_manager as GarminDBConfigManager
from version import print_version


logging.basicConfig(filename='graphs.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class YAxisLabelPostion(enum.Enum):
    """An enum of the label postions for the Y axis."""

    right   = 0
    left    = 1

    @classmethod
    def from_integer(cls, integer):
        """Create an instance of a YAxisLabelPostion enum from an integer."""
        return YAxisLabelPostion(integer % 2)


class Colors(enum.Enum):
    """An enum of the colors used for generating graphs."""

    b   = 0
    g   = 1
    r   = 2
    c   = 3
    m   = 4
    y   = 5
    k   = 6
    w   = 7

    @classmethod
    def from_integer(cls, integer):
        """Create an instance of a Color enum from an integer."""
        return Colors(integer % 8)


class Graph(object):
    """A class that generates graphs for GarminDB data sets."""

    __table = {
        'days'      : HealthDB.DaysSummary,
        'weeks'     : HealthDB.WeeksSummary,
        'months'    : HealthDB.MonthsSummary
    }

    def __init__(self, debug, save):
        """Return an instance of the Graph class."""
        self.debug = debug
        self.save = save

    @classmethod
    def __graph_mulitple_single_axes(cls, time, data_list, stat_name, ylabel, save):
        title = '%s Over Time' % stat_name
        figure = plt.figure()
        for index, data in enumerate(data_list):
            color = Colors.from_integer(index).name
            axes = figure.add_subplot(111, frame_on=(index == 0))
            axes.plot(time, data, color=color)
            axes.grid()
        axes.set_title(title)
        axes.set_xlabel('Time')
        axes.set_ylabel(ylabel)
        if save:
            figure.savefig(stat_name + ".png")
        plt.show()

    @classmethod
    def __graph_mulitple(cls, time, data_list, stat_name, period, ylabel_list, save):
        units = {
            'days'      : 'Day',
            'weeks'     : 'Week',
            'months'    : 'Month'
        }
        title = '%s per %s' % (stat_name, units[period])
        figure = plt.figure()
        for index, data in enumerate(data_list):
            color = Colors.from_integer(index).name
            axes = figure.add_subplot(111, label=ylabel_list[index], frame_on=(index == 0))
            axes.plot(time, data, color=color)
            axes.set_ylabel(ylabel_list[index], color=color)
            axes.yaxis.set_label_position(YAxisLabelPostion.from_integer(index).name)
            if (index % 2) == 0:
                axes.yaxis.tick_right()
            else:
                axes.yaxis.tick_left()
            axes.tick_params(axis='y', colors=color)
            axes.set_ylim([min(data), max(data)])
            axes.grid()
        axes.set_title(title)
        axes.set_xlabel('Time')
        if save:
            figure.savefig(stat_name + ".png")
        plt.show()

    def _graph_steps(self, time, data, period):
        steps = [entry.steps for entry in data]
        steps_goal_percent = [entry.steps_goal_percent for entry in data]
        self.__graph_mulitple(time, [steps, steps_goal_percent], 'Steps', period, ['Steps', 'Step Goal Percent'], self.save)

    def _graph_hr(self, time, data, period):
        rhr = [entry.rhr_avg for entry in data]
        inactive_hr = [entry.inactive_hr_avg for entry in data]
        self.__graph_mulitple(time, [rhr, inactive_hr], 'Heart Rate', period, ['RHR', 'Inactive hr'], self.save)

    def _graph_itime(self, time, data, period):
        itime = [entry.intensity_time_mins for entry in data]
        itime_goal_percent = [entry.intensity_time_goal_percent for entry in data]
        self.__graph_mulitple(time, [itime, itime_goal_percent], 'Intensity Minutes', period, ['Intensity Minutes', 'Intensity Minutes Goal Percent'], self.save)

    def _graph_weight(self, time, data, period):
        weight = [entry.weight_avg for entry in data]
        self.__graph_mulitple_single_axes(time, [weight], 'Weight', 'weight', self.save)

    def graph_activity(self, activity, period, days):
        """Generate a graph for the given activity with points every period spanning days."""
        if period is None or period == 'default':
            period = GarminDBConfigManager.graphs_activity_config(activity, 'period')
        if days is None or days == 'default':
            days = GarminDBConfigManager.graphs_activity_config(activity, 'days')
        db_params_dict = GarminDBConfigManager.get_db_params()
        sum_db = HealthDB.SummaryDB(db_params_dict, self.debug)
        end_ts = datetime.datetime.now()
        start_ts = end_ts - datetime.timedelta(days=days)
        table = self.__table[period]
        data = table.get_for_period(sum_db, start_ts, end_ts, table)
        if period == 'days':
            time = [entry.day for entry in data]
        else:
            time = [entry.first_day for entry in data]
        graph_func_name = '_graph_' + activity
        graph_func = getattr(self, graph_func_name, None)
        graph_func(time, data, period)


def __print_usage(program, error=None):
    if error is not None:
        print(error)
        print
    print('%s [--all | --rhr | --weight] [--latest <x days>]' % program)
    print('    --all        : Graph data for all enabled stats.')
    print('    --hr        : Graph resting heart rate data.')
    print('    --itime      : Graph intensity time data.')
    print('    --weight     : Graph weight data.')
    print('    --steps      : Graph steps data.')
    print('    --latest     : Graph x most recent days.')
    print('    --period     : days, weeks, or months.')
    print('    --trace      : Turn on debug tracing. Extra logging will be written to log file.')
    print('    ')
    sys.exit()


def main(argv):
    """Generate graphs based on commandline options."""
    debug = 0
    save = False
    hr = False
    hr_period = None
    itime = False
    itime_period = None
    steps = False
    steps_period = None
    weight = False
    weight_period = None
    days = None

    try:
        opts, args = getopt.getopt(argv, "adhHl:p:rsSt:wv", ["all", "latest=", "hr=", "itime", "save", "steps=", "trace=", "weight=", "version"])
    except getopt.GetoptError as e:
        __print_usage(sys.argv[0], str(e))

    for opt, arg in opts:
        if opt == '-h':
            __print_usage(sys.argv[0])
        elif opt in ("-v", "--version"):
            print_version(sys.argv[0])
        elif opt in ("-a", "--all"):
            logger.info("All: " + arg)
            hr = GarminDBConfigManager.is_stat_enabled('rhr')
            steps = GarminDBConfigManager.is_stat_enabled('steps')
            itime = GarminDBConfigManager.is_stat_enabled('itime')
            weight = GarminDBConfigManager.is_stat_enabled('weight')
        elif opt in ("-l", "--latest"):
            days = int(arg)
        elif opt in ("-S", "--save"):
            save = True
        elif opt in ("-s", "--steps"):
            logging.debug("Steps: %s", arg)
            steps = True
            steps_period = arg
        elif opt in ("-H", "--hr"):
            logging.debug("HR: %s", arg)
            hr = True
            hr_period = arg
        elif opt in ("-i", "--itime"):
            logging.debug("Intenist time: %s", arg)
            itime = True
            itime_period = arg
        elif opt in ("-w", "--weight"):
            logging.info("Weight: %s", arg)
            weight = True
            weight_period = arg
        elif opt in ("-t", "--trace"):
            debug = int(arg)

    if debug > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    graph = Graph(debug, save)

    if hr:
        graph.graph_activity('hr', hr_period, days)

    if itime:
        graph.graph_activity('itime', itime_period, days)

    if steps:
        graph.graph_activity('steps', steps_period, days)

    if weight:
        graph.graph_activity('weight', weight_period, days)


if __name__ == "__main__":
    main(sys.argv[1:])
