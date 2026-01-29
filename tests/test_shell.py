"""Focused tests for the text shell runner."""

import pytest

from loopy import Loopy
from loopy.shell import run


def test_run_ls_and_grep_pipeline():
    tree = (
        Loopy()
        .mkdir("/animals", parents=True)
        .mkdir("/animals/dogs")
        .mkdir("/animals/cats")
    )

    out = run("ls /animals | grep dog", tree)
    assert out == "dogs/"  # Directories shown with trailing /


def test_run_cat_grep_count_from_stdin():
    tree = Loopy().touch("/notes", "alpha\nbeta\ngamma\nbeta")

    out = run("cat /notes | grep -c beta", tree)
    assert out == "2"


def test_run_cd_and_pwd():
    tree = Loopy().mkdir("/projects/app", parents=True)

    out = run("cd /projects/app", tree)
    assert out == ""
    assert run("pwd", tree) == "/projects/app"


def test_run_parse_errors():
    tree = Loopy()

    with pytest.raises(ValueError):
        run("ls |", tree)

    with pytest.raises(ValueError):
        run("| ls", tree)


def test_run_write_commands():
    tree = Loopy()

    # mkdir and touch
    run("mkdir -p /a/b/c", tree)
    run("touch /a/b/c/file hello world", tree)
    assert run("cat /a/b/c/file", tree) == "hello world"

    # mv
    run("mv /a/b/c/file /a/b/moved", tree)
    assert not tree.exists("/a/b/c/file")
    assert run("cat /a/b/moved", tree) == "hello world"

    # cp
    run("cp /a/b/moved /a/copy", tree)
    assert run("cat /a/copy", tree) == "hello world"
    assert tree.exists("/a/b/moved")  # original still exists

    # rm
    run("rm /a/copy", tree)
    assert not tree.exists("/a/copy")


def test_run_write_with_stdin():
    tree = Loopy()
    tree.mkdir("/docs", parents=True)

    # echo piped to touch
    run("echo some content | touch /docs/file", tree)
    assert run("cat /docs/file", tree) == "some content"

    # echo piped to write (overwrites)
    run("echo new content | write /docs/file", tree)
    assert run("cat /docs/file", tree) == "new content"


def test_mv_into_directory():
    tree = Loopy()
    tree.mkdir("/src", parents=True)
    tree.mkdir("/dst", parents=True)
    tree.touch("/src/file", "data")

    # mv into directory (keeps name)
    run("mv /src/file /dst", tree)
    assert tree.exists("/dst/file")
    assert not tree.exists("/src/file")

    # mv with .. and trailing slash
    tree.cd("/dst")
    run("mv file/ ..", tree)
    assert tree.exists("/file")
    assert not tree.exists("/dst/file")
