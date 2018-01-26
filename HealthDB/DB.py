#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, logging, datetime, time

from sqlalchemy import *
from sqlalchemy.ext.declarative import *
from sqlalchemy.exc import *
from sqlalchemy.orm import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

def day_of_the_year_to_datetime(year, day):
    return datetime.datetime(year, 1, 1) + datetime.timedelta(day - 1)


class DB():
    max_commit_attempts = 15
    commit_errors = 0
    max_query_attempts = max_commit_attempts
    query_errors = 0
    file_suffix = '.db'

    def __init__(self, filename, debug=False):
        url = "sqlite:///" + filename
        logger.debug("DB %s debug %s " % (url, str(debug)))
        self.engine = create_engine(url, echo=debug)
        self.session_maker = sessionmaker(bind=self.engine)
        self._query_session = None

    def session(self):
        return self.session_maker()

    def query_session(self):
        if self._query_session is None:
            self._query_session = self.session()
        return self._query_session

    @classmethod
    def commit(cls, session):
        attempts = 0
        while attempts < DB.max_commit_attempts:
            try:
                session.commit()
                session.close()
                return
            except OperationalError as e:
                attempts += 1
                logger.error("Exeption '%s' on commit %s attempt %d" % (str(e), str(session), attempts))
                session.rollback()
                cls.commit_errors += 1
                time.sleep(attempts)
                continue
            break
        raise IOError("Failed to commit")

    @classmethod
    def query_one_or_none(cls, query):
        attempts = 0
        while attempts < DB.max_query_attempts:
            try:
                return query.one_or_none()
            except OperationalError as e:
                attempts += 1
                logger.error("Exeption '%s' on query %s attempt %d" % (str(e), str(query), attempts))
                cls.query_errors += 1
                time.sleep(attempts)
                continue
            break
        raise IOError("Failed to query")

    @classmethod
    def query_all(cls, query):
        attempts = 0
        while attempts < DB.max_query_attempts:
            try:
                return query.all()
            except OperationalError as e:
                attempts += 1
                logger.error("Exeption '%s' on query %s attempt %d" % (str(e), str(query), attempts))
                cls.query_errors += 1
                time.sleep(attempts)
                continue
            break
        raise IOError("Failed to query")

    @classmethod
    def query_scalar(cls, query):
        attempts = 0
        while attempts < DB.max_query_attempts:
            try:
                return query.scalar()
            except OperationalError as e:
                attempts += 1
                logger.error("Exeption '%s' on query %s attempt %d" % (str(e), str(query), attempts))
                cls.query_errors += 1
                time.sleep(attempts)
                continue
            break
        raise IOError("Failed to query")


class DBObject():

    # defaults, overridden by subclasses
    _updateable_fields = []
    _relational_mappings = {}
    col_translations = {}

    @classmethod
    def filename_from_pathname(cls, pathname):
        return os.path.basename(pathname)

    @classmethod
    def __filter_columns(cls, values_dict):
        return { key : value for key, value in values_dict.iteritems() if key in cls.__dict__}

    @classmethod
    def _filter_columns(cls, values_dict):
        filtered_cols = cls.__filter_columns(values_dict)
        if len(filtered_cols) != len(values_dict):
            logger.debug("filtered some cols for %s from %s" % (cls.__tablename__, repr(values_dict)))
        if len(filtered_cols) == 0:
            raise ValueError("%s: filtered all cols for %s from %s" % (cls.__name__, cls.__tablename__, repr(values_dict)))
        return filtered_cols

    @classmethod
    def matches(cls, values_dict):
        filtered_cols = cls.__filter_columns(values_dict)
        return len(filtered_cols) >= cls.min_row_values

    @classmethod
    def relational_mappings(cls, db, values_dict):
        if len(cls._relational_mappings) == 0:
            return values_dict
        return {
            (cls._relational_mappings[key][0] if key in cls._relational_mappings else key) :
            (cls._relational_mappings[key][1](db, value) if key in cls._relational_mappings else value)
            for key, value in values_dict.iteritems()
        }

    @classmethod
    def _translate_columns(cls, values_dict):
        if len(cls.col_translations) == 0:
            return values_dict
        return {
            key :
            (cls.col_translations[key](value) if key in cls.col_translations else value)
            for key, value in values_dict.iteritems()
        }

    @classmethod
    def _translate_column(cls, col_name, col_value):
        if len(cls.col_translations) == 0:
            return col_value
        return (cls.col_translations[col_name](col_value) if col_name in cls.col_translations else col_value)

    @classmethod
    def find_query(cls, session, values_dict):
        logger.debug("%s::_find %s" % (cls.__name__, repr(values_dict)))
        return cls._find_query(session, cls._translate_columns(values_dict))

    @classmethod
    def find_all(cls, db, values_dict):
        logger.debug("%s::find_all %s" % (cls.__name__, repr(values_dict)))
        return DB.query_all(cls.find_query(db.query_session(), values_dict))

    @classmethod
    def _find_one(cls, session, values_dict):
        logger.debug("%s::_find_one %s" % (cls.__name__, repr(values_dict)))
        return DB.query_one_or_none(cls.find_query(session, values_dict))

    @classmethod
    def find_one(cls, db, values_dict):
        logger.debug("%s::find_one %s" % (cls.__name__, repr(values_dict)))
        return DB.query_one_or_none(cls.find_query(db.query_session(), values_dict))

    @classmethod
    def update_statement(cls, session, values_dict):
        logger.debug("%s::_update %s" % (cls.__name__, repr(values_dict)))
        return cls.find_query(session, values_dict).update(values_dict)

    @classmethod
    def update_one(cls, db, values_dict):
        logger.debug("%s::update_one %s" % (cls.__name__, repr(values_dict)))
        session = db.session()
        cls.update_statement(session, values_dict)
        return DB.commit(session)

    @classmethod
    def find_id(cls, db, values_dict):
        logger.debug("%s::find_id %s" % (cls.__name__, repr(values_dict)))
        instance = cls.find_one(db, values_dict)
        if instance is not None:
            return instance.id
        return None

    @classmethod
    def _create(cls, db, session, values_dict):
        logger.debug("%s::_create %s" % (cls.__name__, repr(values_dict)))
        converted_values = cls._filter_columns(cls._translate_columns(cls.relational_mappings(db, values_dict)))
        non_none_values = 0
        for value in converted_values.values():
            if value is not None:
                non_none_values += 1
        if non_none_values < cls.min_row_values:
            raise ValueError("None row values: %s" % repr(values_dict))
        instance = cls(**converted_values)
        session.add(instance)
        return instance

    @classmethod
    def create(cls, db, values_dict):
        session = db.session()
        cls._create(db, session, values_dict)
        DB.commit(session)

    @classmethod
    def find_or_create(cls, db, values_dict):
        logger.debug("%s::find_or_create %s" % (cls.__name__, repr(values_dict)))
        instance = cls.find_one(db, values_dict)
        if instance is None:
            cls.create(db, values_dict)
            instance = cls.find_one(db, values_dict)
        return instance

    @classmethod
    def find_or_create_id(cls, db, values_dict):
        logger.debug("%s::find_or_create_id %s" % (cls.__name__, repr(values_dict)))
        logger.info("%s::find_or_create_id %s" % (cls.__name__, repr(values_dict)))
        instance = cls.find_or_create(db, values_dict)
        if instance is None:
            return None
        return instance.id

    def update(self, values_dict):
        for field in self._updateable_fields:
            self.__dict__[field] = values_dict[field]

    @classmethod
    def create_or_update(cls, db, values_dict):
        logger.debug("%s::create_or_update %s" % (cls.__name__, repr(values_dict)))
        session = db.query_session()
        instance = cls._find_one(session, values_dict)
        if instance is None:
            instance = cls._create(db, session, values_dict)
        else:
            instance.update(values_dict)
        DB.commit(session)
        return cls.find_one(db, values_dict)

    @classmethod
    def row_to_int(cls, row):
        return int(row[0])

    @classmethod
    def rows_to_ints(cls, rows):
        return [cls.row_to_int(row) for row in rows]

    @classmethod
    def row_to_month(cls, row):
        return datetime.date(1900, int(row[0]), 1).strftime("%b")

    @classmethod
    def rows_to_months(cls, rows):
        return [cls.row_to_month(row) for row in rows]

    @classmethod
    def get_years(cls, db):
        return cls.rows_to_ints(db.session().query(extract('year', cls.time_col)).distinct().all())

    @classmethod
    def get_months(cls, db, year):
          return (db.query_session().query(extract('month', cls.time_col)).filter(extract('year', cls.time_col) == str(year)).distinct().all())

    @classmethod
    def get_month_names(cls, db, year):
          return cls.rows_to_months(cls.get_months(db, year))

    @classmethod
    def get_days(cls, db, year):
        return cls.rows_to_ints(db.session().query(func.strftime("%j", cls.time_col)).filter(extract('year', cls.time_col) == str(year)).distinct().all())

    @classmethod
    def get_col_func(cls, db, col, func, start_ts=None, end_ts=None, ignore_zero=False):
        query = db.query_session().query(func(col))
        if start_ts is not None:
            query = query.filter(cls.time_col >= start_ts)
        if end_ts is not None:
            query = query.filter(cls.time_col < end_ts)
        if ignore_zero:
            query = query.filter(col != 0)
        return query.one()[0]

    @classmethod
    def get_col_avg(cls, db, col, start_ts, end_ts, ignore_zero=False):
        return cls.get_col_func(db, col, func.avg, start_ts, end_ts, ignore_zero)

    @classmethod
    def get_col_min(cls, db, col, start_ts, end_ts, ignore_zero=False):
        return cls.get_col_func(db, col, func.min, start_ts, end_ts, ignore_zero)

    @classmethod
    def get_col_max(cls, db, col, start_ts=None, end_ts=None):
        return cls.get_col_func(db, col, func.max, start_ts, end_ts, False)

    @classmethod
    def get_col_sum(cls, db, col, start_ts, end_ts):
        return cls.get_col_func(db, col, func.sum, start_ts, end_ts, False)

    @classmethod
    def get_col_sum_of_max_per_day(cls, db, col, start_ts, end_ts):
        max_daily_query = (
            db.query_session().query(func.max(col).label('maxes'))
                .filter(cls.timestamp >= start_ts)
                .filter(cls.timestamp < end_ts)
                .group_by(func.strftime("%j", cls.timestamp))
        )
        sum_of_maxes = db.query_session().query(func.sum(max_daily_query.subquery().columns.maxes))
        return DB.query_scalar(sum_of_maxes)

    def __repr__(self):
        classname = self.__class__.__name__
        col_name = cls.find_col.name
        col_value = self.__dict__[col_name]
        return ("<%s(%s=%s)>" % (classname, col.name, col_value))

