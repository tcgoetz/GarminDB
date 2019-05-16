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


#
# All third party Python packages needed to use the project. They will be installed with pip.
#
PYTHON_PACKAGES=sqlalchemy requests python-dateutil enum34 progressbar2


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

# download data files for the period specified in GarminConnectConfig.py and build the dbs
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

clean: test_clean
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
$(SUMMARY_DB): summary

summary: mshealth_summary fitbit_summary garmin_summary

clean_summary_db:
	rm -f $(SUMMARY_DB)

$(BACKUP_DIR):
	mkdir -p $(BACKUP_DIR)

EPOCH=$(shell date +'%s')
backup: $(BACKUP_DIR)
	zip -r $(BACKUP_DIR)/$(EPOCH)_dbs.zip $(DB_DIR)


#
# Garmin targets
#

##  monitoring
GARMIN_MON_DB=$(DB_DIR)/garmin_monitoring.db
$(GARMIN_MON_DB): import_monitoring

build_monitoring_db: $(GARMIN_MON_DB)

clean_monitoring_db:
	rm -f $(GARMIN_MON_DB)

download_monitoring:
	$(PYTHON) download_garmin.py --monitoring

import_monitoring:
	$(PYTHON) import_garmin.py --monitoring

download_new_monitoring:
	$(PYTHON) download_garmin.py --latest --monitoring

import_new_monitoring: download_new_monitoring
	$(PYTHON) import_garmin.py --latest --monitoring

## activities
GARMIN_ACT_DB=$(DB_DIR)/garmin_activities.db
$(GARMIN_ACT_DB): import_activities

build_activities_db: $(GARMIN_ACT_DB)

clean_activities_db:
	rm -f $(GARMIN_ACT_DB)

import_activities:
	$(PYTHON) import_garmin_activities.py

import_new_activities: download_new_activities
	$(PYTHON) import_garmin_activities.py --latest

download_new_activities:
	$(PYTHON) download_garmin.py --activities -c 10

download_all_activities:
	$(PYTHON) download_garmin.py --activities

force_download_all_activities:
	$(PYTHON) download_garmin.py --activities --overwite

## generic garmin
GARMIN_DB=$(DB_DIR)/garmin.db
$(GARMIN_DB): import_sleep import_weight import_rhr

build_garmin_db: $(GARMIN_DB)

clean_garmin_db:
	rm -f $(GARMIN_DB)

## sleep
download_sleep:
	$(PYTHON) download_garmin.py --sleep

import_sleep:
	$(PYTHON) import_garmin.py --sleep

download_new_sleep:
	$(PYTHON) download_garmin.py --latest --sleep

import_new_sleep: download_new_sleep
	$(PYTHON) import_garmin.py --latest --sleep

## weight
import_weight: # download_weight
	$(PYTHON) import_garmin.py --weight

import_new_weight: download_new_weight
	$(PYTHON) import_garmin.py --latest --weight

download_weight:
	$(PYTHON) download_garmin.py --weight

download_new_weight:
	$(PYTHON) download_garmin.py --latest --weight

## rhr
import_rhr: download_rhr
	$(PYTHON) import_garmin.py --rhr

import_new_rhr: download_new_rhr
	$(PYTHON) import_garmin.py --latest --rhr

download_rhr:
	$(PYTHON) download_garmin.py --rhr

download_new_rhr:
	$(PYTHON) download_garmin.py --latest --rhr

## digested garmin data
GARMIN_SUM_DB=$(DB_DIR)/garmin_summary.db
$(GARMIN_SUM_DB): garmin_summary

build_garmin_summary_db: $(GARMIN_SUM_DB)

clean_garmin_summary_db:
	rm -f $(GARMIN_SUM_DB)

garmin_summary:
	$(PYTHON) analyze_garmin.py --analyze --dates

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
$(FITBIT_DB): import_fitbit

clean_fitbit_db:
	rm -f $(FITBIT_DB)

import_fitbit:
	$(PYTHON) import_fitbit_csv.py

fitbit_summary: $(FITBIT_DB)
	$(PYTHON) analyze_fitbit.py --dates

fitbit_db: $(FITBIT_DB)


#
# MS Health targets
#
MSHEALTH_DB=$(DB_DIR)/mshealth.db
$(MSHEALTH_DB): import_mshealth

clean_mshealth_db:
	rm -f $(MSHEALTH_DB)

import_mshealth:
	$(PYTHON) import_mshealth_csv.py

mshealth_summary:
	$(PYTHON) analyze_mshealth.py --dates

mshealth_db: $(MSHEALTH_DB)


#
# test targets
#
test:
	export PROJECT_BASE=$(PROJECT_BASE) && $(MAKE) -C test

test_clean:
	export PROJECT_BASE=$(PROJECT_BASE) && $(MAKE) -C test clean


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
