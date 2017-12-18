
HEALTH_DATA_DIR=$(HOME)/HealthData
FIT_FILE_DIR=$(HEALTH_DATA_DIR)/FitFiles
DB_DIR=$(HEALTH_DATA_DIR)/DBs
BACKUP_DIR=$(HEALTH_DATA_DIR)/Backups

MONITORING_FIT_FILES_DIR=$(FIT_FILE_DIR)/2017_Monitoring
MONITORING_DB=$(DB_DIR)/garmin_monitoring.db


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

test_monitoring_clean:
	rm -f $(MONITORING_DB)

TEST_MONITORING_FILE=15080913324.fit
test_monitoring_file: $(DB_DIR)
	python import.py --input_file "$(MONITORING_FIT_FILES_DIR)/$(TEST_FILE)" --database $(MONITORING_DB)
	python analyze.py --database $(MONITORING_DB) --years --months 2017 --days 2017

import_monitoring: $(DB_DIR)
	python import.py --input_dir "$(MONITORING_FIT_FILES_DIR)" --database $(MONITORING_DB)
	python analyze.py --database $(MONITORING_DB) --years --months 2017 --days 2017

EPOCH=$(shell date +'%s')
backup: $(BACKUP_DIR)
	zip -r $(BACKUP_DIR)/$(EPOCH)_dbs.zip $(DB_DIR)
