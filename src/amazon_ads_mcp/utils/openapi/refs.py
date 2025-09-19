"""Reference utilities for OpenAPI specs.

This module provides utilities for handling OpenAPI specification references
($ref pointers). It includes functionality to dereference JSON Schema
references within OpenAPI documents, allowing access to the actual schema
definitions rather than just reference pointers.
"""

from typing import Any, Optional


def deref(spec: dict, obj: Optional[dict]) -> Optional[dict]:
    """Dereference a $ref pointer in an OpenAPI spec.

    This function resolves JSON Schema references ($ref) within OpenAPI
    specifications. It follows the reference path from the root of the
    specification to retrieve the actual schema object that the reference
    points to.

    The function handles relative references that start with "#/" and
    traverses the specification structure using the path components.
    If the reference cannot be resolved (invalid path, missing keys,
    or non-dict target), it returns the original object unchanged.

    :param spec: The complete OpenAPI specification dictionary
    :type spec: dict
    :param obj: Object that may contain a $ref pointer to dereference
    :type obj: Optional[dict]
    :return: Dereferenced object if successful, original object if
             dereferencing fails or is not needed
    :rtype: Optional[dict]
    """
    if not isinstance(obj, dict):
        return obj
    ref = obj.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return obj
    cur: Any = spec
    for part in ref.lstrip("#/").split("/"):
        if not isinstance(cur, dict) or part not in cur:
            return obj
        cur = cur[part]
    return cur if isinstance(cur, dict) else obj


__all__ = ["deref"]
