# -*- coding: utf-8 -*-

from array import array

SUPPORTED_CONTAINERS = (tuple, list, array, set, frozenset)


def _is_supported_container(obj):
    return isinstance(obj, SUPPORTED_CONTAINERS)


def _type_name(obj):
    return type(obj).__name__


def _pluralize(count, singular, plural=None):
    if count == 1:
        return singular
    return plural if plural is not None else singular + "s"


def _collection_header(obj):
    size = len(obj)
    return f"{_type_name(obj)} with {size} {_pluralize(size, 'element')}"


def _unique_descriptions(descriptions):
    unique = []
    for description in descriptions:
        if description not in unique:
            unique.append(description)
    return unique


def _join_descriptions(descriptions):
    if len(descriptions) == 1:
        return descriptions[0]
    if len(descriptions) == 2:
        return " or ".join(descriptions)
    return ", ".join(descriptions[:-1]) + ", or " + descriptions[-1]


def _format_bullet_block(description, indent):
    lines = description.splitlines()
    prefix = "    " * indent
    block = [f"{prefix}- {lines[0]}"]
    for line in lines[1:]:
        if line.startswith("    "):
            line = line[4:]
        block.append(f"{prefix}  {line}")
    return "\n".join(block)


def _type_signature(obj):
    if isinstance(obj, dict):
        if not obj:
            return "empty dict"

        key_types = _unique_descriptions([_type_signature(key) for key in obj.keys()])
        value_types = _unique_descriptions([_type_signature(value) for value in obj.values()])
        return (
            f"dict from {_join_descriptions(key_types)} "
            f"to {_join_descriptions(value_types)}"
        )

    if _is_supported_container(obj):
        if not obj:
            return f"empty {_type_name(obj)}"

        child_types = _unique_descriptions([_type_signature(item) for item in obj])
        return f"{_type_name(obj)} of {_join_descriptions(child_types)}"

    return _type_name(obj)


def _describe_dict(obj):
    size = len(obj)
    if size == 0:
        return "dict with 0 items (empty)"

    key_types = _unique_descriptions([_type_signature(key) for key in obj.keys()])
    value_types = _unique_descriptions([_type_signature(value) for value in obj.values()])
    return (
        f"dict with {size} {_pluralize(size, 'item')} "
        f"mapping {_join_descriptions(key_types)} to {_join_descriptions(value_types)}"
    )


def _describe_scalar(obj):
    type_name = _type_name(obj)

    if isinstance(obj, dict):
        return _describe_dict(obj)

    try:
        return f"{type_name} with shape {obj.shape}"
    except AttributeError:
        pass

    if isinstance(obj, str):
        return f"str with length {len(obj)}"

    try:
        size = len(obj)
    except TypeError:
        return type_name

    return f"{type_name} with {size} {_pluralize(size, 'element')}"


def _describe(obj):
    if not _is_supported_container(obj):
        return _describe_scalar(obj)

    header = _collection_header(obj)
    if len(obj) == 0:
        return f"{header} (empty)"

    children = [_describe(item) for item in obj]
    if any(_is_supported_container(item) for item in obj):
        lines = [header + ":"]
        for child in children:
            lines.append(_format_bullet_block(child, 1))
        return "\n".join(lines)

    unique_children = _unique_descriptions(children)
    if len(unique_children) == 1:
        return f"{header} containing {unique_children[0]}"

    return f"{header} containing {', '.join(unique_children)}"


def supertype(obj, indent=0):
    description = _describe(obj)
    return description
