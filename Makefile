#!/usr/bin/make -f

PYTHON=python3
TARGET=src/pydepscan.py

.PHONY: default help dist lint clean cleaner distclean

default: help

help:
	@echo "Usage: make <TARGET>"
	@echo "Available targets:"
	@echo "  help      - print this help message"
	@echo "  dist      - generate the distribution packages (source and wheel)"
	@echo "  lint      - perform check with code linter (flake8, black)"
	@echo "  clean     - clean build artifacts"
	@echo "  cleaner   - clean cache files and working directories of al tools"
	@echo "  distclean - clean all the generated files"

dist:
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

lint:
	$(PYTHON) -m flake8 --count --statistics $(TARGET)
	$(PYTHON) -m pydocstyle --count $(TARGET)
	$(PYTHON) -m isort --check $(TARGET)
	$(PYTHON) -m black --check $(TARGET)
	$(PYTHON) -m mypy --check-untyped-defs --ignore-missing-imports $(TARGET)

clean:
	$(RM) -r src/*.egg-info build
	find . -name __pycache__ -type d -exec $(RM) -r {} +

cleaner: clean
	$(RM) -r .coverage htmlcov .pytest_cache .tox .ipynb_checkpoints

distclean: cleaner
	$(RM) -r dist
