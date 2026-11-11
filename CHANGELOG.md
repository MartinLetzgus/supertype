# Changelog

## 1.2.0 (unreleased)

### Fixed
- Self-referencing lists, tuples, sets and dicts no longer raise `RecursionError`; they are
  reported as `list (circular reference)`.
- The `indent` argument now does something: it indents every line of the output.
- Classes such as `numpy.ndarray` (as opposed to instances) are no longer described as having a
  shape.

### Changed
- Flat containers are summarised by element *type*: `["a", "bb"]` is now
  `list with 2 elements containing str` instead of
  `... containing str with length 1, str with length 2`.
- Mixed element types are joined with "or" (`int, str, or float`), matching dict summaries.
- Nested alternatives in type signatures are parenthesised: `list of (list of int or str)`.
- Tree output uses a consistent four-space indent at every level.
- `bytes` and `bytearray` report a length, like `str`.
- Objects with a `dtype` (NumPy, pandas, PyTorch) also show it: `ndarray with shape (3, 4) and dtype float64`.
- Python 3.8 or newer is now required.

### Added
- Dictionaries that hold containers are shown as a tree with one bullet per key
  (`- 'users': list with 3 elements:`). Flat dictionaries keep their one-line summary.
- Consecutive elements with the same structure are merged into one `N x` bullet. When their
  sizes differ, the merged bullet leaves sizes out, and `(or empty)` marks containers that are
  sometimes empty. 10,000 JSON records now print in a handful of lines.
- `max_items` argument (default 20) to cap the number of bullets per container, followed by
  `... and N more elements`.
- `as_hint=True` returns a type hint such as `dict[str, list[dict[str, str | int]]]`, merging
  containers of the same kind.
- `max_depth` argument to collapse deeply nested structures.
- `pyproject.toml` packaging metadata, `__version__`, type hints and a `py.typed` marker.
- Test suite (including README doctests) and a GitHub Actions workflow for Python 3.8 to 3.13.
