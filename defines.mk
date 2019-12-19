
# DEFAULT_PYTHON=yes
DEFAULT_PYTHON ?= yes
PLATFORM=$(shell uname)

#
# Handle multiple Python installs. What python are we using?
#

ifeq ($(PLATFORM), Linux)

PYTHON2=$(shell which python)
PIP3=$(shell which pip3)
PYTHON3=$(shell which python3)

else ifeq ($(PLATFORM), Darwin) # MacOS

ifeq ($(DEFAULT_PYTHON), yes)
PYTHON2=$(shell which python)
PIP3=$(shell which pip3)
PYTHON3=$(shell which python3)
else
#PYTHON3=/usr/bin/python3
PYTHON3=/usr/local/bin/python3
#PIP3=/usr/bin/pip3
PIP3=/usr/local/bin/pip3
endif

else

PYTHON2=$(shell which python)
PIP3=$(shell which pip3)
PYTHON3=$(shell which python3)

endif


#PYTHON=${PYTHON2}
PYTHON=$(PYTHON3)
PIP=$(PIP3)


ifeq ($(PYTHON),)
$(error Python not found)
endif
ifeq ($(PIP),)
$(error pip not found)
endif


export PYTHON PIP
