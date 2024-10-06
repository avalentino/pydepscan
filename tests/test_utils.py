"""Test utility functions and classes."""

import pytest

import pydepscan


@pytest.mark.parametrize(
    ["inputs", "output"],
    [
        pytest.param(
            {
                "dependencies": ["os", "sys"],
                "optional_dependencies": ["re"],
                # "fmt": Format.FLAT,
            },
            """\
# dependencies
os
sys

# optional_dependencies
re""",
            id="default",
        ),
        pytest.param(
            {
                "dependencies": ["os", "sys"],
                "optional_dependencies": ["re"],
                "fmt": pydepscan.Format.FLAT,
            },
            """\
# dependencies
os
sys

# optional_dependencies
re""",
            id="FLAT",
        ),
        pytest.param(
            {
                "dependencies": ["os", "sys"],
                "optional_dependencies": ["re"],
                "fmt": pydepscan.Format.JSON,
            },
            """\
{
    "dependencies": [
        "os",
        "sys"
    ],
    "optional_dependencies": [
        "re"
    ]
}""",
            id="JSON",
        ),
        pytest.param(
            {
                "dependencies": ["os", "sys"],
                "fmt": pydepscan.Format.FLAT,
            },
            """\
# dependencies
os
sys

# optional_dependencies""",
            id="flat_deps_only",
        ),
        pytest.param(
            {
                "dependencies": ["os", "sys"],
                "fmt": pydepscan.Format.JSON,
            },
            """\
{
    "dependencies": [
        "os",
        "sys"
    ],
    "optional_dependencies": []
}""",
            id="json_deps_only",
        ),
    ],
)
def test_format_dependencies(inputs, output):
    out = pydepscan.format_dependencies(**inputs)
    assert out == output


def test_format_dependencies_invalid_format():
    with pytest.raises(ValueError, match="INVALID"):
        pydepscan.format_dependencies(
            ["os"], fmt="INVALID"  # type: ignore[arg-type]
        )
