"""Unittests for the PyDepScan CLI."""

import os
import json

import pytest

import pydepscan


def parse_text_output(data: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "dependencies": [],
        "optional_dependencies": [],
    }
    section = ""
    for line in data.splitlines():
        line = line.strip()
        if line.startswith("#"):
            _, _, section = line.partition(" ")
            section = section.strip()
            assert section in out
        elif line:
            out[section].append(line)
    return out


@pytest.mark.parametrize(
    ["args", "parse_output"],
    [
        pytest.param([pydepscan.__file__], parse_text_output, id="text"),
        pytest.param(
            ["--format", "JSON", pydepscan.__file__],
            json.loads,
            id="json",
        ),
    ],
)
def test_cli_out_no_stdlib(args, parse_output, capsys):
    try:
        pydepscan.main(*args)
    except SystemExit:
        raise RuntimeError("SystemExit exception captured")

    data = parse_output(capsys.readouterr().out)
    assert None not in data

    assert len(data["dependencies"]) == 0
    assert "argcomplete" in data["optional_dependencies"]


@pytest.mark.parametrize(
    ["args", "parse_output"],
    [
        pytest.param(
            ["--include-stdlib", pydepscan.__file__],
            parse_text_output,
            id="text",
        ),
        pytest.param(
            ["--include-stdlib", "--format", "JSON", pydepscan.__file__],
            json.loads,
            id="json",
        ),
    ],
)
def test_cli_out_with_stdlib(args, parse_output, capsys):
    try:
        pydepscan.main(*args)
    except SystemExit:
        raise RuntimeError("SystemExit exception captured")

    data = parse_output(capsys.readouterr().out)
    assert None not in data

    assert "ast" in data["dependencies"]
    assert "argcomplete" in data["optional_dependencies"]


@pytest.mark.parametrize(
    ["args", "ref_data"],
    [
        pytest.param(
            [],
            {
                "dependencies": ["a"],
                "optional_dependencies": ["x"],
            },
            id="default",
        ),
        pytest.param(
            ["-l", "0"],
            {
                "dependencies": ["a"],
                "optional_dependencies": ["x"],
            },
            id="zero",
        ),
        pytest.param(
            ["-l", "1"],
            {
                "dependencies": ["a", "a.b", "a.c"],
                "optional_dependencies": ["x", "x.y", "x.z"],
            },
            id="one",
        ),
    ],
)
def test_cli_level(args, ref_data, capsys, tmp_path):
    code = """
import a
import a.b
from a import c

if True:
    import x
    import x.y
    from x import z
"""

    filename = tmp_path / "code.py"
    filename.write_text(code)
    try:
        pydepscan.main(*args, os.fspath(filename))
    except SystemExit:
        raise RuntimeError("SystemExit exception captured")

    data = parse_text_output(capsys.readouterr().out)
    assert data == ref_data
