

#
# Install Python dependancies as root?
#
INSTALL_DEPS_TO_SYSTEM ?= y
ifeq ($(INSTALL_DEPS_TO_SYSTEM), y)
	DEPS_SUDO = sudo
else
	DEPS_SUDO =
endif

OS := $(shell uname -s)
ARCH := $(shell uname -p)
EPOCH=$(shell date +'%s')
YEAR=$(shell date +'%Y')

#
# Automatically get the username and pasword
#
ifeq ($(OS), Darwin)
	# Find the username and password from the OSX keychain. Works if you have logged into Garmin Connect from Safari or you manually set it.
	# If your using iCloud Keychaion, you have to copy the entry from the iCloud keychain to the login keychain using KeychainAccess.app.
	GC_USER ?= $(shell security find-internet-password -s sso.garmin.com | egrep acct | egrep -o "[A-Za-z]*@[A-Za-z.]*" )
	GC_PASSWORD ?= $(shell security find-internet-password -s sso.garmin.com -w)
	GC_DATE ?= $(shell date -v-1m +'%m/%d/%Y')
else
	# store the username and password in ~/.garmindb.conf ?
	GC_DATE ?= $(shell date -d '-1 month' +'%m/%d/%Y')
endif
GC_DAYS ?= 31


HEALTH_DATA_DIR=$(HOME)/HealthData
FIT_FILE_DIR=$(HEALTH_DATA_DIR)/FitFiles
FITBIT_FILE_DIR=$(HEALTH_DATA_DIR)/FitBitFiles
MSHEALTH_FILE_DIR=$(HEALTH_DATA_DIR)/MSHealth
DB_DIR=$(HEALTH_DATA_DIR)/DBs
BACKUP_DIR=$(HEALTH_DATA_DIR)/Backups
MONITORING_FIT_FILES_DIR=$(FIT_FILE_DIR)/$(YEAR)_Monitoring
SLEEP_FILES_DIR=$(HEALTH_DATA_DIR)/Sleep
ACTIVITES_FIT_FILES_DIR=$(FIT_FILE_DIR)/Activities
WEIGHT_FILES_DIR=$(HEALTH_DATA_DIR)/Weight
RHR_FILES_DIR=$(HEALTH_DATA_DIR)/RHR

BIN_DIR=$(PWD)/bin

TMPDIR = $(shell mktemp -d)

TEST_FILE_DIR=$(HOME)/Downloads
TEST_DB_DIR=$(TMPDIR)

DEFAULT_SLEEP_START=22:00
DEFAULT_SLEEP_STOP=06:00

TEST_GC_ID ?= 10724054307

# define UNITS_OPT="" for metric
UNITS_OPT ?= "-e"


#
# Master targets
#

all: update_dbs

# install all needed code
setup: update deps


clean_dbs: clean_mshealth_db clean_fitbit_db clean_garmin_dbs clean_summary_db

# build dbs from already downloaded data files
build_dbs: build_garmin_dbs mshealth_db fitbit_db mshealth_summary fitbit_summary

# delete the exisitng dbs and build new dbs from already downloaded data files
rebuild_dbs: clean_dbs build_dbs
rebuild_activity_db: clean_activities_db build_activities_db

# download data files for the period specified by GC_DATE and GC_DAYS and build the dbs
create_dbs: download_garmin build_dbs

# update the exisitng dbs by downloading data files for dates after the last in the dbs and update the dbs
update_dbs: update_garmin

#
#
#

update: submodules_update
	git pull --rebase

submodules_update:
	git submodule init
	git submodule update

deps_tcxparser:
	cd python-tcxparser && python setup.py install --record files.txt

clean_deps_tcxparser:
	cd python-tcxparser && cat files.txt | xargs rm -rf

install_deps: deps_tcxparser
	pip install --upgrade sqlalchemy
	pip install --upgrade requests
	pip install --upgrade python-dateutil || true
	pip install --upgrade enum34

deps:
	$(DEPS_SUDO) $(MAKE) install_deps

remove_deps: clean_deps_tcxparser
	pip uninstall sqlalchemy
	pip uninstall selenium
	pip uninstall python-dateutil
	pip uninstall enum34

clean_deps:
	$(DEPS_SUDO) $(MAKE) remove_deps

clean:
	rm -rf *.pyc
	rm -rf Fit/*.pyc
	rm -rf HealthDB/*.pyc
	rm -rf GarminDB/*.pyc
	rm -rf FitBitDB/*.pyc


#
# Fitness System independant
#
SUMMARY_DB=$(DB_DIR)/summary.db
$(SUMMARY_DB): $(DB_DIR)

summary: mshealth_summary fitbit_summary garmin_summary

clean_summary_db:
	rm -f $(SUMMARY_DB)

$(DB_DIR):
	mkdir -p $(DB_DIR)

$(BACKUP_DIR):
	mkdir -p $(BACKUP_DIR)

backup: $(BACKUP_DIR)
	zip -r $(BACKUP_DIR)/$(EPOCH)_dbs.zip $(DB_DIR)


#
# Garmin
#
garmin_profile:
	python import_garmin.py -t1 --profile_dir "$(FIT_FILE_DIR)" --sqlite $(DB_DIR)

## test monitoring
test_import_monitoring: $(DB_DIR)
	python import_garmin.py -t1 --fit_input_file "$(MONITORING_FIT_FILES_DIR)/$(TEST_GC_ID).fit" --sqlite $(DB_DIR)

test_monitoring_file: $(TEST_DB_DIR)
	@if [ -z "$(TEST_DB_DIR)" ]; then echo "TEST_DB_DIR is not defined"; fi
	@if [ -f "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" ]; then \
		python import_garmin.py -t1 --fit_input_file "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" --sqlite $(TEST_DB_DIR); \
	else \
		echo "Expecting " $(TEST_GC_ID).fit " to be found in " $(TEST_FILE_DIR) " but it contains:"; \
		ls -l "$(TEST_FILE_DIR)"; \
	fi

##  monitoring
GARMIN_MON_DB=$(DB_DIR)/garmin_monitoring.db
$(GARMIN_MON_DB): $(DB_DIR) import_monitoring

build_monitoring_db: $(GARMIN_MON_DB)

clean_monitoring_db:
	rm -f $(GARMIN_MON_DB)

$(MONITORING_FIT_FILES_DIR):
	mkdir -p $(MONITORING_FIT_FILES_DIR)

download_monitoring: $(MONITORING_FIT_FILES_DIR)
	python download_garmin.py -d $(GC_DATE) -n $(GC_DAYS) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -m "$(MONITORING_FIT_FILES_DIR)"

import_monitoring: $(DB_DIR)
	for dir in $(shell ls -d $(FIT_FILE_DIR)/*Monitoring*/); do \
		python import_garmin.py --fit_input_dir "$$dir" --sqlite $(DB_DIR); \
	done

download_new_monitoring: $(MONITORING_FIT_FILES_DIR)
	python download_garmin.py -l --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -m "$(MONITORING_FIT_FILES_DIR)"

import_new_monitoring: download_new_monitoring
	for dir in $(shell ls -d $(FIT_FILE_DIR)/*Monitoring*/); do \
		python import_garmin.py -l --fit_input_dir "$$dir" --sqlite $(DB_DIR); \
	done

## activities
GARMIN_ACT_DB=$(DB_DIR)/garmin_activities.db
$(GARMIN_ACT_DB): $(DB_DIR) import_activities

build_activities_db: $(GARMIN_ACT_DB)

clean_activities_db:
	rm -f $(GARMIN_ACT_DB)

$(ACTIVITES_FIT_FILES_DIR):
	mkdir -p $(ACTIVITES_FIT_FILES_DIR)

test_import_fit_activities: $(TEST_DB_DIR)
	@if [ -z "$(TEST_DB_DIR)" ]; then echo "TEST_DB_DIR is not defined"; fi
	@if [ -f "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" ]; then \
		python import_garmin_activities.py -t1 --input_file "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" --sqlite $(TEST_DB_DIR); \
	else \
		echo "Expecting " $(TEST_GC_ID).fit " to be found in " $(TEST_FILE_DIR) " but it contains:"; \
		ls -l "$(TEST_FILE_DIR)"; \
	fi

test_import_details_json_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR)
	python import_garmin_activities.py -t1 --input_file "$(ACTIVITES_FIT_FILES_DIR)/activity_details_$(TEST_GC_ID).json" --sqlite $(DB_DIR)

test_import_tcx_activities: $(TEST_DB_DIR) $(TEST_FILE_DIR)
	python import_garmin_activities.py -t1 --input_file "$(TEST_FILE_DIR)/$(TEST_GC_ID).tcx" --sqlite $(TEST_DB_DIR)

test_import_json_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR)
	@if [ -z "$(TEST_DB_DIR)" ]; then echo "TEST_DB_DIR is not defined"; fi
	@if [ -f "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" ]; then \
		python import_garmin_activities.py -t1 --input_file "$(ACTIVITES_FIT_FILES_DIR)/activity_$(TEST_GC_ID).json" --sqlite $(DB_DIR); \
	else \
		echo "Expecting " $(TEST_GC_ID).fit " to be found in " $(TEST_FILE_DIR) " but it contains:"; \
		ls -l "$(TEST_FILE_DIR)"; \
	fi
import_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR)
	python import_garmin_activities.py --input_dir "$(ACTIVITES_FIT_FILES_DIR)" --sqlite $(DB_DIR)

import_new_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR) download_new_activities
	python import_garmin_activities.py -l --input_dir "$(ACTIVITES_FIT_FILES_DIR)" --sqlite $(DB_DIR)

download_new_activities: $(ACTIVITES_FIT_FILES_DIR)
	python download_garmin.py --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -a "$(ACTIVITES_FIT_FILES_DIR)" -c 10

download_all_activities: $(ACTIVITES_FIT_FILES_DIR)
	python download_garmin.py --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -a "$(ACTIVITES_FIT_FILES_DIR)"

force_download_all_activities: $(ACTIVITES_FIT_FILES_DIR)
	python download_garmin.py --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -a "$(ACTIVITES_FIT_FILES_DIR)" -o

## generic garmin
GARMIN_DB=$(DB_DIR)/garmin.db
$(GARMIN_DB): $(DB_DIR) garmin_config import_sleep import_weight import_rhr

build_garmin_db: $(GARMIN_DB)

clean_garmin_db:
	rm -f $(GARMIN_DB)

## sleep
$(SLEEP_FILES_DIR):
	mkdir -p $(SLEEP_FILES_DIR)

download_sleep: $(SLEEP_FILES_DIR)
	python download_garmin.py -d $(GC_DATE) -n $(GC_DAYS) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -S "$(SLEEP_FILES_DIR)"

import_sleep: $(SLEEP_FILES_DIR)
	python import_garmin.py --sleep_input_dir "$(SLEEP_FILES_DIR)" --sqlite $(DB_DIR)

download_new_sleep: $(SLEEP_FILES_DIR)
	python download_garmin.py -l --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -S "$(SLEEP_FILES_DIR)"

import_new_sleep: download_new_sleep
	python import_garmin.py -l --sleep_input_dir "$(SLEEP_FILES_DIR)" --sqlite $(DB_DIR)

## weight
$(WEIGHT_FILES_DIR):
	mkdir -p $(WEIGHT_FILES_DIR)

import_weight: $(DB_DIR)
	python import_garmin.py --weight_input_dir "$(WEIGHT_FILES_DIR)" --sqlite $(DB_DIR)

import_new_weight: download_weight import_weight

download_weight: $(DB_DIR) $(WEIGHT_FILES_DIR)
	python download_garmin.py --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -w "$(WEIGHT_FILES_DIR)"

## rhr
$(RHR_FILES_DIR):
	mkdir -p $(RHR_FILES_DIR)

import_rhr: $(DB_DIR)
	python import_garmin.py --rhr_input_dir "$(RHR_FILES_DIR)" --sqlite $(DB_DIR)

import_new_rhr: download_rhr import_rhr

download_rhr: $(DB_DIR) $(RHR_FILES_DIR)
	python download_garmin.py --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -r "$(RHR_FILES_DIR)"

## digested garmin data
GARMIN_SUM_DB=$(DB_DIR)/garmin_summary.db
$(GARMIN_SUM_DB): $(DB_DIR) garmin_summary

build_garmin_summary_db: $(GARMIN_SUM_DB)

clean_garmin_summary_db:
	rm -f $(GARMIN_SUM_DB)

garmin_summary:
	python analyze_garmin.py --analyze --dates --sqlite $(DB_DIR)

garmin_config:
	python analyze_garmin.py -S$(DEFAULT_SLEEP_START),$(DEFAULT_SLEEP_STOP) --sqlite /Users/tgoetz/HealthData/DBs

#
# These operations work across all garmin dbs
#
update_garmin: import_new_monitoring import_new_activities import_new_weight import_new_sleep import_new_rhr garmin_summary

download_garmin: download_monitoring download_all_activities download_sleep download_weight download_rhr

build_garmin_dbs: build_garmin_db build_monitoring_db build_activities_db build_garmin_summary_db

clean_garmin_dbs: clean_garmin_db clean_garmin_summary_db clean_monitoring_db clean_activities_db


#
# FitBit
#
FITBIT_DB=$(DB_DIR)/fitbit.db
$(FITBIT_DB): $(DB_DIR) import_fitbit_file

clean_fitbit_db:
	rm -f $(FITBIT_DB)

$(FITBIT_FILE_DIR):
	mkdir -p $(FITBIT_FILE_DIR)

import_fitbit_file: $(DB_DIR) $(FITBIT_FILE_DIR)
	python import_fitbit_csv.py $(UNITS_OPT) --input_dir "$(FITBIT_FILE_DIR)" --sqlite $(DB_DIR)

fitbit_summary: $(FITBIT_DB)
	python analyze_fitbit.py --sqlite $(DB_DIR) --dates

fitbit_db: $(FITBIT_DB)


#
# MS Health
#
MSHEALTH_DB=$(DB_DIR)/mshealth.db
$(MSHEALTH_DB): $(DB_DIR) import_mshealth

clean_mshealth_db:
	rm -f $(MSHEALTH_DB)

$(MSHEALTH_FILE_DIR):
	mkdir -p $(MSHEALTH_FILE_DIR)

import_mshealth: $(DB_DIR) $(MSHEALTH_FILE_DIR)
	python import_mshealth_csv.py $(UNITS_OPT) --input_dir "$(MSHEALTH_FILE_DIR)" --sqlite $(DB_DIR)

mshealth_summary: $(MSHEALTH_DB)
	python analyze_mshealth.py --sqlite $(DB_DIR) --dates

mshealth_db: $(MSHEALTH_DB)


#
# test
#
test:
	export DB_DIR=$(DB_DIR) && python test.py

