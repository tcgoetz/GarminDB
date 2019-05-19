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

clean_dbs: clean_mshealth_db clean_fitbit_db clean_garmin_dbs

# build dbs from already downloaded data files
build_dbs: garmin mshealth fitbit

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
	rm -rf *.log


#
# Fitness System independant targets
#
$(BACKUP_DIR):
	mkdir -p $(BACKUP_DIR)

EPOCH=$(shell date +'%s')
backup: $(BACKUP_DIR)
	zip -r $(BACKUP_DIR)/$(EPOCH)_dbs.zip $(DB_DIR)


#
# Garmin targets
#
garmin:
	$(PYTHON) garmin.py --all --download --import --analyze

update_garmin:
	$(PYTHON) garmin.py --all --download --import --analyze --latest

clean_garmin_dbs:
	$(PYTHON) garmin.py --delete_db



#
# FitBit target
#
fitbit:
	$(PYTHON) fitbit.py

clean_fitbit_db:
	$(PYTHON) fitbit.py --delete_db


#
# MS Health target
#
mshealth: $(MSHEALTH_DB)
	$(PYTHON) mshealth.py

clean_mshealth_db:
	$(PYTHON) mshealth.py --delete_db


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
