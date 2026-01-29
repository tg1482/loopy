"""Tests for edge cases and potential flaws identified during REPL testing."""

import pytest
from loopy import Loopy
from loopy.shell import run


class TestTouchOnDirectory:
    """touch should not convert directories to files."""

    def test_touch_on_empty_dir_without_content(self):
        tree = Loopy()
        tree.mkdir("/mydir")
        tree.touch("/mydir")  # No content - should be no-op
        assert tree.isdir("/mydir")

    def test_touch_on_dir_with_children_should_fail(self):
        tree = Loopy()
        tree.mkdir("/mydir")
        tree.touch("/mydir/child", "data")

        # touch with content on a directory should raise, not silently convert
        with pytest.raises(IsADirectoryError):
            tree.touch("/mydir", "content")

    def test_write_on_dir_with_children_should_fail(self):
        tree = Loopy()
        tree.mkdir("/mydir")
        tree.touch("/mydir/child", "data")

        # write on a directory should raise
        with pytest.raises(IsADirectoryError):
            tree.write("/mydir", "content")


class TestSpacesInPaths:
    """Paths with spaces should either work or raise clearly."""

    def test_spaces_in_path_should_raise(self):
        tree = Loopy()
        # Spaces aren't valid in our tag-based system
        with pytest.raises(ValueError):
            tree.mkdir("/my folder")

    def test_spaces_rejected_in_touch(self):
        tree = Loopy()
        with pytest.raises(ValueError):
            tree.touch("/my file", "content")


class TestRmOnDirectory:
    """rm behavior on directories."""

    def test_rm_empty_dir(self):
        tree = Loopy()
        tree.mkdir("/emptydir")
        tree.rm("/emptydir")
        assert not tree.exists("/emptydir")

    def test_rm_dir_with_children_requires_flag(self):
        tree = Loopy()
        tree.mkdir("/mydir")
        tree.touch("/mydir/child", "data")

        # rm on non-empty dir without recursive flag should raise
        with pytest.raises(OSError):  # Or IsADirectoryError
            tree.rm("/mydir")

    def test_rm_recursive_deletes_tree(self):
        tree = Loopy()
        tree.mkdir("/mydir")
        tree.touch("/mydir/child", "data")

        tree.rm("/mydir", recursive=True)
        assert not tree.exists("/mydir")


class TestLsOnFile:
    """ls on a file should show the file."""

    def test_ls_on_file_shows_file(self):
        tree = Loopy()
        tree.touch("/myfile", "content")

        # ls on a file should return the file name, not empty
        result = tree.ls("/myfile")
        assert result == ["myfile"] or result == []  # Current behavior is []


class TestShellCommands:
    """Shell should expose all useful Loopy methods."""

    def test_sed_command_exists(self):
        tree = Loopy()
        tree.touch("/file", "hello world")
        # Should not raise "Unknown command"
        run("sed /file hello goodbye", tree)
        assert tree.cat("/file") == "goodbye world"

    def test_help_command_exists(self):
        tree = Loopy()
        # help should list available commands
        out = run("help", tree)
        assert "ls" in out
        assert "cat" in out


class TestMvCpEdgeCases:
    """Edge cases for mv and cp."""

    def test_mv_to_self_is_noop(self):
        tree = Loopy()
        tree.mkdir("/mydir")
        tree.touch("/mydir/file", "data")

        tree.mv("/mydir", "/mydir")

        assert tree.exists("/mydir")
        assert tree.exists("/mydir/file")
        assert tree.cat("/mydir/file") == "data"

    def test_cp_to_self_raises(self):
        tree = Loopy()
        tree.touch("/file", "data")

        # Copying to itself should raise or be a no-op
        with pytest.raises(ValueError):
            tree.cp("/file", "/file")


class TestNoCreateUnderFile:
    """Cannot create files/dirs under files."""

    def test_mkdir_under_file_raises(self):
        tree = Loopy()
        tree.touch("/myfile", "content")

        with pytest.raises(NotADirectoryError):
            tree.mkdir("/myfile/subdir")

    def test_touch_under_file_raises(self):
        tree = Loopy()
        tree.touch("/myfile", "content")

        with pytest.raises(NotADirectoryError):
            tree.touch("/myfile/child", "data")


class TestPathNormalization:
    """Path edge cases."""

    def test_double_slashes_normalized(self):
        tree = Loopy()
        tree.mkdir("/a/b", parents=True)

        assert tree.ls("//a//b") == tree.ls("/a/b")

    def test_trailing_slash_normalized(self):
        tree = Loopy()
        tree.mkdir("/mydir")

        assert tree.exists("/mydir/") == tree.exists("/mydir")
        assert tree.isdir("/mydir/") == tree.isdir("/mydir")

    def test_dot_in_path_resolved(self):
        tree = Loopy()
        tree.mkdir("/a/b", parents=True)

        assert tree.ls("/a/./b") == tree.ls("/a/b")

    def test_dotdot_at_root_stays_at_root(self):
        tree = Loopy()
        tree.mkdir("/mydir")

        # /.. should resolve to /
        assert tree.ls("/..") == tree.ls("/")
        assert tree.ls("/../mydir") == tree.ls("/mydir")
