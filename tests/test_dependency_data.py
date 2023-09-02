"""Unittests for the DependencyData class."""

import pytest

import pydepscan


def test_init_empty():
    data = pydepscan.DependencyData()

    assert isinstance(data.dependencies, set)
    assert isinstance(data.optional_dependencies, set)
    assert not data.dependencies
    assert not data.optional_dependencies


def test_init():
    deps = {"a", "b", "c"}
    opt_deps = {"c", "d", "e"}

    data = pydepscan.DependencyData(deps, opt_deps)

    assert isinstance(data.dependencies, set)
    assert isinstance(data.optional_dependencies, set)
    assert data.dependencies == deps
    assert data.optional_dependencies == opt_deps


@pytest.mark.parametrize(
    ["deps", "opt_deps", "ignore_stdlib", "ref_deps", "ref_opt_defs"],
    [
        pytest.param(
            {"a", "b", "c", "sys"},
            {"c", "d", "e", "os"},
            None,
            {"a", "b", "c"},
            {"d", "e"},
            id="default_ignore_stdlib",
        ),
        pytest.param(
            {"a", "b", "c", "sys"},
            {"c", "d", "e", "os"},
            True,
            {"a", "b", "c"},
            {"d", "e"},
            id="ignore_stdlib=True",
        ),
        pytest.param(
            {"a", "b", "c", "sys"},
            {"c", "d", "e", "os"},
            False,
            {"a", "b", "c", "sys"},
            {"d", "e", "os"},
            id="ignore_stdlib=False",
        ),
    ],
)
def test_normalize(deps, opt_deps, ignore_stdlib, ref_deps, ref_opt_defs):
    data = pydepscan.DependencyData(deps, opt_deps)
    if ignore_stdlib is not None:
        data.normalize(ignore_stdlib=ignore_stdlib)
    else:
        data.normalize()

    assert isinstance(data.dependencies, set)
    assert isinstance(data.optional_dependencies, set)
    assert not data.dependencies.intersection(data.optional_dependencies)
    assert data.dependencies == ref_deps
    assert data.optional_dependencies == ref_opt_defs


@pytest.mark.parametrize(
    ["deps", "opt_deps", "ref_deps", "ref_opt_defs"],
    [
        pytest.param(
            {"a", "b", "c"},
            {"c", "d", "e"},
            {"a", "b", "c"},
            {"c", "d", "e"},
            id="no_stdlib",
        ),
        pytest.param(
            {"a", "b", "c", "sys"},
            {"c", "d", "e", "os"},
            {"a", "b", "c"},
            {"c", "d", "e"},
            id="stdlib",
        ),
        pytest.param(
            {"os", "sys"},
            {"re"},
            set(),
            set(),
            id="only_stdlib",
        ),
    ],
)
def test_remove_stdlib(deps, opt_deps, ref_deps, ref_opt_defs):
    data = pydepscan.DependencyData(deps, opt_deps)
    data.remove_stdlib()

    assert isinstance(data.dependencies, set)
    assert isinstance(data.optional_dependencies, set)
    assert data.dependencies == ref_deps
    assert data.optional_dependencies == ref_opt_defs


@pytest.mark.parametrize(
    ["deps", "opt_deps", "discard", "ref_deps", "ref_opt_defs"],
    [
        pytest.param(
            {"a", "b", "c"},
            {"c", "d", "e"},
            "c",
            {"a", "b"},
            {"d", "e"},
            id="included_item",
        ),
        pytest.param(
            {"a", "b", "c"},
            {"c", "d", "e"},
            "x",
            {"a", "b", "c"},
            {"c", "d", "e"},
            id="not_includes_item",
        ),
    ],
)
def test_discard(deps, opt_deps, discard, ref_deps, ref_opt_defs):
    data = pydepscan.DependencyData(deps, opt_deps)
    data.discard(discard)

    assert isinstance(data.dependencies, set)
    assert isinstance(data.optional_dependencies, set)
    assert data.dependencies == ref_deps
    assert data.optional_dependencies == ref_opt_defs


def test_clear():
    deps = {"a", "b", "c"}
    opt_deps = {"c", "d", "e"}
    data = pydepscan.DependencyData(deps, opt_deps)

    assert data.dependencies == deps
    assert data.optional_dependencies == opt_deps

    data.clear()

    assert isinstance(data.dependencies, set)
    assert isinstance(data.optional_dependencies, set)
    assert not data.dependencies
    assert not data.optional_dependencies
