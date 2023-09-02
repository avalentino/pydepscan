#!/usr/bin/make -f

PYTHON=python3
PYTARGETS=src/pydepscan.py tests

.PHONY: default help dist check fullcheck coverage lint clean cleaner distclean

default: help

help:
	@echo "Usage: make <TARGET>"
	@echo "Available targets:"
	@echo "  help      - print this help message"
	@echo "  dist      - generate the distribution packages (source and wheel)"
	@echo "  check     - run a full test (using pytest)"
	@echo "  fullcheck - run a full test (using tox)"
	@echo "  coverage  - run tests and generate the coverage report"
	@echo "  lint      - perform check with code linter (flake8, black)"
	@echo "  clean     - clean build artifacts"
	@echo "  cleaner   - clean cache files and working directories of al tools"
	@echo "  distclean - clean all the generated files"

dist:
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

check:
	env PYTHONPATH=${PWD}/src $(PYTHON) -m pytest

fullcheck:
	$(PYTHON) -m tox

coverage:
	env PYTHONPATH=${PWD}/src $(PYTHON) -m pytest --cov=pydepscan --cov-report=html --cov-report=term

lint:
	$(PYTHON) -m flake8 --count --statistics $(PYTARGETS)
	$(PYTHON) -m pydocstyle --count $(PYTARGETS)
	$(PYTHON) -m isort --check $(PYTARGETS)
	$(PYTHON) -m black --check $(PYTARGETS)
	$(PYTHON) -m mypy --check-untyped-defs --ignore-missing-imports $(PYTARGETS)

clean:
	$(RM) -r src/*.egg-info build
	find . -name __pycache__ -type d -exec $(RM) -r {} +

cleaner: clean
	$(RM) -r .coverage htmlcov
	$(RM) -r .pytest_cache .tox .ipynb_checkpoints .mypy_cache

distclean: cleaner
	$(RM) -r dist
