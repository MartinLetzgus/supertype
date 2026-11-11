# supertype

[![PyPI version](https://img.shields.io/pypi/v/supertype-python)](https://pypi.org/project/supertype-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/supertype-python)](https://pypi.org/project/supertype-python/)
[![Tests](https://github.com/MartinLetzgus/supertype/actions/workflows/tests.yml/badge.svg)](https://github.com/MartinLetzgus/supertype/actions/workflows/tests.yml)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/supertype-python?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/supertype-python)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**`type()` tells you what an object is. `supertype()` also tells you what is inside it.**

`supertype` is a tiny, dependency-free Python package with a single function. Point it at a
nested data structure (an API response, a parsed config, a batch of tensors) and get a readable
summary of its shape instead of scrolling through a wall of `print()` output.

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

## What it describes

| Object | Example output |
| --- | --- |
| `list`, `tuple`, `set`, `frozenset`, `array.array` | `list with 3 elements containing int or str` |
| Containers of containers | an indented tree, one bullet per element |
| `dict` | `dict with 2 items mapping str to list of int` |
| `str`, `bytes`, `bytearray` | `str with length 12` |
| Objects with a `shape` (NumPy, pandas, PyTorch…) | `ndarray with shape (3, 4) and dtype float64` |
| Other objects with a length | `range with 10 elements` |
| Anything else | the type name, e.g. `int`, `NoneType`, `MyClass` |

Mixed contents are listed as alternatives, in the order they first appear:

```python
>>> print(supertype([1, "a", 2.5, "b"]))
list with 4 elements containing int, str, or float

```

Dictionaries are summarised by the types of their keys and values, recursively:

```python
>>> print(supertype({"users": [{"name": "Ada", "age": 36}]}))
dict with 1 item mapping str to list of dict from str to (str or int)

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
supertype(obj, indent=0, max_depth=None)
```

- **`max_depth`** limits how many nested levels are shown as a tree. Deeper levels are collapsed
  into a one-line summary:

  ```python
  >>> print(supertype([[[1, 2]], [[3]]], max_depth=0))
  list with 2 elements containing list of list of int

  ```

- **`indent`** prepends that many indentation levels (four spaces each) to every line, which is
  handy when embedding the output in a log or a larger report.

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

## License

[MIT](LICENSE)
