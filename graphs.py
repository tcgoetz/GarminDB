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
import version.version as version


logging.basicConfig(filename='graphs.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class YAxisLabelPostion(enum.Enum):
    right   = 0
    left    = 1

    @classmethod
    def from_integer(cls, integer):
        """Create an instance of a YAxisLabelPostion enum from an integer."""
        return YAxisLabelPostion(integer % 2)


class Colors(enum.Enum):
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


def __graph_mulitple_single_axes(time, data_list, stat_name, ylabel, save):
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


def __graph_mulitple(time, data_list, stat_name, period, ylabel_list, save):
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


def graph_steps(time, data, period, save):
    steps = [entry.steps for entry in data]
    steps_goal_percent = [entry.steps_goal_percent for entry in data]
    __graph_mulitple(time, [steps, steps_goal_percent], 'Steps', period, ['Steps', 'Step Goal Percent'], save)


def graph_hr(time, data, period, save):
    rhr = [entry.rhr_avg for entry in data]
    inactive_hr = [entry.inactive_hr_avg for entry in data]
    __graph_mulitple(time, [rhr, inactive_hr], 'Heart Rate', period, ['RHR', 'Inactive hr'], save)


def graph_itime(time, data, period, save):
    itime = [entry.intensity_time_mins for entry in data]
    itime_goal_percent = [entry.intensity_time_goal_percent for entry in data]
    __graph_mulitple(time, [itime, itime_goal_percent], 'Intensity Minutes', period, ['Intensity Minutes', 'Intensity Minutes Goal Percent'], save)


def graph_weight(time, data, period, save):
    weight = [entry.weight_avg for entry in data]
    __graph_mulitple_single_axes(time, [weight], 'Weight', 'weight', save)


def __print_usage(program, error=None):
    if error is not None:
        print error
        print
    print '%s [--all | --rhr | --weight] [--latest <x days>]' % program
    print '    --all        : Graph data for all enabled stats.'
    print '    --hr        : Graph resting heart rate data.'
    print '    --itime      : Graph intensity time data.'
    print '    --weight     : Graph weight data.'
    print '    --steps      : Graph steps data.'
    print '    --latest     : Graph x most recent days.'
    print '    --period     : days, weeks, or months.'
    print '    --trace      : Turn on debug tracing. Extra logging will be written to log file.'
    print '    '
    sys.exit()


def __print_version(program):
    print '%s' % version


def main(argv):
    debug = 0
    save = False
    hr = False
    itime = False
    steps = False
    weight = False
    days = 31
    end_ts = datetime.datetime.now()
    start_ts = end_ts - datetime.timedelta(days=days)
    period = 'days'
    table = {
        'days'      : HealthDB.DaysSummary,
        'weeks'     : HealthDB.WeeksSummary,
        'months'    : HealthDB.MonthsSummary
    }

    try:
        opts, args = getopt.getopt(argv, "adhHl:p:rsSt:wv", ["all", "latest=", "period=", "hr", "itime", "save", "steps", "trace=", "weight", "version"])
    except getopt.GetoptError as e:
        __print_usage(sys.argv[0], str(e))

    for opt, arg in opts:
        if opt == '-h':
            __print_usage(sys.argv[0])
        elif opt in ("-v", "--version"):
            __print_version(sys.argv[0])
        elif opt in ("-a", "--all"):
            logger.info("All: " + arg)
            hr = GarminDBConfigManager.is_stat_enabled('rhr')
        elif opt in ("-l", "--latest"):
            days = int(arg)
            end_ts = datetime.datetime.now()
            start_ts = end_ts - datetime.timedelta(days=days)
        elif opt in ("-p", "--period"):
            logging.info("Period: %s", arg)
            period = arg
        elif opt in ("-S", "--save"):
            save = True
        elif opt in ("-s", "--steps"):
            steps = True
        elif opt in ("-H", "--hr"):
            logging.debug("HR")
            hr = True
        elif opt in ("-i", "--itime"):
            logging.debug("Intenist time")
            itime = True
        elif opt in ("-w", "--weight"):
            logging.info("Weight")
            weight = True
        elif opt in ("-t", "--trace"):
            debug = int(arg)

    if debug > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    db_params_dict = GarminDBConfigManager.get_db_params()
    sum_db = HealthDB.SummaryDB(db_params_dict, debug)
    data = table[period].get_for_period(sum_db, table[period], start_ts, end_ts)
    if period == 'days':
        time = [entry.day for entry in data]
    else:
        time = [entry.first_day for entry in data]

    if hr:
        graph_hr(time, data, period, save)

    if itime:
        graph_itime(time, data, period, save)

    if steps:
        graph_steps(time, data, period, save)

    if weight:
        graph_weight(time, data, period, save)


if __name__ == "__main__":
    main(sys.argv[1:])
