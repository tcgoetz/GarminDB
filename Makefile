
HEALTH_DATA_DIR=$(HOME)/HealthData
FIT_FILE_DIR=$(HEALTH_DATA_DIR)/FitFiles
DB_DIR=$(HEALTH_DATA_DIR)/DBs
BACKUP_DIR=$(HEALTH_DATA_DIR)/Backups

MONITORING_FIT_FILES_DIR=$(FIT_FILE_DIR)/2017_Monitoring


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
	rm -rf GarminSqlite/*.pyc

TEST_DB_PATH=/tmp/DBs
test_monitoring_clean:
	rm -rf $(TEST_DB_PATH)

#TEST_MONITORING_FILE=15080913324.fit
TEST_MONITORING_FILE=10036777080.fit
test_monitoring_file: $(DB_DIR)
	mkdir -p $(TEST_DB_PATH)
	python import.py --input_file "$(MONITORING_FIT_FILES_DIR)/$(TEST_MONITORING_FILE)" --dbpath $(TEST_DB_PATH)
	python analyze.py --dbpath $(TEST_DB_PATH) --years --months 2017 --days 2017 --summary

clean_monitoring:
	rm -f $(DB_DIR)/garmin_monitoring.db

import_monitoring: $(DB_DIR)
	python import.py --input_dir "$(MONITORING_FIT_FILES_DIR)" --dbpath $(DB_DIR)

clean_summary:
	rm -f $(DB_DIR)/garmin_monitoring_summary.db

summary:
	python analyze.py --dbpath $(DB_DIR) --years --months 2017 --days 2017 --summary

EPOCH=$(shell date +'%s')
backup: $(BACKUP_DIR)
	zip -r $(BACKUP_DIR)/$(EPOCH)_dbs.zip $(DB_DIR)
