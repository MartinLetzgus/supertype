from array import array

import pytest

from supertype import supertype


@pytest.mark.parametrize(
    "obj, expected",
    [
        (5, "int"),
        (None, "NoneType"),
        (3.5, "float"),
        ("abc", "str with length 3"),
        (b"ab", "bytes with length 2"),
        (range(4), "range with 4 elements"),
        (list, "type"),
        ((i for i in range(3)), "generator"),
    ],
)
def test_leaf_objects(obj, expected):
    assert supertype(obj) == expected


@pytest.mark.parametrize(
    "obj, expected",
    [
        ([], "list with 0 elements (empty)"),
        ((), "tuple with 0 elements (empty)"),
        ({}, "dict with 0 items (empty)"),
        (set(), "set with 0 elements (empty)"),
    ],
)
def test_empty_containers(obj, expected):
    assert supertype(obj) == expected


def test_singular_and_plural():
    assert supertype((1,)) == "tuple with 1 element containing int"
    assert supertype({"a": 1}) == "dict with 1 item mapping str to int"
    assert supertype({"a": 1, "b": 2}) == "dict with 2 items mapping str to int"


def test_flat_container_of_strings_is_summarised_by_type():
    assert supertype(["a", "bb", "ccc"]) == "list with 3 elements containing str"


def test_mixed_types_are_listed_as_alternatives():
    assert supertype([1, 2]) == "list with 2 elements containing int"
    assert supertype([1, "a"]) == "list with 2 elements containing int or str"
    assert (
        supertype([1, "a", 2.0])
        == "list with 3 elements containing int, str, or float"
    )


def test_array_and_frozenset():
    assert supertype(array("l", [1, 2, 3])) == "array with 3 elements containing int"
    assert supertype(frozenset({1.0})) == "frozenset with 1 element containing float"


def test_dict_signatures_describe_nested_types():
    assert supertype({"a": [1, 2]}) == "dict with 1 item mapping str to list of int"
    assert (
        supertype({1: {"x": None}, "k": []})
        == "dict with 2 items mapping int or str to dict from str to NoneType or empty list"
    )


def test_list_of_dicts():
    assert (
        supertype([{"a": 1}, {"b": 2}])
        == "list with 2 elements containing dict from str to int"
    )


def test_nested_containers_are_shown_as_a_tree():
    obj = (array("l", [1, 2]), [[0, 1], "bbb"], 5, {"x": "X"}, {10})
    assert supertype(obj) == "\n".join(
        [
            "tuple with 5 elements:",
            "    - array with 2 elements containing int",
            "    - list with 2 elements:",
            "        - list with 2 elements containing int",
            "        - str with length 3",
            "    - int",
            "    - dict with 1 item mapping str to str",
            "    - set with 1 element containing int",
        ]
    )


def test_deep_nesting_uses_consistent_indentation():
    assert supertype([[[1]]]) == "\n".join(
        [
            "list with 1 element:",
            "    - list with 1 element:",
            "        - list with 1 element containing int",
        ]
    )


def test_max_depth_collapses_deeper_levels():
    assert supertype([[[1]]], max_depth=0) == (
        "list with 1 element containing list of list of int"
    )
    assert supertype([[[1]]], max_depth=1) == "\n".join(
        [
            "list with 1 element:",
            "    - list with 1 element containing list of int",
        ]
    )


def test_indent_prefixes_every_line():
    assert supertype([[1]], indent=1) == "\n".join(
        [
            "    list with 1 element:",
            "        - list with 1 element containing int",
        ]
    )


@pytest.mark.parametrize("kwargs", [{"indent": -1}, {"max_depth": -1}])
def test_negative_arguments_are_rejected(kwargs):
    with pytest.raises(ValueError):
        supertype([1], **kwargs)


def test_self_referencing_list_does_not_recurse_forever():
    obj = [1]
    obj.append(obj)
    assert supertype(obj) == "\n".join(
        [
            "list with 2 elements:",
            "    - int",
            "    - list (circular reference)",
        ]
    )


def test_self_referencing_dict_does_not_recurse_forever():
    obj = {}
    obj["self"] = obj
    assert (
        supertype(obj)
        == "dict with 1 item mapping str to dict (circular reference)"
    )


def test_shared_but_acyclic_references_are_not_circular():
    inner = [1]
    assert supertype([inner, inner]) == "\n".join(
        [
            "list with 2 elements:",
            "    - list with 1 element containing int",
            "    - list with 1 element containing int",
        ]
    )


class _Shaped:
    shape = (2, 3)
    dtype = "float64"


class _Sized:
    def __len__(self):
        return 4


def test_objects_with_shape_and_dtype():
    assert supertype(_Shaped()) == "_Shaped with shape (2, 3) and dtype float64"


def test_custom_sized_object():
    assert supertype(_Sized()) == "_Sized with 4 elements"


def test_classes_are_not_mistaken_for_instances():
    assert supertype(_Shaped) == "type"


def test_numpy_array():
    np = pytest.importorskip("numpy")
    assert (
        supertype(np.zeros((2, 3), dtype="int64"))
        == "ndarray with shape (2, 3) and dtype int64"
    )


def test_version_is_exposed():
    import supertype as package

    assert package.__version__


def test_nested_alternatives_are_parenthesised():
    assert (
        supertype([[[0, 1], "bbb"]], max_depth=0)
        == "list with 1 element containing list of (list of int or str)"
    )
    assert (
        supertype({"k": [{"a": 1, "b": "x"}]})
        == "dict with 1 item mapping str to list of dict from str to (int or str)"
    )
