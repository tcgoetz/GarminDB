
-include $(PROJECT_BASE)/my-defines.mk

CONF_DIR=$(HOME)/.GarminDb

#
# Handle multiple Python installs. What python are we using?
#
PLATFORM=$(shell uname)

ifeq ($(PLATFORM), Linux)

SHELL = /usr/bin/bash
TIME ?= $(shell which time)

else ifeq ($(PLATFORM), Darwin) # MacOS

SHELL ?= /usr/bin/bash
TIME ?= time

else

TIME ?= $(shell which time)

endif

PYTHON ?= python3
# what python should the venv be based on?
SYS_PYTHON_PATH ?= $(shell which python3)
PIP ?= pip3


ifeq ($(PYTHON),)
$(error Python not found)
endif
ifeq ($(PIP),)
$(error pip not found)
endif

MODULE=garmindb

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

export MODULE SHELL TIME PLATFORM PYTHON PIP FLAKE8
