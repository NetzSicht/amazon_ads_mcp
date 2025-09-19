"""JSON and path helpers for OpenAPI specs.

This module provides utility functions for working with JSON files and
OpenAPI path templates. It includes functionality for loading JSON files
with proper encoding and converting OpenAPI path templates to regular
expressions for pattern matching.
"""

import json
import re
from pathlib import Path


def json_load(path: Path) -> dict:
    """Load JSON from a file path with UTF-8 encoding.

    This function opens a JSON file at the specified path and loads
    its contents as a Python dictionary. It ensures proper UTF-8
    encoding handling and automatically closes the file after reading.

    :param path: Path to the JSON file to load
    :type path: Path
    :return: Parsed JSON content as a dictionary
    :rtype: dict
    :raises FileNotFoundError: If the specified file path does not exist
    :raises json.JSONDecodeError: If the file contains invalid JSON
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def oai_template_to_regex(path_template: str) -> str:
    """Convert OpenAPI path template to regex pattern.

    This function converts OpenAPI path templates (e.g., "/users/{id}/posts")
    to regular expression patterns that can be used for matching actual
    URL paths. It handles parameter placeholders by converting them to
    regex patterns that match any non-slash characters.

    The function ensures the resulting regex is anchored to the start and
    end of the string, and handles trailing slashes appropriately.

    :param path_template: OpenAPI path template string (e.g., "/users/{id}")
    :type path_template: str
    :return: Regular expression pattern string
    :rtype: str
    """
    return (
        "^"
        + re.sub(r"\{[^/]+\}", r"[^/]+", path_template.rstrip("/") or "/")
        + "$"
    )


__all__ = ["json_load", "oai_template_to_regex"]
