"""Objects for analyzing health data from Garmin devices and genrating summary tables."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import logging
import datetime
import calendar
from tqdm import tqdm

import fitfile

from garmindb import summarydb
from .garmindb import GarminDb, Attributes, Weight, Stress, RestingHeartRate, IntensityHR, Sleep
from .garmindb import MonitoringDb, Monitoring, MonitoringHeartRate, MonitoringIntensity, MonitoringClimb
from .garmindb import ActivitiesDb, Activities, StepsActivities
from .garmindb import GarminSummaryDb, DaysSummary, DailySummary, WeeksSummary, MonthsSummary, YearsSummary
from .garmin_connect_config_manager import GarminConnectConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class Analyze(object):
    """Object for analyzing health data from Garmin devices."""

    def __init__(self, db_params, debug):
        """Return an instance of the Analyze class."""
        self.garmin_db = GarminDb(db_params, debug)
        self.garmin_mon_db = MonitoringDb(db_params, debug)
        self.garmin_sum_db = GarminSummaryDb(db_params, debug)
        self.sum_db = summarydb.SummaryDb(db_params, debug)
        self.garmin_act_db = ActivitiesDb(db_params, debug)
        self.measurement_system = Attributes.measurements_type(self.garmin_db)
        self.unit_strings = fitfile.units.unit_strings[self.measurement_system]

    def __populate_hr_intensity(self, day_date, garmin_mon_session, garmin_sum_session, overwrite=False):
        if IntensityHR.s_row_count_for_day(garmin_sum_session, day_date) == 0 or overwrite:
            monitoring_rows = Monitoring._get_for_day(garmin_mon_session, day_date, not_none_col=Monitoring.intensity)
            previous_ts = None
            for monitoring in monitoring_rows:
                # Heart rate value is for one minute, reported at the end of the minute. Only take HR values where the
                # measurement period falls within the activity period.
                if previous_ts is not None and (monitoring.timestamp - previous_ts).total_seconds() > 60:
                    hr_rows = MonitoringHeartRate.s_get_for_period(garmin_mon_session, previous_ts, previous_ts + datetime.timedelta(seconds=60), not_none_col=monitoring.timestamp)
                    for hr in hr_rows:
                        entry = {
                            'timestamp'     : hr.timestamp,
                            'intensity'     : monitoring.intensity,
                            'heart_rate'    : hr.heart_rate
                        }
                        IntensityHR.s_insert_or_update(garmin_sum_session, entry, ignore_none=True)
                previous_ts = monitoring.timestamp

    def __calculate_day_stats(self, day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        stats = DailySummary.get_daily_stats(garmin_session, day_date)
        # prefer getting stats from the daily summary.
        if stats.get('rhr_avg') is None:
            stats.update(RestingHeartRate.get_daily_stats(garmin_session, day_date))
        if stats.get('stress_avg') is None:
            stats.update(Stress.get_daily_stats(garmin_session, day_date))
        if stats.get('intensity_time') is None:
            stats.update(MonitoringIntensity.get_daily_stats(garmin_mon_session, day_date))
        if stats.get('floors') is None:
            stats.update(MonitoringClimb.get_daily_stats(garmin_mon_session, day_date, self.measurement_system))
        if stats.get('steps') is None:
            stats.update(Monitoring.get_daily_stats(garmin_mon_session, day_date))
        stats.update(MonitoringHeartRate.get_daily_stats(garmin_mon_session, day_date))
        stats.update(IntensityHR.get_daily_stats(garmin_sum_session, day_date))
        stats.update(Weight.get_daily_stats(garmin_session, day_date))
        stats.update(Sleep.get_daily_stats(garmin_session, day_date))
        stats.update(Activities.get_daily_stats(garmin_act_session, day_date))
        # save it to the db
        DaysSummary.s_insert_or_update(garmin_sum_session, stats)
        summarydb.DaysSummary.s_insert_or_update(sum_session, stats)

    def __calculate_days(self, year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        days = Monitoring.s_get_days(garmin_mon_session, year)
        for day in tqdm(days, unit='days'):
            day_date = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
            self.__populate_hr_intensity(day_date, garmin_mon_session, garmin_sum_session)
            self.__calculate_day_stats(day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)

    def __calculate_week_stats(self, day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        stats = DailySummary.get_weekly_stats(garmin_session, day_date)
        # prefer getting stats from the daily summary.
        if stats.get('rhr_avg') is None:
            stats.update(RestingHeartRate.get_weekly_stats(garmin_session, day_date))
        if stats.get('stress_avg') is None:
            stats.update(Stress.get_weekly_stats(garmin_session, day_date))
        if stats.get('intensity_time') is None:
            stats.update(MonitoringIntensity.get_weekly_stats(garmin_mon_session, day_date))
        if stats.get('floors') is None:
            stats.update(MonitoringClimb.get_weekly_stats(garmin_mon_session, day_date, self.measurement_system))
        if stats.get('steps') is None:
            stats.update(Monitoring.get_weekly_stats(garmin_mon_session, day_date))
        stats.update(MonitoringHeartRate.get_weekly_stats(garmin_mon_session, day_date))
        stats.update(IntensityHR.get_weekly_stats(garmin_sum_session, day_date))
        stats.update(Weight.get_weekly_stats(garmin_session, day_date))
        stats.update(Sleep.get_weekly_stats(garmin_session, day_date))
        stats.update(Activities.get_weekly_stats(garmin_act_session, day_date))
        # save it to the db
        WeeksSummary.s_insert_or_update(garmin_sum_session, stats)
        summarydb.WeeksSummary.s_insert_or_update(sum_session, stats)

    def __calculate_weeks(self, year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        for week_starting_day in tqdm(range(1, 365, 7), unit='weeks'):
            day_date = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
            if day_date < datetime.datetime.now().date():
                self.__calculate_week_stats(day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)

    def __calculate_month_stats(self, start_day_date, end_day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        stats = DailySummary.get_monthly_stats(garmin_session, start_day_date, end_day_date)
        # prefer getting stats from the daily summary.
        if 'rhr_avg' in stats:
            stats.update(RestingHeartRate.get_monthly_stats(garmin_session, start_day_date, end_day_date))
        if 'stress_avg' in stats:
            stats.update(Stress.get_monthly_stats(garmin_session, start_day_date, end_day_date))
        if 'intensity_time' in stats:
            stats.update(MonitoringIntensity.get_monthly_stats(garmin_mon_session, start_day_date, end_day_date))
        if 'floors' in stats:
            stats.update(MonitoringClimb.get_monthly_stats(garmin_mon_session, start_day_date, end_day_date, self.measurement_system))
        if 'steps' in stats:
            stats.update(Monitoring.get_monthly_stats(garmin_mon_session, start_day_date, end_day_date))
        stats.update(MonitoringHeartRate.get_monthly_stats(garmin_mon_session, start_day_date, end_day_date))
        stats.update(IntensityHR.get_monthly_stats(garmin_sum_session, start_day_date, end_day_date))
        stats.update(Weight.get_monthly_stats(garmin_session, start_day_date, end_day_date))
        stats.update(Sleep.get_monthly_stats(garmin_session, start_day_date, end_day_date))
        stats.update(Activities.get_monthly_stats(garmin_act_session, start_day_date, end_day_date))
        # save it to the db
        MonthsSummary.s_insert_or_update(garmin_sum_session, stats)
        summarydb.MonthsSummary.s_insert_or_update(sum_session, stats)

    def __calculate_months(self, year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        months = Monitoring.s_get_months(garmin_mon_session, year)
        for month in tqdm(months, unit='months'):
            start_day_date = datetime.date(year, month, 1)
            end_day_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
            self.__calculate_month_stats(start_day_date, end_day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)

    def __calculate_year_stats(self, year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        stats = DailySummary.get_yearly_stats(garmin_session, year)
        # prefer getting stats from the daily summary.
        if 'rhr_avg' in stats:
            stats.update(RestingHeartRate.get_yearly_stats(garmin_session, year))
        if 'stress_avg' in stats:
            stats.update(Stress.get_yearly_stats(garmin_session, year))
        if 'intensity_time' in stats:
            stats.update(MonitoringIntensity.get_yearly_stats(garmin_mon_session, year))
        if 'floors' in stats:
            stats.update(MonitoringClimb.get_yearly_stats(garmin_mon_session, year, self.measurement_system))
        if 'steps' in stats:
            stats.update(Monitoring.get_yearly_stats(garmin_mon_session, year))
        stats.update(MonitoringHeartRate.get_yearly_stats(garmin_mon_session, year))
        stats.update(IntensityHR.get_yearly_stats(garmin_sum_session, year))
        stats.update(Weight.get_yearly_stats(garmin_session, year))
        stats.update(Sleep.get_yearly_stats(garmin_session, year))
        stats.update(Activities.get_yearly_stats(garmin_act_session, year))
        # save it to the db
        YearsSummary.s_insert_or_update(garmin_sum_session, stats)
        summarydb.YearsSummary.s_insert_or_update(sum_session, stats)

    def __calculate_year(self, year):
        with self.garmin_db.managed_session() as garmin_session, self.garmin_mon_db.managed_session() as garmin_mon_session, \
                self.garmin_act_db.managed_session() as garmin_act_session, self.garmin_sum_db.managed_session() as garmin_sum_session, \
                self.sum_db.managed_session() as sum_session:
            # calculate part of the years
            self.__calculate_days(year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)
            self.__calculate_weeks(year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)
            self.__calculate_months(year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)
            # now calculate the year itself
            self.__calculate_year_stats(year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)

    def summary(self):
        """Summarize Garmin health data. Daily, weekly, and monthly, tables will be generated."""
        logger.info("Summary Tables Generation:")
        years = Monitoring.get_years(self.garmin_mon_db)
        for year in years:
            logger.info("Generating table entries for %s", year)
            self.__calculate_year(year)

    def create_dynamic_views(self):
        """Create database views specific to the data in this database."""
        gc_config = GarminConnectConfigManager()
        course_ids = gc_config.course_views('steps')
        if course_ids:
            for course_id in course_ids:
                StepsActivities.create_course_view(self.garmin_act_db, course_id)
