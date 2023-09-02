"""Unittests for the PyDepScan CLI."""

import json
import collections

import pytest

import pydepscan


def parse_text_output(data: str):
    out = collections.defaultdict(list)
    section = None
    for line in data.splitlines():
        line = line.strip()
        if line.startswith("#"):
            _, _, section = line.partition(" ")
            section = section.strip()
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
