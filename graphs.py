#!/usr/bin/env python3

"""A script that generated graphs for health data in a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import argparse
import datetime
import enum

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import dateutil.parser

import HealthDB
import GarminDB
from garmin_db_config_manager import GarminDBConfigManager
from version import format_version
from statistics import Statistics
from garmin_connect_config_manager import GarminConnectConfigManager


logging.basicConfig(filename='graphs.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()

gc_config = GarminConnectConfigManager()


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
    def __remove_discontinuities(cls, data):
        last = 0
        for index, entry in enumerate(data):
            if not entry:
                data[index] = last
            else:
                last = data[index]
        return data

    @classmethod
    def __graph_multiple_single_axes(cls, time, data_list, stat_name, ylabel, save):
        title = f'{stat_name} Over Time'
        figure = plt.figure(figsize=GarminDBConfigManager.graphs('size'))
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
    def __graph_multiple(cls, time, data_list, stat_name, period, ylabel_list, yrange_list, save):
        title = f'{stat_name} by {period}'
        figure = plt.figure(figsize=GarminDBConfigManager.graphs('size'))
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
            if yrange_list is None:
                axes.set_ylim([min(data), max(data)])
            else:
                axes.set_ylim(yrange_list[index])
            axes.grid()
        axes.set_title(title)
        axes.set_xlabel('Time')
        if save:
            figure.savefig(stat_name + ".png")
        plt.show()

    @classmethod
    def __graph_over(cls, date, over_data_dicts, under_data_dict, title, xlabel, ylabel, save_name=None):
        figure = plt.figure(figsize=GarminDBConfigManager.graphs('size'))
        # First graph the data that appears under
        axes = figure.add_subplot(111, frame_on=True)
        axes.fill_between(under_data_dict['time'], under_data_dict['data'], 0, color=Colors.c.name)
        axes.set_ylim(under_data_dict['limits'])
        axes.set_xticks([])
        axes.set_yticks([])
        # then graph the data that appears on top
        colors = [Colors.r.name, Colors.b.name]
        for index, _ in enumerate(over_data_dicts):
            over_data_dict = over_data_dicts[index]
            color = colors[index]
            label = over_data_dict['label']
            axes = figure.add_subplot(111, frame_on=False, label=label)
            axes.plot(over_data_dict['time'], over_data_dict['data'], color=color)
            axes.set_ylabel(label, color=color)
            axes.yaxis.set_label_position(YAxisLabelPostion.from_integer(index).name)
            if (index % 2) == 0:
                axes.yaxis.tick_right()
                axes.set_xticks([])
            else:
                axes.yaxis.tick_left()
            limits = over_data_dicts[index].get('limits')
            if limits is not None:
                axes.set_ylim(limits)
            axes.grid()
        axes.set_title(title)
        axes.set_xlabel(xlabel)
        x_format = mdates.DateFormatter('%H:%M')
        axes.xaxis.set_major_formatter(x_format)
        if save_name:
            figure.savefig(save_name)
        plt.show()

    def _graph_steps(self, time, data, period):
        steps = self.__remove_discontinuities([entry.steps for entry in data])
        steps_goal_percent = self.__remove_discontinuities([entry.steps_goal_percent for entry in data])
        yrange_list = [(0, max(steps) * 1.1), (0, max(steps_goal_percent) * 2)]
        self.__graph_multiple(time, [steps, steps_goal_percent], 'Steps', period, ['Steps', 'Step Goal Percent'], yrange_list, self.save)

    def _graph_hr(self, time, data, period):
        rhr = self.__remove_discontinuities([entry.rhr_avg for entry in data])
        inactive_hr = self.__remove_discontinuities([entry.inactive_hr_avg for entry in data])
        self.__graph_multiple(time, [rhr, inactive_hr], 'Heart Rate', period, ['RHR', 'Inactive hr'], [(30, 100), (30, 100)], self.save)

    def _graph_itime(self, time, data, period):
        itime = [entry.intensity_time_mins for entry in data]
        itime_goal_percent = self.__remove_discontinuities([entry.intensity_time_goal_percent for entry in data])
        itime_goal_max = max([entry.intensity_time_goal_mins for entry in data])
        yrange_list = [(0, itime_goal_max * 5), (0, max(itime_goal_percent) * 1.1)]
        self.__graph_multiple(time, [itime, itime_goal_percent], 'Intensity Minutes', period, ['Intensity Minutes', 'Intensity Minutes Goal Percent'],
                              yrange_list, self.save)

    def _graph_weight(self, time, data, period):
        weight = [entry.weight_avg for entry in data]
        self.__graph_multiple_single_axes(time, [weight], 'Weight', 'weight', self.save)

    def graph_activity(self, activity, period, days):
        """Generate a graph for the given activity with points every period spanning days."""
        if period is None:
            period = GarminDBConfigManager.graphs_activity_config(activity, 'period')
        if days is None:
            days = GarminDBConfigManager.graphs_activity_config(activity, 'days')
        db_params = GarminDBConfigManager.get_db_params()
        sum_db = HealthDB.SummaryDB(db_params, self.debug)
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

    def __format_steps(self, data):
        steps = []
        steps_count = {}
        for entry in data:
            if entry.steps is not None:
                if entry.activity_type in steps_count:
                    if entry.steps > steps_count[entry.activity_type]:
                        steps_count[entry.activity_type] = entry.steps
                else:
                    steps_count[entry.activity_type] = entry.steps
            steps.append(sum(steps_count.values()))
        return steps

    def graph_date(self, date):
        """Generate a graph for the given date."""
        if date is None:
            date = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        db_params = GarminDBConfigManager.get_db_params()
        mon_db = GarminDB.MonitoringDB(db_params, self.debug)
        start_ts = datetime.datetime.combine(date, datetime.datetime.min.time())
        end_ts = datetime.datetime.combine(date, datetime.datetime.max.time())
        hr_data = GarminDB.MonitoringHeartRate.get_for_period(mon_db, start_ts, end_ts, GarminDB.MonitoringHeartRate)
        data = GarminDB.Monitoring.get_for_period(mon_db, start_ts, end_ts, GarminDB.Monitoring)
        over_data_dict = [
            {
                'label'     : 'Cumulative Steps',
                'time'      : [entry.timestamp for entry in data],
                'data'      : self.__format_steps(data),
            },
            {
                'label'     : 'Heart Rate',
                'time'      : [entry.timestamp for entry in hr_data],
                'data'      : [entry.heart_rate for entry in hr_data],
                'limits'    : (30, 220)
            }
        ]
        under_data_dict = {
            'time'      : [entry.timestamp for entry in data],
            'data'      : self.__remove_discontinuities([entry.intensity for entry in data]),
            'limits'    : (0, 10)
        }
        # self.__graph_day(date, (hr_time, hr), (mon_time, activity), self.save)
        save_name = f"{date}_daily.png" if self.save else None
        self.__graph_over(date, over_data_dict, under_data_dict, f'Daily Summary for {date}: Heart Rate and Steps over Activity',
                          'Time of Day', 'heart rate', save_name=save_name)


def main(argv):
    """Generate graphs based on commandline options."""
    def date_from_string(date_string):
        return dateutil.parser.parse(date_string).date()

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="print the program's version", action='version', version=format_version(sys.argv[0]))
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    parser.add_argument("-S", "--save", help="Save graphs to images files.", action="store_true", default=False)
    # stat types to operate on
    stats_group = parser.add_argument_group('Statistics', 'Graph statistics over a period of time')
    stats_group.add_argument("-A", "--all", help="Graph data for all enabled statistics.", action='store_const', dest='stats', const=gc_config.enabled_stats(), default=[])
    stats_group.add_argument("-m", "--monitoring", help="Graph monitoring data.", dest='stats', action='append_const', const=Statistics.monitoring)
    stats_group.add_argument("-r", "--hr", help="Graph heart rate data.", dest='stats', action='append_const', const=Statistics.rhr)
    stats_group.add_argument("-s", "--steps", help="Graph steps data.", dest='stats', action='append_const', const=Statistics.steps)
    stats_group.add_argument("-w", "--weight", help="Graph weight data.", dest='stats', action='append_const', const=Statistics.weight)
    stats_group.add_argument("-p", "--period", help="Graph period granularity.", dest='period', type=str, default=None, choices=['days', 'weeks', 'months'])
    daily_group = parser.add_argument_group('Daily')
    daily_group.add_argument("-d", "--day", help="Graph composite data for a single day.", type=date_from_string)
    modifiers_group = parser.add_argument_group('Modifiers')
    modifiers_group.add_argument("-l", "--latest", help="Graph the latest data.", dest='days', type=int, default=None)
    args = parser.parse_args()

    if args.trace > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    graph = Graph(args.trace, args.save)

    if Statistics.rhr in args.stats:
        graph.graph_activity('hr', args.period, args.days)

    if Statistics.itime in args.stats:
        graph.graph_activity('itime', args.period, args.days)

    if Statistics.steps in args.stats:
        graph.graph_activity('steps', args.period, args.days)

    if Statistics.weight in args.stats:
        graph.graph_activity('weight', args.period, args.days)

    if args.day:
        graph.graph_date(args.day)


if __name__ == "__main__":
    main(sys.argv[1:])
