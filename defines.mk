
#
# What python are we using?
#
PYTHON=python

#
# Directories where data is stored
#
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

#
# System supplied temp file directory
#
TMPDIR = $(shell mktemp -d)

TEST_FILE_DIR=$(HOME)/Downloads
TEST_DB_DIR=$(TMPDIR)

#
# Install Python dependancies as root (as opposed to installing as the user)?
#
INSTALL_DEPS_TO_SYSTEM ?= y

#
# File ID for test activities
#
TEST_GC_ID ?= 10724054307

#
# Are we metric or english units?
#
# define UNITS_OPT="" for metric
UNITS_OPT ?= "-e"

#
# Default values used for start and end of the sleep period
#
DEFAULT_SLEEP_START=22:00
DEFAULT_SLEEP_STOP=06:00

#
# File name to use when generating a bug report.
#
BUGREPORT=bugreport.txt
