"""Advanced tests to challenge Loopy's grep, sed, find, glob, and edge cases."""

from loopy import Loopy


class TestGrep:
    """Test grep with various options."""

    def setup_method(self):
        self.tree = Loopy()
        self.tree.mkdir("/logs/errors", parents=True)
        self.tree.mkdir("/logs/warnings", parents=True)
        self.tree.mkdir("/logs/info", parents=True)
        self.tree.touch("/logs/errors/error_001", "NullPointerException in UserService")
        self.tree.touch("/logs/errors/error_002", "ConnectionTimeout to database")
        self.tree.touch("/logs/warnings/warn_001", "Deprecated API usage")
        self.tree.touch("/logs/info/info_001", "User logged in successfully")

    def test_grep_basic(self):
        results = self.tree.grep("error")
        assert "/logs/errors" in results
        assert "/logs/errors/error_001" in results
        assert "/logs/errors/error_002" in results

    def test_grep_content_search(self):
        """Search inside content, not just names."""
        results = self.tree.grep("NullPointer", content=True)
        assert "/logs/errors/error_001" in results

        results = self.tree.grep("database", content=True)
        assert "/logs/errors/error_002" in results

    def test_grep_case_sensitive(self):
        results = self.tree.grep("ERROR", ignore_case=False)
        assert len(results) == 0  # No exact "ERROR" in names

        results = self.tree.grep("error", ignore_case=False)
        assert "/logs/errors" in results

    def test_grep_invert(self):
        """Find paths NOT matching pattern."""
        results = self.tree.grep("error", invert=True)
        assert "/logs/errors" not in results
        assert "/logs/warnings" in results
        assert "/logs/info" in results

    def test_grep_count(self):
        count = self.tree.grep("error", count=True)
        assert count == 3  # errors, error_001, error_002

    def test_grep_scoped_path(self):
        """Start search from specific path."""
        results = self.tree.grep("001", path="/logs/errors")
        assert "/logs/errors/error_001" in results
        assert "/logs/warnings/warn_001" not in results

    def test_grep_regex(self):
        """Complex regex patterns."""
        results = self.tree.grep(r"error_\d{3}")
        assert "/logs/errors/error_001" in results
        assert "/logs/errors/error_002" in results
        assert "/logs/errors" not in results


class TestSed:
    """Test sed with various options."""

    def setup_method(self):
        self.tree = Loopy()
        self.tree.touch("/doc", "hello world world world")

    def test_sed_basic(self):
        self.tree.sed("/doc", "world", "universe")
        assert self.tree.cat("/doc") == "hello universe universe universe"

    def test_sed_count_limit(self):
        """Replace only first N occurrences."""
        tree = Loopy()
        tree.touch("/doc", "aaa bbb aaa bbb aaa")
        tree.sed("/doc", "aaa", "XXX", count=1)
        assert tree.cat("/doc") == "XXX bbb aaa bbb aaa"

    def test_sed_case_insensitive(self):
        tree = Loopy()
        tree.touch("/doc", "Hello HELLO hello")
        tree.sed("/doc", "hello", "hi", ignore_case=True)
        assert tree.cat("/doc") == "hi hi hi"

    def test_sed_recursive(self):
        """Apply sed to all descendants."""
        tree = Loopy()
        tree.touch("/docs/a", "foo bar")
        tree.touch("/docs/b", "foo baz")
        tree.touch("/docs/sub/c", "foo qux")

        tree.sed("/docs", "foo", "FOO", recursive=True)

        assert tree.cat("/docs/a") == "FOO bar"
        assert tree.cat("/docs/b") == "FOO baz"
        assert tree.cat("/docs/sub/c") == "FOO qux"

    def test_sed_backreference(self):
        """Use capture groups in replacement."""
        tree = Loopy()
        tree.touch("/doc", "error_123 error_456")
        tree.sed("/doc", r"error_(\d+)", r"ERR[\1]")
        assert tree.cat("/doc") == "ERR[123] ERR[456]"

    def test_sed_no_match(self):
        """Sed on non-matching content should be no-op."""
        tree = Loopy()
        tree.touch("/doc", "hello world")
        tree.sed("/doc", "xyz", "abc")
        assert tree.cat("/doc") == "hello world"


class TestGlob:
    """Test glob pattern matching."""

    def setup_method(self):
        self.tree = Loopy()
        self.tree.touch("/images/cats/persian.jpg", "data1")
        self.tree.touch("/images/cats/siamese.jpg", "data2")
        self.tree.touch("/images/dogs/labrador.jpg", "data3")
        self.tree.touch("/images/dogs/poodle.png", "data4")
        self.tree.touch("/docs/readme.txt", "data5")

    def test_glob_star(self):
        """Single * matches within one level."""
        results = self.tree.glob("/images/cats/*")
        assert "/images/cats/persian.jpg" in results
        assert "/images/cats/siamese.jpg" in results
        assert "/images/dogs/labrador.jpg" not in results

    def test_glob_double_star(self):
        """Double ** matches any depth."""
        results = self.tree.glob("/images/**")
        assert "/images/cats" in results
        assert "/images/cats/persian.jpg" in results
        assert "/images/dogs/labrador.jpg" in results

    def test_glob_extension(self):
        """Match by extension pattern."""
        results = self.tree.glob("/**/*.jpg")
        assert "/images/cats/persian.jpg" in results
        assert "/images/dogs/labrador.jpg" in results
        assert "/images/dogs/poodle.png" not in results

    def test_glob_question_mark(self):
        """? matches single character."""
        results = self.tree.glob("/images/???s/*")
        # cats and dogs both have 4 chars
        assert "/images/cats/persian.jpg" in results
        assert "/images/dogs/labrador.jpg" in results


class TestFind:
    """Test find with type filters."""

    def setup_method(self):
        self.tree = Loopy()
        self.tree.mkdir("/a/b/c", parents=True)
        self.tree.touch("/a/b/c/file1", "content")
        self.tree.touch("/a/b/file2", "content")
        self.tree.touch("/a/file3", "content")

    def test_find_directories_only(self):
        results = self.tree.find("/", type="d")
        assert "/" in results
        assert "/a" in results
        assert "/a/b" in results
        assert "/a/b/c" in results
        assert "/a/file3" not in results

    def test_find_files_only(self):
        results = self.tree.find("/", type="f")
        assert "/a/b/c/file1" in results
        assert "/a/b/file2" in results
        assert "/a/file3" in results
        assert "/a" not in results

    def test_find_by_name(self):
        results = self.tree.find("/", name=r"file\d")
        assert "/a/b/c/file1" in results
        assert "/a/b/file2" in results


class TestWalk:
    """Test os.walk() style traversal."""

    def test_walk(self):
        tree = Loopy()
        tree.mkdir("/a/b", parents=True)
        tree.touch("/a/b/file1")
        tree.touch("/a/file2")
        tree.touch("/a/b/file3")

        walked = tree.walk("/")
        paths = [w[0] for w in walked]

        assert "/" in paths
        assert "/a" in paths
        assert "/a/b" in paths

        # Check structure
        root_entry = next(w for w in walked if w[0] == "/")
        assert "a" in root_entry[1]  # dirs
        assert len(root_entry[2]) == 0  # files at root

        a_entry = next(w for w in walked if w[0] == "/a")
        assert "b" in a_entry[1]  # dirs
        assert "file2" in a_entry[2]  # files


class TestDu:
    """Test disk usage calculation."""

    def test_du_node_count(self):
        tree = Loopy()
        tree.mkdir("/a/b/c", parents=True)
        tree.touch("/a/b/c/d")

        # root + a + b + c + d = 5 nodes
        assert tree.du("/") == 5
        assert tree.du("/a") == 4
        assert tree.du("/a/b/c") == 2

    def test_du_content_size(self):
        tree = Loopy()
        tree.touch("/a", "hello")  # 5 bytes
        tree.touch("/b", "world!")  # 6 bytes

        assert tree.du("/", content_size=True) == 11


class TestEdgeCases:
    """Edge cases and stress tests."""

    def test_deep_nesting(self):
        """Handle deeply nested paths."""
        tree = Loopy()
        deep_path = "/a/b/c/d/e/f/g/h/i/j/k/l/m/n/o/p"
        tree.mkdir(deep_path, parents=True)
        tree.touch(f"{deep_path}/leaf", "deep content")

        assert tree.exists(deep_path)
        assert tree.cat(f"{deep_path}/leaf") == "deep content"

    def test_special_content(self):
        """Content with special characters."""
        tree = Loopy()
        # Content that looks like tags
        tree.touch("/doc", "Use <tag> and </tag> in text")
        assert tree.cat("/doc") == "Use <tag> and </tag> in text"

    def test_unicode_content(self):
        """Unicode in content."""
        tree = Loopy()
        tree.touch("/emoji", "Hello 🌍 World 日本語")
        assert "🌍" in tree.cat("/emoji")
        assert "日本語" in tree.cat("/emoji")

    def test_empty_operations(self):
        """Operations on empty tree."""
        tree = Loopy()
        assert tree.ls("/") == []
        assert tree.du("/") == 1  # just root
        assert tree.grep("anything") == []  # nothing matches "anything"
        assert tree.grep("root") == ["/"]  # root name matches

    def test_repeated_names(self):
        """Same name at different levels."""
        tree = Loopy()
        tree.mkdir("/data/data/data", parents=True)
        tree.touch("/data/data/data/data", "innermost")

        assert tree.exists("/data/data/data/data")
        assert tree.cat("/data/data/data/data") == "innermost"
        assert tree.ls("/data") == ["data"]
        assert tree.ls("/data/data") == ["data"]

    def test_mv_rename_in_place(self):
        """Rename without changing parent."""
        tree = Loopy()
        tree.touch("/old_name", "content")
        tree.mv("/old_name", "/new_name")

        assert not tree.exists("/old_name")
        assert tree.exists("/new_name")
        assert tree.cat("/new_name") == "content"

    def test_cp_preserves_structure(self):
        """Copy subtree preserves children."""
        tree = Loopy()
        tree.mkdir("/src/a/b", parents=True)
        tree.touch("/src/a/b/file", "data")

        tree.cp("/src/a", "/dst/a")

        assert tree.exists("/dst/a/b/file")
        assert tree.cat("/dst/a/b/file") == "data"

    def test_rm_cleans_properly(self):
        """Remove doesn't leave artifacts."""
        tree = Loopy()
        tree.mkdir("/a/b/c", parents=True)
        tree.rm("/a/b", recursive=True)

        assert tree.exists("/a")
        assert not tree.exists("/a/b")
        assert "<b>" not in tree.raw
        assert "</b>" not in tree.raw

    def test_concurrent_like_operations(self):
        """Multiple operations in sequence."""
        tree = Loopy()

        # Simulate agent rapidly categorizing items
        for i in range(50):
            category = ["animals", "vehicles", "plants"][i % 3]
            subcategory = ["type_a", "type_b"][i % 2]
            tree.touch(f"/data/{category}/{subcategory}/item_{i:03d}", f"content_{i}")

        # Verify structure
        assert len(tree.ls("/data")) == 3
        assert tree.du("/data") > 50

        # Search
        animals = tree.grep("animals")
        assert len(animals) > 0

        # Bulk sed
        tree.sed("/data", r"content_(\d+)", r"processed_\1", recursive=True)
        assert "processed_" in tree.cat("/data/animals/type_a/item_000")


class TestInfo:
    """Test node metadata."""

    def test_info_file(self):
        tree = Loopy()
        tree.touch("/file", "hello world")

        info = tree.info("/file")
        assert info["name"] == "file"
        assert info["type"] == "file"
        assert info["content_length"] == 11
        assert info["children_count"] == 0

    def test_info_directory(self):
        tree = Loopy()
        tree.mkdir("/dir/child", parents=True)

        info = tree.info("/dir")
        assert info["name"] == "dir"
        assert info["type"] == "directory"
        assert info["children_count"] == 1

    def test_isdir_isfile(self):
        """Note: In Loopy, isdir = has children, isfile = no children (leaf).
        Empty directories appear as files since they have no children."""
        tree = Loopy()
        tree.mkdir("/dir/subdir", parents=True)
        tree.touch("/dir/file")
        tree.touch("/dir/subdir/child")  # Give subdir a child so it's a "dir"

        assert tree.isdir("/dir")
        assert tree.isdir("/dir/subdir")  # Now has children
        assert not tree.isdir("/dir/file")

        assert tree.isfile("/dir/file")
        assert tree.isfile("/dir/subdir/child")
        assert not tree.isfile("/dir")


class TestFilenamesWithDots:
    """Test filenames containing dots, hyphens, etc."""

    def test_cat_ignores_children_with_dots(self):
        """Parent's cat() should not include child tags like <file.txt>."""
        tree = Loopy()
        tree.mkdir("/project/src", parents=True)
        tree.touch("/project/src/main.py", "print('hello')")
        tree.touch("/project/README.md", "# Docs")

        # Parent directories should have empty content
        assert tree.cat("/project") == ""
        assert tree.cat("/project/src") == ""

        # Leaves should have their content
        assert tree.cat("/project/src/main.py") == "print('hello')"
        assert tree.cat("/project/README.md") == "# Docs"

    def test_tree_no_raw_xml_in_directories(self):
        """Tree output should not show raw XML for directory nodes."""
        tree = Loopy()
        tree.touch("/a/file.txt", "content")
        tree.touch("/a/data.json", '{"key": "value"}')

        viz = tree.tree()

        # Should NOT contain raw tags in the visualization
        assert "<file.txt>" not in viz
        assert "<data.json>" not in viz

        # Should show clean directory
        assert "a/" in viz

    def test_ls_with_dotted_names(self):
        """ls should return filenames with dots."""
        tree = Loopy()
        tree.touch("/src/app.min.js", "minified")
        tree.touch("/src/style.css", "styles")
        tree.touch("/.hidden", "secret")

        assert "app.min.js" in tree.ls("/src")
        assert "style.css" in tree.ls("/src")
        assert ".hidden" in tree.ls("/")

    def test_operations_on_dotted_paths(self):
        """All operations should work with dotted filenames."""
        tree = Loopy()
        tree.touch("/config.dev.json", '{"env": "dev"}')

        # mv
        tree.mv("/config.dev.json", "/config.prod.json")
        assert tree.exists("/config.prod.json")
        assert not tree.exists("/config.dev.json")

        # cp
        tree.cp("/config.prod.json", "/backup/config.prod.json")
        assert tree.exists("/backup/config.prod.json")

        # sed
        tree.sed("/config.prod.json", "dev", "prod")
        assert "prod" in tree.cat("/config.prod.json")

        # grep
        assert "/config.prod.json" in tree.grep("config")


class TestCd:
    """Test cd (change directory) functionality."""

    def test_cd_basic(self):
        tree = Loopy()
        tree.mkdir("/a/b/c", parents=True)

        tree.cd("/a/b")
        assert tree.cwd == "/a/b"

        tree.cd("c")  # relative
        assert tree.cwd == "/a/b/c"

    def test_cd_affects_operations(self):
        tree = Loopy()
        tree.mkdir("/project/src", parents=True)
        tree.cd("/project")

        # touch with relative path
        tree.touch("README.md", "hello")
        assert tree.exists("/project/README.md")

        # ls without args = cwd
        assert "src" in tree.ls()
        assert "README.md" in tree.ls()

        # cat with relative path
        assert tree.cat("README.md") == "hello"

    def test_cd_chaining(self):
        tree = (
            Loopy()
            .mkdir("/a/b", parents=True)
            .cd("/a")
            .touch("file1", "content1")
            .cd("b")
            .touch("file2", "content2")
        )

        assert tree.cwd == "/a/b"
        assert tree.cat("/a/file1") == "content1"
        assert tree.cat("/a/b/file2") == "content2"

    def test_cd_nonexistent_raises(self):
        tree = Loopy()
        try:
            tree.cd("/nonexistent")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass

    def test_cd_dot_means_cwd(self):
        tree = Loopy()
        tree.mkdir("/a/b", parents=True)
        tree.cd("/a/b")

        # "." should resolve to cwd
        assert tree.ls(".") == tree.ls()
        assert tree.tree(".") == tree.tree()

    def test_parent_path_dotdot(self):
        tree = Loopy()
        tree.mkdir("/a/b/c", parents=True)
        tree.touch("/a/sibling", "data")
        tree.cd("/a/b/c")

        # ".." should navigate to parent
        assert tree.ls("..") == ["c"]  # /a/b contains c
        assert tree.ls("../..") == ["b", "sibling"]  # /a contains b and sibling
        assert tree.cat("../../sibling") == "data"

        # cd with ..
        tree.cd("..")
        assert tree.cwd == "/a/b"
        tree.cd("..")
        assert tree.cwd == "/a"

        # .. at root stays at root
        tree.cd("/")
        tree.cd("..")
        assert tree.cwd == "/"


class TestHeadTail:
    """Test head/tail operations."""

    def test_head(self):
        tree = Loopy()
        tree.touch("/doc", "abcdefghijklmnop")

        assert tree.head("/doc", 5) == "abcde"
        assert tree.head("/doc", 100) == "abcdefghijklmnop"

    def test_tail(self):
        tree = Loopy()
        tree.touch("/doc", "abcdefghijklmnop")

        assert tree.tail("/doc", 5) == "lmnop"
        assert tree.tail("/doc", 100) == "abcdefghijklmnop"


if __name__ == "__main__":
    import sys

    # Run all test classes
    test_classes = [
        TestGrep,
        TestSed,
        TestGlob,
        TestFind,
        TestWalk,
        TestDu,
        TestEdgeCases,
        TestInfo,
        TestFilenamesWithDots,
        TestCd,
        TestHeadTail,
    ]

    failed = 0
    passed = 0

    for cls in test_classes:
        print(f"\n{'='*50}")
        print(f"Running {cls.__name__}")
        print('='*50)

        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                if hasattr(instance, "setup_method"):
                    instance.setup_method()
                try:
                    getattr(instance, method_name)()
                    print(f"  ✓ {method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  ✗ {method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {type(e).__name__}: {e}")
                    failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print('='*50)

    sys.exit(0 if failed == 0 else 1)
