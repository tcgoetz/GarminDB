#
# This Makefile automates running tests for the project.
#

PROJECT_BASE ?= $(PWD)/../.

include $(PROJECT_BASE)/defines.mk

DB_TEST_GROUPS=garmin_db activities_db monitoring_db garmin_summary_db summary_db
DB_OBJECTS_TEST_GROUPS=garmin_db_objects
TEST_GROUPS=$(DB_TEST_GROUPS) $(DB_OBJECTS_TEST_GROUPS) fit_file fit_field_enum tcx_file

#
# Over all targets
#
all: $(TEST_GROUPS)

db: $(DB_TEST_GROUPS)

db_objects: $(DB_OBJECTS_TEST_GROUPS)

clean:
	rm -f *.pyc
	rm -f *.log

#
# Targets for testing smaller slices of functionality.
#
$(TEST_GROUPS):
	$(PYTHON) test_$@.py
