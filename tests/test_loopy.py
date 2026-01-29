"""Quick tests for Loopy."""

from loopy import Loopy


def test_basic():
    tree = Loopy()
    assert tree.raw == "<root/>"
    assert tree.exists("/")
    assert tree.ls("/") == []


def test_mkdir():
    tree = Loopy()
    tree.mkdir("/animals/mammals", parents=True)
    assert tree.exists("/animals")
    assert tree.exists("/animals/mammals")
    assert tree.ls("/animals") == ["mammals"]


def test_touch_and_cat():
    tree = Loopy()
    tree.touch("/notes/idea1", "build a tree structure")
    assert tree.cat("/notes/idea1") == "build a tree structure"


def test_rm():
    tree = Loopy()
    tree.mkdir("/a/b/c", parents=True)
    tree.rm("/a/b", recursive=True)
    assert tree.exists("/a")
    assert not tree.exists("/a/b")


def test_mv():
    tree = Loopy()
    tree.touch("/old/item", "data")
    tree.mv("/old/item", "/new/item")
    assert not tree.exists("/old/item")
    assert tree.exists("/new/item")
    assert tree.cat("/new/item") == "data"


def test_cp():
    tree = Loopy()
    tree.touch("/src/file", "content")
    tree.cp("/src/file", "/dst/file")
    assert tree.exists("/src/file")
    assert tree.exists("/dst/file")
    assert tree.cat("/dst/file") == "content"


def test_grep():
    tree = Loopy()
    tree.mkdir("/animals/mammals/dogs", parents=True)
    tree.mkdir("/animals/mammals/cats", parents=True)
    tree.mkdir("/animals/birds", parents=True)

    results = tree.grep("mam")
    assert "/animals/mammals" in results


def test_sed():
    tree = Loopy()
    tree.touch("/doc", "hello world")
    tree.sed("/doc", "world", "universe")
    assert tree.cat("/doc") == "hello universe"


def test_tree_viz():
    tree = Loopy()
    tree.mkdir("/animals/mammals/dogs", parents=True)
    tree.touch("/animals/mammals/dogs/labrador", "friendly")
    tree.mkdir("/animals/birds", parents=True)

    viz = tree.tree()
    assert "animals" in viz
    assert "mammals" in viz
    assert "dogs" in viz


def test_agent_usecase():
    """Simulate an agent categorizing items."""
    tree = Loopy()

    # Agent sees an image and wants to categorize it
    category_path = "/images/animals/dogs/golden_retriever"

    # Check if similar path exists, if not create it
    if not tree.exists("/images/animals/dogs"):
        tree.mkdir("/images/animals/dogs", parents=True)

    tree.touch(category_path, "img_001.jpg, img_002.jpg")

    # Agent sees another image
    tree.touch("/images/animals/cats/persian", "img_003.jpg")

    # Search for all animal images
    animal_paths = tree.grep("animals")
    assert len(animal_paths) > 0

    # View the structure
    print("\n" + tree.tree())
    print("\nRaw:", tree.raw)


if __name__ == "__main__":
    test_basic()
    test_mkdir()
    test_touch_and_cat()
    test_rm()
    test_mv()
    test_cp()
    test_grep()
    test_sed()
    test_tree_viz()
    test_agent_usecase()
    print("\n✓ All tests passed!")
