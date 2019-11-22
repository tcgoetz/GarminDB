
#
# What python are we using?
#
PYTHON2=/usr/bin/python
#PYTHON3=/usr/bin/python3
PYTHON3=/usr/local/bin/python3
#PYTHON=${PYTHON2}
PYTHON=${PYTHON3}

PIP3=/usr/local/bin/pip3
PIP=${PIP3}
export PYTHON PIP

#
# Directories where data is stored
#
HEALTH_DATA_DIR=$(HOME)/HealthData
DB_DIR=$(HEALTH_DATA_DIR)/DBs
BACKUP_DIR=$(HEALTH_DATA_DIR)/Backups


#
# File ID for test activities
#
TEST_GC_ID ?= 10724054307
