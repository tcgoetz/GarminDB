
HEALTH_DATA_DIR=$(HOME)/HealthData
FIT_FILE_DIR=$(HEALTH_DATA_DIR)/FitFiles
FITBIT_FILE_DIR=$(HEALTH_DATA_DIR)/FitBitFiles
MSHEALTH_FILE_DIR=$(HEALTH_DATA_DIR)/MSHealth
DB_DIR=$(HEALTH_DATA_DIR)/DBs
BACKUP_DIR=$(HEALTH_DATA_DIR)/Backups

MONITORING_FIT_FILES_DIR=$(FIT_FILE_DIR)/2017_Monitoring
MEW_MONITORING_FIT_FILES_DIR=$(FIT_FILE_DIR)/Incoming


TEST_DB=/tmp/test.db

$(DB_DIR):
	mkdir -p $(DB_DIR)

$(BACKUP_DIR):
	mkdir -p $(BACKUP_DIR)

deps:
	sudo pip install sqlalchemy

clean:
	rm -rf *.pyc
	rm -rf Fit/*.pyc
	rm -rf HealthDB/*.pyc
	rm -rf GarminDB/*.pyc
	rm -rf FitBitDB/*.pyc

TEST_DB_PATH=/tmp/DBs
$(TEST_DB_PATH):
	mkdir -p $(TEST_DB_PATH)

test_monitoring_clean:
	rm -rf $(TEST_DB_PATH)

TEST_FIT_FILE_DIR=$(HEALTH_DATA_DIR)/TestFitFiles
test_monitoring_file: $(TEST_DB_PATH)
#	python import_garmin_fit.py -e --input_file "$(TEST_FIT_FILE_DIR)/15053994801.fit" --dbpath $(TEST_DB_PATH)
#	python import_garmin_fit.py -e --input_file "$(TEST_FIT_FILE_DIR)/15044952621.fit" --dbpath $(TEST_DB_PATH)
	python import_garmin_fit.py -e --input_dir "$(TEST_FIT_FILE_DIR)" --dbpath $(TEST_DB_PATH)
	python analyze_garmin.py --dbpath $(TEST_DB_PATH) --years --months 2017 --days 2017 --summary

clean_monitoring:
	rm -f $(DB_DIR)/garmin_monitoring.db

import_monitoring: $(DB_DIR)
	python import_garmin_fit.py -e --input_dir "$(MONITORING_FIT_FILES_DIR)" --dbpath $(DB_DIR)

import_new_monitoring: $(DB_DIR)
	python import_garmin_fit.py -e --input_dir "$(MEW_MONITORING_FIT_FILES_DIR)" --dbpath $(DB_DIR)

clean_garmin_summary:
	rm -f $(DB_DIR)/garmin_monitoring_summary.db

garmin_summary:
	python analyze_garmin.py --dbpath $(DB_DIR) --years --months 2017 --days 2017 --summary
	python analyze_garmin.py --dbpath $(DB_DIR) --years --months 2018 --days 2018 --summary

new_garmin: import_new_monitoring clean_garmin_summary garmin_summary

clean_garmin: clean_garmin_summary clean_monitoring


import_fitbit_file: $(DB_DIR)
	python import_fitbit_csv.py -e --input_file "$(FITBIT_FILE_DIR)/2015_fitbit_all.csv" --dbpath $(DB_DIR)

clean_fitbit:
	rm -f $(DB_DIR)/fitbit.db


import_mshealth_file: $(DB_DIR)
	python import_mshealth_csv.py -e --input_file "$(MSHEALTH_FILE_DIR)/Daily_Summary_20151230_20161004.csv" --dbpath $(DB_DIR)
	python import_mshealth_csv.py -e --input_file "$(MSHEALTH_FILE_DIR)/Daily_Summary_20160101_20161231.csv" --dbpath $(DB_DIR)
	python import_mshealth_csv.py -e --input_file "$(MSHEALTH_FILE_DIR)/Daily_Summary_20170101_20170226.csv" --dbpath $(DB_DIR)

clean_mshealth:
	rm -f $(DB_DIR)/mshealth.db


EPOCH=$(shell date +'%s')
backup: $(BACKUP_DIR)
	zip -r $(BACKUP_DIR)/$(EPOCH)_dbs.zip $(DB_DIR)
