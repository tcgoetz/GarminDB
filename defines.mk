
-include my-defines.mk

PLATFORM=$(shell uname)

#
# Handle multiple Python installs. What python are we using?
#

ifeq ($(PLATFORM), Linux)

TIME ?= $(shell which time)
PYTHON2=$(shell which python)
PIP3=$(shell which pip3)
PYTHON3=$(shell which python3)

else ifeq ($(PLATFORM), Darwin) # MacOS

TIME ?= time
PYTHON2=$(shell which python)
PIP3=$(shell which pip3)
PYTHON3=$(shell which python3)

else

TIME ?= $(shell which time)
PYTHON2=$(shell which python)
PIP3=$(shell which pip3)
PYTHON3=$(shell which python3)

endif


#PYTHON ?= ${PYTHON2}
PYTHON ?= $(PYTHON3)
PIP ?= $(PIP3)


ifeq ($(PYTHON),)
$(error Python not found)
endif
ifeq ($(PIP),)
$(error pip not found)
endif


export PLATFORM PYTHON PIP
