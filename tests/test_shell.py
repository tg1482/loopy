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


def test_run_ls_recursive():
    tree = (
        Loopy()
        .mkdir("/a/b", parents=True)
        .touch("/a/root", "root")
        .touch("/a/b/file", "leaf")
    )

    out = run("ls -R /a", tree)
    assert out == "\n".join(
        [
            "/a:",
            "b/",
            "root",
            "",
            "/a/b:",
            "file",
        ]
    )


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


def test_head_basic():
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 21))  # 20 lines
    tree.touch("/file", content)

    # Default: first 10 lines
    out = run("head /file", tree)
    assert out == "\n".join(f"line{i}" for i in range(1, 11))


def test_head_with_n_option():
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 21))
    tree.touch("/file", content)

    # -n 5
    out = run("head -n 5 /file", tree)
    assert out == "\n".join(f"line{i}" for i in range(1, 6))

    # -n5 (no space)
    out = run("head -n5 /file", tree)
    assert out == "\n".join(f"line{i}" for i in range(1, 6))


def test_head_from_stdin():
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 21))
    tree.touch("/file", content)

    # Pipe cat to head
    out = run("cat /file | head -n 3", tree)
    assert out == "line1\nline2\nline3"


def test_head_n_zero():
    tree = Loopy()
    tree.touch("/file", "line1\nline2\nline3")

    out = run("head -n 0 /file", tree)
    assert out == ""


def test_tail_basic():
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 21))  # 20 lines
    tree.touch("/file", content)

    # Default: last 10 lines
    out = run("tail /file", tree)
    assert out == "\n".join(f"line{i}" for i in range(11, 21))


def test_tail_with_n_option():
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 21))
    tree.touch("/file", content)

    # -n 5
    out = run("tail -n 5 /file", tree)
    assert out == "\n".join(f"line{i}" for i in range(16, 21))

    # -n5 (no space)
    out = run("tail -n5 /file", tree)
    assert out == "\n".join(f"line{i}" for i in range(16, 21))


def test_tail_from_stdin():
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 21))
    tree.touch("/file", content)

    # Pipe cat to tail
    out = run("cat /file | tail -n 3", tree)
    assert out == "line18\nline19\nline20"


def test_tail_n_zero():
    tree = Loopy()
    tree.touch("/file", "line1\nline2\nline3")

    out = run("tail -n 0 /file", tree)
    assert out == ""


def test_head_tail_fewer_lines_than_requested():
    tree = Loopy()
    tree.touch("/file", "line1\nline2\nline3")

    # Request more lines than exist
    out = run("head -n 100 /file", tree)
    assert out == "line1\nline2\nline3"

    out = run("tail -n 100 /file", tree)
    assert out == "line1\nline2\nline3"


def test_head_tail_errors():
    tree = Loopy()
    tree.touch("/file", "content")

    # Unknown option
    with pytest.raises(ValueError, match="unknown option"):
        run("head -x /file", tree)

    # -n without number
    with pytest.raises(ValueError, match="-n requires a number"):
        run("head -n", tree)

    # -n with non-number
    with pytest.raises(ValueError, match="-n requires a number"):
        run("head -n abc /file", tree)

    # Multiple paths
    with pytest.raises(ValueError, match="takes at most one path"):
        run("head /file /file2", tree)


def test_split_basic():
    tree = Loopy()
    tree.touch("/file", "a,b,c")

    out = run("split -d , /file", tree)
    assert out == "a\nb\nc"


def test_split_long_delimiter():
    tree = Loopy()
    tree.touch("/file", "a::b::c")

    out = run("split -d :: /file", tree)
    assert out == "a\nb\nc"


def test_split_from_stdin():
    tree = Loopy()
    tree.touch("/file", "foo;bar;baz")

    out = run("cat /file | split -d ';'", tree)
    assert out == "foo\nbar\nbaz"


def test_split_pipe_delimiter_from_stdin():
    tree = Loopy()
    tree.touch("/file", "a|b||c")

    out = run('cat /file | split "|"', tree)
    assert out == "a\nb\n\nc"


def test_split_with_long_option():
    tree = Loopy()
    tree.touch("/file", "x:y:z")

    out = run("split --delimiter : /file", tree)
    assert out == "x\ny\nz"


def test_split_no_matches():
    tree = Loopy()
    tree.touch("/file", "no delimiter here")

    out = run("split -d , /file", tree)
    assert out == "no delimiter here"


def test_split_empty_parts():
    tree = Loopy()
    tree.touch("/file", "a,,b")

    out = run("split -d , /file", tree)
    assert out == "a\n\nb"


def test_split_errors():
    tree = Loopy()
    tree.touch("/file", "content")

    # Missing delimiter
    with pytest.raises(ValueError, match="split requires a delimiter"):
        run("split /file", tree)

    # -d without value
    with pytest.raises(ValueError, match="split -d requires a delimiter"):
        run("split -d", tree)

    # Unknown option
    with pytest.raises(ValueError, match="unknown split option"):
        run("split -x /file", tree)

    # Multiple paths
    with pytest.raises(ValueError, match="takes at most one path"):
        run("split -d , /file /file2", tree)


def test_cat_range_basic():
    tree = Loopy()
    tree.touch("/file", "Hello, World!")

    # Extract "World"
    out = run("cat /file --range 7 5", tree)
    assert out == "World"


def test_cat_range_from_start():
    tree = Loopy()
    tree.touch("/file", "abcdefghij")

    # Extract from beginning
    out = run("cat /file --range 0 3", tree)
    assert out == "abc"


def test_cat_range_to_end():
    tree = Loopy()
    tree.touch("/file", "abcdefghij")

    # Extract beyond content length (should return to end)
    out = run("cat /file --range 7 100", tree)
    assert out == "hij"


def test_cat_range_zero_length():
    tree = Loopy()
    tree.touch("/file", "content")

    out = run("cat /file --range 3 0", tree)
    assert out == ""


def test_cat_range_from_stdin():
    tree = Loopy()
    tree.touch("/file", "Hello, World!")

    # Pipe cat to cat with range
    out = run("cat /file | cat --range 0 5", tree)
    assert out == "Hello"


def test_cat_range_stdin_no_path():
    tree = Loopy()

    # Use stdin directly with range
    out = run("echo 'abcdefghij' | cat --range 2 4", tree)
    assert out == "cdef"


def test_cat_range_option_before_path():
    tree = Loopy()
    tree.touch("/file", "Hello, World!")

    # --range before path
    out = run("cat --range 0 5 /file", tree)
    assert out == "Hello"


def test_cat_range_errors():
    tree = Loopy()
    tree.touch("/file", "content")

    # --range without arguments
    with pytest.raises(ValueError, match="--range requires start and length"):
        run("cat /file --range", tree)

    # --range with only start
    with pytest.raises(ValueError, match="--range requires start and length"):
        run("cat /file --range 5", tree)

    # --range with non-integer start
    with pytest.raises(ValueError, match="--range start must be an integer"):
        run("cat /file --range abc 5", tree)

    # --range with non-integer length
    with pytest.raises(ValueError, match="--range length must be an integer"):
        run("cat /file --range 0 xyz", tree)

    # --range with negative start
    with pytest.raises(ValueError, match="--range start must be non-negative"):
        run("cat /file --range -1 5", tree)

    # --range with negative length
    with pytest.raises(ValueError, match="--range length must be non-negative"):
        run("cat /file --range 0 -5", tree)

    # Unknown option
    with pytest.raises(ValueError, match="unknown cat option"):
        run("cat /file -x", tree)

    # Multiple paths
    with pytest.raises(ValueError, match="cat takes at most one path"):
        run("cat /file /file2", tree)


def test_help_includes_head():
    tree = Loopy()
    out = run("help", tree)
    assert "head" in out
    assert "-n N" in out or "-n" in out


def test_help_includes_tail():
    tree = Loopy()
    out = run("help", tree)
    assert "tail" in out
    assert "-n N" in out or "-n" in out


def test_help_includes_split():
    tree = Loopy()
    out = run("help", tree)
    assert "split" in out
    assert "-d" in out or "delimiter" in out.lower()


def test_help_includes_cat_range():
    tree = Loopy()
    out = run("help", tree)
    assert "cat" in out
    assert "--range" in out


# ============================================================================
# Tests for command defaults
# ============================================================================


def test_ls_default_cwd():
    """ls with no arguments lists current directory."""
    tree = Loopy().mkdir("/home", parents=True).touch("/home/file1", "content")
    tree.cd("/home")
    out = run("ls", tree)
    assert out == "file1"


def test_ls_classify_default():
    """ls shows directories with trailing / by default."""
    tree = Loopy().mkdir("/test/subdir", parents=True).touch("/test/file", "content")
    out = run("ls /test", tree)
    assert "subdir/" in out
    assert "file" in out
    assert not out.endswith("file/")


def test_cat_default_reads_from_stdin():
    """cat with no path reads from stdin."""
    tree = Loopy()
    out = run("echo hello world | cat", tree)
    assert out == "hello world"


def test_grep_default_searches_cwd():
    """grep with no path searches current directory."""
    tree = Loopy().mkdir("/search", parents=True)
    tree.touch("/search/file1", "needle in haystack")
    tree.touch("/search/file2", "no match here")
    tree.cd("/search")
    out = run("grep needle", tree)
    # grep returns matching file paths when searching filesystem
    assert "file1" in out


def test_find_default_cwd():
    """find with no path searches current directory."""
    tree = (
        Loopy()
        .mkdir("/project/src", parents=True)
        .touch("/project/src/main.py", "code")
    )
    tree.cd("/project")
    out = run("find -name main.py", tree)
    assert "main.py" in out


def test_tree_default_cwd():
    """tree with no path shows current directory."""
    tree = Loopy().mkdir("/app/lib", parents=True).touch("/app/lib/util", "code")
    tree.cd("/app")
    out = run("tree", tree)
    assert "lib" in out
    assert "util" in out


def test_du_default_cwd():
    """du with no path counts current directory."""
    tree = (
        Loopy().mkdir("/data", parents=True).touch("/data/a", "1").touch("/data/b", "2")
    )
    tree.cd("/data")
    out = run("du", tree)
    assert out == "3"  # 1 dir + 2 files


def test_du_content_size():
    """du -c counts content size instead of nodes."""
    tree = Loopy().mkdir("/data", parents=True).touch("/data/file", "hello")
    out = run("du -c /data", tree)
    assert out == "5"  # len("hello")


def test_pwd_no_args():
    """pwd returns current working directory."""
    tree = Loopy().mkdir("/some/path", parents=True)
    tree.cd("/some/path")
    out = run("pwd", tree)
    assert out == "/some/path"


def test_info_default_cwd():
    """info with no path shows current directory info."""
    tree = Loopy().mkdir("/mydir", parents=True)
    tree.cd("/mydir")
    out = run("info", tree)
    # info returns metadata about the path
    assert "name: mydir" in out
    assert "path: /mydir" in out


def test_head_default_10_lines():
    """head with no -n option returns first 10 lines."""
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 16))  # 15 lines
    tree.touch("/file", content)
    out = run("head /file", tree)
    lines = out.splitlines()
    assert len(lines) == 10
    assert lines[0] == "line1"
    assert lines[9] == "line10"


def test_tail_default_10_lines():
    """tail with no -n option returns last 10 lines."""
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 16))  # 15 lines
    tree.touch("/file", content)
    out = run("tail /file", tree)
    lines = out.splitlines()
    assert len(lines) == 10
    assert lines[0] == "line6"
    assert lines[9] == "line15"


def test_rm_requires_path():
    """rm without path raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="rm requires a path"):
        run("rm", tree)


def test_mkdir_requires_path():
    """mkdir without path raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="mkdir requires a path"):
        run("mkdir", tree)


def test_mkdir_parents_flag():
    """mkdir -p creates intermediate directories."""
    tree = Loopy()
    run("mkdir -p /deep/nested/path", tree)
    assert tree.isdir("/deep/nested/path")


def test_echo_empty():
    """echo with no args returns empty string."""
    tree = Loopy()
    out = run("echo", tree)
    assert out == ""


# ============================================================================
# Tests for stdin piping
# ============================================================================


def test_grep_stdin_piping():
    """grep reads from stdin when piped."""
    tree = Loopy()
    out = run("echo 'apple\nbanana\napricot' | grep ap", tree)
    assert "apple" in out
    assert "apricot" in out
    assert "banana" not in out


def test_grep_stdin_invert():
    """grep -v inverts match on stdin."""
    tree = Loopy()
    out = run("echo 'apple\nbanana\napricot' | grep -v ap", tree)
    assert out == "banana"


def test_grep_stdin_ignore_case():
    """grep -i ignores case on stdin."""
    tree = Loopy()
    out = run("echo 'Apple\nBANANA' | grep -i apple", tree)
    assert out == "Apple"


def test_grep_stdin_count():
    """grep -c counts matches on stdin."""
    tree = Loopy()
    out = run("echo 'a\na\nb\na' | grep -c a", tree)
    assert out == "3"


def test_head_stdin_piping():
    """head reads from stdin when no path given."""
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 21))
    tree.touch("/file", content)
    out = run("cat /file | head -n 3", tree)
    assert out == "line1\nline2\nline3"


def test_tail_stdin_piping():
    """tail reads from stdin when no path given."""
    tree = Loopy()
    content = "\n".join(f"line{i}" for i in range(1, 21))
    tree.touch("/file", content)
    out = run("cat /file | tail -n 3", tree)
    assert out == "line18\nline19\nline20"


def test_split_stdin_piping():
    """split reads from stdin when no path given."""
    tree = Loopy()
    out = run("echo 'a,b,c' | split -d ','", tree)
    assert out == "a\nb\nc"


def test_multi_stage_pipeline():
    """Pipeline with multiple stages processes correctly."""
    tree = Loopy()
    tree.touch("/data", "foo\nbar\nbaz\nfoo\nqux")
    out = run("cat /data | grep foo | head -n 1", tree)
    assert out == "foo"


def test_pipeline_grep_then_split():
    """Pipeline: grep then split."""
    tree = Loopy()
    tree.touch("/file", "skip:this\nkeep:a,b,c\nskip:that")
    out = run("cat /file | grep keep | split -d ':'", tree)
    assert out == "keep\na,b,c"


def test_touch_stdin_content():
    """touch uses stdin as content when piped."""
    tree = Loopy().mkdir("/dir", parents=True)
    run("echo piped content | touch /dir/file", tree)
    assert run("cat /dir/file", tree) == "piped content"


def test_write_stdin_content():
    """write uses stdin as content when piped."""
    tree = Loopy().mkdir("/dir", parents=True).touch("/dir/file", "old")
    run("echo new content | write /dir/file", tree)
    assert run("cat /dir/file", tree) == "new content"


# ============================================================================
# Edge case tests
# ============================================================================


def test_empty_file_cat():
    """cat on empty file returns empty string."""
    tree = Loopy().touch("/empty", "")
    out = run("cat /empty", tree)
    assert out == ""


def test_empty_file_head():
    """head on empty file returns empty string."""
    tree = Loopy().touch("/empty", "")
    out = run("head /empty", tree)
    assert out == ""


def test_empty_file_tail():
    """tail on empty file returns empty string."""
    tree = Loopy().touch("/empty", "")
    out = run("tail /empty", tree)
    assert out == ""


def test_empty_file_grep():
    """grep on empty file returns empty string."""
    tree = Loopy().touch("/empty", "")
    out = run("cat /empty | grep pattern", tree)
    assert out == ""


def test_empty_directory_ls():
    """ls on empty directory returns empty string."""
    tree = Loopy().mkdir("/empty", parents=True)
    out = run("ls /empty", tree)
    assert out == ""


def test_single_line_file_head_tail():
    """head and tail on single line file."""
    tree = Loopy().touch("/single", "only line")
    assert run("head /single", tree) == "only line"
    assert run("tail /single", tree) == "only line"


def test_special_chars_in_content():
    """Files with special characters in content."""
    tree = Loopy()
    content = "line with\ttab\nline with 'quotes'\nline with \"double\""
    tree.touch("/special", content)
    out = run("cat /special", tree)
    assert "line with\ttab" in out
    assert "'quotes'" in out
    assert '"double"' in out


def test_grep_special_regex_chars():
    """grep with regex special characters."""
    tree = Loopy()
    tree.touch("/file", "file.txt\nfile-txt\nfiletxt")
    # Literal dot requires escaping
    out = run(r"cat /file | grep 'file\.txt'", tree)
    assert out == "file.txt"


def test_unknown_command_error():
    """Unknown command raises KeyError."""
    tree = Loopy()
    with pytest.raises(KeyError, match="Unknown command"):
        run("nonexistent", tree)


def test_empty_command_returns_empty():
    """Empty command string returns empty list from parser."""
    from loopy.shell import _parse_pipeline

    result = _parse_pipeline("")
    assert result == []


def test_ls_unknown_option_error():
    """ls with unknown option raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="unknown ls option"):
        run("ls -z", tree)


def test_find_unknown_option_error():
    """find with unknown option raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="unknown find option"):
        run("find -q", tree)


def test_du_unknown_option_error():
    """du with unknown option raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="unknown du option"):
        run("du -x", tree)


def test_rm_unknown_option_error():
    """rm with unknown option raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="unknown rm option"):
        run("rm -x /file", tree)


def test_mkdir_unknown_option_error():
    """mkdir with unknown option raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="unknown mkdir option"):
        run("mkdir -x /dir", tree)


def test_sed_unknown_option_error():
    """sed with unknown option raises error."""
    tree = Loopy().touch("/file", "content")
    with pytest.raises(ValueError, match="unknown sed option"):
        run("sed /file pattern repl -x", tree)


def test_cd_requires_path():
    """cd without path raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="cd requires a path"):
        run("cd", tree)


def test_mv_requires_two_args():
    """mv with wrong number of args raises error."""
    tree = Loopy().touch("/file", "content")
    with pytest.raises(ValueError, match="mv requires source and destination"):
        run("mv /file", tree)


def test_cp_requires_two_args():
    """cp with wrong number of args raises error."""
    tree = Loopy().touch("/file", "content")
    with pytest.raises(ValueError, match="cp requires source and destination"):
        run("cp /file", tree)


def test_touch_requires_path():
    """touch without path raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="touch requires a path"):
        run("touch", tree)


def test_write_requires_path():
    """write without path raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="write requires a path"):
        run("write", tree)


def test_sed_requires_three_positional():
    """sed requires path, pattern, replacement."""
    tree = Loopy()
    with pytest.raises(ValueError, match="sed requires"):
        run("sed /file pattern", tree)


def test_find_name_requires_pattern():
    """find -name without pattern raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="-name requires a pattern"):
        run("find -name", tree)


def test_find_type_requires_value():
    """find -type without value raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="-type requires"):
        run("find -type", tree)


def test_grep_requires_pattern():
    """grep without pattern raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="grep requires a pattern"):
        run("grep", tree)


def test_grep_unknown_flag():
    """grep with unknown flag raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="unknown grep flag"):
        run("grep -z pattern", tree)


def test_grep_double_dash_separator():
    """grep -- allows pattern starting with dash."""
    tree = Loopy()
    tree.touch("/file", "-test\nother")
    out = run("cat /file | grep -- -test", tree)
    assert out == "-test"


def test_pwd_extra_args_error():
    """pwd with arguments raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="pwd takes no arguments"):
        run("pwd extra", tree)


def test_tree_multiple_paths_error():
    """tree with multiple paths raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="tree takes at most one path"):
        run("tree /a /b", tree)


def test_info_multiple_paths_error():
    """info with multiple paths raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="info takes at most one path"):
        run("info /a /b", tree)


def test_ls_multiple_paths_error():
    """ls with multiple paths raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="ls takes at most one path"):
        run("ls /a /b", tree)


def test_find_multiple_paths_error():
    """find with multiple paths raises error."""
    tree = Loopy().mkdir("/a", parents=True).mkdir("/b", parents=True)
    with pytest.raises(ValueError, match="find takes at most one path"):
        run("find /a /b", tree)


def test_du_multiple_paths_error():
    """du with multiple paths raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="du takes at most one path"):
        run("du /a /b", tree)


def test_rm_multiple_paths_error():
    """rm with multiple paths raises error."""
    tree = Loopy().touch("/a", "").touch("/b", "")
    with pytest.raises(ValueError, match="rm takes one path"):
        run("rm /a /b", tree)


def test_mkdir_multiple_paths_error():
    """mkdir with multiple paths raises error."""
    tree = Loopy()
    with pytest.raises(ValueError, match="mkdir takes one path"):
        run("mkdir /a /b", tree)


def test_grep_multiple_paths_error():
    """grep with multiple paths raises error."""
    tree = Loopy().touch("/a", "").touch("/b", "")
    with pytest.raises(ValueError, match="grep takes at most one path"):
        run("grep pattern /a /b", tree)


def test_rm_recursive():
    """rm -r removes directories recursively."""
    tree = Loopy().mkdir("/dir/subdir", parents=True).touch("/dir/subdir/file", "data")
    run("rm -r /dir", tree)
    assert not tree.exists("/dir")


def test_rm_rf_flag():
    """rm -rf removes directories recursively."""
    tree = Loopy().mkdir("/dir", parents=True)
    run("rm -rf /dir", tree)
    assert not tree.exists("/dir")


def test_ls_no_classify():
    """ls --no-classify hides trailing slash on directories."""
    tree = Loopy().mkdir("/test/subdir", parents=True)
    out = run("ls --no-classify /test", tree)
    assert "subdir" in out
    assert "subdir/" not in out


def test_head_negative_n_error():
    """head with negative -n raises error."""
    tree = Loopy().touch("/file", "content")
    with pytest.raises(ValueError, match="non-negative"):
        run("head -n -5 /file", tree)


def test_tail_negative_n_error():
    """tail with negative -n raises error."""
    tree = Loopy().touch("/file", "content")
    with pytest.raises(ValueError, match="non-negative"):
        run("tail -n -5 /file", tree)


def test_run_with_initial_stdin():
    """run function accepts initial stdin parameter."""
    tree = Loopy()
    out = run("cat", tree, stdin="initial stdin")
    assert out == "initial stdin"


def test_run_stdin_passed_through_pipeline():
    """stdin flows through pipeline stages."""
    tree = Loopy()
    out = run("cat | grep hello", tree, stdin="hello world\ngoodbye")
    assert out == "hello world"


# ============================================================================
# Tests for README examples
# ============================================================================


def test_readme_shell_example_build_knowledge_base():
    """Test the shell example from README - building a knowledge base."""
    tree = Loopy()

    # Build a knowledge base
    run("mkdir -p /ml/supervised", tree)
    run("touch /ml/supervised/regression 'predicts continuous values'", tree)
    run("touch /ml/supervised/classification 'predicts discrete labels'", tree)
    run("mkdir -p /ml/unsupervised", tree)
    run("touch /ml/unsupervised/clustering 'groups similar items'", tree)

    # Verify structure was created
    assert tree.isdir("/ml/supervised")
    assert tree.isdir("/ml/unsupervised")
    assert tree.isfile("/ml/supervised/regression")
    assert tree.isfile("/ml/supervised/classification")
    assert tree.isfile("/ml/unsupervised/clustering")

    # Verify content
    assert tree.cat("/ml/supervised/regression") == "predicts continuous values"
    assert tree.cat("/ml/supervised/classification") == "predicts discrete labels"
    assert tree.cat("/ml/unsupervised/clustering") == "groups similar items"


def test_readme_shell_example_tree_output():
    """Test tree command from README example."""
    tree = Loopy()
    run("mkdir -p /ml/supervised", tree)
    run("touch /ml/supervised/regression 'predicts continuous values'", tree)
    run("touch /ml/supervised/classification 'predicts discrete labels'", tree)
    run("mkdir -p /ml/unsupervised", tree)
    run("touch /ml/unsupervised/clustering 'groups similar items'", tree)

    out = run("tree /ml", tree)
    assert "ml" in out
    assert "supervised" in out
    assert "unsupervised" in out
    assert "regression" in out
    assert "classification" in out
    assert "clustering" in out


def test_readme_shell_example_grep_search():
    """Test grep search from README example."""
    tree = Loopy()
    run("mkdir -p /ml/supervised", tree)
    run("touch /ml/supervised/regression 'predicts continuous values'", tree)
    run("touch /ml/supervised/classification 'predicts discrete labels'", tree)
    run("mkdir -p /ml/unsupervised", tree)
    run("touch /ml/unsupervised/clustering 'groups similar items'", tree)

    # Search by content
    out = run("grep predicts /ml", tree)
    assert "regression" in out
    assert "classification" in out


def test_readme_shell_example_pipeline():
    """Test pipeline from README example."""
    tree = Loopy()
    run("mkdir -p /ml/supervised", tree)
    run("touch /ml/supervised/regression 'predicts continuous values'", tree)
    run("touch /ml/supervised/classification 'predicts discrete labels'", tree)
    run("mkdir -p /ml/unsupervised", tree)
    run("touch /ml/unsupervised/clustering 'groups similar items'", tree)

    # Pipeline: find all files, filter by name
    out = run("find /ml -type f | grep class", tree)
    assert "classification" in out


def test_readme_shell_example_cat():
    """Test cat command from README example."""
    tree = Loopy()
    run("mkdir -p /ml/supervised", tree)
    run("touch /ml/supervised/regression 'predicts continuous values'", tree)

    out = run("cat /ml/supervised/regression", tree)
    assert out == "predicts continuous values"


def test_readme_shell_example_du():
    """Test du command from README example."""
    tree = Loopy()
    run("mkdir -p /ml/supervised", tree)
    run("touch /ml/supervised/regression 'predicts continuous values'", tree)
    run("touch /ml/supervised/classification 'predicts discrete labels'", tree)
    run("mkdir -p /ml/unsupervised", tree)
    run("touch /ml/unsupervised/clustering 'groups similar items'", tree)

    out = run("du /ml", tree)
    # ml (1) + supervised (1) + unsupervised (1) + regression (1) + classification (1) + clustering (1) = 6
    assert out == "6"


def test_readme_shell_example_sed():
    """Test sed command from README example."""
    tree = Loopy()
    run("mkdir -p /ml/supervised", tree)
    run("touch /ml/supervised/regression 'predicts continuous values'", tree)

    run("sed /ml/supervised/regression 'continuous' 'numeric'", tree)
    out = run("cat /ml/supervised/regression", tree)
    assert out == "predicts numeric values"


def test_readme_shell_example_cp_mv():
    """Test cp and mv commands from README example."""
    tree = Loopy()
    run("mkdir -p /ml/supervised", tree)
    run("touch /ml/supervised/regression 'predicts continuous values'", tree)
    run("mkdir -p /ml/unsupervised", tree)
    run("touch /ml/unsupervised/clustering 'groups similar items'", tree)

    # Copy
    run("cp /ml/supervised/regression /ml/linear_regression", tree)
    assert tree.exists("/ml/linear_regression")
    assert tree.cat("/ml/linear_regression") == "predicts continuous values"
    assert tree.exists("/ml/supervised/regression")  # original still exists

    # Move
    run("mv /ml/unsupervised/clustering /ml/kmeans", tree)
    assert tree.exists("/ml/kmeans")
    assert not tree.exists("/ml/unsupervised/clustering")


def test_readme_shell_example_echo_pipe():
    """Test echo piped to touch from README example."""
    tree = Loopy()
    run("mkdir -p /ml", tree)

    run("echo 'neural network model' | touch /ml/deep_learning", tree)
    assert tree.cat("/ml/deep_learning") == "neural network model"
