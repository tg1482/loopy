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


# ============================================================================
# Symlink Tests
# ============================================================================


def test_symlink_parse_emit():
    """Test parsing and emitting symlink syntax."""
    # Parse symlink
    tree = Loopy('<root><tasks><task1>content</task1></tasks><refs><task1 @="/tasks/task1"/></refs></root>')
    assert tree.exists("/tasks/task1")
    assert tree.exists("/refs/task1")
    assert tree.islink("/refs/task1")
    assert not tree.islink("/tasks/task1")

    # Round-trip
    raw = tree.raw
    tree2 = Loopy(raw)
    assert tree2.islink("/refs/task1")
    assert tree2.readlink("/refs/task1") == "/tasks/task1"


def test_symlink_ln():
    """Test creating symlinks with ln()."""
    tree = Loopy()
    tree.touch("/tasks/task1", "implement feature")
    tree.ln("/tasks/task1", "/tags/urgent/task1")

    assert tree.exists("/tags/urgent/task1")
    assert tree.islink("/tags/urgent/task1")
    assert tree.readlink("/tags/urgent/task1") == "/tasks/task1"


def test_symlink_ln_into_directory():
    """Test ln when dest is a directory."""
    tree = Loopy()
    tree.touch("/tasks/task1", "content")
    tree.mkdir("/tags/urgent", parents=True)
    tree.ln("/tasks/task1", "/tags/urgent")  # Should create /tags/urgent/task1

    assert tree.islink("/tags/urgent/task1")
    assert tree.readlink("/tags/urgent/task1") == "/tasks/task1"


def test_symlink_ln_dangling():
    """Test that dangling links are allowed."""
    tree = Loopy()
    tree.mkdir("/refs")
    tree.ln("/nonexistent/path", "/refs/dangling")

    assert tree.islink("/refs/dangling")
    assert tree.readlink("/refs/dangling") == "/nonexistent/path"


def test_symlink_ln_exists_error():
    """Test that ln raises error if dest exists."""
    tree = Loopy()
    tree.touch("/a", "content")
    tree.touch("/b", "other")

    try:
        tree.ln("/a", "/b")
        assert False, "Should have raised FileExistsError"
    except FileExistsError:
        pass


def test_symlink_islink_readlink():
    """Test islink() and readlink() methods."""
    tree = Loopy()
    tree.touch("/file", "content")
    tree.ln("/file", "/link")

    assert tree.islink("/link")
    assert not tree.islink("/file")
    assert tree.readlink("/link") == "/file"

    try:
        tree.readlink("/file")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Not a symlink" in str(e)


def test_symlink_cat_follows():
    """Test that cat() follows symlinks."""
    tree = Loopy()
    tree.touch("/real/file", "the content")
    tree.ln("/real/file", "/link")

    assert tree.cat("/link") == "the content"
    assert tree.cat("/link", follow_links=False) == ""  # Link has no content itself


def test_symlink_chain():
    """Test following a chain of symlinks."""
    tree = Loopy()
    tree.touch("/deep/file", "found it")
    tree.ln("/deep/file", "/level1")
    tree.ln("/level1", "/level2")
    tree.ln("/level2", "/level3")

    assert tree.cat("/level3") == "found it"


def test_symlink_cycle_detection():
    """Test that circular symlinks are detected."""
    tree = Loopy()
    tree.mkdir("/a")
    tree.mkdir("/b")
    # Manually create a cycle by parsing
    tree = Loopy('<root><a><b @="/b/a"/></a><b><a @="/a/b"/></b></root>')

    try:
        tree.cat("/a/b")  # Should detect cycle
        assert False, "Should have raised ValueError for cycle"
    except ValueError as e:
        assert "cycle" in str(e).lower()


def test_symlink_ls_follows():
    """Test that ls() follows symlinks to directories."""
    tree = Loopy()
    tree.mkdir("/real/dir", parents=True)
    tree.touch("/real/dir/file1", "a")
    tree.touch("/real/dir/file2", "b")
    tree.ln("/real/dir", "/link_to_dir")

    # ls on link to dir should show target's children
    children = tree.ls("/link_to_dir")
    assert "file1" in children
    assert "file2" in children


def test_symlink_ls_classify():
    """Test that ls(classify=True) shows @ for symlinks."""
    tree = Loopy()
    tree.mkdir("/dir")
    tree.touch("/dir/file", "content")
    tree.ln("/dir/file", "/dir/link")

    classified = tree.ls("/dir", classify=True)
    assert "file" in classified
    assert "link@" in classified


def test_symlink_isdir_isfile_follow():
    """Test isdir/isfile follow symlinks by default."""
    tree = Loopy()
    tree.mkdir("/realdir")
    tree.touch("/realfile", "content")
    tree.ln("/realdir", "/linktodir")
    tree.ln("/realfile", "/linktofile")

    # Following links (default)
    assert tree.isdir("/linktodir")
    assert tree.isfile("/linktofile")

    # Not following links
    assert not tree.isdir("/linktodir", follow_links=False)
    assert not tree.isfile("/linktofile", follow_links=False)


def test_symlink_rm_removes_link():
    """Test that rm removes the link, not the target."""
    tree = Loopy()
    tree.touch("/real", "content")
    tree.ln("/real", "/link")

    tree.rm("/link")

    assert not tree.exists("/link")
    assert tree.exists("/real")
    assert tree.cat("/real") == "content"


def test_symlink_mv_moves_link():
    """Test that mv moves the link, not the target."""
    tree = Loopy()
    tree.touch("/real", "content")
    tree.ln("/real", "/link1")

    tree.mv("/link1", "/link2")

    assert not tree.exists("/link1")
    assert tree.islink("/link2")
    assert tree.readlink("/link2") == "/real"
    assert tree.exists("/real")


def test_symlink_cp_copies_link():
    """Test that cp creates a new link pointing to same target."""
    tree = Loopy()
    tree.touch("/real", "content")
    tree.ln("/real", "/link1")

    tree.cp("/link1", "/link2")

    assert tree.islink("/link1")
    assert tree.islink("/link2")
    assert tree.readlink("/link1") == "/real"
    assert tree.readlink("/link2") == "/real"


def test_symlink_write_follows():
    """Test that write() follows symlinks."""
    tree = Loopy()
    tree.touch("/real", "old content")
    tree.ln("/real", "/link")

    tree.write("/link", "new content")

    assert tree.cat("/real") == "new content"
    assert tree.cat("/link") == "new content"


def test_symlink_tree_display():
    """Test that tree() shows symlinks with -> notation."""
    tree = Loopy()
    tree.touch("/tasks/task1", "content")
    tree.ln("/tasks/task1", "/tags/urgent/task1")

    viz = tree.tree()
    assert "-> /tasks/task1" in viz


def test_symlink_find_type_l():
    """Test that find(type='l') finds symlinks."""
    tree = Loopy()
    tree.touch("/file1", "a")
    tree.touch("/file2", "b")
    tree.ln("/file1", "/link1")
    tree.ln("/file2", "/link2")
    tree.mkdir("/dir")

    links = tree.find("/", type="l")
    assert "/link1" in links
    assert "/link2" in links
    assert "/file1" not in links
    assert "/dir" not in links


def test_symlink_backlinks():
    """Test backlinks() finds all links to a path."""
    tree = Loopy()
    tree.touch("/tasks/task1", "content")
    tree.ln("/tasks/task1", "/tags/auth/task1")
    tree.ln("/tasks/task1", "/tags/urgent/task1")
    tree.ln("/tasks/task1", "/pages/login/task1")

    links = tree.backlinks("/tasks/task1")
    assert len(links) == 3
    assert "/tags/auth/task1" in links
    assert "/tags/urgent/task1" in links
    assert "/pages/login/task1" in links


def test_symlink_info():
    """Test that info() includes link information."""
    tree = Loopy()
    tree.touch("/real", "content")
    tree.ln("/real", "/link")

    info = tree.info("/link")
    assert info["is_link"] is True
    assert info["link_target"] == "/real"
    assert info["type"] == "link"

    real_info = tree.info("/real")
    assert real_info["is_link"] is False
    assert real_info["link_target"] is None


def test_symlink_real_world_scenario():
    """Test a realistic scenario: tasks with multiple tags."""
    tree = Loopy()

    # Create some tasks
    tree.touch("/tasks/task_001", "implement login|status:open")
    tree.touch("/tasks/task_002", "fix auth bug|status:open")
    tree.touch("/tasks/task_003", "add logout|status:done")

    # Tag them
    tree.ln("/tasks/task_001", "/tags/auth/task_001")
    tree.ln("/tasks/task_001", "/tags/urgent/task_001")
    tree.ln("/tasks/task_002", "/tags/auth/task_002")
    tree.ln("/tasks/task_002", "/tags/bug/task_002")
    tree.ln("/tasks/task_003", "/tags/auth/task_003")

    # Associate with pages
    tree.ln("/tasks/task_001", "/pages/login/task_001")
    tree.ln("/tasks/task_003", "/pages/login/task_003")

    # Query: What tasks are tagged 'auth'?
    auth_tasks = tree.ls("/tags/auth")
    assert len(auth_tasks) == 3

    # Query: What are the backlinks to task_001?
    links = tree.backlinks("/tasks/task_001")
    assert len(links) == 3  # auth, urgent, login page

    # Update a task - should reflect everywhere
    tree.write("/tasks/task_001", "implement login|status:done")
    assert "done" in tree.cat("/tags/urgent/task_001")
    assert "done" in tree.cat("/pages/login/task_001")

    # View structure
    print("\n" + tree.tree())


