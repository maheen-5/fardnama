from hashlib import sha256

from app.services.merkle import merkle_root


def _leaf(x):
    return sha256(("leaf:" + x).encode()).hexdigest()


def _node(a, b):
    return sha256(("node:" + a + ":" + b).encode()).hexdigest()


def test_merkle_tree_single_leaf():
    assert merkle_root(["abc"]) == merkle_root(["abc"])
    assert merkle_root(["abc"]) != merkle_root(["def"])
    assert merkle_root(["abc"]) == _leaf("abc")


def test_merkle_tree_odd_number_of_leaves():
    root = merkle_root(["a", "b", "c"])
    assert isinstance(root, str)
    assert len(root) == 64
    # Expected structure: node(node(a,b), c) with the odd leaf promoted, not duplicated.
    assert root == _node(_node(_leaf("a"), _leaf("b")), _leaf("c"))


def test_merkle_root_changes_on_tamper():
    assert merkle_root(["a", "b", "c"]) != merkle_root(["a", "x", "c"])


def test_merkle_tamper_detected_at_every_position():
    leaves = [sha256(f"evidence-{i}".encode()).hexdigest() for i in range(7)]
    original = merkle_root(leaves)
    for i in range(len(leaves)):
        altered = list(leaves)
        altered[i] = sha256(b"tampered").hexdigest()
        assert merkle_root(altered) != original, f"tamper at leaf {i} not detected"


def test_merkle_root_depends_on_order():
    assert merkle_root(["a", "b"]) != merkle_root(["b", "a"])


def test_merkle_odd_node_is_not_duplicated():
    # Regression: with duplicate-last-leaf, these two different evidence sets had the SAME root.
    assert merkle_root(["a", "b", "c"]) != merkle_root(["a", "b", "c", "c"])


def test_merkle_empty_tree_is_defined_and_distinct():
    empty = merkle_root([])
    assert len(empty) == 64
    assert empty != merkle_root([""])


def test_merkle_expected_root_for_two_leaves():
    assert merkle_root(["a", "b"]) == _node(_leaf("a"), _leaf("b"))
