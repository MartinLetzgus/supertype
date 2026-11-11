# supertype

[![PyPI version](https://img.shields.io/pypi/v/supertype-python)](https://pypi.org/project/supertype-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/supertype-python)](https://pypi.org/project/supertype-python/)
[![Tests](https://github.com/MartinLetzgus/supertype/actions/workflows/tests.yml/badge.svg)](https://github.com/MartinLetzgus/supertype/actions/workflows/tests.yml)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/supertype-python?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/supertype-python)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**`type()` tells you what an object is. `supertype()` also tells you what is inside it.**

`supertype` is a tiny, dependency-free Python package with a single function. Point it at a
nested data structure (an API response, a parsed config, a batch of tensors) and get a readable
summary of its shape instead of scrolling through a wall of `print()` output, or a type hint you
can paste into your code.

## Installation

```bash
pip install supertype-python
```

Requires Python 3.8 or newer. The package has no dependencies.

## Quick start

```python
>>> from array import array
>>> from supertype import supertype
>>> data = (
...     array("l", [1, 2, 3, 4, 5]),
...     [[0, 1, 2], "bbb"],
...     5,
...     {"x": "X", "y": "Y", "z": "Z"},
...     {10, 20, 30},
... )
>>> print(supertype(data))
tuple with 5 elements:
    - array with 5 elements containing int
    - list with 2 elements:
        - list with 3 elements containing int
        - str with length 3
    - int
    - dict with 3 items mapping str to str
    - set with 3 elements containing int

```

Compare with what the built-in gives you:

```python
>>> type(data)
<class 'tuple'>

```

## Exploring JSON and other nested data

Dictionaries that hold containers are shown as a tree, one bullet per key. Consecutive elements
with the same structure are merged into a single `N x` bullet, so a list of thousands of
records stays readable:

```python
>>> response = {
...     "status": "ok",
...     "users": [
...         {"name": "Ada", "age": 36, "roles": ["admin"]},
...         {"name": "Charlotte", "age": 29, "roles": []},
...         {"name": "Bob", "age": 41, "roles": ["dev", "ops"]},
...     ],
... }
>>> print(supertype(response))
dict with 2 items:
    - 'status': str with length 2
    - 'users': list with 3 elements:
        - 3 x dict with 3 items:
            - 'name': str
            - 'age': int
            - 'roles': list containing str (or empty)

```

When merged elements differ in size (string lengths, number of elements), the sizes are left out
of the merged bullet, and `(or empty)` marks containers that are sometimes empty.

## Getting a type hint

Pass `as_hint=True` to get a type hint you can paste into your code:

```python
>>> supertype(response, as_hint=True)
'dict[str, str | list[dict[str, str | int | list[str]]]]'

```

Containers of the same kind are merged into one hint (`list[int] | list[str]` becomes
`list[int | str]`), short tuples are written positionally (`tuple[int, str]`) and long ones as
`tuple[int, ...]`. The `X | Y` syntax needs Python 3.10+ at runtime, or
`from __future__ import annotations` in older versions.

## What it describes

| Object | Example output |
| --- | --- |
| `list`, `tuple`, `set`, `frozenset`, `array.array` | `list with 3 elements containing int or str` |
| Containers of containers | an indented tree, one bullet per element |
| `dict` with flat values | `dict with 2 items mapping str to int or str` |
| `dict` holding containers | an indented tree, one bullet per key |
| `str`, `bytes`, `bytearray` | `str with length 12` |
| Objects with a `shape` (NumPy, pandas, PyTorch, ...) | `ndarray with shape (3, 4) and dtype float64` |
| Other objects with a length | `range with 10 elements` |
| Anything else | the type name, e.g. `int`, `NoneType`, `MyClass` |

Mixed contents are listed as alternatives, in the order they first appear:

```python
>>> print(supertype([1, "a", 2.5, "b"]))
list with 4 elements containing int, str, or float

```

Self-referencing structures are detected instead of crashing:

```python
>>> loop = [1]
>>> loop.append(loop)
>>> print(supertype(loop))
list with 2 elements:
    - int
    - list (circular reference)

```

## Options

```python
supertype(obj, indent=0, max_depth=None, max_items=20, as_hint=False)
```

- **`max_items`** caps the number of bullets shown for each container (a merged `N x` bullet
  counts as one). Pass `None` to show everything. One-line summaries still take every element
  into account.

  ```python
  >>> print(supertype([[1], "a"] * 50, max_items=3))
  list with 100 elements:
      - list with 1 element containing int
      - str with length 1
      - list with 1 element containing int
      - ... and 97 more elements

  ```

- **`max_depth`** limits how many nested levels are shown as a tree. Deeper levels are collapsed
  into a one-line summary:

  ```python
  >>> print(supertype([[[1, 2]], [[3]]], max_depth=0))
  list with 2 elements containing list of list of int

  ```

- **`indent`** prepends that many indentation levels (four spaces each) to every line, which is
  handy when embedding the output in a log or a larger report.

- **`as_hint`** returns a type hint instead of a description (see above). The other options do
  not apply to hints.

## Development

```bash
git clone https://github.com/MartinLetzgus/supertype.git
cd supertype
pip install -e ".[test]"
pytest
```

`pytest` runs the unit tests and also checks every example in this README, so the documentation
cannot drift from the real output.

Ideas, bug reports and pull requests are welcome on the
[issue tracker](https://github.com/MartinLetzgus/supertype/issues).

## Contributors

- Martin Letzgus
- Antoine Thiol
- Quentin Petit
- Claude (Anthropic)

## License

[MIT](LICENSE)
