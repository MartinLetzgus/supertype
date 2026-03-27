## Overview

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/supertype-python?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/supertype-python)

Supertype-python is a package containing a single function, supertype(). This one works like type but gives more information, which could be useful in a development phase.

## Installation

```bash
pip install supertype-python
```

## Usage

Without this package, it would take some precious time and precious attention to know the content of an object like this :

```python
a = [0,1,2]
b = 'bbb'
c = 5
d = {"x": "X", "y": "Y", "z": "Z"}
e = [a,b]
f = array('l', [1, 2, 3, 4, 5])
g = (f,e,c,d)
```
Now, you can import supertype() and inspect the object `g`:
```python
from supertype import supertype

print(supertype(g))
```

This returns:

```
tuple with 4 elements:
    - array with 5 elements containing int
    - list with 2 elements:
      - list with 3 elements containing int
      - str with length 3
    - int
    - dict with 3 items mapping str to str
```

This also works with objects from other librairies and even with you homemade objects !


## What should be added soon

-correction of language approximations\
-specific treatment for some types (not very useful to know the size of a string for example)\
-better comments\
-check compatibility with all python 3, see if it can go to python 2\
-...

If you have any idea or suggestion feel free to contact me on my email.

## Contributors

Martin Letzgus\
Antoine Thiol\
Quentin Petit

## License
[MIT](https://choosealicense.com/licenses/mit/)