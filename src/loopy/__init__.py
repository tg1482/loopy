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
from .file_store import FileBackedLoopy, load, save

__version__ = "0.2.3"
__all__ = ["Loopy", "FileBackedLoopy", "load", "save"]
