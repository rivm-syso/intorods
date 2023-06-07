

.PHONY: build docs

VENV_ROOT=venv
VENV_BIN=$(VENV_ROOT)/bin
VENV_PIP=$(VENV_BIN)/pip3
VENV_PYTHON=$(VENV_BIN)/python

export PATH := $(VENV_BIN):$(PATH)

VERSION=$(shell python -c 'from src.intorods import __VERSION__ ; print(__VERSION__)')

WHEEL=dist/intorods-$(VERSION)-py3-none-any.whl
PKG=dist/intorods-$(VERSION).tar.gz
SOURCES = $(wildcard src/intorods/*.py src/intorods/*/*.py)

print-%  : ; @echo $* = $($*)

default: list-tasks

$(VENV_ROOT): buildreq.txt
	@echo "Creating virtualenv"
	if [ -d venv ] ; then \
		mv -f $(VENV_ROOT) $(VENV_ROOT).old ; \
		rm -rf $(VENV_ROOT).old & \
	fi
	python3 -m venv $(VENV_ROOT)
	. $(VENV_ROOT)/bin/activate && python3 -m pip install -r buildreq.txt


###############################################################################
# Default task to get a list of tasks when `make' is run without args.
# <https://stackoverflow.com/questions/4219255>
###############################################################################

list-tasks:
	@echo Available tasks:
	@echo ----------------
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'
	@echo

all: docs build

clean:
	rm -rf docs/build/ build/ dist/ venv/ src/intorods.egg-info/

#  DOCS

docs: venv docs-html docs-md README.md

README.md: docs-md
	cp docs/build/markdown/introduction.md README.md

docs-html:
	@echo Generating html documentation pages
	. $(VENV_ROOT)/bin/activate && cd docs && make html

docs-md:
	@echo Generating md documentation pages
	. $(VENV_ROOT)/bin/activate && cd docs && make markdown

# BUILD

$(WHEEL) $(PKG): venv $(SOURCES)
	rm -rf build/ dist/
	$(VENV_PYTHON) -m build

build: $(WHEEL) $(PKG)

publish: build
	$(VENV_PYTHON) -m twine upload dist/*

publish-test: build
	$(VENV_PYTHON) -m twine upload --repository testpypi dist/*


