"""Check the standalone package identity, public surface, and dependency boundary."""

from __future__ import annotations

import re
import subprocess
import sys
from importlib import import_module, metadata
from importlib.resources import files

import spawn_join_common
from spawn_join_common import FieldReader
from spawn_join_common.parsing import FieldReader as ParsingFieldReader


def test_package_is_importable() -> None:
    assert spawn_join_common.__file__ is not None


def test_public_exports_are_explicit_and_identical() -> None:
    assert spawn_join_common.__all__ == ["FieldReader", "__version__"]
    assert FieldReader is ParsingFieldReader
    assert spawn_join_common.__version__ == "0.1.0"
    assert set(spawn_join_common.__dict__) >= {"FieldReader", "__version__"}


def test_distribution_identity() -> None:
    package_metadata = metadata.metadata("spawn-join-common")
    assert package_metadata["Name"] == "spawn-join-common"
    assert package_metadata["Version"] == "0.1.0"


def test_py_typed_marker_is_packaged() -> None:
    assert (files("spawn_join_common") / "py.typed").is_file()


def test_base_runtime_dependencies_are_empty_and_validation_is_optional() -> None:
    requirements = metadata.requires("spawn-join-common") or []
    assert requirements
    assert all('extra == "validation"' in requirement for requirement in requirements)
    dependency_names = {
        re.split(r"[<>=!~;\[\s]", requirement, maxsplit=1)[0]
        for requirement in requirements
    }
    assert dependency_names == {"pydantic"}


def test_root_import_does_not_load_pydantic() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import spawn_join_common; "
                "assert 'pydantic' not in sys.modules; "
                "assert 'spawn_join_common.validation' not in sys.modules"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_optional_namespace_exports_only_validate_with() -> None:
    validation = import_module("spawn_join_common.validation")
    assert validation.__all__ == ["validate_with"]
    assert callable(validation.validate_with)
