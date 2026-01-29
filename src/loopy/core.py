"""Core Loopy implementation."""

import re
from typing import Optional

# Regex pattern for valid tag names (alphanumeric, underscore, hyphen, dot)
TAG_NAME = r"[\w.\-]+"
_TAG_NAME_RE = re.compile(f"^{TAG_NAME}$")


def _validate_segment(seg: str) -> None:
    """Raise ValueError if segment contains invalid characters."""
    if not _TAG_NAME_RE.match(seg):
        raise ValueError(f"Invalid path segment: {seg!r} (only alphanumeric, underscore, hyphen, dot allowed)")


def _escape(text: str) -> str:
    """Escape special characters for storage."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _unescape(text: str) -> str:
    """Unescape special characters when reading."""
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def _skip_tag(content: str, tag_name: str, start: int) -> int:
    """
    Skip past a tag and its contents, handling nesting.
    Returns position after the closing tag (or after /> for self-closing).
    """
    close_tag = f"</{tag_name}>"
    depth = 1
    pos = start
    while depth > 0 and pos < len(content):
        next_open = re.search(rf"<{re.escape(tag_name)}(/?>)", content[pos:])
        next_close = content.find(close_tag, pos)
        if next_close == -1:
            return len(content)
        if next_open and pos + next_open.start() < next_close:
            if next_open.group(1) != "/>":
                depth += 1
            pos = pos + next_open.end()
        else:
            depth -= 1
            pos = next_close + len(close_tag)
    return pos


class Loopy:
    """A lightweight tree structure stored as a string with filesystem operations."""

    def __init__(self, data: str = "<root/>"):
        self._data = data if data else "<root/>"
        self._cwd = "/"

    @property
    def cwd(self) -> str:
        """Current working directory."""
        return self._cwd

    def _resolve(self, path: str) -> str:
        """Resolve path relative to cwd. Supports '.' and '..' components."""
        if not path or path == ".":
            return self._cwd
        if path.startswith("/"):
            full = path
        elif self._cwd == "/":
            full = f"/{path}"
        else:
            full = f"{self._cwd}/{path}"

        # Resolve . and .. components
        parts = []
        for seg in full.split("/"):
            if seg == "" or seg == ".":
                continue
            elif seg == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(seg)
        return "/" + "/".join(parts) if parts else "/"

    def cd(self, path: str = "/") -> "Loopy":
        """Change working directory. Returns self for chaining."""
        resolved = self._resolve(path)
        if not self.exists(resolved):
            raise KeyError(f"Path does not exist: {resolved}")
        if not self.isdir(resolved):
            raise NotADirectoryError(f"Not a directory: {resolved}")
        self._cwd = resolved
        return self

    @property
    def raw(self) -> str:
        """The raw string representation."""
        return self._data

    def __str__(self) -> str:
        return self._data

    def __repr__(self) -> str:
        return f"Loopy({self._data!r})"

    def __contains__(self, path: str) -> bool:
        return self.exists(path)

    # --- Core Path Utilities ---

    def _normalize_path(self, path: str, validate: bool = True) -> list[str]:
        """Convert path string to list of segments, optionally validating."""
        path = path.strip("/")
        if not path:
            return []
        segments = [s for s in path.split("/") if s and s != "."]
        if validate:
            for seg in segments:
                if seg != "..":
                    _validate_segment(seg)
        return segments

    def _find_node(self, path: str) -> tuple[int, int, bool, str]:
        """
        Find a node by path.
        Returns: (start_idx, end_idx, has_content, content)
        Raises KeyError if not found.
        """
        segments = self._normalize_path(path)
        if not segments:
            # Root node
            m = re.search(r"<root(/?>)", self._data)
            if m:
                if m.group(1) == "/>":
                    return m.start(), m.end(), False, ""
                else:
                    end = self._data.find("</root>")
                    return m.start(), end + 7, True, self._data[m.end():end]
            raise KeyError(path)

        # Start search from within root's content
        root_match = re.search(r"<root(/?>)", self._data)
        if not root_match:
            raise KeyError(path)
        if root_match.group(1) == "/>":
            raise KeyError(path)  # Root is empty, can't find anything
        root_end = self._data.find("</root>")
        search_start = root_match.end()
        search_end = root_end

        for i, seg in enumerate(segments):
            # Look for self-closing or opening tag - but only DIRECT children
            search_region = self._data[search_start:search_end]

            # Find direct child by parsing at current level only
            match = None
            pos = 0
            while pos < len(search_region):
                tag_match = re.search(rf"<({TAG_NAME})(/?>)", search_region[pos:])
                if not tag_match:
                    break

                tag_name = tag_match.group(1)
                tag_end_type = tag_match.group(2)

                if tag_name == seg:
                    # Found our segment as a direct child
                    match = tag_match
                    match_pos = pos  # Track position for absolute calculation
                    break

                # Skip this tag (not our target) - need to skip its entire content
                if tag_end_type == "/>":
                    pos = pos + tag_match.end()
                else:
                    # Find matching close tag
                    close_tag = f"</{tag_name}>"
                    depth = 1
                    scan = pos + tag_match.end()
                    while depth > 0 and scan < len(search_region):
                        next_open = re.search(rf"<{re.escape(tag_name)}(/?>)", search_region[scan:])
                        next_close = search_region.find(close_tag, scan)
                        if next_close == -1:
                            break
                        if next_open and scan + next_open.start() < next_close:
                            if next_open.group(1) != "/>":
                                depth += 1
                            scan = scan + next_open.end()
                        else:
                            depth -= 1
                            scan = next_close + len(close_tag)
                    pos = scan

            if not match:
                raise KeyError(path)

            abs_start = search_start + match_pos + match.start()

            if match.group(2) == "/>":
                # Self-closing tag
                if i == len(segments) - 1:
                    return abs_start, search_start + match_pos + match.end(), False, ""
                else:
                    raise KeyError(path)  # Can't traverse into self-closing
            else:
                # Opening tag - find closing
                close_tag = f"</{seg}>"
                depth = 1
                scan_pos = search_start + match_pos + match.end()

                while depth > 0:
                    next_open = re.search(rf"<{re.escape(seg)}(/?>)", self._data[scan_pos:search_end])
                    next_close = self._data.find(close_tag, scan_pos, search_end)

                    if next_close == -1:
                        raise KeyError(f"Malformed: unclosed <{seg}>")

                    if next_open and scan_pos + next_open.start() < next_close:
                        if next_open.group(1) != "/>":
                            depth += 1
                        scan_pos = scan_pos + next_open.end()
                    else:
                        depth -= 1
                        if depth == 0:
                            abs_end = next_close + len(close_tag)
                            content_start = search_start + match_pos + match.end()
                            content = self._data[content_start:next_close]

                            if i == len(segments) - 1:
                                return abs_start, abs_end, True, content
                            else:
                                # Narrow search bounds to this node's content
                                search_start = content_start
                                search_end = next_close
                        else:
                            scan_pos = next_close + len(close_tag)

        raise KeyError(path)

    def _extract_children(self, content: str) -> list[str]:
        """Extract immediate child tag names from content string."""
        children = []
        pos = 0
        while pos < len(content):
            match = re.search(rf"<({TAG_NAME})(/?>)", content[pos:])
            if not match:
                break
            name = match.group(1)
            children.append(name)
            if match.group(2) == "/>":
                pos = pos + match.end()
            else:
                pos = _skip_tag(content, name, pos + match.end())
        return children

    # --- Filesystem Operations ---

    def exists(self, path: str) -> bool:
        """Check if a path exists."""
        path = self._resolve(path)
        try:
            self._find_node(path)
            return True
        except KeyError:
            return False

    def ls(self, path: str = ".", classify: bool = False) -> list[str]:
        """List children of a node. Use classify=True to append / to directories (like ls -F)."""
        path = self._resolve(path)
        _, _, has_content, content = self._find_node(path)
        if not has_content:
            return []
        children = self._extract_children(content)
        if classify:
            result = []
            for child in children:
                child_path = f"{path.rstrip('/')}/{child}"
                if self.isdir(child_path):
                    result.append(f"{child}/")
                else:
                    result.append(child)
            return result
        return children

    def cat(self, path: str) -> str:
        """Get the text content of a node (excludes child tags)."""
        path = self._resolve(path)
        _, _, has_content, content = self._find_node(path)
        if not has_content:
            return ""
        # Remove all child elements, keeping only direct text
        result = []
        pos = 0
        while pos < len(content):
            match = re.search(rf"<({TAG_NAME})(/?>)", content[pos:])
            if not match:
                result.append(content[pos:])
                break
            result.append(content[pos : pos + match.start()])
            if match.group(2) == "/>":
                pos = pos + match.end()
            else:
                pos = _skip_tag(content, match.group(1), pos + match.end())
        return _unescape("".join(result).strip())

    def mkdir(self, path: str, parents: bool = False) -> "Loopy":
        """Create a directory node. Use parents=True for mkdir -p behavior."""
        path = self._resolve(path)
        segments = self._normalize_path(path)
        if not segments:
            return self

        # Find how much of the path exists
        existing = []
        for i, seg in enumerate(segments):
            test_path = "/" + "/".join(segments[: i + 1])
            if self.exists(test_path):
                existing.append(seg)
            else:
                break

        to_create = segments[len(existing):]

        if not to_create:
            return self  # Already exists

        if len(to_create) > 1 and not parents:
            parent_path = "/" + "/".join(segments[:-1])
            raise KeyError(f"Parent path does not exist: {parent_path}")

        # Check if we're trying to create under a file (has text content)
        if existing:
            parent_path = "/" + "/".join(existing)
            if self.isfile(parent_path):
                raise NotADirectoryError(f"Cannot create directory under file: {parent_path}")

        # Build nested tags for new nodes (innermost first)
        # Use open/close tags (not self-closing) so directories are distinguishable from files
        new_nodes = f"<{to_create[-1]}></{to_create[-1]}>"
        for seg in reversed(to_create[:-1]):
            new_nodes = f"<{seg}>{new_nodes}</{seg}>"

        # Insert into parent
        if existing:
            parent_path = "/" + "/".join(existing)
        else:
            parent_path = "/"

        start, end, has_content, content = self._find_node(parent_path)

        if has_content:
            # Insert before closing tag
            parent_name = existing[-1] if existing else "root"
            close_pos = self._data.rfind(f"</{parent_name}>", start, end)
            self._data = self._data[:close_pos] + new_nodes + self._data[close_pos:]
        else:
            # Convert self-closing to open/close
            parent_name = existing[-1] if existing else "root"
            self._data = (
                self._data[:start]
                + f"<{parent_name}>{new_nodes}</{parent_name}>"
                + self._data[end:]
            )

        return self

    def touch(self, path: str, content: str = "") -> "Loopy":
        """Create a leaf node with optional content."""
        path = self._resolve(path)
        if self.exists(path):
            # Update content if exists
            if content:
                return self.write(path, content)
            return self

        segments = self._normalize_path(path)
        if not segments:
            return self

        # Ensure parent exists and is not a file
        if len(segments) > 1:
            parent_path = "/" + "/".join(segments[:-1])
            if not self.exists(parent_path):
                self.mkdir(parent_path, parents=True)
            elif self.isfile(parent_path):
                raise NotADirectoryError(f"Cannot create file under file: {parent_path}")

        name = segments[-1]
        if content:
            new_node = f"<{name}>{_escape(content)}</{name}>"
        else:
            new_node = f"<{name}/>"

        # Insert into parent
        parent_path = "/" + "/".join(segments[:-1]) if len(segments) > 1 else "/"
        start, end, has_content, _ = self._find_node(parent_path)

        if has_content:
            parent_name = segments[-2] if len(segments) > 1 else "root"
            close_pos = self._data.rfind(f"</{parent_name}>", start, end)
            self._data = self._data[:close_pos] + new_node + self._data[close_pos:]
        else:
            parent_name = segments[-2] if len(segments) > 1 else "root"
            self._data = (
                self._data[:start]
                + f"<{parent_name}>{new_node}</{parent_name}>"
                + self._data[end:]
            )

        return self

    def write(self, path: str, content: str) -> "Loopy":
        """Write/overwrite content to a node. Raises IsADirectoryError for directories."""
        path = self._resolve(path)
        if not self.exists(path):
            return self.touch(path, content)

        # Don't allow writing content to directories
        if self.ls(path):
            raise IsADirectoryError(f"Cannot write content to directory: {path}")

        segments = self._normalize_path(path)
        name = segments[-1] if segments else "root"

        start, end, has_content, old_content = self._find_node(path)

        # Preserve children, replace text content
        children_tags = ""
        for child in self._extract_children(old_content):
            child_start = old_content.find(f"<{child}")
            if old_content[child_start:].startswith(f"<{child}/>"):
                children_tags += f"<{child}/>"
            else:
                child_end = old_content.find(f"</{child}>", child_start) + len(f"</{child}>")
                children_tags += old_content[child_start:child_end]

        escaped_content = _escape(content)
        new_inner = escaped_content + children_tags if children_tags else escaped_content
        self._data = self._data[:start] + f"<{name}>{new_inner}</{name}>" + self._data[end:]

        return self

    def rm(self, path: str, recursive: bool = False) -> "Loopy":
        """Remove a node. Use recursive=True for non-empty directories."""
        path = self._resolve(path)
        if path == "/" or not path:
            if not recursive:
                raise OSError("Cannot remove root without recursive=True")
            self._data = "<root/>"
            return self

        # Check if non-empty directory
        if self.ls(path) and not recursive:
            raise OSError(f"Directory not empty: {path} (use recursive=True)")

        start, end, _, _ = self._find_node(path)
        self._data = self._data[:start] + self._data[end:]
        return self

    def _insert_node(self, node_str: str, src_name: str, dst: str) -> None:
        """Insert a node string at destination path, renaming if needed."""
        dst_segments = self._normalize_path(dst)
        new_name = dst_segments[-1]

        # Ensure destination parent exists
        if len(dst_segments) > 1:
            dst_parent = "/" + "/".join(dst_segments[:-1])
            if not self.exists(dst_parent):
                self.mkdir(dst_parent, parents=True)

        # Rename node if needed
        if src_name != new_name:
            node_str = re.sub(rf"^<{re.escape(src_name)}(/?>)", f"<{new_name}\\1", node_str)
            node_str = re.sub(rf"</{re.escape(src_name)}>$", f"</{new_name}>", node_str)

        # Insert at destination parent
        dst_parent = "/" + "/".join(dst_segments[:-1]) if len(dst_segments) > 1 else "/"
        start, end, has_content, _ = self._find_node(dst_parent)
        parent_name = dst_segments[-2] if len(dst_segments) > 1 else "root"

        if has_content:
            close_pos = self._data.rfind(f"</{parent_name}>", start, end)
            self._data = self._data[:close_pos] + node_str + self._data[close_pos:]
        else:
            self._data = f"{self._data[:start]}<{parent_name}>{node_str}</{parent_name}>{self._data[end:]}"

    def mv(self, src: str, dst: str) -> "Loopy":
        """Move a node to a new location. If dst is a directory, moves into it."""
        src, dst = self._resolve(src.rstrip("/")), self._resolve(dst.rstrip("/"))

        # mv to self is a no-op (check before directory expansion)
        if src == dst:
            return self

        # If destination is existing directory, move INTO it with same name
        if self.exists(dst) and self.isdir(dst):
            src_name = self._normalize_path(src)[-1]
            dst = f"{dst.rstrip('/')}/{src_name}"
            # Check again after expansion
            if src == dst:
                return self

        start, end, _, _ = self._find_node(src)
        node_str = self._data[start:end]
        src_name = self._normalize_path(src)[-1]

        self._data = self._data[:start] + self._data[end:]  # Remove source
        self._insert_node(node_str, src_name, dst)
        return self

    def cp(self, src: str, dst: str) -> "Loopy":
        """Copy a node to a new location. If dst is a directory, copies into it."""
        src, dst = self._resolve(src.rstrip("/")), self._resolve(dst.rstrip("/"))

        # cp to self is an error (check before directory expansion)
        if src == dst:
            raise ValueError(f"Cannot copy to self: {src}")

        # If destination is existing directory, copy INTO it with same name
        if self.exists(dst) and self.isdir(dst):
            src_name = self._normalize_path(src)[-1]
            dst = f"{dst.rstrip('/')}/{src_name}"
            # Check again after expansion
            if src == dst:
                raise ValueError(f"Cannot copy to self: {src}")

        start, end, _, _ = self._find_node(src)
        node_str = self._data[start:end]
        src_name = self._normalize_path(src)[-1]

        self._insert_node(node_str, src_name, dst)
        return self

    def grep(
        self,
        pattern: str,
        path: str = ".",
        content: bool = False,
        ignore_case: bool = True,
        invert: bool = False,
        count: bool = False,
    ) -> list[str] | int:
        """
        Search for nodes matching a pattern.

        Args:
            pattern: Regex pattern to search
            path: Starting path (default: root)
            content: If True, also search node content (not just names)
            ignore_case: Case insensitive matching (default: True)
            invert: Return non-matching paths instead (-v flag)
            count: Return count instead of list (-c flag)

        Returns:
            List of matching paths, or count if count=True
        """
        path = self._resolve(path)
        flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(pattern, flags)
        results = []

        def _walk(current_path: str):
            segments = self._normalize_path(current_path)
            name = segments[-1] if segments else "root"

            matches = bool(regex.search(name))

            # Also search content if requested
            if not matches and content:
                try:
                    node_content = self.cat(current_path)
                    if node_content and regex.search(node_content):
                        matches = True
                except KeyError:
                    pass

            # Apply invert
            if invert:
                matches = not matches

            if matches:
                results.append(current_path)

            # Recurse into children
            for child in self.ls(current_path):
                _walk(f"{current_path.rstrip('/')}/{child}")

        _walk(path)
        return len(results) if count else results

    def sed(
        self,
        path: str,
        pattern: str,
        replacement: str,
        count: int = 0,
        ignore_case: bool = False,
        recursive: bool = False,
    ) -> "Loopy":
        """
        Replace pattern in node's text content.

        Args:
            path: Path to the node
            pattern: Regex pattern to match
            replacement: Replacement string (supports \\1, \\2 backrefs)
            count: Max replacements (0 = unlimited, like sed default)
            ignore_case: Case insensitive matching
            recursive: Apply to all descendants too

        Returns:
            self for chaining
        """
        path = self._resolve(path)
        flags = re.IGNORECASE if ignore_case else 0

        def _apply(node_path: str):
            content = self.cat(node_path)
            if content:
                new_content = re.sub(pattern, replacement, content, count=count, flags=flags)
                if new_content != content:
                    self.write(node_path, new_content)

        _apply(path)

        if recursive:
            for child in self.ls(path):
                child_path = f"{path.rstrip('/')}/{child}"
                self.sed(child_path, pattern, replacement, count, ignore_case, recursive=True)

        return self

    def tree(self, path: str = ".") -> str:
        """Return a tree visualization."""
        path = self._resolve(path)
        lines = []

        def _walk(current_path: str, prefix: str, is_last: bool, is_root: bool):
            segments = self._normalize_path(current_path)
            name = segments[-1] if segments else "root"

            # Connector for this node
            if is_root:
                connector = ""
            else:
                connector = "└── " if is_last else "├── "

            content = self.cat(current_path)
            if content:
                lines.append(f"{prefix}{connector}{name}: {content[:50]}{'...' if len(content) > 50 else ''}")
            else:
                lines.append(f"{prefix}{connector}{name}/")

            children = self.ls(current_path)
            for i, child in enumerate(children):
                child_is_last = i == len(children) - 1
                child_path = f"{current_path.rstrip('/')}/{child}"
                if is_root:
                    child_prefix = ""
                else:
                    child_prefix = prefix + ("    " if is_last else "│   ")
                _walk(child_path, child_prefix, child_is_last, False)

        _walk(path, "", True, True)
        return "\n".join(lines)

    def find(self, path: str = ".", name: Optional[str] = None, type: Optional[str] = None) -> list[str]:
        """
        Find nodes by name pattern (like find -name).

        Args:
            path: Starting path
            name: Regex pattern to match node names
            type: 'd' for directories (nodes with children), 'f' for files (leaf nodes)
        """
        path = self._resolve(path)
        results = []
        pattern = re.compile(name, re.IGNORECASE) if name else None

        def _walk(current_path: str):
            segments = self._normalize_path(current_path)
            node_name = segments[-1] if segments else "root"
            children = self.ls(current_path)
            is_dir = len(children) > 0

            # Type filter
            if type == 'd' and not is_dir:
                pass
            elif type == 'f' and is_dir:
                pass
            elif pattern is None or pattern.search(node_name):
                results.append(current_path)

            for child in children:
                _walk(f"{current_path.rstrip('/')}/{child}")

        _walk(path)
        return results

    def walk(self, path: str = ".") -> list[tuple[str, list[str], list[str]]]:
        """
        Walk the tree like os.walk().
        Yields (dirpath, dirnames, filenames) tuples.
        Directories = nodes with children, Files = leaf nodes.
        """
        path = self._resolve(path)
        results = []

        def _walk(current_path: str):
            children = self.ls(current_path)
            dirs = []
            files = []
            for child in children:
                child_path = f"{current_path.rstrip('/')}/{child}"
                if self.ls(child_path):  # Has children = directory
                    dirs.append(child)
                else:
                    files.append(child)
            results.append((current_path, dirs, files))
            for d in dirs:
                _walk(f"{current_path.rstrip('/')}/{d}")

        _walk(path)
        return results

    def glob(self, pattern: str, path: str = ".") -> list[str]:
        """
        Match paths using glob patterns.
        Supports: * (any chars), ** (any depth), ? (single char)
        Example: /animals/*/dog, /images/**/*.jpg
        """
        path = self._resolve(path)
        # Convert glob to regex
        regex_pattern = pattern
        regex_pattern = regex_pattern.replace(".", r"\.")
        regex_pattern = regex_pattern.replace("**", "<<<GLOBSTAR>>>")
        regex_pattern = regex_pattern.replace("*", r"[^/]*")
        regex_pattern = regex_pattern.replace("<<<GLOBSTAR>>>", r".*")
        regex_pattern = regex_pattern.replace("?", r"[^/]")
        regex_pattern = f"^{regex_pattern}$"

        regex = re.compile(regex_pattern)
        results = []

        def _walk(current_path: str):
            if regex.match(current_path):
                results.append(current_path)
            for child in self.ls(current_path):
                _walk(f"{current_path.rstrip('/')}/{child}")

        _walk(path)
        return results

    def head(self, path: str, n: int = 10) -> str:
        """Get first n characters of content."""
        path = self._resolve(path)
        content = self.cat(path)
        return content[:n]

    def tail(self, path: str, n: int = 10) -> str:
        """Get last n characters of content."""
        path = self._resolve(path)
        content = self.cat(path)
        return content[-n:] if content else ""

    def du(self, path: str = ".", content_size: bool = False) -> int:
        """
        Calculate size: node count or total content bytes.

        Args:
            path: Starting path
            content_size: If True, return total bytes of content. If False, return node count.
        """
        path = self._resolve(path)
        total = 0

        def _walk(current_path: str):
            nonlocal total
            if content_size:
                total += len(self.cat(current_path))
            else:
                total += 1
            for child in self.ls(current_path):
                _walk(f"{current_path.rstrip('/')}/{child}")

        _walk(path)
        return total

    def info(self, path: str) -> dict:
        """Get metadata about a node."""
        path = self._resolve(path)
        _, _, has_content, content = self._find_node(path)
        children = self.ls(path)
        text_content = self.cat(path)

        segments = self._normalize_path(path)
        name = segments[-1] if segments else "root"

        return {
            "name": name,
            "path": path,
            "type": "directory" if children else "file",
            "children_count": len(children),
            "content_length": len(text_content),
            "has_content": bool(text_content),
        }

    def isdir(self, path: str) -> bool:
        """Check if path is a directory (open/close tag that can contain children)."""
        path = self._resolve(path)
        try:
            _, _, has_content, content = self._find_node(path)
            # Directory = open/close tag with no text content (only children or empty)
            # Check if any text exists outside of child tags
            if not has_content:
                return False  # Self-closing = file
            text_only = self.cat(path)
            return not text_only  # Directory if no text content
        except KeyError:
            return False

    def isfile(self, path: str) -> bool:
        """Check if path is a file (self-closing or has text content)."""
        path = self._resolve(path)
        try:
            _, _, has_content, _ = self._find_node(path)
            if not has_content:
                return True  # Self-closing = file
            # Has text content = file (even if it has children)
            return bool(self.cat(path))
        except KeyError:
            return False
