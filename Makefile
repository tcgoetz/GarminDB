#
# This Makefile handles downloading data from Garmin Connect and generating SQLite DB files from that data. The Makefile targets handle the dependaancies
# between downloading and geenrating varies types of data. It wraps the core Python scripts and runs them with appropriate parameters.
#
PROJECT_BASE=$(PWD)

include defines.mk

#
# Install Python dependancies as root?
#
ifeq ($(INSTALL_DEPS_TO_SYSTEM), y)
	DEPS_SUDO = sudo
else
	DEPS_SUDO =
endif

OS := $(shell uname -s)
ARCH := $(shell uname -p)
EPOCH=$(shell date +'%s')
YEAR=$(shell date +'%Y')

ifeq ($(OS), Darwin)
	# Find the Garmin Connect username and password from the OSX keychain. Works if you have logged into Garmin Connect from Safari and
	# choosen to save your password or you manually set it.  If your using iCloud Keychain, you have to copy the entry from the iCloud
	# keychain to the login keychain using KeychainAccess.app.
	GC_USER ?= $(shell security find-internet-password -s sso.garmin.com | egrep acct | egrep -o "[A-Za-z]*@[A-Za-z.]*" )
	GC_PASSWORD ?= $(shell security find-internet-password -s sso.garmin.com -w)
	GC_DATE ?= $(shell date -v-1m +'%m/%d/%Y')
else
	# store the username and password in ~/.garmindb.conf ?
	GC_DATE ?= $(shell date -d '-1 month' +'%m/%d/%Y')
endif
GC_USER = $(shell cat $(PROJECT_BASE)/.gc_user.conf)
GC_DAYS ?= 31

PYTHON_PACKAGES=sqlalchemy requests python-dateutil enum34

test_target:
	echo $(GC_USER)

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
rebuild_summary_db: clean_garmin_summary_db clean_summary_db build_garmin_summary_db

# download data files for the period specified by GC_DATE and GC_DAYS and build the dbs
create_dbs: download_garmin build_dbs

# update the exisitng dbs by downloading data files for dates after the last in the dbs and update the dbs
update_dbs: update_garmin


#
# Project maintainance targets
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
	for package in $(PYTHON_PACKAGES); do \
		pip install --upgrade  $$package; \
	done

deps:
	$(DEPS_SUDO) $(MAKE) install_deps

remove_deps: clean_deps_tcxparser
	for package in $(PYTHON_PACKAGES); do \
		pip uninstall -y $$package; \
	done

clean_deps:
	$(DEPS_SUDO) $(MAKE) remove_deps

clean:
	rm -rf *.pyc
	rm -rf Fit/*.pyc
	rm -rf HealthDB/*.pyc
	rm -rf GarminDB/*.pyc
	rm -rf FitBitDB/*.pyc
	rm -f $(BUGREPORT)


#
# Fitness System independant targets
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
# Garmin targets
#
garmin_profile:
	$(PYTHON) import_garmin.py -t1 --profile_dir "$(FIT_FILE_DIR)" --sqlite $(DB_DIR)

## test monitoring
test_import_monitoring: $(DB_DIR)
	python import_garmin.py -t1 --fit_input_file "$(MONITORING_FIT_FILES_DIR)/$(TEST_GC_ID).fit" --sqlite $(DB_DIR)

test_monitoring_file: $(TEST_DB_DIR)
	@if [ -z "$(TEST_DB_DIR)" ]; then echo "TEST_DB_DIR is not defined"; fi
	@if [ -f "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" ]; then \
		$(PYTHON) import_garmin.py -t1 --fit_input_file "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" --sqlite $(TEST_DB_DIR); \
	else \
		echo "Expecting " $(TEST_GC_ID).fit " to be found in " $(TEST_FILE_DIR) " but it contains:"; \
		ls -l "$(TEST_FILE_DIR)"; \
	fi

##  monitoring
GARMIN_MON_DB=$(DB_DIR)/garmin_monitoring.db
$(GARMIN_MON_DB): $(DB_DIR) garmin_profile import_monitoring

build_monitoring_db: $(GARMIN_MON_DB)

clean_monitoring_db:
	rm -f $(GARMIN_MON_DB)

$(MONITORING_FIT_FILES_DIR):
	mkdir -p $(MONITORING_FIT_FILES_DIR)

download_monitoring: $(MONITORING_FIT_FILES_DIR)
	$(PYTHON) download_garmin.py -d $(GC_DATE) -n $(GC_DAYS) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -m "$(MONITORING_FIT_FILES_DIR)"

import_monitoring: $(DB_DIR)
	for dir in $(shell ls -d $(FIT_FILE_DIR)/*Monitoring*/); do \
		$(PYTHON) import_garmin.py --fit_input_dir "$$dir" --sqlite $(DB_DIR); \
	done

download_new_monitoring: $(MONITORING_FIT_FILES_DIR) garmin_profile
	$(PYTHON) download_garmin.py -l --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -m "$(MONITORING_FIT_FILES_DIR)"

import_new_monitoring: download_new_monitoring
	for dir in $(shell ls -d $(FIT_FILE_DIR)/*Monitoring*/); do \
		$(PYTHON) import_garmin.py -l --fit_input_dir "$$dir" --sqlite $(DB_DIR); \
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
		$(PYTHON) import_garmin_activities.py -t1 --input_file "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" --sqlite $(TEST_DB_DIR); \
	else \
		echo "Expecting " $(TEST_GC_ID).fit " to be found in " $(TEST_FILE_DIR) " but it contains:"; \
		ls -l "$(TEST_FILE_DIR)"; \
	fi

test_import_details_json_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR)
	$(PYTHON) import_garmin_activities.py -t1 --input_file "$(ACTIVITES_FIT_FILES_DIR)/activity_details_$(TEST_GC_ID).json" --sqlite $(DB_DIR)

test_import_tcx_activities: $(TEST_DB_DIR) $(TEST_FILE_DIR)
	$(PYTHON) import_garmin_activities.py -t1 --input_file "$(TEST_FILE_DIR)/$(TEST_GC_ID).tcx" --sqlite $(TEST_DB_DIR)

test_import_json_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR)
	@if [ -z "$(TEST_DB_DIR)" ]; then echo "TEST_DB_DIR is not defined"; fi
	@if [ -f "$(TEST_FILE_DIR)/$(TEST_GC_ID).fit" ]; then \
		$(PYTHON) import_garmin_activities.py -t1 --input_file "$(ACTIVITES_FIT_FILES_DIR)/activity_$(TEST_GC_ID).json" --sqlite $(DB_DIR); \
	else \
		echo "Expecting " $(TEST_GC_ID).fit " to be found in " $(TEST_FILE_DIR) " but it contains:"; \
		ls -l "$(TEST_FILE_DIR)"; \
	fi
import_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR)
	$(PYTHON) import_garmin_activities.py --input_dir "$(ACTIVITES_FIT_FILES_DIR)" --sqlite $(DB_DIR)

import_new_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR) download_new_activities
	$(PYTHON) import_garmin_activities.py -l --input_dir "$(ACTIVITES_FIT_FILES_DIR)" --sqlite $(DB_DIR)

download_new_activities: $(ACTIVITES_FIT_FILES_DIR)
	$(PYTHON) download_garmin.py --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -a "$(ACTIVITES_FIT_FILES_DIR)" -c 10

download_all_activities: $(ACTIVITES_FIT_FILES_DIR)
	$(PYTHON) download_garmin.py --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -a "$(ACTIVITES_FIT_FILES_DIR)"

force_download_all_activities: $(ACTIVITES_FIT_FILES_DIR)
	$(PYTHON) download_garmin.py --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -a "$(ACTIVITES_FIT_FILES_DIR)" -o

## generic garmin
GARMIN_DB=$(DB_DIR)/garmin.db
$(GARMIN_DB): $(DB_DIR) garmin_profile garmin_config import_sleep import_weight import_rhr

build_garmin_db: $(GARMIN_DB)

clean_garmin_db:
	rm -f $(GARMIN_DB)

## sleep
$(SLEEP_FILES_DIR):
	mkdir -p $(SLEEP_FILES_DIR)

download_sleep: $(SLEEP_FILES_DIR)
	$(PYTHON) download_garmin.py -d $(GC_DATE) -n $(GC_DAYS) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -S "$(SLEEP_FILES_DIR)"

import_sleep: $(SLEEP_FILES_DIR)
	$(PYTHON) import_garmin.py --sleep_input_dir "$(SLEEP_FILES_DIR)" --sqlite $(DB_DIR)

download_new_sleep: $(SLEEP_FILES_DIR)
	$(PYTHON) download_garmin.py -l --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -S "$(SLEEP_FILES_DIR)"

import_new_sleep: download_new_sleep
	$(PYTHON) import_garmin.py -l --sleep_input_dir "$(SLEEP_FILES_DIR)" --sqlite $(DB_DIR)

## weight
$(WEIGHT_FILES_DIR):
	mkdir -p $(WEIGHT_FILES_DIR)

import_weight: download_weight
	$(PYTHON) import_garmin.py --weight_input_dir "$(WEIGHT_FILES_DIR)" --sqlite $(DB_DIR)

import_new_weight: download_new_weight
	$(PYTHON) import_garmin.py -l --weight_input_dir "$(WEIGHT_FILES_DIR)" --sqlite $(DB_DIR)

download_weight: $(DB_DIR) $(WEIGHT_FILES_DIR)
	$(PYTHON) download_garmin.py -d $(GC_DATE) -n $(GC_DAYS) --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -w "$(WEIGHT_FILES_DIR)"

download_new_weight: $(DB_DIR) $(WEIGHT_FILES_DIR)
	$(PYTHON) download_garmin.py -l --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -w "$(WEIGHT_FILES_DIR)"

## rhr
$(RHR_FILES_DIR):
	mkdir -p $(RHR_FILES_DIR)

import_rhr: download_rhr
	$(PYTHON) import_garmin.py --rhr_input_dir "$(RHR_FILES_DIR)" --sqlite $(DB_DIR)

import_new_rhr: download_new_rhr
	$(PYTHON) import_garmin.py -l --rhr_input_dir "$(RHR_FILES_DIR)" --sqlite $(DB_DIR)

download_rhr: $(DB_DIR) $(RHR_FILES_DIR)
	$(PYTHON) download_garmin.py -d $(GC_DATE) -n $(GC_DAYS) --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -r "$(RHR_FILES_DIR)"

download_new_rhr: $(DB_DIR) $(RHR_FILES_DIR)
	$(PYTHON) download_garmin.py -l --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -P "$(FIT_FILE_DIR)" -r "$(RHR_FILES_DIR)"

## digested garmin data
GARMIN_SUM_DB=$(DB_DIR)/garmin_summary.db
$(GARMIN_SUM_DB): $(DB_DIR) garmin_summary

build_garmin_summary_db: $(GARMIN_SUM_DB)

clean_garmin_summary_db:
	rm -f $(GARMIN_SUM_DB)

garmin_summary:
	$(PYTHON) analyze_garmin.py --analyze --dates --sqlite $(DB_DIR)

garmin_config:
	$(PYTHON) analyze_garmin.py -S$(DEFAULT_SLEEP_START),$(DEFAULT_SLEEP_STOP) --sqlite /Users/tgoetz/HealthData/DBs

#
# These operations work across all garmin dbs
#
update_garmin: import_new_monitoring import_new_activities import_new_weight import_new_sleep import_new_rhr garmin_summary

download_garmin: download_monitoring download_all_activities download_sleep download_weight download_rhr

build_garmin_dbs: build_garmin_db build_monitoring_db build_activities_db build_garmin_summary_db

clean_garmin_dbs: clean_garmin_db clean_garmin_summary_db clean_monitoring_db clean_activities_db


#
# FitBit targets
#
FITBIT_DB=$(DB_DIR)/fitbit.db
$(FITBIT_DB): $(DB_DIR) import_fitbit_file

clean_fitbit_db:
	rm -f $(FITBIT_DB)

$(FITBIT_FILE_DIR):
	mkdir -p $(FITBIT_FILE_DIR)

import_fitbit_file: $(DB_DIR) $(FITBIT_FILE_DIR)
	$(PYTHON) import_fitbit_csv.py $(UNITS_OPT) --input_dir "$(FITBIT_FILE_DIR)" --sqlite $(DB_DIR)

fitbit_summary: $(FITBIT_DB)
	$(PYTHON) analyze_fitbit.py --sqlite $(DB_DIR) --dates

fitbit_db: $(FITBIT_DB)


#
# MS Health targets
#
MSHEALTH_DB=$(DB_DIR)/mshealth.db
$(MSHEALTH_DB): $(DB_DIR) import_mshealth

clean_mshealth_db:
	rm -f $(MSHEALTH_DB)

$(MSHEALTH_FILE_DIR):
	mkdir -p $(MSHEALTH_FILE_DIR)

import_mshealth: $(DB_DIR) $(MSHEALTH_FILE_DIR)
	$(PYTHON) import_mshealth_csv.py $(UNITS_OPT) --input_dir "$(MSHEALTH_FILE_DIR)" --sqlite $(DB_DIR)

mshealth_summary: $(MSHEALTH_DB)
	$(PYTHON) analyze_mshealth.py --sqlite $(DB_DIR) --dates

mshealth_db: $(MSHEALTH_DB)


#
# test targets
#
test:
	export PROJECT_BASE=$(PROJECT_BASE) && $(MAKE) -C test


#
# bugreport target
#
bugreport:
	uname -a > $(BUGREPORT)
	which $(PYTHON) >> $(BUGREPORT)
	$(PYTHON) --version >> $(BUGREPORT) 2>&1
	echo $(PYTHON_PACKAGES)
	for package in $(PYTHON_PACKAGES); do \
		pip show $$package >> $(BUGREPORT); \
	done

.PHONY: all setup build_dbs rebuild_dbs clean clean_dbs test
