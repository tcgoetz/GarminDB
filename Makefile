


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
else
	# store the username and password in ~/.garmindb.conf ?
endif


HEALTH_DATA_DIR=$(HOME)/HealthData
FIT_FILE_DIR=$(HEALTH_DATA_DIR)/FitFiles
FITBIT_FILE_DIR=$(HEALTH_DATA_DIR)/FitBitFiles
MSHEALTH_FILE_DIR=$(HEALTH_DATA_DIR)/MSHealth
DB_DIR=$(HEALTH_DATA_DIR)/DBs
TEST_DB_DIR=/tmp/DBs
BACKUP_DIR=$(HEALTH_DATA_DIR)/Backups
MONITORING_FIT_FILES_DIR=$(FIT_FILE_DIR)/$(YEAR)_Monitoring
MEW_MONITORING_FIT_FILES_DIR=$(FIT_FILE_DIR)/Incoming
ACTIVITES_FIT_FILES_DIR=$(FIT_FILE_DIR)/Activities
ACTIVITES_TCX_FILES_DIR=$(HEALTH_DATA_DIR)/TcxFiles

BIN_DIR=$(PWD)/bin

TEST_DB=$(TMPDIR)/test.db

DEFAULT_SLEEP_START=22:00
DEFAULT_SLEEP_STOP=06:00

#
# Master targets
#
all: import_new_monitoring scrape_new_weight

setup: update deps

update: submodules_update
	git pull --rebase

submodules_update:
	git submodule init
	git submodule update

deps: install_geckodriver
	sudo pip install --upgrade sqlalchemy
	sudo pip install --upgrade selenium

clean_deps: clean_geckodriver
	sudo pip uninstall sqlalchemy
	sudo pip uninstall selenium

clean:
	rm -rf *.pyc
	rm -rf Fit/*.pyc
	rm -rf HealthDB/*.pyc
	rm -rf GarminDB/*.pyc
	rm -rf FitBitDB/*.pyc


#
# Manage dependancies for scraping
#
$(BIN_DIR):
	mkdir -p $(BIN_DIR)

GECKO_DRIVER_URL=https://github.com/mozilla/geckodriver/releases/download/v0.19.1/
ifeq ($(OS), Darwin)
	GECKO_DRIVER_FILE=geckodriver-v0.19.1-macos.tar.gz
else ifeq ($(OS), Linux)
	ifeq ($(ARCH), x86_64)
		GECKO_DRIVER_FILE=geckodriver-v0.19.1-linux64.tar.gz
	else
		GECKO_DRIVER_FILE=geckodriver-v0.19.1-linux32.tar.gz
	endif
endif
install_geckodriver: $(BIN_DIR)
	curl -L $(GECKO_DRIVER_URL)/$(GECKO_DRIVER_FILE) | tar -C $(BIN_DIR) -x -z -f -

clean_geckodriver:
	rm -f $(BIN_DIR)/geckodriver*


#
# Fitness System independant
#
SUMMARY_DB=$(DB_DIR)/summary.db
$(SUMMARY_DB): $(DB_DIR)

rebuild_dbs: clean_dbs fitbit_db mshealth_db garmin_dbs

clean_dbs: clean_mshealth_db clean_fitbit_db clean_garmin_dbs clean_summary_db

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

## test monitoring
$(TEST_DB_DIR):
	mkdir -p $(TEST_DB_DIR)

test_monitoring_clean:
	rm -rf $(TEST_DB_DIR)

TEST_FIT_FILE_DIR=$(HEALTH_DATA_DIR)/TestFitFiles
test_monitoring_file: $(TEST_DB_DIR)
#	python import_garmin_fit.py -e --input_file "$(TEST_FIT_FILE_DIR)/15044952621.fit" --dbpath $(TEST_DB_DIR)
	python import_garmin_fit.py -t -e --input_dir "$(TEST_FIT_FILE_DIR)" --sqlite $(TEST_DB_DIR) && \
	python analyze_garmin.py --analyze --dates  --sqlite $(TEST_DB_DIR)

##  monitoring
GARMIN_MON_DB=$(DB_DIR)/garmin_monitoring.db
$(GARMIN_MON_DB): $(DB_DIR) import_monitoring

clean_monitoring_db:
	rm -f $(GARMIN_MON_DB)

$(MONITORING_FIT_FILES_DIR):
	mkdir -p $(MONITORING_FIT_FILES_DIR)

$(MEW_MONITORING_FIT_FILES_DIR):
	mkdir -p $(MEW_MONITORING_FIT_FILES_DIR)

scrape_monitoring: $(MEW_MONITORING_FIT_FILES_DIR)
	python scrape_garmin.py -d $(GC_DATE) -n $(GC_DAYS) -u $(GC_USER) -p $(GC_PASSWORD)  -m "$(MEW_MONITORING_FIT_FILES_DIR)"

import_monitoring: $(DB_DIR)
	for dir in $(shell ls -d $(FIT_FILE_DIR)/*Monitoring*/); do \
		python import_garmin_fit.py -e --input_dir "$(MONITORING_FIT_FILES_DIR)" --sqlite $(DB_DIR); \
	done

scrape_new_monitoring: $(MEW_MONITORING_FIT_FILES_DIR)
	python scrape_garmin.py -l --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD)  -m "$(MEW_MONITORING_FIT_FILES_DIR)"

import_new_monitoring: scrape_new_monitoring $(MONITORING_FIT_FILES_DIR)
	if ls $(MEW_MONITORING_FIT_FILES_DIR)/*.fit 1> /dev/null 2>&1; then \
		python import_garmin_fit.py -e --input_dir "$(MEW_MONITORING_FIT_FILES_DIR)" --sqlite $(DB_DIR) && \
		mv $(MEW_MONITORING_FIT_FILES_DIR)/*.fit $(MONITORING_FIT_FILES_DIR)/.; \
	fi

## weight
scrape_weight: $(DB_DIR)
	python scrape_garmin.py -d $(GC_DATE) -n $(GC_DAYS) --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -w

scrape_new_weight: $(DB_DIR)
	python scrape_garmin.py -l --sqlite $(DB_DIR) -u $(GC_USER) -p $(GC_PASSWORD) -w

## activities
GARMIN_ACT_DB=$(DB_DIR)/garmin_activities.db
$(GARMIN_ACT_DB): $(DB_DIR) import_activities

clean_activities_db:
	rm -f $(GARMIN_ACT_DB)

$(ACTIVITES_FIT_FILES_DIR):
	mkdir -p $(ACTIVITES_FIT_FILES_DIR)

$(ACTIVITES_TCX_FILES_DIR):
	mkdir -p $(ACTIVITES_TCX_FILES_DIR)

import_activities: $(DB_DIR) $(ACTIVITES_FIT_FILES_DIR)
	python import_garmin_activities.py -e --input_dir "$(ACTIVITES_FIT_FILES_DIR)" --sqlite $(DB_DIR)

download_new_activities: $(ACTIVITES_FIT_FILES_DIR)
	python garmin-connect-export/gcexport.py -c 50 -f original --unzip --username $(GC_USER) --password $(GC_PASSWORD) -d "$(ACTIVITES_FIT_FILES_DIR)"

download_all_activities: $(ACTIVITES_FIT_FILES_DIR)
	python garmin-connect-export/gcexport.py -c all -f original --unzip --username $(GC_USER) --password $(GC_PASSWORD) -d "$(ACTIVITES_FIT_FILES_DIR)"

download_activities_tcx: $(ACTIVITES_TCX_FILES_DIR)
	python garmin-connect-export/gcexport.py -c all -f tcx --unzip --username $(GC_USER) --password $(GC_PASSWORD) -d "$(ACTIVITES_TCX_FILES_DIR)"

## generic garmin
GARMIN_DB=$(DB_DIR)/garmin.db
$(GARMIN_DB): $(DB_DIR) garmin_config scrape_new_weight

clean_garmin_dbs: clean_garmin_summary_db clean_monitoring_db
	rm -f $(GARMIN_DB)

GARMIN_SUM_DB=$(DB_DIR)/garmin_summary.db
$(GARMIN_SUM_DB): $(DB_DIR) garmin_summary

clean_garmin_summary_db:
	rm -f $(GARMIN_SUM_DB)

garmin_summary:
	python analyze_garmin.py --analyze --dates --sqlite $(DB_DIR)

new_garmin: import_new_monitoring garmin_summary

garmin_config:
	python analyze_garmin.py -S$(DEFAULT_SLEEP_START),$(DEFAULT_SLEEP_STOP)  --sqlite /Users/tgoetz/HealthData/DBs

#garmin_dbs: $(GARMIN_DB) $(GARMIN_MON_DB) $(GARMIN_ACT_DB) $(GARMIN_SUM_DB)
garmin_dbs: $(GARMIN_DB) $(GARMIN_MON_DB) $(GARMIN_SUM_DB)


#
# FitBit
#
FITBIT_DB=$(DB_DIR)/fitbit.db
$(FITBIT_DB): $(DB_DIR) import_fitbit_file

clean_fitbit_db:
	rm -f $(FITBIT_DB)

import_fitbit_file: $(DB_DIR)
	python import_fitbit_csv.py -e --input_file "$(FITBIT_FILE_DIR)/2015_fitbit_all.csv" --sqlite $(DB_DIR)

fitbit_summary: $(FITBIT_DB)
	python analyze_fitbit.py --sqlite $(DB_DIR) --years --months 2015 --days 2015

fitbit_db: $(FITBIT_DB)


#
# MS Health
#
MSHEALTH_DB=$(DB_DIR)/mshealth.db
$(MSHEALTH_DB): $(DB_DIR) import_mshealth_file import_healthvault_file

clean_mshealth_db:
	rm -f $(MSHEALTH_DB)

import_mshealth_file: $(DB_DIR)
	python import_mshealth_csv.py -e --input_file "$(MSHEALTH_FILE_DIR)/Daily_Summary_20151230_20161004.csv" --sqlite $(DB_DIR) -m
	python import_mshealth_csv.py -e --input_file "$(MSHEALTH_FILE_DIR)/Daily_Summary_20160101_20161231.csv" --sqlite $(DB_DIR) -m
	python import_mshealth_csv.py -e --input_file "$(MSHEALTH_FILE_DIR)/Daily_Summary_20170101_20170226.csv" --sqlite $(DB_DIR) -m

import_healthvault_file: $(DB_DIR)
	python import_mshealth_csv.py -e --input_file "$(MSHEALTH_FILE_DIR)/HealthVault_Weight_20150106_20160315.csv" --sqlite $(DB_DIR) -v

mshealth_summary: $(MSHEALTH_DB)
	python analyze_mshealth.py --sqlite $(DB_DIR) --years --months 2015 --days 2015
	python analyze_mshealth.py --sqlite $(DB_DIR) --years --months 2016 --days 2016

mshealth_db: $(MSHEALTH_DB)
