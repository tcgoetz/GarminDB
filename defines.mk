
-include my-defines.mk

CONF_DIR=$(HOME)/.GarminDb

#
# Handle multiple Python installs. What python are we using?
#
PLATFORM=$(shell uname)

ifeq ($(PLATFORM), Linux)

SHELL=/usr/bin/bash
TIME ?= $(shell which time)
YESTERDAY = $(shell date --date yesterday +"%m/%d/%Y")

else ifeq ($(PLATFORM), Darwin) # MacOS

SHELL=/usr/local/bin/bash
TIME ?= time
YESTERDAY = $(shell date -v-1d +"%m/%d/%Y")

else

TIME ?= $(shell which time)

endif


# HEALTH_DATA_DIR=$(shell python3 -c 'from garmindb import ConfigManager; print(ConfigManager.get_base_dir())')

# PYTHON3=$(shell which python3)
PYTHON3=python3
# PIP3=$(shell which pip3)
PIP3=pip3

PYTHON ?= $(PYTHON3)
PIP ?= $(PIP3)


ifeq ($(PYTHON),)
$(error Python not found)
endif
ifeq ($(PIP),)
$(error pip not found)
endif


export SHELL TIME PLATFORM PYTHON PIP YESTERDAY FLAKE8
