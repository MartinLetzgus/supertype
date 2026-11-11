"""Core implementation of :func:`supertype`.

The prose output has two forms:

* a *summary*, used when a container holds only "flat" values, for example
  ``list with 3 elements containing int or str``;
* a *tree*, used when a container holds other containers. Each element (or,
  for a dict, each key) is then described on its own bullet line, indented by
  four spaces per level. Consecutive identical elements are merged into a
  single ``N x`` bullet.

With ``as_hint=True`` a type hint such as ``list[dict[str, int | str]]`` is
returned instead.
"""

from __future__ import annotations

import reprlib
from array import array
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union

__all__ = ["supertype"]

#: Container types whose elements are inspected recursively.
SUPPORTED_CONTAINERS = (tuple, list, array, set, frozenset)

#: Sized types whose length is reported as a "length" rather than a number of
#: elements.
_TEXT_TYPES = (str, bytes, bytearray)

#: Types that are written with type parameters in hints (``list[int]``).
#: Subclasses (namedtuples, custom lists...) are written as their bare name,
#: since they are not necessarily generic.
_GENERIC_HINT_TYPES = (list, set, frozenset, dict, array)

#: Tuples up to this length get a positional hint (``tuple[int, str]``);
#: longer ones are written ``tuple[int | str, ...]``.
_MAX_POSITIONAL_TUPLE = 5

_INDENT = "    "

_key_repr = reprlib.Repr()
_key_repr.maxstring = 40
_key_repr.maxother = 40


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


_EMPTY = " (empty)"
_OR_EMPTY = " (or empty)"


def _merge_loose(first: str, second: str) -> Optional[str]:
    """Merge two loose descriptions that only differ by empty containers.

    ``list (empty)`` and ``list containing str`` merge into
    ``list containing str (or empty)``. Returns None when the descriptions
    have a different structure.
    """
    if first == second:
        return first
    first_lines, second_lines = first.splitlines(), second.splitlines()
    if len(first_lines) != len(second_lines):
        return None
    merged = []
    for a, b in zip(first_lines, second_lines):
        if a == b:
            merged.append(a)
            continue
        line = _merge_empty_line(a, b) or _merge_empty_line(b, a)
        if line is None:
            return None
        merged.append(line)
    return "\n".join(merged)


def _strip_suffix(text: str, suffix: str) -> str:
    return text[: -len(suffix)] if text.endswith(suffix) else text


def _merge_empty_line(empty: str, other: str) -> Optional[str]:
    if _strip_suffix(empty, _OR_EMPTY) == _strip_suffix(other, _OR_EMPTY):
        return _strip_suffix(other, _OR_EMPTY) + _OR_EMPTY
    if not empty.endswith(_EMPTY):
        return None
    prefix = empty[: -len(_EMPTY)] + " containing "
    if not other.startswith(prefix):
        return None
    return other if other.endswith(_OR_EMPTY) else other + _OR_EMPTY


def _bullet(description: str, label: str = "") -> str:
    """Turn a (possibly multi-line) description into an indented bullet."""
    lines = description.splitlines()
    block = [f"{_INDENT}- {label}{lines[0]}"]
    block.extend(_INDENT + line for line in lines[1:])
    return "\n".join(block)


class _Union:
    """An ordered union of hint nodes.

    Generic nodes of the same kind are merged rather than repeated, so
    ``list[int] | list[str] | list`` becomes ``list[int | str]`` and two dicts
    with different value types become a single ``dict[str, A | B]``.
    """

    def __init__(self) -> None:
        self.members: Dict[Any, _HintNode] = {}

    def add(self, node: _HintNode) -> None:
        if isinstance(node, _Generic):
            existing = self.members.get(node.key)
            if isinstance(existing, _Generic):
                existing.merge(node)
                return
            self.members[node.key] = node
        else:
            self.members.setdefault(node, node)

    def render(self) -> str:
        return " | ".join(_render(member) for member in self.members.values())


class _Generic:
    """A parameterised type such as ``list[...]`` or ``dict[..., ...]``."""

    def __init__(self, name: str, arity: int, variadic: bool = False) -> None:
        self.name = name
        self.variadic = variadic
        self.params = [_Union() for _ in range(arity)]

    @property
    def key(self) -> Tuple[str, bool]:
        return (self.name, self.variadic)

    def merge(self, other: "_Generic") -> None:
        for mine, theirs in zip(self.params, other.params):
            for member in theirs.members.values():
                mine.add(member)

    def render(self) -> str:
        if not any(param.members for param in self.params):
            return self.name
        params = ", ".join(param.render() for param in self.params)
        return f"{self.name}[{params}, ...]" if self.variadic else f"{self.name}[{params}]"


#: A hint is either a plain string (``int``, ``tuple[int, str]``) or a generic.
_HintNode = Union[str, _Generic]


def _render(node: _HintNode) -> str:
    return node.render() if isinstance(node, _Generic) else node


class _Describer:
    """Holds the options and traversal state for one call to :func:`supertype`."""

    def __init__(self, max_depth: Optional[int], max_items: Optional[int]) -> None:
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be None or a non-negative integer")
        if max_items is not None and max_items < 1:
            raise ValueError("max_items must be None or a positive integer")
        self.max_depth = max_depth
        self.max_items = max_items
        # ids of the containers on the current path, to detect cycles.
        self._path: Set[int] = set()

    def _enter(self, obj: Any) -> bool:
        """Mark ``obj`` as being visited; return False if it already is."""
        if id(obj) in self._path:
            return False
        self._path.add(id(obj))
        return True

    def _leave(self, obj: Any) -> None:
        self._path.discard(id(obj))

    def _can_expand(self, depth: int) -> bool:
        return self.max_depth is None or depth < self.max_depth

    def _expands(self, obj: Any, depth: int) -> bool:
        """Whether ``obj``, described at ``depth``, is shown as a tree."""
        if not self._can_expand(depth) or not obj:
            return False
        if isinstance(obj, dict):
            return any(_is_inspected(value) for value in obj.values())
        # A sequence or set becomes a tree when it holds another sequence or
        # set, or a dict that is itself shown as a tree.
        return any(
            _is_supported_container(item)
            or (isinstance(item, dict) and self._expands(item, depth + 1))
            for item in obj
        )

    # -- short type signatures ("list of int", "dict from str to int") ------

    def signature(self, obj: Any) -> str:
        if not _is_inspected(obj):
            return _type_name(obj)
        if not obj:
            return f"empty {_type_name(obj)}"
        if not self._enter(obj):
            return _circular(obj)
        try:
            if isinstance(obj, dict):
                keys = _group(_unique(self.signature(k) for k in obj))
                values = _group(_unique(self.signature(v) for v in obj.values()))
                return f"{_type_name(obj)} from {keys} to {values}"
            items = _group(_unique(self.signature(i) for i in obj))
            return f"{_type_name(obj)} of {items}"
        finally:
            self._leave(obj)

    # -- type hints ("list[int]", "dict[str, int | str]") --------------------

    def hint(self, obj: Any) -> _HintNode:
        if obj is None:
            return "None"
        name = _type_name(obj)
        is_tuple = type(obj) is tuple
        if not (is_tuple or type(obj) in _GENERIC_HINT_TYPES):
            return name
        if not obj:
            return "tuple[()]" if is_tuple else _Generic(name, 2 if name == "dict" else 1)
        if not self._enter(obj):
            # Recursive types cannot be written inline: fall back to the
            # unparameterised name.
            return name
        try:
            if isinstance(obj, dict):
                node = _Generic(name, 2)
                for key, value in obj.items():
                    node.params[0].add(self.hint(key))
                    node.params[1].add(self.hint(value))
                return node
            if is_tuple and len(obj) <= _MAX_POSITIONAL_TUPLE:
                return f"tuple[{', '.join(_render(self.hint(i)) for i in obj)}]"
            node = _Generic(name, 1, variadic=is_tuple)
            for item in obj:
                node.params[0].add(self.hint(item))
            return node
        finally:
            self._leave(obj)

    # -- full descriptions ---------------------------------------------------

    def describe(self, obj: Any, depth: int = 0, exact: bool = True) -> str:
        """Describe ``obj``.

        With ``exact=False`` the description leaves out sizes (string
        lengths, element counts, shapes). Such *loose* descriptions are used
        to merge consecutive elements that have the same structure but not
        the same size, such as records whose strings differ in length.
        """
        if _is_inspected(obj):
            return self._describe_collection(obj, depth, exact)
        return _describe_leaf(obj) if exact else _type_name(obj)

    def _describe_collection(self, obj: Any, depth: int, exact: bool) -> str:
        is_dict = isinstance(obj, dict)
        if is_dict or exact:
            # A dict's size is implied by the keys listed in its tree, so it
            # is kept even in loose descriptions.
            noun = "item" if is_dict else "element"
            header = f"{_type_name(obj)} with {_count(len(obj), noun)}"
        else:
            header = _type_name(obj)
        if not obj:
            return f"{header} (empty)"
        if id(obj) in self._path:
            return _circular(obj)

        expands = self._expands(obj, depth)
        self._enter(obj)
        try:
            if is_dict and expands:
                return self._dict_tree(header, obj, depth, exact)
            if expands:
                return self._container_tree(header, obj, depth, exact)
            if is_dict:
                keys = _join_alternatives(_unique(self.signature(k) for k in obj))
                values = _join_alternatives(
                    _unique(self.signature(v) for v in obj.values())
                )
                return f"{header} mapping {keys} to {values}"
            items = _join_alternatives(_unique(self.signature(i) for i in obj))
            return f"{header} containing {items}"
        finally:
            self._leave(obj)

    def _container_tree(self, header: str, obj: Any, depth: int, exact: bool) -> str:
        lines = [header + ":"]
        shown = 0
        for run in self._runs(obj, depth + 1, exact):
            if self.max_items is not None and len(lines) > self.max_items:
                break
            count, child = run
            # Counts are sizes too, so loose descriptions leave them out.
            label = f"{count} x " if count > 1 and exact else ""
            lines.append(_bullet(child, label))
            shown += count
        return self._finish(lines, len(obj) - shown, "element")

    def _runs(self, obj: Any, depth: int, exact: bool) -> Iterator[Tuple[int, str]]:
        """Group consecutive elements of ``obj`` with the same structure.

        Yields ``(count, description)``. The description is exact when every
        element of the run has the same exact description, and loose
        otherwise.
        """
        count = 0
        loose: Optional[str] = None
        precise: Optional[str] = None
        for item in obj:
            item_loose = self.describe(item, depth, exact=False)
            item_precise = self.describe(item, depth) if exact else item_loose
            merged = _merge_loose(loose, item_loose) if count else None
            if merged is not None:
                count += 1
                loose = merged
                if precise != item_precise:
                    precise = None
                continue
            if count:
                yield count, precise if precise is not None else loose
            count, loose, precise = 1, item_loose, item_precise
        if count:
            yield count, precise if precise is not None else loose

    def _dict_tree(self, header: str, obj: dict, depth: int, exact: bool) -> str:
        lines = [header + ":"]
        for key, value in obj.items():
            if self.max_items is not None and len(lines) > self.max_items:
                break
            child = self.describe(value, depth + 1, exact)
            lines.append(_bullet(child, f"{_key_repr.repr(key)}: "))
        return self._finish(lines, len(obj) - (len(lines) - 1), "item")

    @staticmethod
    def _finish(lines: List[str], remaining: int, noun: str) -> str:
        if remaining > 0:
            lines.append(f"{_INDENT}- ... and {_count(remaining, 'more ' + noun)}")
        return "\n".join(lines)


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


def supertype(
    obj: Any,
    indent: int = 0,
    max_depth: Optional[int] = None,
    max_items: Optional[int] = 20,
    as_hint: bool = False,
) -> str:
    """Return a human-readable description of ``obj`` and of what it contains.

    Like :func:`type`, but recursive: tuples, lists, sets, frozensets,
    :class:`array.array` and dictionaries are inspected element by element,
    and other objects are described by their type plus their length or
    ``shape`` when available (which covers NumPy arrays, pandas DataFrames,
    and similar objects).

    Args:
        obj: Any Python object.
        indent: Number of indentation levels (four spaces each) prepended to
            every line of the result. Useful when embedding the output in a
            larger report.
        max_depth: Maximum number of nested levels shown as a tree. Deeper
            containers are summarised on a single line. ``None`` (the default)
            means no limit.
        max_items: Maximum number of bullets shown for each container in a
            tree; the rest is reported as ``... and N more elements``. Runs of
            identical elements count as one bullet. ``None`` means no limit.
            Summaries always take every element into account.
        as_hint: Return a type hint such as ``list[dict[str, int | str]]``
            instead of a description. ``indent``, ``max_depth`` and
            ``max_items`` do not apply to hints.

    Returns:
        The description (possibly spanning several lines) or the type hint.

    Example:
        >>> print(supertype([1, 2, [3, "a"]]))
        list with 3 elements:
            - 2 x int
            - list with 2 elements containing int or str
        >>> supertype([1, 2, [3, "a"]], as_hint=True)
        'list[int | list[int | str]]'
    """
    if indent < 0:
        raise ValueError("indent must be a non-negative integer")
    describer = _Describer(max_depth, max_items)
    if as_hint:
        return _render(describer.hint(obj))
    description = describer.describe(obj)
    if indent:
        prefix = _INDENT * indent
        description = "\n".join(prefix + line for line in description.splitlines())
    return description
