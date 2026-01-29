"""
Stress tests and edge cases that push Loopy to its limits.
"""

import pytest
from loopy import Loopy


class TestDeepNesting:
    """Test extremely deep tree structures."""

    def test_100_levels_deep(self):
        tree = Loopy()
        path = "/".join([f"level{i}" for i in range(100)])
        tree.mkdir(f"/{path}", parents=True)
        tree.touch(f"/{path}/leaf", "deep content")

        assert tree.exists(f"/{path}/leaf")
        assert tree.cat(f"/{path}/leaf") == "deep content"

    def test_deep_traversal(self):
        tree = Loopy()
        path = "/a/b/c/d/e/f/g/h/i/j"
        tree.touch(f"{path}/file", "data")

        # Find should traverse all levels
        files = tree.find("/", type="f")
        assert f"{path}/file" in files

        # du should count all nodes
        assert tree.du("/") == 12  # root + 10 dirs + 1 file

    def test_deep_cd_navigation(self):
        tree = Loopy()
        tree.mkdir("/a/b/c/d/e", parents=True)

        tree.cd("/a").cd("b").cd("c").cd("d").cd("e")
        assert tree.cwd == "/a/b/c/d/e"

        tree.touch("file", "content")
        assert tree.exists("/a/b/c/d/e/file")


class TestWideTree:
    """Test trees with many siblings."""

    def test_100_siblings(self):
        tree = Loopy()
        for i in range(100):
            tree.touch(f"/files/file_{i:03d}", f"content_{i}")

        children = tree.ls("/files")
        assert len(children) == 100
        assert "file_000" in children
        assert "file_099" in children

    def test_wide_grep(self):
        tree = Loopy()
        for i in range(50):
            tree.touch(f"/logs/error_{i:03d}", f"Error message {i}")
            tree.touch(f"/logs/info_{i:03d}", f"Info message {i}")

        errors = tree.grep("error")
        assert len(errors) == 50

    def test_wide_glob(self):
        tree = Loopy()
        for i in range(30):
            tree.touch(f"/src/module_{i}.py", f"# module {i}")
            tree.touch(f"/src/module_{i}.test.py", f"# test {i}")

        py_files = tree.glob("/src/*.py")
        assert len(py_files) == 60

        test_files = tree.glob("/src/*.test.py")
        assert len(test_files) == 30


class TestLargeContent:
    """Test nodes with large content."""

    def test_1mb_content(self):
        tree = Loopy()
        large_content = "x" * (1024 * 1024)  # 1MB
        tree.touch("/large", large_content)

        assert len(tree.cat("/large")) == 1024 * 1024
        assert tree.du("/large", content_size=True) == 1024 * 1024

    def test_multiline_content(self):
        tree = Loopy()
        content = "\n".join([f"Line {i}" for i in range(1000)])
        tree.touch("/multiline", content)

        retrieved = tree.cat("/multiline")
        assert retrieved.count("\n") == 999
        assert "Line 0" in retrieved
        assert "Line 999" in retrieved

    def test_content_with_all_ascii(self):
        tree = Loopy()
        # All printable ASCII except < > & and space (cat strips whitespace)
        content = "".join(chr(i) for i in range(33, 127) if chr(i) not in "<>&")
        tree.touch("/ascii", content)
        assert tree.cat("/ascii") == content


class TestSpecialPathNames:
    """Test unusual but valid path names."""

    def test_numeric_names(self):
        tree = Loopy()
        tree.touch("/123/456/789", "numbers")
        assert tree.cat("/123/456/789") == "numbers"

    def test_underscores_and_hyphens(self):
        tree = Loopy()
        tree.touch("/my-folder/sub_folder/file-name_v2", "content")
        assert tree.exists("/my-folder/sub_folder/file-name_v2")

    def test_dots_everywhere(self):
        tree = Loopy()
        tree.touch("/config.d/nginx.conf.bak", "backup")
        tree.touch("/.hidden/.secret", "shhh")

        assert tree.cat("/config.d/nginx.conf.bak") == "backup"
        assert tree.cat("/.hidden/.secret") == "shhh"

    def test_long_names(self):
        tree = Loopy()
        long_name = "a" * 200
        tree.touch(f"/folder/{long_name}", "long name content")

        assert tree.exists(f"/folder/{long_name}")
        assert long_name in tree.ls("/folder")

    def test_unicode_path_names(self):
        tree = Loopy()
        tree.touch("/文件夹/文件", "中文内容")
        tree.touch("/папка/файл", "русский")
        tree.touch("/φάκελος/αρχείο", "ελληνικά")

        assert tree.cat("/文件夹/文件") == "中文内容"
        assert tree.cat("/папка/файл") == "русский"
        assert tree.cat("/φάκελος/αρχείο") == "ελληνικά"


class TestSpecialContent:
    """Test content that could break parsing."""

    def test_xml_like_content(self):
        tree = Loopy()
        tree.touch("/xml", "<root><child>text</child></root>")
        assert tree.cat("/xml") == "<root><child>text</child></root>"

    def test_nested_tags_in_content(self):
        tree = Loopy()
        tree.touch("/html", "<div><p><span>nested</span></p></div>")
        assert "<div>" in tree.cat("/html")
        assert "</div>" in tree.cat("/html")

    def test_ampersands(self):
        tree = Loopy()
        tree.touch("/url", "https://example.com?a=1&b=2&c=3")
        assert tree.cat("/url") == "https://example.com?a=1&b=2&c=3"

    def test_mixed_special_chars(self):
        tree = Loopy()
        content = "if (a < b && c > d) { return a <=> b; }"
        tree.touch("/code", content)
        assert tree.cat("/code") == content

    def test_quotes_in_content(self):
        tree = Loopy()
        tree.touch("/quotes", '''He said "Hello" and she said 'Hi'.''')
        assert '"Hello"' in tree.cat("/quotes")
        assert "'Hi'" in tree.cat("/quotes")

    def test_backslashes(self):
        tree = Loopy()
        tree.touch("/path", "C:\\Users\\name\\file.txt")
        assert tree.cat("/path") == "C:\\Users\\name\\file.txt"

    def test_null_like_content(self):
        tree = Loopy()
        tree.touch("/null", "null")
        tree.touch("/none", "None")
        tree.touch("/empty", "")

        assert tree.cat("/null") == "null"
        assert tree.cat("/none") == "None"
        assert tree.cat("/empty") == ""

    def test_whitespace_content(self):
        tree = Loopy()
        tree.touch("/spaces", "   ")
        tree.touch("/tabs", "\t\t\t")
        tree.touch("/mixed", "  \t  \n  ")

        # Note: cat strips whitespace
        assert tree.cat("/spaces") == ""
        assert tree.cat("/tabs") == ""


class TestOperationEdgeCases:
    """Test edge cases for each operation."""

    def test_mkdir_already_exists(self):
        tree = Loopy()
        tree.mkdir("/a/b/c", parents=True)
        tree.mkdir("/a/b/c", parents=True)  # Should be no-op

        assert tree.exists("/a/b/c")
        # Should not create duplicates
        assert tree.ls("/a/b") == ["c"]

    def test_touch_updates_existing(self):
        tree = Loopy()
        tree.touch("/file", "original")
        tree.touch("/file", "updated")

        assert tree.cat("/file") == "updated"

    def test_touch_no_content_on_existing(self):
        tree = Loopy()
        tree.touch("/file", "original")
        tree.touch("/file")  # No content = no update

        assert tree.cat("/file") == "original"

    def test_rm_root_resets_tree(self):
        tree = Loopy()
        tree.touch("/a/b/c", "content")
        tree.rm("/", recursive=True)

        assert tree.raw == "<root/>"
        assert tree.ls("/") == []

    def test_rm_nonexistent_raises(self):
        tree = Loopy()
        with pytest.raises(KeyError):
            tree.rm("/nonexistent")

    def test_mv_to_same_parent(self):
        tree = Loopy()
        tree.touch("/folder/old_name", "content")
        tree.mv("/folder/old_name", "/folder/new_name")

        assert not tree.exists("/folder/old_name")
        assert tree.exists("/folder/new_name")
        assert tree.cat("/folder/new_name") == "content"

    def test_mv_preserves_children(self):
        tree = Loopy()
        tree.touch("/src/dir/child1", "c1")
        tree.touch("/src/dir/child2", "c2")
        tree.mv("/src/dir", "/dst/dir")

        assert tree.cat("/dst/dir/child1") == "c1"
        assert tree.cat("/dst/dir/child2") == "c2"

    def test_cp_is_independent(self):
        tree = Loopy()
        tree.touch("/original", "content")
        tree.cp("/original", "/copy")
        tree.write("/original", "modified")

        assert tree.cat("/original") == "modified"
        assert tree.cat("/copy") == "content"  # Unchanged

    def test_cd_to_file_raises(self):
        tree = Loopy()
        tree.touch("/file", "content")

        # cd to a file should raise NotADirectoryError
        with pytest.raises(NotADirectoryError):
            tree.cd("/file")

    def test_cd_to_nonexistent_raises(self):
        tree = Loopy()
        with pytest.raises(KeyError):
            tree.cd("/nonexistent")

    def test_write_on_directory_raises(self):
        tree = Loopy()
        tree.touch("/parent/child", "child content")

        # Writing content to a directory with children is now an error
        with pytest.raises(IsADirectoryError):
            tree.write("/parent", "parent content")


class TestGrepEdgeCases:
    """Test grep with tricky patterns."""

    def test_grep_empty_pattern(self):
        tree = Loopy()
        tree.touch("/a", "content")

        # Empty pattern matches everything
        results = tree.grep("")
        assert "/" in results
        assert "/a" in results

    def test_grep_special_regex_chars(self):
        tree = Loopy()
        tree.touch("/file.txt", "content")
        tree.touch("/file_txt", "content")

        # . in regex matches any char
        results = tree.grep(r"file.txt")
        assert "/file.txt" in results
        assert "/file_txt" in results  # . matches _

        # Escaped . matches literal
        results = tree.grep(r"file\.txt")
        assert "/file.txt" in results
        assert "/file_txt" not in results

    def test_grep_anchors(self):
        tree = Loopy()
        tree.touch("/test", "content")
        tree.touch("/testing", "content")
        tree.touch("/pretest", "content")

        results = tree.grep("^test$")
        assert "/test" in results
        assert "/testing" not in results

    def test_grep_content_vs_name(self):
        tree = Loopy()
        tree.touch("/file", "searchterm")

        # By name - no match
        results = tree.grep("searchterm", content=False)
        assert "/file" not in results

        # By content - match
        results = tree.grep("searchterm", content=True)
        assert "/file" in results

    def test_grep_case_sensitivity(self):
        tree = Loopy()
        tree.touch("/File", "Content")

        results = tree.grep("file", ignore_case=True)
        assert "/File" in results

        results = tree.grep("file", ignore_case=False)
        assert "/File" not in results


class TestSedEdgeCases:
    """Test sed with tricky patterns."""

    def test_sed_no_match(self):
        tree = Loopy()
        tree.touch("/file", "hello world")
        tree.sed("/file", "xyz", "abc")

        assert tree.cat("/file") == "hello world"  # Unchanged

    def test_sed_empty_replacement(self):
        tree = Loopy()
        tree.touch("/file", "hello world")
        tree.sed("/file", "world", "")

        assert tree.cat("/file") == "hello"

    def test_sed_special_chars_in_replacement(self):
        tree = Loopy()
        tree.touch("/file", "hello")
        tree.sed("/file", "hello", "a < b & c > d")

        assert tree.cat("/file") == "a < b & c > d"

    def test_sed_overlapping_matches(self):
        tree = Loopy()
        tree.touch("/file", "aaa")
        tree.sed("/file", "aa", "b")

        # First match wins
        assert tree.cat("/file") == "ba"

    def test_sed_backreference_groups(self):
        tree = Loopy()
        tree.touch("/file", "hello world")
        tree.sed("/file", r"(\w+) (\w+)", r"\2 \1")

        assert tree.cat("/file") == "world hello"

    def test_sed_count_zero_vs_one(self):
        tree = Loopy()
        tree.touch("/file", "a a a")

        tree2 = Loopy()
        tree2.touch("/file", "a a a")

        tree.sed("/file", "a", "b", count=0)  # All
        tree2.sed("/file", "a", "b", count=1)  # First only

        assert tree.cat("/file") == "b b b"
        assert tree2.cat("/file") == "b a a"


class TestGlobEdgeCases:
    """Test glob with tricky patterns."""

    def test_glob_no_matches(self):
        tree = Loopy()
        tree.touch("/file.txt", "content")

        results = tree.glob("/**/*.py")
        assert results == []

    def test_glob_root_only(self):
        tree = Loopy()
        results = tree.glob("/")
        assert results == ["/"]

    def test_glob_question_mark(self):
        tree = Loopy()
        tree.touch("/a1", "")
        tree.touch("/a2", "")
        tree.touch("/a10", "")
        tree.touch("/ab", "")

        results = tree.glob("/a?")
        assert "/a1" in results
        assert "/a2" in results
        assert "/ab" in results
        assert "/a10" not in results  # Two chars after a

    def test_glob_double_star_depth(self):
        tree = Loopy()
        tree.touch("/a/b/c/d/file.txt", "deep")
        tree.touch("/a/file.txt", "shallow")

        results = tree.glob("/**/file.txt")
        # ** matches one or more path components
        assert "/a/file.txt" in results
        assert "/a/b/c/d/file.txt" in results


class TestSerializationRoundTrip:
    """Test that serialization preserves everything."""

    def test_basic_roundtrip(self):
        tree = Loopy()
        tree.touch("/a/b/c", "content")

        raw = tree.raw
        restored = Loopy(raw)

        assert restored.cat("/a/b/c") == "content"
        assert restored.raw == raw

    def test_complex_roundtrip(self):
        tree = Loopy()
        tree.touch("/files/doc.txt", "Hello <world> & goodbye")
        tree.touch("/files/data.json", '{"key": "value"}')
        tree.mkdir("/empty_dir", parents=True)

        raw = tree.raw
        restored = Loopy(raw)

        assert restored.cat("/files/doc.txt") == "Hello <world> & goodbye"
        assert restored.cat("/files/data.json") == '{"key": "value"}'
        assert restored.exists("/empty_dir")

    def test_unicode_roundtrip(self):
        tree = Loopy()
        tree.touch("/emoji", "Hello 🌍🎉")
        tree.touch("/chinese", "你好世界")

        raw = tree.raw
        restored = Loopy(raw)

        assert "🌍" in restored.cat("/emoji")
        assert restored.cat("/chinese") == "你好世界"


class TestConsistency:
    """Test that operations maintain consistency."""

    def test_order_preserved_after_operations(self):
        tree = Loopy()
        tree.touch("/c", "")
        tree.touch("/a", "")
        tree.touch("/b", "")

        # Order should be insertion order
        children = tree.ls("/")
        assert children == ["c", "a", "b"]

    def test_state_after_failed_operation(self):
        tree = Loopy()
        tree.touch("/existing", "content")

        original_raw = tree.raw

        try:
            tree.rm("/nonexistent")
        except KeyError:
            pass

        # Tree should be unchanged
        assert tree.raw == original_raw

    def test_chained_operations_atomicity(self):
        tree = Loopy()

        # This chain should work completely or fail completely
        result = (
            tree
            .mkdir("/a/b/c", parents=True)
            .touch("/a/b/c/file", "content")
            .mv("/a/b/c/file", "/a/b/file")
            .rm("/a/b/c")
        )

        assert result is tree
        assert tree.exists("/a/b/file")
        assert not tree.exists("/a/b/c")


class TestCdInteraction:
    """Test cd interaction with all operations."""

    def test_grep_respects_cwd(self):
        tree = Loopy()
        tree.touch("/a/match", "")
        tree.touch("/b/match", "")

        tree.cd("/a")
        results = tree.grep("match")

        # Should only search from /a
        assert "/a/match" in results
        assert "/b/match" not in results

    def test_find_respects_cwd(self):
        tree = Loopy()
        tree.touch("/a/file1", "")
        tree.touch("/b/file2", "")

        tree.cd("/a")
        results = tree.find(type="f")

        assert "/a/file1" in results
        assert "/b/file2" not in results

    def test_glob_with_relative_start(self):
        tree = Loopy()
        tree.touch("/project/src/main.py", "")
        tree.touch("/project/src/lib/util.py", "")

        tree.cd("/project/src")

        # Glob with absolute still works
        results = tree.glob("/**/*.py")
        assert len(results) >= 2

    def test_walk_respects_cwd(self):
        tree = Loopy()
        tree.touch("/a/sub/file", "")
        tree.touch("/b/other", "")

        tree.cd("/a")
        walked = tree.walk()
        paths = [w[0] for w in walked]

        assert "/a" in paths
        assert "/b" not in paths


class TestMemoryAndPerformance:
    """Tests that verify reasonable performance characteristics."""

    def test_many_operations(self):
        tree = Loopy()

        # 500 creates
        for i in range(500):
            tree.touch(f"/files/file_{i:04d}", f"content_{i}")

        # 500 reads
        for i in range(500):
            assert tree.cat(f"/files/file_{i:04d}") == f"content_{i}"

        # 100 updates
        for i in range(100):
            tree.sed(f"/files/file_{i:04d}", f"content_{i}", f"updated_{i}")

        # Verify
        assert tree.cat("/files/file_0050") == "updated_50"
        assert tree.cat("/files/file_0150") == "content_150"

    def test_repeated_serialization(self):
        tree = Loopy()
        tree.touch("/data", "content")

        # Serialize and restore 100 times
        for _ in range(100):
            raw = tree.raw
            tree = Loopy(raw)

        assert tree.cat("/data") == "content"


class TestInfoAndMetadata:
    """Test info and metadata operations."""

    def test_info_completeness(self):
        tree = Loopy()
        tree.touch("/parent/child1", "hello")
        tree.touch("/parent/child2", "world")

        info = tree.info("/parent")

        assert info["name"] == "parent"
        assert info["path"] == "/parent"
        assert info["type"] == "directory"
        assert info["children_count"] == 2
        assert info["content_length"] == 0
        assert info["has_content"] == False

    def test_du_accuracy(self):
        tree = Loopy()
        tree.touch("/a", "12345")  # 5 bytes
        tree.touch("/b", "123456789")  # 9 bytes
        tree.touch("/c/d", "12")  # 2 bytes

        assert tree.du("/", content_size=True) == 16
        assert tree.du("/") == 5  # root, a, b, c, d

    def test_isdir_isfile_consistency(self):
        tree = Loopy()
        tree.mkdir("/dir/subdir", parents=True)
        tree.touch("/dir/file", "content")
        tree.touch("/dir/subdir/nested", "nested")

        # Directories
        assert tree.isdir("/dir")
        assert tree.isdir("/dir/subdir")
        assert not tree.isfile("/dir")
        assert not tree.isfile("/dir/subdir")

        # Files
        assert tree.isfile("/dir/file")
        assert tree.isfile("/dir/subdir/nested")
        assert not tree.isdir("/dir/file")
        assert not tree.isdir("/dir/subdir/nested")

    def test_head_tail_edge_cases(self):
        tree = Loopy()
        tree.touch("/short", "abc")
        tree.touch("/empty", "")

        assert tree.head("/short", 10) == "abc"
        assert tree.tail("/short", 10) == "abc"
        assert tree.head("/short", 2) == "ab"
        assert tree.tail("/short", 2) == "bc"
        assert tree.head("/empty", 5) == ""
        assert tree.tail("/empty", 5) == ""
