"""Load model catalogs from an explicit YAML file and resolve API keys."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml

from spawn_join_llm_provider import ConfigurationError


def _check_duplicate_keys(node: yaml.Node) -> None:
    """Reject literal duplicate keys and recursive aliases in one document."""
    _walk_node(node, active=set(), visited=set())


def _walk_node(
    node: yaml.Node,
    *,
    active: set[int],
    visited: set[int],
) -> None:
    node_id = id(node)
    if node_id in active:
        raise ConfigurationError("Model file contains a recursive alias")
    if node_id in visited:
        return

    active.add(node_id)
    try:
        if isinstance(node, yaml.MappingNode):
            seen: set[str] = set()
            for key_node, value_node in node.value:
                if isinstance(key_node, yaml.ScalarNode):
                    if key_node.value in seen:
                        line = key_node.start_mark.line + 1
                        column = key_node.start_mark.column + 1
                        raise ConfigurationError(
                            f"Model file contains a duplicate key at line {line}, "
                            f"column {column}"
                        )
                    seen.add(key_node.value)
                _walk_node(key_node, active=active, visited=visited)
                _walk_node(value_node, active=active, visited=visited)
        elif isinstance(node, yaml.SequenceNode):
            for item in node.value:
                _walk_node(item, active=active, visited=visited)
    finally:
        active.remove(node_id)
    visited.add(node_id)


def _load_yaml_document(path: Path) -> object:  # pyright: ignore[reportUnusedFunction]
    """Read one YAML document, rejecting duplicate keys and unsafe tags."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeError as exc:
        raise ConfigurationError(f"Model file is not valid UTF-8: {path}") from exc
    except OSError as exc:
        raise ConfigurationError(f"Model file could not be read: {path}") from exc

    try:
        node = cast(
            "yaml.Node | None",
            yaml.compose(  # pyright: ignore[reportUnknownMemberType]
                text, Loader=yaml.SafeLoader
            ),
        )
        if node is not None:
            _check_duplicate_keys(node)
        document: object = yaml.safe_load(text)
    except yaml.MarkedYAMLError as exc:
        problem = exc.problem or "invalid YAML"
        mark = exc.problem_mark
        location = ""
        if mark is not None:
            location = f" at line {mark.line + 1}, column {mark.column + 1}"
        raise ConfigurationError(
            f"Model file is not valid YAML{location}: {problem}"
        ) from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError("Model file is not valid YAML") from exc

    return document
