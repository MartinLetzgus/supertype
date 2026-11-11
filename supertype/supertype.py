"""Core implementation of :func:`supertype`.

The output has two forms:

* a *summary*, used when a container holds only "flat" values, for example
  ``list with 3 elements containing int or str``;
* a *tree*, used when a container holds other containers. Each child is then
  described on its own bullet line, indented by four spaces per level.
"""

from __future__ import annotations

from array import array
from typing import Any, Iterable, List, Optional, Set

__all__ = ["supertype"]

#: Container types whose elements are inspected recursively.
SUPPORTED_CONTAINERS = (tuple, list, array, set, frozenset)

#: Sized types whose length is reported as a "length" rather than a number of
#: elements.
_TEXT_TYPES = (str, bytes, bytearray)

_INDENT = "    "


def _is_supported_container(obj: Any) -> bool:
    return isinstance(obj, SUPPORTED_CONTAINERS)


def _is_inspected(obj: Any) -> bool:
    """Return True for objects whose content is inspected recursively."""
    return isinstance(obj, dict) or _is_supported_container(obj)


def _type_name(obj: Any) -> str:
    return type(obj).__name__


def _pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    if count == 1:
        return singular
    return plural if plural is not None else singular + "s"


def _count(size: int, noun: str) -> str:
    return f"{size} {_pluralize(size, noun)}"


def _unique(descriptions: Iterable[str]) -> List[str]:
    """Deduplicate while preserving the order of first appearance."""
    return list(dict.fromkeys(descriptions))


def _join_alternatives(descriptions: List[str]) -> str:
    if len(descriptions) == 1:
        return descriptions[0]
    if len(descriptions) == 2:
        return " or ".join(descriptions)
    return ", ".join(descriptions[:-1]) + ", or " + descriptions[-1]


def _group(descriptions: List[str]) -> str:
    """Join alternatives, parenthesised when there are several.

    Used inside type signatures so that ``list of (list of int or str)`` is
    not confused with ``list of list of (int or str)``.
    """
    joined = _join_alternatives(descriptions)
    return f"({joined})" if len(descriptions) > 1 else joined


def _circular(obj: Any) -> str:
    return f"{_type_name(obj)} (circular reference)"


class _Describer:
    """Holds the traversal state for one call to :func:`supertype`."""

    def __init__(self, max_depth: Optional[int]) -> None:
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be None or a non-negative integer")
        self.max_depth = max_depth
        # ids of the containers on the current path, to detect cycles.
        self._path: Set[int] = set()

    # -- short type signatures ("list of int", "dict from str to int") ------

    def signature(self, obj: Any) -> str:
        if not _is_inspected(obj):
            return _type_name(obj)
        if id(obj) in self._path:
            return _circular(obj)
        if not obj:
            return f"empty {_type_name(obj)}"

        self._path.add(id(obj))
        try:
            if isinstance(obj, dict):
                keys = _group(_unique(self.signature(k) for k in obj))
                values = _group(_unique(self.signature(v) for v in obj.values()))
                return f"{_type_name(obj)} from {keys} to {values}"
            items = _group(_unique(self.signature(i) for i in obj))
            return f"{_type_name(obj)} of {items}"
        finally:
            self._path.discard(id(obj))

    # -- full descriptions ---------------------------------------------------

    def describe(self, obj: Any, depth: int = 0) -> str:
        if isinstance(obj, dict):
            return self._describe_dict(obj)
        if _is_supported_container(obj):
            return self._describe_container(obj, depth)
        return _describe_leaf(obj)

    def _describe_dict(self, obj: dict) -> str:
        if id(obj) in self._path:
            return _circular(obj)
        header = f"{_type_name(obj)} with {_count(len(obj), 'item')}"
        if not obj:
            return f"{header} (empty)"

        self._path.add(id(obj))
        try:
            keys = _join_alternatives(_unique(self.signature(k) for k in obj))
            values = _join_alternatives(_unique(self.signature(v) for v in obj.values()))
        finally:
            self._path.discard(id(obj))
        return f"{header} mapping {keys} to {values}"

    def _describe_container(self, obj: Any, depth: int) -> str:
        if id(obj) in self._path:
            return _circular(obj)
        header = f"{_type_name(obj)} with {_count(len(obj), 'element')}"
        if not obj:
            return f"{header} (empty)"

        self._path.add(id(obj))
        try:
            has_nested = any(_is_supported_container(item) for item in obj)
            depth_left = self.max_depth is None or depth < self.max_depth
            if has_nested and depth_left:
                lines = [header + ":"]
                for item in obj:
                    child = self.describe(item, depth + 1)
                    lines.append(_bullet(child))
                return "\n".join(lines)

            items = _join_alternatives(_unique(self.signature(i) for i in obj))
            return f"{header} containing {items}"
        finally:
            self._path.discard(id(obj))


def _describe_leaf(obj: Any) -> str:
    """Describe an object whose content is not inspected."""
    type_name = _type_name(obj)

    # Classes (e.g. ``numpy.ndarray`` itself) expose ``shape`` and ``__len__``
    # as descriptors; they must not be mistaken for instances.
    if isinstance(obj, type):
        return type_name

    shape = getattr(obj, "shape", None)
    if shape is not None and not callable(shape):
        try:
            shape = tuple(shape)
        except TypeError:
            pass
        description = f"{type_name} with shape {shape}"
        dtype = getattr(obj, "dtype", None)
        if dtype is not None and not callable(dtype):
            description += f" and dtype {dtype}"
        return description

    if isinstance(obj, _TEXT_TYPES):
        return f"{type_name} with length {len(obj)}"

    try:
        size = len(obj)
    except TypeError:
        return type_name
    return f"{type_name} with {_count(size, 'element')}"


def _bullet(description: str) -> str:
    """Turn a (possibly multi-line) description into an indented bullet."""
    lines = description.splitlines()
    block = [f"{_INDENT}- {lines[0]}"]
    block.extend(_INDENT + line for line in lines[1:])
    return "\n".join(block)


def supertype(obj: Any, indent: int = 0, max_depth: Optional[int] = None) -> str:
    """Return a human-readable description of ``obj`` and of what it contains.

    Like :func:`type`, but recursive: tuples, lists, sets, frozensets and
    :class:`array.array` are inspected element by element, dictionaries are
    summarised by the types of their keys and values, and other objects are
    described by their type plus their length or ``shape`` when available
    (which covers NumPy arrays, pandas DataFrames, and similar objects).

    Args:
        obj: Any Python object.
        indent: Number of indentation levels (four spaces each) prepended to
            every line of the result. Useful when embedding the output in a
            larger report.
        max_depth: Maximum number of nested levels shown as a tree. Deeper
            containers are summarised on a single line. ``None`` (the default)
            means no limit.

    Returns:
        The description, possibly spanning several lines.

    Example:
        >>> print(supertype([1, 2, [3, "a"]]))
        list with 3 elements:
            - int
            - int
            - list with 2 elements containing int or str
    """
    if indent < 0:
        raise ValueError("indent must be a non-negative integer")
    description = _Describer(max_depth).describe(obj)
    if indent:
        prefix = _INDENT * indent
        description = "\n".join(prefix + line for line in description.splitlines())
    return description
