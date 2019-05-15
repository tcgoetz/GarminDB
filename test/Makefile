#
# This Makefile automates running tests for the project.
#
PROJECT_BASE ?= $(PWD)/../.

include $(PROJECT_BASE)/defines.mk


#
# Over all targets
#
all: db dbobjects fit

db: garmindb activitiesdb monitoringdb garminsummarydb summarydb

dbobjects: garmindb_objects

clean:
	rm -f *.pyc
	rm -f *.log

#
# Targets for testing smaller slices of functionality.
#
garmindb:
	$(PYTHON) TestGarminDb.py

garmindb_objects:
	$(PYTHON) TestGarminDbObjects.py

activitiesdb:
	$(PYTHON) TestActivitiesDb.py

monitoringdb:
	$(PYTHON) TestMonitoringDB.py

garminsummarydb:
	$(PYTHON) TestGarminSummaryDB.py

summarydb:
	$(PYTHON) TestSummaryDB.py

fit:
	$(PYTHON) TestFit.py
