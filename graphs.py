#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, sys, getopt, datetime
import matplotlib
import matplotlib.pyplot as plt
#import numpy

from version import version
import HealthDB
import GarminDBConfigManager


logging.basicConfig(filename='graphs.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def graph_mulitple_single_axes(time, data_list, state_name, ylabel, save):
    figure = plt.figure()
    for index, data in enumerate(data_list):
        axes.plot(time, data)
    title = '%s Over Time' % state_name
    axes.set(xlabel='Time', ylabel=ylabel, title=title)
    axes.grid()
    if save:
        figure.savefig(state_name + ".png")
    plt.show()

def graph_mulitple(time, data_list, state_name, ylabel_list, save):
    title = '%s Over Time' % state_name
    figure = plt.figure()
    for index, data in enumerate(data_list):
        axes = figure.add_subplot(111, label=ylabel_list[index])
        axes.plot(time, data)
        axes.set_xlabel('Time', color="C1")
        axes.set_ylabel(ylabel_list[index], color="C1")
        axes.set_ylim([min(data), max(data)])
        axes.grid()
    axes.set_title(title, color="C1")
    if save:
        figure.savefig(state_name + ".png")
    plt.show()

def calc_steps_goal_percent(entry):
    if entry.steps is not None and entry.steps_goal is not None:
      return (entry.steps_goal * 100.0) / entry.steps

def graph_steps(data, save):
    time = [entry.day for entry in data]
    steps = [entry.steps for entry in data]
    steps_goal_percent = [calc_steps_goal_percent(entry) for entry in data]
    graph_mulitple(time, [steps, steps_goal_percent], 'Steps', 'Steps', save)

def graph_hr(data, save):
    time = [entry.day for entry in data]
    rhr = [entry.rhr_avg for entry in data]
    inactive_hr = [entry.inactive_hr_avg for entry in data]
    graph_mulitple_single_axes(time, [rhr, inactive_hr], 'Heart Rate', 'rhr, inactive hr (bpm)', save)

def graph_weight(data, save):
    time = [entry.day for entry in data]
    weight = [entry.weight_avg for entry in data]
    graph_mulitple_single_axes(time, [weight], 'Weight', 'weight', save)

def print_usage(program, error=None):
    if error is not None:
        print error
        print
    print '%s [--all | --rhr | --weight] [--latest <x days>]' % program
    print '    --all        : Graph data for all enabled stats.'
    print '    --rhr        : Graph resting heart rate data.'
    print '    --weight     : Download and/or import weight data.'
    print '    --latest     : Graph x most recent days.'
    print '    --period     : days, weeks, or months.'
    print '    --trace      : Turn on debug tracing. Extra logging will be written to log file.'
    print '    '
    sys.exit()

def print_version(program):
    print '%s' % version

def main(argv):
    debug = 0
    test = False
    save = False
    hr = False
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
        opts, args = getopt.getopt(argv,"adhHl:p:rsSt:wv", ["all", "latest=", "period=", "hr", "save", "steps", "trace=", "weight", "version"])
    except getopt.GetoptError as e:
        print_usage(sys.argv[0], str(e))

    for opt, arg in opts:
        if opt == '-h':
            print_usage(sys.argv[0])
        elif opt in ("-v", "--version"):
            print_version(sys.argv[0])
        elif opt in ("-a", "--all"):
            logger.info("All: " + arg)
            rhr = GarminDBConfigManager.is_stat_enabled('rhr')
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
    data = table[period].get_for_period(sum_db, HealthDB.DaysSummary, start_ts, end_ts)

    if hr:
        graph_hr(data, save)

    if steps:
        graph_steps(data, save)

    if weight:
        graph_weight(data, save)



if __name__ == "__main__":
    main(sys.argv[1:])
