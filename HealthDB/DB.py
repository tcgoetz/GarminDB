#
# copyright Tom Goetz
#

import os
import logging
import datetime

from contextlib import contextmanager

from sqlalchemy import create_engine, func, desc, extract, and_
from sqlalchemy.orm import sessionmaker, synonym, Query
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import set_attribute
from sqlalchemy.ext.hybrid import hybrid_method

from Utilities import filter_dict_by_list, dict_filter_none_values


logger = logging.getLogger(__name__)


class DB(object):

    def __init__(self, db_params_dict, debug=False):
        logger.info("%s: %r debug: %s ", self.__class__.__name__, db_params_dict, debug)
        if debug > 0:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        self.db_params_dict = db_params_dict
        url_func = getattr(self, self.db_params_dict['db_type'] + '_url')
        self.engine = create_engine(url_func(self.db_params_dict), echo=(debug > 1))
        self.session_maker = sessionmaker(bind=self.engine, expire_on_commit=False)

    @classmethod
    def sqlite_url(cls, db_params_dict):
        return "sqlite:///" + db_params_dict['db_path'] + '/' + cls.db_name + '.db'

    @classmethod
    def sqlite_delete(cls, db_params_dict):
        filename = db_params_dict['db_path'] + '/' + cls.db_name + '.db'
        try:
            os.remove(filename)
        except Exception:
            logger.warning('%s not removed', filename)

    @classmethod
    def mysql_url(cls, db_params_dict):
        return "mysql+pymysql://%s:%s@%s/%s" % (db_params_dict['db_username'], db_params_dict['db_password'], db_params_dict['db_host'], cls.db_name)

    def session(self):
        return self.session_maker()

    @contextmanager
    def managed_session(self):
        session = self.session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def delete_db(cls, db_params_dict):
        delete_func = getattr(cls, db_params_dict['db_type'] + '_delete')
        delete_func(db_params_dict)


#
####
#


class DBObject(object):

    # defaults, overridden by subclasses
    time_col_name = None
    match_col_names = None

    @classmethod
    def round_col_text(cls, col_name, alt_col_name=None, places=1, seperator=','):
        if alt_col_name is None:
            alt_col_name = col_name
        return 'ROUND(%s, %d) AS %s%s ' % (col_name, places, alt_col_name, seperator)

    @classmethod
    def round_col(cls, col_name, alt_col_name=None, places=1):
        if alt_col_name is None:
            alt_col_name = col_name
        return 'ROUND(%s, %d) AS %s ' % (col_name, places, alt_col_name)

    @declared_attr
    def col_count(cls):
        if hasattr(cls, '__table__'):
            return len(cls.__table__.columns)

    @declared_attr
    def time_col(cls):
        if cls.time_col_name is not None:
            return synonym(cls.time_col_name)

    @declared_attr
    def match_cols(cls):
        if cls.match_col_names is not None:
            return {col_name : synonym(col_name) for col_name in cls.match_col_names}
        cls.match_col_names = [cls.time_col_name]
        return {cls.time_col_name : synonym(cls.time_col_name)}

    @hybrid_method
    def during(self, start_ts, end_ts):
        return self.time_col >= start_ts and self.time_col < end_ts

    @during.expression
    def during(cls, start_ts, end_ts):
        return and_(cls.time_col >= start_ts, cls.time_col < end_ts)

    @hybrid_method
    def after(self, start_ts):
        if start_ts is not None:
            return self.time_col >= start_ts

    @after.expression
    def after(cls, start_ts):
        return cls.time_col >= start_ts

    @hybrid_method
    def before(self, end_ts):
        return self.time_col < end_ts

    @before.expression
    def before(cls, end_ts):
        return cls.time_col < end_ts

    @classmethod
    def get_default_view_name(cls):
        return cls.__tablename__ + '_view'

    @classmethod
    def get_col_names(cls):
        return [col.name for col in cls.__table__.columns]

    @classmethod
    def get_col_by_name(cls, name):
        for col in cls.__table__._columns:
            if col.name == name:
                return col

    def set_col_value(self, name, value):
        if name in self.get_col_names():
            set_attribute(self, name, value)

    def update_from_dict(self, values_dict, ignore_none=False):
        for key, value in values_dict.iteritems():
            if not ignore_none or value is not None:
                self.set_col_value(key, value)
        return self

    @classmethod
    def _delete_view(cls, db, view_name):
        with db.managed_session() as session:
            session.execute('DROP VIEW IF EXISTS ' + view_name)

    @classmethod
    def delete_view(cls, db, view_name=None):
        cls._delete_view(db, view_name if view_name is not None else cls.get_default_view_name())

    @classmethod
    def _create_view_if_not_exists(cls, session, view_name, query_str):
        session.execute('CREATE VIEW IF NOT EXISTS ' + view_name + ' AS ' + query_str)

    @classmethod
    def create_view_if_doesnt_exist(cls, db, view_name, query_str):
        with db.managed_session() as session:
            cls._create_view_if_not_exists(session, view_name, query_str)

    @classmethod
    def create_join_view(cls, db, view_name, selectable, join_table, order_by):
        with db.managed_session() as session:
            query = Query(selectable, session=session).join(join_table).order_by(order_by)
            cls._create_view_if_not_exists(session, view_name, str(query))

    @classmethod
    def create_multi_join_view(cls, db, view_name, selectable, joins, order_by):
        with db.managed_session() as session:
            query = Query(selectable, session=session)
            for (join_table, join_clause) in joins:
                query = query.join(join_table, join_clause)
            query = query.order_by(order_by)
            cls._create_view_if_not_exists(session, view_name, str(query))

    @classmethod
    def _create_view(cls, db, view_name, selectable, order_by):
        with db.managed_session() as session:
            query = Query(selectable, session=session).order_by(order_by)
            cls._create_view_if_not_exists(session, view_name, str(query))

    @classmethod
    def intersection(cls, values_dict):
        return filter_dict_by_list(values_dict, cls.get_col_names())

    @classmethod
    def _find_query(cls, session, values_dict):
        query = session.query(cls)
        if cls.match_col_names is not None:
            # for match_col_name, match_col in cls.match_cols.iteritems():
            #     query = query.filter(match_col == values_dict[match_col_name])
            for match_col_name in cls.match_col_names:
                query = query.filter(cls.get_col_by_name(match_col_name) == values_dict[match_col_name])
        else:
            query = query.filter(cls.time_col == values_dict[cls.time_col_name])
        return query

    @classmethod
    def _find_one(cls, session, values_dict):
        logger.debug("%s::_find_one %r", cls.__name__, values_dict)
        return cls._find_query(session, values_dict).one_or_none()

    @classmethod
    def find_one(cls, db, values_dict):
        with db.managed_session() as session:
            return cls._find_one(session, values_dict)

    @classmethod
    def _find_id(cls, session, values_dict):
        logger.debug("%s::find_id %r", cls.__name__, values_dict)
        return cls._find_one(session, values_dict).id

    @classmethod
    def find_id(cls, db, values_dict):
        with db.managed_session() as session:
            return cls._find_id(session, values_dict)

    @classmethod
    def _create(cls, session, values_dict, ignore_none=False):
        logger.debug("%s::_create %r", cls.__name__, values_dict)
        if ignore_none:
            values_dict = dict_filter_none_values(values_dict)
        instance = cls(**values_dict)
        session.add(instance)

    @classmethod
    def _find_or_create(cls, session, values_dict):
        logger.debug("%s::find_or_create %r", cls.__name__, values_dict)
        if cls._find_one(session, values_dict) is None:
            cls._create(session, values_dict)

    @classmethod
    def find_or_create(cls, db, values_dict):
        with db.managed_session() as session:
            cls._find_or_create(session, values_dict)

    @classmethod
    def _create_or_update(cls, session, values_dict, ignore_none=False):
        logger.debug("%s::create_or_update %r", cls.__name__, values_dict)
        instance = cls._find_one(session, values_dict)
        if instance is None:
            cls._create(session, values_dict, ignore_none)
        else:
            instance.update_from_dict(values_dict, ignore_none)

    @classmethod
    def create_or_update(cls, db, values_dict, ignore_none=False):
        with db.managed_session() as session:
            cls._create_or_update(session, values_dict, ignore_none)

    @classmethod
    def _create_or_update_not_none(cls, session, values_dict):
        logger.debug("%s::_create_or_update_not_none %r", cls.__name__, values_dict)
        cls._create_or_update(session, values_dict, True)

    @classmethod
    def create_or_update_not_none(cls, db, values_dict):
        cls.create_or_update(db, values_dict, True)

    @classmethod
    def secs_from_time(cls, col):
        return func.strftime('%s', col) - func.strftime('%s', '00:00')

    @classmethod
    def time_from_secs(cls, value):
        return func.time(value, 'unixepoch')

    @classmethod
    def row_to_int(cls, row):
        return int(row[0])

    @classmethod
    def row_to_int_not_none(cls, row):
        if row[0] is not None:
            return cls.row_to_int(row)

    @classmethod
    def rows_to_ints(cls, rows):
        return [cls.row_to_int(row) for row in rows]

    @classmethod
    def rows_to_ints_not_none(cls, rows):
        return [cls.row_to_int_not_none(row) for row in rows]

    @classmethod
    def row_to_month(cls, row):
        return datetime.date(1900, row, 1).strftime("%b")

    @classmethod
    def rows_to_months(cls, rows):
        return [cls.row_to_month(row) for row in rows]

    @classmethod
    def get_years(cls, db):
        with db.managed_session() as session:
            return cls.rows_to_ints_not_none(session.query(extract('year', cls.time_col)).distinct().all())

    @classmethod
    def _get_months(cls, session, year):
        return cls.rows_to_ints_not_none(session.query(extract('month', cls.time_col)).filter(extract('year', cls.time_col) == str(year)).distinct().all())

    @classmethod
    def get_months(cls, db, year):
        with db.managed_session() as session:
            return cls._get_months(session, year)

    @classmethod
    def get_month_names(cls, db, year):
        return cls.rows_to_months(cls.get_months(db, year))

    @classmethod
    def _get_days(cls, session, year):
        return cls.rows_to_ints(session.query(func.strftime("%j", cls.time_col)).filter(extract('year', cls.time_col) == str(year)).distinct().all())

    @classmethod
    def get_days(cls, db, year):
        with db.managed_session() as session:
            return cls._get_days(session, year)

    @classmethod
    def _query(cls, session, selectable, order_by=None, start_ts=None, end_ts=None, ignore_le_zero_col=None):
        query = session.query(selectable)
        if order_by is not None:
            query = query.order_by(order_by)
        if start_ts is not None and end_ts is not None:
            query = query.filter(cls.during(start_ts, end_ts))
        elif start_ts is not None:
            query = query.filter(cls.after(start_ts))
        elif end_ts is not None:
            query = query.filter(cls.before(end_ts))
        if ignore_le_zero_col is not None:
            query = query.filter(ignore_le_zero_col > 0)
        return query

    @classmethod
    def _get_for_period(cls, session, selectable, start_ts, end_ts, not_none_col=None):
        query = cls._query(session, selectable, cls.time_col, start_ts, end_ts)
        if not_none_col is not None:
            # filter does not use 'is not None'
            query = query.filter(not_none_col != None)
        return query.all()

    @classmethod
    def get_for_period(cls, db, selectable, start_ts, end_ts, not_none_col=None):
        with db.managed_session() as session:
            return cls._get_for_period(session, selectable, start_ts, end_ts, not_none_col)

    @classmethod
    def _get_for_day(cls, db, selectable, day_date, not_none_col=None):
        start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        end_ts = start_ts + datetime.timedelta(1)
        return cls._get_for_period(db, selectable, start_ts, end_ts, not_none_col)

    @classmethod
    def get_for_day(cls, db, selectable, day_date, not_none_col=None):
        start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        end_ts = start_ts + datetime.timedelta(1)
        return cls.get_for_period(db, selectable, start_ts, end_ts, not_none_col)

    @classmethod
    def get_col_values(cls, db, get_col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        with db.managed_session() as session:
            return cls._query(session, get_col, cls.time_col, start_ts, end_ts, ignore_le_zero).filter(match_col == match_value).all()

    @classmethod
    def _get_col_func_query(cls, session, col, func, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._query(session, func(col), None, start_ts, end_ts, col if ignore_le_zero else None)

    @classmethod
    def get_col_distinct(cls, db, col, start_ts=None, end_ts=None):
        with db.managed_session() as session:
            return [row[0] for row in cls._get_col_func_query(session, col, func.distinct, start_ts, end_ts).all()]

    @classmethod
    def _get_col_avg(cls, session, col, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._get_col_func_query(session, col, func.avg, start_ts, end_ts, col if ignore_le_zero else None).scalar()

    @classmethod
    def get_col_avg(cls, db, col, start_ts=None, end_ts=None, ignore_le_zero=False):
        with db.managed_session() as session:
            return cls._get_col_avg(session, col, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def _get_col_min(cls, session, col, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._get_col_func_query(session, col, func.min, start_ts, end_ts, col if ignore_le_zero else None).scalar()

    @classmethod
    def get_col_min(cls, db, col, start_ts=None, end_ts=None, ignore_le_zero=False):
        with db.managed_session() as session:
            return cls._get_col_func_query(session, col, func.min, start_ts, end_ts, col if ignore_le_zero else None).scalar()

    @classmethod
    def _get_col_max(cls, session, col, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._get_col_func_query(session, col, func.max, start_ts, end_ts, ignore_le_zero).scalar()

    @classmethod
    def get_col_max(cls, db, col, start_ts=None, end_ts=None, ignore_le_zero=False):
        with db.managed_session() as session:
            return cls._get_col_func_query(session, col, func.max, start_ts, end_ts, ignore_le_zero).scalar()

    @classmethod
    def _get_col_sum(cls, session, col, start_ts=None, end_ts=None):
        return cls._get_col_func_query(session, col, func.sum, start_ts, end_ts).scalar()

    @classmethod
    def get_col_sum(cls, db, col, start_ts=None, end_ts=None):
        with db.managed_session() as session:
            return cls._get_col_sum(session, col, start_ts, end_ts)

    @classmethod
    def _get_time_col_func(cls, session, col, stat_func, start_ts=None, end_ts=None):
        result = (
            cls._query(session, cls.time_from_secs(stat_func(cls.secs_from_time(col))),
                       None, start_ts, end_ts, cls.secs_from_time(col)).scalar()
        )
        return datetime.datetime.strptime(result, '%H:%M:%S').time() if result is not None else datetime.time.min

    @classmethod
    def get_time_col_func(cls, db, col, stat_func, start_ts=None, end_ts=None):
        with db.managed_session() as session:
            return cls._get_time_col_func(session, col, stat_func, start_ts, end_ts)

    @classmethod
    def _get_time_col_avg(cls, session, col, start_ts=None, end_ts=None):
        return cls._get_time_col_func(session, col, func.avg, start_ts, end_ts)

    @classmethod
    def get_time_col_avg(cls, db, col, start_ts=None, end_ts=None):
        return cls.get_time_col_func(db, col, func.avg, start_ts, end_ts)

    @classmethod
    def _get_time_col_min(cls, session, col, start_ts=None, end_ts=None):
        return cls._get_time_col_func(session, col, func.min, start_ts, end_ts)

    @classmethod
    def get_time_col_min(cls, db, col, start_ts=None, end_ts=None):
        return cls.get_time_col_func(db, col, func.min, start_ts, end_ts)

    @classmethod
    def _get_time_col_max(cls, session, col, start_ts=None, end_ts=None):
        return cls._get_time_col_func(session, col, func.max, start_ts, end_ts)

    @classmethod
    def get_time_col_max(cls, db, col, start_ts=None, end_ts=None):
        return cls.get_time_col_func(db, col, func.max, start_ts, end_ts)

    @classmethod
    def _get_time_col_sum(cls, session, col, start_ts=None, end_ts=None):
        return cls._get_time_col_func(session, col, func.sum, start_ts, end_ts)

    @classmethod
    def get_time_col_sum(cls, db, col, start_ts=None, end_ts=None):
        return cls.get_time_col_func(db, col, func.sum, start_ts, end_ts)

    @classmethod
    def get_col_latest(cls, db, col, ignore_le_zero=False):
        with db.managed_session() as session:
            query = session.query(col)
            if ignore_le_zero:
                if col == cls.time_col:
                    query = query.filter(cls.secs_from_time(col) > 0)
                else:
                    query = query.filter(col > 0)
            return query.order_by(desc(cls.time_col)).limit(1).scalar()

    @classmethod
    def get_time_col_latest(cls, db, col):
        with db.managed_session() as session:
            return session.query(col).filter(cls.secs_from_time(col) > 0).order_by(desc(cls.time_col)).limit(1).scalar()

    @classmethod
    def _get_col_func_of_max_per_day_for_value(cls, session, col, stat_func, start_ts, end_ts, match_col=None, match_value=None):
        max_daily_query = (
            session.query(func.max(col).label('maxes')).filter(cls.during(start_ts, end_ts)).group_by(func.strftime("%j", cls.time_col))
        )
        if match_col is not None and match_value is not None:
            max_daily_query.filter(match_col == match_value)
        return session.query(stat_func(max_daily_query.subquery().columns.maxes)).scalar()

    @classmethod
    def get_col_func_of_max_per_day_for_value(cls, db, col, stat_func, start_ts, end_ts, match_col=None, match_value=None):
        with db.managed_session() as session:
            return cls._get_col_func_of_max_per_day_for_value(session, col, stat_func, start_ts, end_ts, match_col, match_value)

    @classmethod
    def get_col_sum_of_max_per_day_for_value(cls, db, col, match_col, match_value, start_ts, end_ts):
        return cls.get_col_func_of_max_per_day_for_value(db, col, func.sum, start_ts, end_ts, match_col, match_value)

    @classmethod
    def _get_col_avg_of_max_per_day_for_value(cls, session, col, match_col, match_value, start_ts, end_ts):
        return cls._get_col_func_of_max_per_day_for_value(session, col, func.avg, start_ts, end_ts, match_col, match_value)

    @classmethod
    def get_col_avg_of_max_per_day_for_value(cls, db, col, match_col, match_value, start_ts, end_ts):
        return cls.get_col_func_of_max_per_day_for_value(db, col, func.avg, start_ts, end_ts, match_col, match_value)

    @classmethod
    def _get_col_func_of_max_per_day(cls, session, col, stat_func, start_ts, end_ts):
        return cls._get_col_func_of_max_per_day_for_value(session, col, func.sum, start_ts, end_ts)

    @classmethod
    def get_col_func_of_max_per_day(cls, db, col, stat_func, start_ts, end_ts):
        return cls.get_col_func_of_max_per_day_for_value(db, col, func.sum, start_ts, end_ts)

    @classmethod
    def _get_col_sum_of_max_per_day(cls, session, col, start_ts, end_ts):
        return cls._get_col_func_of_max_per_day(session, col, func.sum, start_ts, end_ts)

    @classmethod
    def get_col_sum_of_max_per_day(cls, db, col, start_ts, end_ts):
        return cls.get_col_func_of_max_per_day(db, col, func.sum, start_ts, end_ts)

    @classmethod
    def get_col_avg_of_max_per_day(cls, db, col, start_ts, end_ts):
        return cls.get_col_func_of_max_per_day(db, col, func.avg, start_ts, end_ts)

    @classmethod
    def get_col_min_of_max_per_day(cls, db, col, start_ts, end_ts):
        return cls.get_col_func_of_max_per_day(db, col, func.min, start_ts, end_ts)

    @classmethod
    def get_col_max_of_max_per_day(cls, db, col, start_ts, end_ts):
        return cls.get_col_func_of_max_per_day(db, col, func.max, start_ts, end_ts)

    @classmethod
    def latest_time(cls, db, not_zero_col):
        return cls.get_col_max_greater_than_value(db, cls.time_col, not_zero_col, 0)

    @classmethod
    def row_count(cls, db, col=None, col_value=None):
        with db.managed_session() as session:
            query = session.query(cls)
            if col is not None:
                query = query.filter(col == col_value)
            return query.count()

    @classmethod
    def _row_count_for_period(cls, session, start_ts, end_ts):
        return session.query(cls).filter(cls.time_col >= start_ts).filter(cls.time_col < end_ts).count()

    @classmethod
    def row_count_for_period(cls, db, start_ts, end_ts):
        with db.managed_session() as session:
            return cls._row_count_for_period(session, start_ts, end_ts)

    @classmethod
    def _row_count_for_day(cls, session, day_date):
        start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        end_ts = start_ts + datetime.timedelta(1)
        return cls._row_count_for_period(session, start_ts, end_ts)

    @classmethod
    def row_count_for_day(cls, db, day_date):
        start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        end_ts = start_ts + datetime.timedelta(1)
        return cls.row_count_for_period(db, start_ts, end_ts)

    @classmethod
    def _get_col_func_for_value(cls, session, col, stat_func, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._query(session, stat_func(col), None, start_ts, end_ts, col if ignore_le_zero else None).filter(match_col == match_value).scalar()

    @classmethod
    def get_col_func_for_value(cls, db, col, stat_func, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        with db.managed_session() as session:
            return cls._query(session, stat_func(col), None, start_ts, end_ts, col if ignore_le_zero else None).filter(match_col == match_value).scalar()

    @classmethod
    def _get_col_sum_for_value(cls, session, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._get_col_func_for_value(session, col, func.sum, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def get_col_sum_for_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls.get_col_func_for_value(db, col, func.sum, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def _get_col_avg_for_value(cls, session, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._get_col_func_for_value(session, col, func.avg, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def get_col_avg_for_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls.get_col_func_for_value(db, col, func.avg, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def _get_col_min_for_value(cls, session, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._get_col_func_for_value(session, col, func.min, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def get_col_min_for_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls.get_col_func_for_value(db, col, func.min, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def _get_col_max_for_value(cls, session, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls._get_col_func_for_value(session, col, func.max, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def get_col_max_for_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls.get_col_func_for_value(db, col, func.max, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def get_col_func_greater_than_value(cls, db, col, stat_func, match_col, match_value, start_ts=None, end_ts=None):
        with db.managed_session() as session:
            return cls._query(session, stat_func(col), None, start_ts, end_ts).filter(match_col > match_value).scalar()

    @classmethod
    def get_col_avg_greater_than_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None):
        return cls.get_col_func_greater_than_value(db, col, func.avg, match_col, match_value, start_ts, end_ts)

    @classmethod
    def get_col_max_greater_than_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None):
        return cls.get_col_func_greater_than_value(db, col, func.max, match_col, match_value, start_ts, end_ts)

    @classmethod
    def get_col_func_less_than_value(cls, db, col, stat_func, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        with db.managed_session() as session:
            return cls._query(session, stat_func(col), None, start_ts, end_ts, col if ignore_le_zero else None).filter(match_col < match_value).scalar()

    @classmethod
    def get_col_avg_less_than_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls.get_col_func_less_than_value(db, col, func.avg, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def get_col_min_less_than_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls.get_col_func_less_than_value(db, col, func.min, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def get_col_max_less_than_value(cls, db, col, match_col, match_value, start_ts=None, end_ts=None, ignore_le_zero=False):
        return cls.get_col_func_less_than_value(db, col, func.max, match_col, match_value, start_ts, end_ts, ignore_le_zero)

    @classmethod
    def get_daily_stats(cls, session, day_ts):
        stats = cls.get_stats(session, day_ts, day_ts + datetime.timedelta(1))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, session, first_day_ts):
        stats = cls.get_stats(session, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, session, first_day_ts, last_day_ts):
        stats = cls.get_stats(session, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts
        return stats

    def __repr__(self):
        classname = self.__class__.__name__
        values = {col_name : getattr(self, col_name) for col_name in self.get_col_names()}
        return ("<%s() %r>" % (classname, values))
