#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

"""Dependency scanner for Python source code.

PyDepScan analyses Python source files looking for import statements and
produces lists of mandatory and optional dependencies.

Optional dependencies are the ones for which the import statement
is executed under some condition (e.g. included in an `if` statement
of `try`/`except` block or within a function).

To determine optional dependencies a quite simple heuristic is used,
hence there could be cases in which the result is not fully accurate.

Results are always sorted.
"""


import os
import ast
import sys
import enum
import logging
import pathlib
import argparse
import dataclasses
from collections.abc import Sequence

__version__ = "1.0.dev0"


PathType = str | os.PathLike[str]
NodeType = ast.AST


@dataclasses.dataclass(slots=True, frozen=True)
class DependencyData:
    """Dependency data."""

    dependencies: set[str] = dataclasses.field(default_factory=set)
    optional_dependencies: set[str] = dataclasses.field(default_factory=set)

    def remove_stdlib(self):
        """Remove dependencies coming from the Python standard library."""
        self.dependencies.difference_update(sys.stdlib_module_names)
        self.optional_dependencies.difference_update(sys.stdlib_module_names)

    def normalize(self, ignore_stdlib: bool = True):
        """Normalize the dependency sets.

        Remove mandatory items form the set of optional items.
        Optionally discard modules/packages of the standard Python library
        from dependencies.
        """
        if ignore_stdlib:
            self.remove_stdlib()
        self.optional_dependencies.difference_update(self.dependencies)

    def clear(self):
        """Delete all the collected data."""
        self.dependencies.clear()
        self.optional_dependencies.clear()

    def discard(self, name: str):
        """Discard the specified dependency."""
        self.dependencies.discard(name)
        self.optional_dependencies.discard(name)


class DependencyScanner(ast.NodeVisitor):
    """Scan Python source code for dependencies."""

    def __init__(self, *args, ignore_stdlib: bool = True, **kwargs):
        """Initialize the dependency scanner.

        The `ignore_stdlib` option is used to determine whenever the
        modules/packages of the standard Python library should be included
        or not in the list of dependencies.

        All the other parameters and keyword arguments are directly passed to
        the parent class initializer.

        .. seealso:: :class:`ast.NodeVisitor`.
        """
        self._ignore_stdlib: bool = ignore_stdlib
        super().__init__(*args, **kwargs)
        self.data: DependencyData = DependencyData()

    def visit(self, node: NodeType):
        """Visit and AST node and normalize the identified imports."""
        super().visit(node)
        self.data.normalize(ignore_stdlib=self._ignore_stdlib)

    @staticmethod
    def is_global(node: NodeType) -> bool:
        """Return True if the node contains global code.

        An heuristic consisting in checking the indentation level is used
        for the purpose.
        """
        # TODO: use a safer criterion
        return bool(node.col_offset == 0)  # type: ignore[attr-defined]

    def _get_imports(self, mandatory: bool = False) -> set[str]:
        if mandatory:
            return self.data.dependencies
        else:
            return self.data.optional_dependencies

    @staticmethod
    def _get_basename(name: str) -> str:
        # a.b.c --> a
        return name.split(".")[0]

    def visit_Import(self, node: ast.Import):  # noqa: N802
        """Detect dependencies from Import nodes."""
        s = self._get_imports(self.is_global(node))
        s.update(self._get_basename(item.name) for item in node.names)
        return self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):  # noqa: N802
        """Detect dependencies from ImportFrom nodes."""
        # Skip:
        #   form . import ...
        #   from .something import ...
        if node.module is not None and node.level == 0:
            s = self._get_imports(self.is_global(node))
            s.add(self._get_basename(node.module))
        return self.generic_visit(node)

    def scan(self, path: PathType):
        """Scan the specified path."""
        module = pathlib.Path(path)
        source = module.read_text()
        ast_root = ast.parse(source, module)
        self.visit(ast_root)


def scan(
    *paths: PathType,
    ignore_stdlib: bool = True,
    pattern: str | None = "**/*.py",
) -> DependencyData:
    """Scan the input modules for dependencies."""
    log = logging.getLogger(__name__)
    scanner = DependencyScanner(ignore_stdlib=ignore_stdlib)
    for path in paths:
        path = pathlib.Path(path)
        if not path.exists():
            raise FileNotFoundError(str(path))
        elif path.is_dir():
            if pattern is not None:
                package = path
                log.debug(f"scan {package} directory ...")
                for module in package.glob(pattern):
                    log.debug(f"scan {module} module ...")
                    scanner.scan(module)
                scanner.data.discard(package.name)
        else:
            scanner.scan(path)

    return scanner.data


class Format(enum.Enum):
    """Enumeration for the output format."""

    FLAT = "FLAT"
    JSON = "JSON"

    def __str__(self):
        """Return the string representation of the output format enum."""
        return self.value


def format_dependencies(
    dependencies: Sequence[str],
    optional_dependencies: Sequence[str] | None = None,
    fmt: Format = Format.FLAT,
) -> str:
    """Format dependencies according to the specified format."""
    if optional_dependencies is None:
        optional_dependencies = []

    if fmt is Format.FLAT:
        return "\n".join(
            [
                "# dependencies",
                *dependencies,
                "",
                "# optional_dependencies",
                *optional_dependencies,
            ]
        )
    elif fmt is Format.JSON:
        import json

        data = dict(
            dependencies=list(dependencies),
            optional_dependencies=optional_dependencies,
        )
        return json.dumps(data, indent="    ")
    else:
        raise ValueError(f"Invalid fmt: {fmt!r}")


# --- CLI ---------------------------------------------------------------------


PROG = pathlib.Path(__file__).stem
LOGFMT = "%(levelname)s: %(message)s"
DEFAULT_LOGLEVEL = "WARNING"
# DEFAULT_LOGLEVEL = "DEBUG"

try:
    from os import EX_OK
except ImportError:  # pragma: no cover
    EX_OK = 0
EX_FAILURE = 1
EX_INTERRUPT = 130


def _autocomplete(parser):
    try:
        import argcomplete
    except ImportError:  # pragma: no cover
        pass
    else:
        argcomplete.autocomplete(parser)


def _add_logging_control_args(parser, default_loglevel=DEFAULT_LOGLEVEL):
    """Add command line options for logging control."""
    loglevels = [logging.getLevelName(level) for level in range(10, 60, 10)]

    parser.add_argument(
        "--loglevel",
        default=default_loglevel,
        choices=loglevels,
        help="logging level (default: %(default)s)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="loglevel",
        action="store_const",
        const="ERROR",
        help="suppress standard output messages, "
        "only errors are printed to screen",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        action="store_const",
        const="INFO",
        help="print verbose output messages",
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="loglevel",
        action="store_const",
        const="DEBUG",
        help="print debug messages",
    )


def get_parser(subparsers=None):
    """Instantiate the command line argument (sub-)parser."""
    name = PROG
    synopsis = __doc__.splitlines()[0]
    doc = __doc__

    if subparsers is None:
        parser = argparse.ArgumentParser(prog=name, description=doc)
        parser.add_argument(
            "--version", action="version", version="%(prog)s v" + __version__
        )
    else:
        parser = subparsers.add_parser(name, description=doc, help=synopsis)
        # parser.set_defaults(func=info)

    _add_logging_control_args(parser)

    # Command line options
    parser.add_argument(
        "-f",
        "--format",
        dest="fmt",
        choices=Format,
        type=Format.__getitem__,
        default=Format.FLAT,
        help="specify the format to dump dependencies (default: %(default)r)",
    )
    parser.add_argument(
        "--pattern",
        default="**/*.py",
        help=(
            "scan directories and analyse files matching the specified "
            "pattern (default: %(default)r)"
        ),
    )
    parser.add_argument(
        "--no-recursive",
        dest="pattern",
        action="store_const",
        const=None,
        help=(
            "ignore directories (including the one provided in the input list)"
        ),
    )
    parser.add_argument(
        "--include-stdlib",
        dest="ignore_stdlib",
        action="store_false",
        default=True,
        help=(
            "also include in the list of dependencies modules and packages "
            "belonging to the Python standard library"
        ),
    )

    # Positional arguments
    parser.add_argument(
        "modules",
        nargs="+",
        metavar="MODULE",
        help="path to the Python module or package to be analyzed",
    )

    if subparsers is None:
        _autocomplete(parser)

    return parser


def parse_args(args=None, namespace=None, parser=None):
    """Parse command line arguments."""
    if parser is None:
        parser = get_parser()

    args = parser.parse_args(args, namespace)

    return args


def main(*argv):
    """Implement the main CLI interface."""
    # setup logging
    logging.basicConfig(format=LOGFMT, level=DEFAULT_LOGLEVEL)
    logging.captureWarnings(True)
    log = logging.getLogger(__name__)

    # parse cmd line arguments
    args = parse_args(argv if argv else None)

    # execute main tasks
    exit_code = EX_OK
    try:
        logging.getLogger().setLevel(args.loglevel)

        results = scan(*args.modules, ignore_stdlib=args.ignore_stdlib)

        deps = sorted(results.dependencies)
        optional_deps = sorted(results.optional_dependencies)

        print(format_dependencies(deps, optional_deps, args.fmt))
    except Exception as exc:
        log.critical(
            "unexpected exception caught: {!r} {}".format(
                type(exc).__name__, exc
            )
        )
        log.debug("stacktrace:", exc_info=True)
        exit_code = EX_FAILURE
    except KeyboardInterrupt:
        log.warning("Keyboard interrupt received: exit the program")
        exit_code = EX_INTERRUPT

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
