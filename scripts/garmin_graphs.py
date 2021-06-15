#!/usr/bin/env python3

"""A script that generated graphs for health data in a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import argparse

import matplotlib.pyplot as plt
import dateutil.parser

from garmindb import Graph, GarminConnectConfigManager, Statistics, format_version


logging.basicConfig(filename='graphs.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()

gc_config = GarminConnectConfigManager()


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
        plt.show()

    if Statistics.itime in args.stats:
        graph.graph_activity('itime', args.period, args.days)
        plt.show()

    if Statistics.steps in args.stats:
        graph.graph_activity('steps', args.period, args.days)
        plt.show()

    if Statistics.weight in args.stats:
        graph.graph_activity('weight', args.period, args.days)
        plt.show()

    if args.day:
        graph.graph_date(args.day)
        plt.show()


if __name__ == "__main__":
    main(sys.argv[1:])
