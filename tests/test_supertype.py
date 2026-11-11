import sys
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


def test_flat_dict_is_summarised_on_one_line():
    assert (
        supertype({1: "a", "k": None})
        == "dict with 2 items mapping int or str to str or NoneType"
    )


def test_dict_with_containers_is_shown_as_a_tree():
    assert supertype({1: {"x": None}, "k": []}) == "\n".join(
        [
            "dict with 2 items:",
            "    - 1: dict with 1 item mapping str to NoneType",
            "    - 'k': list with 0 elements (empty)",
        ]
    )


def test_json_like_data():
    data = {
        "status": "ok",
        "users": [{"name": "Ada", "tags": ["x"]}, {"name": "Bob", "tags": ["y"]}],
    }
    assert supertype(data) == "\n".join(
        [
            "dict with 2 items:",
            "    - 'status': str with length 2",
            "    - 'users': list with 2 elements:",
            "        - 2 x dict with 2 items:",
            "            - 'name': str with length 3",
            "            - 'tags': list with 1 element containing str",
        ]
    )


def test_long_keys_are_shortened():
    line = supertype({"k" * 100: [1]}).splitlines()[1]
    assert len(line) < 100
    assert "..." in line


def test_dict_signatures_describe_nested_types():
    assert (
        supertype({"a": {"b": [1, 2]}}, max_depth=0)
        == "dict with 1 item mapping str to dict from str to list of int"
    )


def test_list_of_flat_dicts_stays_on_one_line():
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


@pytest.mark.parametrize(
    "kwargs", [{"indent": -1}, {"max_depth": -1}, {"max_items": 0}]
)
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
    assert supertype(obj) == "\n".join(
        ["dict with 1 item:", "    - 'self': dict (circular reference)"]
    )
    assert supertype(obj, max_depth=0) == (
        "dict with 1 item mapping str to dict (circular reference)"
    )


def test_shared_but_acyclic_references_are_not_circular():
    inner = [1]
    assert supertype([inner, inner]) == "\n".join(
        ["list with 2 elements:", "    - 2 x list with 1 element containing int"]
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
        supertype({"k": [{"a": 1, "b": "x"}]}, max_depth=0)
        == "dict with 1 item mapping str to list of dict from str to (int or str)"
    )


# -- merging and truncation ------------------------------------------------


def test_consecutive_identical_elements_are_merged():
    assert supertype([[1, 2]] * 1000) == "\n".join(
        ["list with 1000 elements:", "    - 1000 x list with 2 elements containing int"]
    )


def test_only_consecutive_elements_are_merged():
    assert supertype([[1], [1], "a", [1]]) == "\n".join(
        [
            "list with 4 elements:",
            "    - 2 x list with 1 element containing int",
            "    - str with length 1",
            "    - list with 1 element containing int",
        ]
    )


def test_records_with_different_sizes_are_merged_without_sizes():
    users = [
        {"name": "Ada", "roles": ["admin"]},
        {"name": "Charlotte", "roles": ["dev", "ops"]},
    ]
    assert supertype(users) == "\n".join(
        [
            "list with 2 elements:",
            "    - 2 x dict with 2 items:",
            "        - 'name': str",
            "        - 'roles': list containing str",
        ]
    )


def test_empty_containers_merge_with_non_empty_ones():
    records = [{"id": i, "tags": ["a"] * (i % 3)} for i in range(10_000)]
    assert supertype(records) == "\n".join(
        [
            "list with 10000 elements:",
            "    - 10000 x dict with 2 items:",
            "        - 'id': int",
            "        - 'tags': list containing str (or empty)",
        ]
    )
    assert supertype([[], ["a"], [], ["b", "c"]]) == "\n".join(
        ["list with 4 elements:", "    - 4 x list containing str (or empty)"]
    )


def test_different_structures_are_not_merged():
    assert supertype([{"a": [1]}, {"b": [1]}, {"a": ["x"]}]) == "\n".join(
        [
            "list with 3 elements:",
            "    - dict with 1 item:",
            "        - 'a': list with 1 element containing int",
            "    - dict with 1 item:",
            "        - 'b': list with 1 element containing int",
            "    - dict with 1 item:",
            "        - 'a': list with 1 element containing str",
        ]
    )


def test_max_items_truncates_long_trees():
    obj = [[i] if i % 2 else ("x",) for i in range(30)]
    assert supertype(obj, max_items=3) == "\n".join(
        [
            "list with 30 elements:",
            "    - tuple with 1 element containing str",
            "    - list with 1 element containing int",
            "    - tuple with 1 element containing str",
            "    - ... and 27 more elements",
        ]
    )
    assert len(supertype(obj).splitlines()) == 1 + 20 + 1
    assert len(supertype(obj, max_items=None).splitlines()) == 1 + 30


def test_max_items_counts_merged_runs_as_one_bullet():
    obj = [[1]] * 5 + ["a"] + [[1]] * 5
    assert supertype(obj, max_items=2) == "\n".join(
        [
            "list with 11 elements:",
            "    - 5 x list with 1 element containing int",
            "    - str with length 1",
            "    - ... and 5 more elements",
        ]
    )


def test_max_items_truncates_dict_trees():
    obj = {i: [i] for i in range(4)}
    assert supertype(obj, max_items=2) == "\n".join(
        [
            "dict with 4 items:",
            "    - 0: list with 1 element containing int",
            "    - 1: list with 1 element containing int",
            "    - ... and 2 more items",
        ]
    )


def test_summaries_still_consider_every_element():
    obj = [[1]] * 50 + [["a"]]
    assert supertype(obj, max_depth=0) == (
        "list with 51 elements containing list of int or list of str"
    )


def test_output_is_ascii():
    supertype([[1]] * 3 + list(range(40)), max_items=2).encode("ascii")


# -- type hints --------------------------------------------------------------


@pytest.mark.parametrize(
    "obj, expected",
    [
        (5, "int"),
        (None, "None"),
        ("s", "str"),
        ([1, 2], "list[int]"),
        ([1, "a", None], "list[int | str | None]"),
        ({1, 2}, "set[int]"),
        (frozenset({"a"}), "frozenset[str]"),
        (array("d", [1.0]), "array[float]"),
        ({"a": 1, "b": "x"}, "dict[str, int | str]"),
        ((1, "a"), "tuple[int, str]"),
        (tuple(range(9)), "tuple[int, ...]"),
        ((), "tuple[()]"),
        ([], "list"),
        ({}, "dict"),
        ([[1, 2], "a"], "list[list[int] | str]"),
    ],
)
def test_type_hints(obj, expected):
    assert supertype(obj, as_hint=True) == expected


def test_hints_merge_containers_of_the_same_kind():
    assert supertype([[], [1], ["a"]], as_hint=True) == "list[list[int | str]]"
    assert (
        supertype([{"a": 1}, {"b": None, "c": []}], as_hint=True)
        == "list[dict[str, int | None | list]]"
    )


def test_hint_for_json_like_data():
    data = {"users": [{"name": "Ada", "age": 36}], "page": 1}
    assert supertype(data, as_hint=True) == "dict[str, list[dict[str, str | int]] | int]"


def test_hint_for_circular_reference():
    obj = [1]
    obj.append(obj)
    assert supertype(obj, as_hint=True) == "list[int | list]"


def test_hint_for_subclasses_uses_bare_name():
    from collections import OrderedDict, namedtuple

    Point = namedtuple("Point", "x y")
    assert supertype(Point(1, 2), as_hint=True) == "Point"
    assert supertype(OrderedDict(a=1), as_hint=True) == "OrderedDict"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="X | Y needs Python 3.10")
def test_hints_evaluate_to_real_types():
    hint = supertype({"a": [(1, "x")], "b": {2.5}, "c": None}, as_hint=True)
    assert hint == "dict[str, list[tuple[int, str]] | set[float] | None]"
    eval(hint)
