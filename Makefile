#
# This Makefile handles downloading data from Garmin Connect and generating SQLite DB files from that data. The Makefile targets handle the dependancies
# between downloading and generating varies types of data. It wraps the core Python scripts and runs them with appropriate parameters.
#
export PROJECT_BASE=$(CURDIR)
export VENV=$(PROJECT_BASE)/.venv

include defines.mk

$(info $$PROJECT_BASE is [${PROJECT_BASE}])
$(info $$VENV is [${VENV}])
$(info $$PLATFORM is [${PLATFORM}])
$(info $$SHELL is [${SHELL}])

export PIP_PATH=$(VENV)/bin/$(PIP)
$(info $$PIP_PATH is [${PIP_PATH}])
export PYTHON_PATH=$(VENV)/bin/$(PYTHON)
$(info $$PYTHON_PATH is [${PYTHON_PATH}])
export GARMINDB_CLI=$(VENV)/bin/garmindb_cli.py
$(info $$GARMINDB_CLI is [${GARMINDB_CLI}])


#
# Master targets
#
all: update_dbs

# install all needed code
setup_repo: $(CONF_DIR)/GarminConnectConfig.json $(VENV) submodules_update

setup_install: version_check deps devdeps install_all

setup: setup_repo setup_install

setup_pipeline: devdeps install_all

clean_dbs: clean_mshealth_db clean_fitbit_db clean_garmin_dbs

# Use for an intial download or when the start dates have been changed.
download_all: download_all_garmin

# build dbs from already downloaded data files
build_dbs: build_garmin mshealth fitbit
create_dbs: garmin mshealth fitbit
create_copy_dbs: copy_garmin mshealth fitbit

# delete the exisitng dbs and build new dbs from already downloaded data files
rebuild_dbs: rebuild_fitbit rebuild_mshealth rebuild_garmin

# update the exisitng dbs by downloading data files for dates after the last in the dbs and update the dbs
update_dbs: update_garmin
update_dbs_bin: update_garmin_bin
update_copy_dbs: copy_garmin_latest


#
# Project maintainance targets
#
SUBMODULES=Fit Tcx utilities
SUBDIRS=fitbitdb garmindb healthdb mshealthdb

$(CONF_DIR):
	mkdir $(CONF_DIR)

$(CONF_DIR)/GarminConnectConfig.json: $(CONF_DIR)
	cp $(PROJECT_BASE)/garmindb/GarminConnectConfig.json.example $(CONF_DIR)/GarminConnectConfig.json

activate_venv: $(VENV)
	source $(VENV)/bin/activate

update_venv:
	$(VENV)/bin/python -m pip install --upgrade pip

$(VENV):
	$(SYS_PYTHON_PATH) -m venv --upgrade-deps $(VENV)

clean_venv:
	echo "Cleaning venv"
	rm -rf $(VENV)

version_check:
	python -c 'import sys; import garmindb.version; garmindb.version.python_dev_version_check(sys.argv[0])'

update: submodules_update
	git pull

submodules_update:
	git submodule init
	git submodule update


publish_check: build
	$(PYTHON_PATH) -m twine check dist/*

publish: clean publish_check
	$(PYTHON_PATH) -m twine upload dist/* --verbose

builddeps: $(VENV) devdeps

build: builddeps
	cp pyproject.toml.in pyproject.toml
	uv add -r requirements.txt --frozen
	$(PYTHON_PATH) -m build

build_clean:
	echo "Cleaning build"
	rm -rf pyproject.toml
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	rm -rf uv.lock

$(PROJECT_BASE)/dist/$(MODULE)-*.whl: build

install: $(PROJECT_BASE)/dist/$(MODULE)-*.whl
	$(PIP_PATH) install --upgrade $(PROJECT_BASE)/dist/$(MODULE)-*.whl

$(SUBMODULES:%=%-install):
	$(MAKE) -C $(subst -install,,$@) install

install_all: $(SUBMODULES:%=%-install) install

install_pip:
	$(PIP_PATH) install --upgrade garmindb

$(SUBMODULES:%=%-install_pip):
	$(MAKE) -C $(subst -install_pip,,$@) install_pip

install_pip_all: $(SUBMODULES:%=%-install_pip) install_pip

reinstall: clean $(PROJECT_BASE)/dist/$(MODULE)-*.whl
	$(PIP_PATH) install --upgrade --force-reinstall --no-deps $(PROJECT_BASE)/dist/$(MODULE)-*.whl

reinstall_all: clean builddeps uninstall_all install_all

$(SUBMODULES:%=%-uninstall):
	$(MAKE) -C $(subst -uninstall,,$@) uninstall

uninstall:
	$(PIP_PATH) uninstall -y $(MODULE)

uninstall_all: uninstall $(SUBMODULES:%=%-uninstall)

republish_plugins:
	$(MAKE) -C Plugins republish_plugins

$(SUBMODULES:%=%-deps):
	$(MAKE) -C $(subst -deps,,$@) deps

requirements.txt:
	$(PIP_PATH) freeze -r requirements.in > requirements.txt

dev-requirements.txt:
	$(PIP_PATH) freeze -r dev-requirements.in > dev-requirements.txt

Jupyter/requirements.txt:
	$(PIP_PATH) freeze -r Jupyter/requirements.in > Jupyter/requirements.txt

Jupyter/requirements_graphs.txt:
	$(PIP_PATH) freeze -r Jupyter/requirements_graphs.in > Jupyter/requirements_graphs.txt

update_pip_packages:
	$(PIP_PATH) list --outdated | egrep -v "Package|---" | cut -d' ' -f1 | xargs pip install --upgrade

deps: $(SUBMODULES:%=%-deps)
	$(PIP_PATH) install --upgrade --requirement requirements.txt

$(SUBMODULES:%=%-devdeps):
	$(MAKE) -C $(subst -devdeps,,$@) devdeps

devdeps: $(SUBMODULES:%=%-devdeps)
	$(PIP_PATH) install --upgrade --requirement dev-requirements.txt

graphdeps:
	$(PIP_PATH) install --upgrade --requirement Jupyter/requirements_graphs.txt

jupiterdeps: graphdeps
	$(PIP_PATH) install --upgrade --requirement Jupyter/requirements.txt

alldeps: update_pip_packages deps devdeps jupiterdeps

$(SUBMODULES:%=%-remove_deps):
	$(MAKE) -C $(subst -remove_deps,,$@) remove_deps

remove_deps: $(SUBMODULES:%=%-remove_deps)
	$(PIP_PATH) uninstall -y --requirement requirements.txt
	$(PIP_PATH) uninstall -y --requirement dev-requirements.txt
	$(PIP_PATH) uninstall -y --requirement Jupyter/requirements.txt
	$(PIP_PATH) uninstall -y --requirement Jupyter/requirements_graphs.txt

clean_deps: remove_deps

$(SUBMODULES:%=%-clean):
	$(MAKE) -C $(subst -clean,,$@) clean

$(SUBDIRS:%=%-clean):
	rm -f garmindb/$(subst -clean,,$@)/*.pyc
	rm -rf garmindb/$(subst -clean,,$@)/__pycache__

clean: $(SUBMODULES:%=%-clean) $(SUBDIRS:%=%-clean) test_clean build_clean
	echo "Cleaning project"
	rm -f *.pyc
	rm -f *.log
	rm -f scripts/*.log
	rm -f Jupyter/*.log
	rm -f *.spec
	rm -f *.zip
	rm -f *.png
	rm -f *stats.txt
	rm -f scripts/*stats.txt
	rm -f Jupyter/*stats.txt
	rm -rf __pycache__

realclean: clean clean_venv
	echo "Done realclean"

checkup: update_garmin
	garmindb_checkup.py --battery
	garmindb_checkup.py --goals

# define CHECKUP_COURSE_ID in my-defines.mk
checkup_course:
	garmin_checkup.py --course $(CHECKUP_COURSE_ID)

daily: all checkup graph_yesterday

#
# Garmin targets
#
backup:
	$(GARMINDB_CLI) --backup

download_all_garmin:
	$(GARMINDB_CLI) --all --download

redownload_garmin_activities:
	$(GARMINDB_CLI) --activities --download --overwrite

garmin:
	$(GARMINDB_CLI) --all --download --import --analyze

build_garmin:
	$(GARMINDB_CLI) --all --import --analyze

rebuild_garmin:
	$(GARMINDB_CLI) --rebuild_db

build_garmin_monitoring:
	$(GARMINDB_CLI) --monitoring --import --analyze

import_garmin_monitoring:
	$(GARMINDB_CLI) --monitoring --import --latest

build_garmin_activities:
	$(GARMINDB_CLI) --activities --import --analyze

copy_garmin_settings:
	$(GARMINDB_CLI) --copy

copy_garmin:
	$(GARMINDB_CLI) --all --copy --import --analyze

update_garmin:
	$(GARMINDB_CLI) --all --download --import --analyze --latest

update_garmin_activities:
	$(GARMINDB_CLI) --activities --download --import --analyze --latest

copy_garmin_latest:
	$(GARMINDB_CLI) --all --copy --import --analyze --latest

# define EXPORT_ACTIVITY_ID in my-defines.mk
export_activity:
	$(GARMINDB_CLI) --export-activity $(EXPORT_ACTIVITY_ID)

# define EXPORT_ACTIVITY_ID in my-defines.mk
basecamp_activity:
	$(GARMINDB_CLI) --basecamp-activity $(EXPORT_ACTIVITY_ID)

# define EXPORT_ACTIVITY_ID in my-defines.mk
google_earth_activity:
	$(GARMINDB_CLI) --google-earth-activity $(EXPORT_ACTIVITY_ID)

clean_garmin_dbs:
	$(GARMINDB_CLI) --delete_db --all

clean_garmin_monitoring_dbs:
	$(GARMINDB_CLI) --delete_db --monitoring

clean_garmin_activities_dbs:
	$(GARMINDB_CLI) --delete_db --activities


#
# FitBit target
#
fitbit:
	fitbit.py

clean_fitbit_db:
	fitbit.py --delete_db

rebuild_fitbit:
	fitbit.py --rebuild_db


#
# MS Health target
#
mshealth: $(MSHEALTH_DB)
	mshealth.py

clean_mshealth_db:
	mshealth.py --delete_db

rebuild_mshealth:
	mshealth.py --rebuild_db


#
# test targets
#
$(SUBMODULES:%=%-test):
	$(MAKE) -C $(subst -test,,$@) test

test: flake8 $(SUBMODULES:%=%-test)
	$(MAKE) -C test all

$(SUBMODULES:%=%-verify_commit):
	$(MAKE) -C $(subst -verify_commit,,$@) verify_commit

verify_commit: $(SUBMODULES:%=%-test)
	$(MAKE) -C test verify_commit

$(SUBMODULES:%=%-test_clean):
	$(MAKE) -C $(subst -test_clean,,$@) clean

test_clean:
	$(MAKE) -C test clean

$(SUBMODULES:%=%-flake8):
	$(MAKE) -C $(subst -flake8,,$@) flake8

flake8: $(SUBMODULES:%=%-flake8)
	$(PYTHON_PATH) -m flake8 garmindb/*.py garmindb/garmindb/*.py garmindb/summarydb/*.py garmindb/fitbitdb/*.py garmindb/mshealthdb/*.py --max-line-length=180 --ignore=E203,E221,E241,W503

regression_test_run: flake8 rebuild_dbs
	grep ERROR garmindb.log || [ $$? -eq 1 ]

regression_test: clean regression_test_run test


#
# bugreport target
#
bugreport:
	./bugreport.sh


merge_develop:
	git fetch --all && git merge remotes/origin/develop

.PHONY: all setup install install_all uninstall uninstall_all update deps create_dbs rebuild_dbs update_dbs clean clean_dbs test zip_packages release clean test test_clean daily flake8 $(SUBMODULES:%=%-flake8) merge_develop
