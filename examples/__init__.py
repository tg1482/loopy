"""Pre-built Loopy databases for learning and experimentation."""

from .product_catalog import product_catalog
from .bookmarks import bookmarks
from .knowledge_graph import knowledge_graph
from .recipes import recipes
from .org_chart import org_chart

__all__ = [
    "product_catalog",
    "bookmarks",
    "knowledge_graph",
    "recipes",
    "org_chart",
]
