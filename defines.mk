
-include my-defines.mk

DIST=dist

PLATFORM=$(shell uname)

#
# Handle multiple Python installs. What python are we using?
#

ifeq ($(PLATFORM), Linux)

TIME ?= $(shell which time)
YESTERDAY = $(shell date --date yesterday +"%m/%d/%Y")
PYTHON2=$(shell which python)

else ifeq ($(PLATFORM), Darwin) # MacOS

TIME ?= time
YESTERDAY = $(shell date -v-1d +"%m/%d/%Y")
PYTHON2=$(shell which python)

else

TIME ?= $(shell which time)
PYTHON2=$(shell which python)

endif


PYTHON3=$(shell which python3)
PIP3=$(shell which pip3)
PYINSTALLER ?= $(shell which pyinstaller)



#PYTHON ?= ${PYTHON2}
PYTHON ?= $(PYTHON3)
PIP ?= $(PIP3)


ifeq ($(PYTHON),)
$(error Python not found)
endif
ifeq ($(PIP),)
$(error pip not found)
endif


export TIME PLATFORM PYTHON PIP YESTERDAY PYINSTALLER FLAKE8
