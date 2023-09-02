"""Unittests for the DependencyScanner class."""

import pathlib

import pytest

import pydepscan

TEST_CODE = """\
import sys
from os import path

import requests
import numpy as np


if sys.platform == "win32":
    import winreg
    import scipy

try:
    import collections
    import lxml
except ImportError:
    pass


def func():
    import re
    import pandas as pd

    return True


class Klass:
    def method(self):
        import pathlib
        import yaml

        return True
"""

EXPECTED_RESULTS = {
    True: pydepscan.DependencyData(
        {"requests", "numpy"},
        {"scipy", "lxml", "pandas", "yaml"},
    ),
    False: pydepscan.DependencyData(
        {"sys", "os", "requests", "numpy"},
        {
            "winreg",
            "scipy",
            "collections",
            "lxml",
            "re",
            "pandas",
            "pathlib",
            "yaml",
        },
    ),
}


@pytest.fixture(scope="session")
def test_module_path(tmp_path_factory):
    filename: pathlib.Path = tmp_path_factory.getbasetemp() / "mod.py"
    filename.write_text(TEST_CODE)
    return filename


@pytest.mark.parametrize(
    ["ignore_stdlib", "results"],
    [
        pytest.param(True, EXPECTED_RESULTS[True], id="ignore_stdlib=True"),
        pytest.param(False, EXPECTED_RESULTS[False], id="ignore_stdlib=False"),
        pytest.param(None, EXPECTED_RESULTS[True], id="defaulr_ignore_stdlib"),
    ],
)
def test_dependency_scanner(ignore_stdlib, results, test_module_path):
    if ignore_stdlib is not None:
        scanner = pydepscan.DependencyScanner(ignore_stdlib=ignore_stdlib)
    else:
        scanner = pydepscan.DependencyScanner()
    scanner.scan(test_module_path)
    assert scanner.data.dependencies == results.dependencies
    assert scanner.data.optional_dependencies == results.optional_dependencies
