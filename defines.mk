
#
# What python are we using?
#
PYTHON=python

#
# Directories where data is stored
#
HEALTH_DATA_DIR=$(HOME)/HealthData
DB_DIR=$(HEALTH_DATA_DIR)/DBs
BACKUP_DIR=$(HEALTH_DATA_DIR)/Backups


#
# Install Python dependancies as root (as opposed to installing as the user)?
#
INSTALL_DEPS_TO_SYSTEM ?= y

#
# File ID for test activities
#
TEST_GC_ID ?= 10724054307
