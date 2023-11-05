#!/usr/bin/env python3

"""A script that generated graphs for health data in a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import datetime
import enum

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from garmindb import ConfigManager
from garmindb.garmindb import MonitoringDb, Monitoring, MonitoringHeartRate
from garmindb.summarydb import DaysSummary, WeeksSummary, MonthsSummary, SummaryDb


config = {
    'size'                  : [16.0, 12.0],
    'steps'                 : {'period' : 'weeks', 'days' : 730},
    'hr'                    : {'period' : 'weeks', 'days' : 730},
    'itime'                 : {'period' : 'weeks', 'days' : 730},
    'weight'                : {'period' : 'weeks', 'days' : 730}
}


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


class Graph():
    """A class that generates graphs for GarminDb data sets."""

    __table = {
        'days'      : DaysSummary,
        'weeks'     : WeeksSummary,
        'months'    : MonthsSummary
    }

    def __init__(self, debug=False, save=False):
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
    def __graph_multiple_single_axes(cls, time, data_list, stat_name, ylabel, save, geometry=111):
        title = f'{stat_name} Over Time'
        figure = plt.figure(figsize=config.get('size'))
        for index, data in enumerate(data_list):
            color = Colors.from_integer(index).name
            axes = figure.add_subplot(geometry, frame_on=(index == 0))
            axes.plot(time, data, color=color)
            axes.grid()
        axes.set_title(title)
        axes.set_xlabel('Time')
        axes.set_ylabel(ylabel)
        if save:
            figure.savefig(stat_name + ".png")

    @classmethod
    def __graph_multiple(cls, time, data_list, stat_name, period, ylabel_list, yrange_list, save, geometry=111):
        title = f'{stat_name} by {period}'
        figure = plt.figure(figsize=config.get('size'))
        for index, data in enumerate(data_list):
            color = Colors.from_integer(index).name
            axes = figure.add_subplot(geometry, label=ylabel_list[index], frame_on=(index == 0))
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

    @classmethod
    def __graph_over(cls, date, over_data_dicts, under_data_dict, title, xlabel, ylabel, save_name=None, geometry=111):
        figure = plt.figure(figsize=config.get('size'))
        # First graph the data that appears under
        axes = figure.add_subplot(geometry, frame_on=True)
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
            axes = figure.add_subplot(geometry, frame_on=False, label=label)
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

    def _graph_steps(self, time, data, period, geometry=111):
        steps = self.__remove_discontinuities([entry.steps for entry in data])
        steps_goal_percent = self.__remove_discontinuities([entry.steps_goal_percent for entry in data])
        yrange_list = [(0, max(steps) * 1.1), (0, max(steps_goal_percent) * 2)]
        self.__graph_multiple(time, [steps, steps_goal_percent], 'Steps', period, ['Steps', 'Step Goal Percent'], yrange_list, self.save, geometry)

    def _graph_hr(self, time, data, period, geometry=111):
        rhr = self.__remove_discontinuities([entry.rhr_avg for entry in data])
        inactive_hr = self.__remove_discontinuities([entry.inactive_hr_avg for entry in data])
        self.__graph_multiple(time, [rhr, inactive_hr], 'Heart Rate', period, ['RHR', 'Inactive hr'], [(30, 100), (30, 100)], self.save, geometry)

    def _graph_itime(self, time, data, period, geometry=111):
        itime = [entry.intensity_time_mins for entry in data]
        itime_goal_percent = self.__remove_discontinuities([entry.intensity_time_goal_percent for entry in data])
        itime_goal_max = max([entry.intensity_time_goal_mins for entry in data])
        yrange_list = [(0, itime_goal_max * 5), (0, max(itime_goal_percent) * 1.1)]
        self.__graph_multiple(time, [itime, itime_goal_percent], 'Intensity Minutes', period, ['Intensity Minutes', 'Intensity Minutes Goal Percent'],
                              yrange_list, self.save, geometry)

    def _graph_weight(self, time, data, period, geometry=111):
        weight = [entry.weight_avg for entry in data]
        self.__graph_multiple_single_axes(time, [weight], 'Weight', 'weight', self.save, geometry)

    def graph_activity(self, activity, period=None, days=None, geometry=111):
        """Generate a graph for the given activity with points every period spanning days."""
        if period is None:
            period = config[activity]['period']
        if days is None:
            days = config[activity]['days']
        db_params = ConfigManager.get_db_params()
        sum_db = SummaryDb(db_params, self.debug)
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
        graph_func(time, data, period, geometry)

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

    def graph_date(self, date, geometry=111):
        """Generate a graph for the given date."""
        if date is None:
            date = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        db_params = ConfigManager.get_db_params()
        mon_db = MonitoringDb(db_params, self.debug)
        start_ts = datetime.datetime.combine(date, datetime.datetime.min.time())
        end_ts = datetime.datetime.combine(date, datetime.datetime.max.time())
        hr_data = MonitoringHeartRate.get_for_period(mon_db, start_ts, end_ts, MonitoringHeartRate)
        data = Monitoring.get_for_period(mon_db, start_ts, end_ts, Monitoring)
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
        save_name = f"{date}_daily.png" if self.save else None
        self.__graph_over(date, over_data_dict, under_data_dict, f'Daily Summary for {date}: Heart Rate and Steps over Activity',
                          'Time of Day', 'heart rate', save_name=save_name, geometry=geometry)
