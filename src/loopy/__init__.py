"""
Loopy - A filesystem-like API over a tree stored as a string.

Usage:
    from loopy import Loopy

    tree = Loopy()
    tree.mkdir("/animals/mammals", parents=True)
    tree.touch("/animals/mammals/dog", "golden retriever")
    tree.cat("/animals/mammals/dog")  # -> "golden retriever"
    tree.ls("/animals")  # -> ["mammals"]
    tree.grep("mam")  # -> ["/animals/mammals"]
"""

from .core_v2 import Loopy

__version__ = "0.1.0"
__all__ = ["Loopy"]
