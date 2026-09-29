export PROJECT_BASE=$(CURDIR)/..
export VENV=$(PROJECT_BASE)/.venv

include ../defines.mk


$(info $$PROJECT_BASE is [${PROJECT_BASE}])
$(info $$VENV is [${VENV}])
$(info $$PLATFORM is [${PLATFORM}])
$(info $$SHELL is [${SHELL}])

export PIP_PATH=$(VENV)/bin/$(PIP)
$(info $$PIP_PATH is [${PIP_PATH}])
export PYTHON_PATH=$(VENV)/bin/$(PYTHON)
$(info $$PYTHON_PATH is [${PYTHON_PATH}])

all: deps

install:

deps:
	$(PIP_PATH) install --upgrade --requirement requirements.txt

devdeps:

remove_deps:
	# $(PIP_PATH) uninstall -y --requirement requirements.txt

requirements.txt:
	$(PIP_PATH) freeze -r requirements.in > requirements.txt

requirements_graphs.txt:
	$(PIP_PATH) freeze -r requirements_graphs.in > requirements_graphs.txt

flake8:

clean:
	rm -f *.pyc
	rm -f *.log
	rm -rf __pycache__
