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
    from astropy import coordinates

    return True


class Klass:
    def method(self):
        import pathlib
        import yaml
        import email.message

        return True
"""


@pytest.fixture(scope="session")
def test_module_path(tmp_path_factory):
    filename: pathlib.Path = tmp_path_factory.getbasetemp() / "mod.py"
    filename.write_text(TEST_CODE)
    return filename


@pytest.fixture(scope="session")
def test_package_path(tmp_path_factory):
    pkgname = tmp_path_factory.getbasetemp().joinpath("pkg")
    pkgname.mkdir()
    pkgname.joinpath("__init__.py").write_text("import pkgdep\n")
    pkgname.joinpath("mod.py").write_text(TEST_CODE)

    subpkgname = pkgname.joinpath("subpkag")
    subpkgname.mkdir()
    subpkgname.joinpath("__init__.py").write_text("import subpkgdep\n")

    return pkgname


@pytest.mark.parametrize(
    ["ignore_stdlib", "level", "ref"],
    [
        pytest.param(
            True,
            None,
            pydepscan.DependencyData(
                {"requests", "numpy"},
                {"scipy", "lxml", "pandas", "yaml", "astropy"},
            ),
            id="ignore_stdlib=True",
        ),
        pytest.param(
            False,
            None,
            pydepscan.DependencyData(
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
                    "astropy",
                    "email",
                },
            ),
            id="ignore_stdlib=False",
        ),
        pytest.param(
            None,
            None,
            pydepscan.DependencyData(
                {"requests", "numpy"},
                {"scipy", "lxml", "pandas", "yaml", "astropy"},
            ),
            id="default",
        ),
        pytest.param(
            None,
            0,
            pydepscan.DependencyData(
                {"requests", "numpy"},
                {"scipy", "lxml", "pandas", "yaml", "astropy"},
            ),
            id="leval_zero",
        ),
        pytest.param(
            None,
            1,
            pydepscan.DependencyData(
                {"requests", "numpy"},
                {"scipy", "lxml", "pandas", "yaml", "astropy.coordinates"},
            ),
            id="level_one",
        ),
        pytest.param(
            False,
            1,
            pydepscan.DependencyData(
                {"sys", "os.path", "requests", "numpy"},
                {
                    "winreg",
                    "scipy",
                    "collections",
                    "lxml",
                    "re",
                    "pandas",
                    "pathlib",
                    "yaml",
                    "astropy.coordinates",
                    "email.message",
                },
            ),
            id="level_one_syspackages",
        ),
    ],
)
def test_dependency_scanner(ignore_stdlib, level, ref, test_module_path):
    kwargs = {}
    if ignore_stdlib is not None:
        kwargs["ignore_stdlib"] = ignore_stdlib
    if level is not None:
        kwargs["level"] = level

    scanner = pydepscan.DependencyScanner(**kwargs)
    scanner.scan(test_module_path)
    assert scanner.data.dependencies == ref.dependencies
    assert scanner.data.optional_dependencies == ref.optional_dependencies


@pytest.mark.parametrize(
    ["ignore_stdlib", "level", "ref"],
    [
        pytest.param(
            None,
            None,
            pydepscan.DependencyData(
                {"requests", "numpy", "pkgdep", "subpkgdep"},
                {"scipy", "lxml", "pandas", "yaml", "astropy"},
            ),
            id="default",
        ),
        pytest.param(
            False,
            None,
            pydepscan.DependencyData(
                {"sys", "os", "requests", "numpy", "pkgdep", "subpkgdep"},
                {
                    "winreg",
                    "scipy",
                    "collections",
                    "lxml",
                    "re",
                    "pandas",
                    "pathlib",
                    "yaml",
                    "astropy",
                    "email",
                },
            ),
            id="ignore_stdlib=False",
        ),
        pytest.param(
            None,
            1,
            pydepscan.DependencyData(
                {"requests", "numpy", "pkgdep", "subpkgdep"},
                {"scipy", "lxml", "pandas", "yaml", "astropy.coordinates"},
            ),
            id="level_one",
        ),
    ],
)
def test_scan(ignore_stdlib, level, ref, test_package_path):
    kwargs = {}
    if ignore_stdlib is not None:
        kwargs["ignore_stdlib"] = ignore_stdlib
    if level is not None:
        kwargs["level"] = level

    deps = pydepscan.scan(test_package_path, **kwargs)

    assert deps.dependencies == ref.dependencies
    assert deps.optional_dependencies == ref.optional_dependencies


def test_scan_invalid_path(test_package_path):
    path = test_package_path / "invalid.py"
    with pytest.raises(FileNotFoundError, match=path.name):
        pydepscan.scan(path)


def test_scan_pattern(test_package_path):
    ref = pydepscan.DependencyData(
        {"requests", "numpy", "pkgdep"},
        {"scipy", "lxml", "pandas", "yaml", "astropy"},
    )

    deps = pydepscan.scan(test_package_path, pattern="*.py")

    assert deps.dependencies == ref.dependencies
    assert deps.optional_dependencies == ref.optional_dependencies
