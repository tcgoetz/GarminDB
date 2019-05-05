
TOP ?= $(PWD)/../.

include $(TOP)/defines.mk


all: db dbobjects fit

db: garmindb activitiesdb monitoringdb garminsummarydb

dbobjects: garmindb_objects

garmindb:
	export DB_DIR=$(DB_DIR) && $(PYTHON) TestGarminDb.py

garmindb_objects:
	export DB_DIR=$(TEST_DB_DIR) && $(PYTHON) TestGarminDbObjects.py

activitiesdb:
	export DB_DIR=$(DB_DIR) && $(PYTHON) TestActivitiesDb.py

monitoringdb:
	export DB_DIR=$(DB_DIR) && $(PYTHON) TestMonitoringDB.py

garminsummarydb:
	export DB_DIR=$(DB_DIR) && $(PYTHON) TestGarminSummaryDB.py

fit:
	export DB_DIR=$(DB_DIR) && $(PYTHON) TestFit.py

clean:
	rm -f *.pyc
	rm -f *.log
