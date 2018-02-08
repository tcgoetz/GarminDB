#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class ActivitiesDB(DB):
    Base = declarative_base()
    db_name = 'garmin_activities'

    def __init__(self, db_params_dict, debug=False):
        logger.info("ActivitiesDB: %s debug: %s " % (repr(db_params_dict), str(debug)))
        DB.__init__(self, db_params_dict, debug)
        ActivitiesDB.Base.metadata.create_all(self.engine)
