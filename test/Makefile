#
# This Makefile automates running tests for the project.
#

PROJECT_BASE ?= $(CURDIR)/../.

include $(PROJECT_BASE)/defines.mk


DB_TEST_GROUPS=garmin_db activities_db monitoring_db garmin_summary_db summary_db
DB_OBJECTS_TEST_GROUPS=garmin_db_objects
FILE_PARSE_TEST_GROUPS=fit_file tcx_loop tcx_file profile_file
ALL_TEST_GROUPS=$(DB_TEST_GROUPS) $(DB_OBJECTS_TEST_GROUPS) $(FILE_PARSE_TEST_GROUPS)
MANUAL_TEST_GROUPS=copy
BASE_TESTGROUP=config
TEST_GROUPS=$(DB_TEST_GROUPS) $(DB_OBJECTS_TEST_GROUPS) $(FILE_PARSE_TEST_GROUPS) $(MANUAL_TEST_GROUPS) $(BASE_TESTGROUP)

#
# Over all targets
#
all: $(ALL_TEST_GROUPS)

db: $(DB_TEST_GROUPS)

manual: $(MANUAL_TEST_GROUPS)

file_parse: $(FILE_PARSE_TEST_GROUPS)

db_objects: $(DB_OBJECTS_TEST_GROUPS)

verify_commit: db_objects

clean:
	rm -f *.pyc
	rm -f *.log
	rm -f *.txt
	rm -rf __pycache__

#
# Targets for testing smaller slices of functionality.
#
$(TEST_GROUPS):
	$(PYTHON) test_$@.py

test_%:
	$(PYTHON) -m unittest -v $@

.PHONY: all db file_parse db_objects clean
