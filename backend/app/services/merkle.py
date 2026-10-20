"""Small SHA-256 Merkle-tree utility for core-module tests/prototype use.

This is a Mid-1 PROTOTYPE of the integrity primitive. It is not a custody ledger and nothing
here is anchored on a blockchain.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Iterable


def _hash_leaf(leaf: str) -> str:
    # The "leaf:" prefix separates leaf hashes from internal-node hashes.
    return sha256(("leaf:" + leaf).encode("utf-8")).hexdigest()


def _hash_pair(left: str, right: str) -> str:
    # The "node:" prefix separates internal nodes from raw evidence hashes.
    return sha256(("node:" + left + ":" + right).encode("utf-8")).hexdigest()


def merkle_root(leaves: Iterable[str]) -> str:
    """Return a deterministic Merkle root.

    Leaf strings are treated as already-computed digest values and are domain-prefixed before
    combining. An empty tree returns the SHA-256 digest of an explicit empty marker.

    Odd levels: the unpaired last node is PROMOTED unchanged to the next level (it is not
    duplicated). Duplicating it would make [a, b, c] and [a, b, c, c] produce the same root,
    so two different evidence sets could not be told apart.
    """
    current = list(leaves)
    if not current:
        return sha256(b"fardnama:empty-merkle-tree").hexdigest()

    current = [_hash_leaf(leaf) for leaf in current]
    while len(current) > 1:
        next_level = [
            _hash_pair(current[index], current[index + 1])
            for index in range(0, len(current) - 1, 2)
        ]
        if len(current) % 2 == 1:
            next_level.append(current[-1])  # promote the odd node
        current = next_level
    return current[0]
