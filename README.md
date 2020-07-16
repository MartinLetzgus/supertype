## Overview

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
f = (e,c,d)
```
Now, you can import supertype() and just ask the supertype of the object f :
```python
from supertype import supertype

supertype(f)
```

This returns :

```
tuple of 3 elements containing :
    -list of 2 elements containing :
        -list of 3 elements containing {'int'}
        -str of 3 elements
    -int
    -dict of 3 elements
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
