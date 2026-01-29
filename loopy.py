"""
Loopy - A filesystem-like API over a tree stored as a string.

Usage:
    tree = Loopy()
    tree.mkdir("/animals/mammals", parents=True)
    tree.touch("/animals/mammals/dog", "golden retriever")
    tree.cat("/animals/mammals/dog")  # -> "golden retriever"
    tree.ls("/animals")  # -> ["mammals"]
    tree.grep("mam")  # -> ["/animals/mammals"]
"""

import re
from typing import Optional


def _escape(text: str) -> str:
    """Escape special characters for storage."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _unescape(text: str) -> str:
    """Unescape special characters when reading."""
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


class Loopy:
    """A lightweight tree structure stored as a string with filesystem operations."""

    def __init__(self, data: str = "<root/>"):
        self._data = data if data else "<root/>"

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

    def _normalize_path(self, path: str) -> list[str]:
        """Convert path string to list of segments."""
        path = path.strip("/")
        if not path:
            return []
        return path.split("/")

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

        # Search within bounds (start with full string, narrow down)
        search_start = 0
        search_end = len(self._data)

        for i, seg in enumerate(segments):
            # Look for self-closing or opening tag within current bounds
            pattern = rf"<({re.escape(seg)})(/?>)"
            search_region = self._data[search_start:search_end]
            match = re.search(pattern, search_region)
            if not match:
                raise KeyError(path)

            abs_start = search_start + match.start()

            if match.group(2) == "/>":
                # Self-closing tag
                if i == len(segments) - 1:
                    return abs_start, search_start + match.end(), False, ""
                else:
                    raise KeyError(path)  # Can't traverse into self-closing
            else:
                # Opening tag - find closing
                close_tag = f"</{seg}>"
                depth = 1
                scan_pos = search_start + match.end()

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
                            content_start = search_start + match.end()
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
            # Match tag names: alphanumeric, underscore, hyphen, dot
            match = re.search(r"<([\w.\-]+)(/?>)", content[pos:])
            if not match:
                break
            name = match.group(1)
            children.append(name)

            if match.group(2) == "/>":
                pos = pos + match.end()
            else:
                # Find closing tag, accounting for nesting
                close_tag = f"</{name}>"
                depth = 1
                search_pos = pos + match.end()
                while depth > 0:
                    next_open = re.search(rf"<{re.escape(name)}(/?>)", content[search_pos:])
                    next_close = content.find(close_tag, search_pos)
                    if next_close == -1:
                        break
                    if next_open and search_pos + next_open.start() < next_close:
                        if next_open.group(1) != "/>":
                            depth += 1
                        search_pos = search_pos + next_open.end()
                    else:
                        depth -= 1
                        search_pos = next_close + len(close_tag)
                pos = search_pos

        return children

    # --- Filesystem Operations ---

    def exists(self, path: str) -> bool:
        """Check if a path exists."""
        try:
            self._find_node(path)
            return True
        except KeyError:
            return False

    def ls(self, path: str = "/") -> list[str]:
        """List children of a node."""
        _, _, has_content, content = self._find_node(path)
        if not has_content:
            return []
        return self._extract_children(content)

    def cat(self, path: str) -> str:
        """Get the text content of a node (excludes child tags)."""
        _, _, has_content, content = self._find_node(path)
        if not has_content:
            return ""
        # Remove all child elements, keeping only direct text
        result = []
        pos = 0
        while pos < len(content):
            # Find next tag
            tag_match = re.search(r"<(\w+)(/?>)", content[pos:])
            if not tag_match:
                result.append(content[pos:])
                break

            # Add text before the tag
            result.append(content[pos : pos + tag_match.start()])

            if tag_match.group(2) == "/>":
                # Self-closing, skip it
                pos = pos + tag_match.end()
            else:
                # Find matching close tag
                tag_name = tag_match.group(1)
                close_tag = f"</{tag_name}>"
                depth = 1
                scan = pos + tag_match.end()
                while depth > 0 and scan < len(content):
                    next_open = re.search(rf"<{re.escape(tag_name)}(/?>)", content[scan:])
                    next_close = content.find(close_tag, scan)
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

        return _unescape("".join(result).strip())

    def mkdir(self, path: str, parents: bool = False) -> "Loopy":
        """Create a directory node. Use parents=True for mkdir -p behavior."""
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

        # Build nested tags for new nodes
        new_nodes = ""
        for seg in to_create:
            new_nodes = f"<{seg}>{new_nodes}</{seg}>" if new_nodes else f"<{seg}/>"

        # Wait, that's backwards. Let me fix:
        new_nodes = ""
        for seg in reversed(to_create):
            if new_nodes:
                new_nodes = f"<{seg}>{new_nodes}</{seg}>"
            else:
                new_nodes = f"<{seg}/>"

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
        if self.exists(path):
            # Update content if exists
            if content:
                return self.write(path, content)
            return self

        segments = self._normalize_path(path)
        if not segments:
            return self

        # Ensure parent exists
        if len(segments) > 1:
            parent_path = "/" + "/".join(segments[:-1])
            if not self.exists(parent_path):
                self.mkdir(parent_path, parents=True)

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
        """Write/overwrite content to a node."""
        if not self.exists(path):
            return self.touch(path, content)

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

    def rm(self, path: str) -> "Loopy":
        """Remove a node and its children."""
        if path == "/" or not path:
            self._data = "<root/>"
            return self

        start, end, _, _ = self._find_node(path)
        self._data = self._data[:start] + self._data[end:]

        return self

    def mv(self, src: str, dst: str) -> "Loopy":
        """Move a node to a new location."""
        # Get source node
        start, end, _, _ = self._find_node(src)
        node_str = self._data[start:end]

        # Remove from source
        self._data = self._data[:start] + self._data[end:]

        # Ensure destination parent exists
        dst_segments = self._normalize_path(dst)
        if len(dst_segments) > 1:
            dst_parent = "/" + "/".join(dst_segments[:-1])
            if not self.exists(dst_parent):
                self.mkdir(dst_parent, parents=True)

        # Rename node if needed
        src_segments = self._normalize_path(src)
        old_name = src_segments[-1]
        new_name = dst_segments[-1]

        if old_name != new_name:
            node_str = re.sub(
                rf"^<{re.escape(old_name)}(/?>)",
                f"<{new_name}\\1",
                node_str,
            )
            node_str = re.sub(
                rf"</{re.escape(old_name)}>$",
                f"</{new_name}>",
                node_str,
            )

        # Insert at destination
        dst_parent = "/" + "/".join(dst_segments[:-1]) if len(dst_segments) > 1 else "/"
        start, end, has_content, _ = self._find_node(dst_parent)
        parent_name = dst_segments[-2] if len(dst_segments) > 1 else "root"

        if has_content:
            close_pos = self._data.rfind(f"</{parent_name}>", start, end)
            self._data = self._data[:close_pos] + node_str + self._data[close_pos:]
        else:
            self._data = (
                self._data[:start]
                + f"<{parent_name}>{node_str}</{parent_name}>"
                + self._data[end:]
            )

        return self

    def cp(self, src: str, dst: str) -> "Loopy":
        """Copy a node to a new location."""
        start, end, _, _ = self._find_node(src)
        node_str = self._data[start:end]

        # Ensure destination parent exists
        dst_segments = self._normalize_path(dst)
        if len(dst_segments) > 1:
            dst_parent = "/" + "/".join(dst_segments[:-1])
            if not self.exists(dst_parent):
                self.mkdir(dst_parent, parents=True)

        # Rename node if needed
        src_segments = self._normalize_path(src)
        old_name = src_segments[-1]
        new_name = dst_segments[-1]

        if old_name != new_name:
            node_str = re.sub(
                rf"^<{re.escape(old_name)}(/?>)",
                f"<{new_name}\\1",
                node_str,
            )
            node_str = re.sub(
                rf"</{re.escape(old_name)}>$",
                f"</{new_name}>",
                node_str,
            )

        # Insert at destination
        dst_parent = "/" + "/".join(dst_segments[:-1]) if len(dst_segments) > 1 else "/"
        start, end, has_content, _ = self._find_node(dst_parent)
        parent_name = dst_segments[-2] if len(dst_segments) > 1 else "root"

        if has_content:
            close_pos = self._data.rfind(f"</{parent_name}>", start, end)
            self._data = self._data[:close_pos] + node_str + self._data[close_pos:]
        else:
            self._data = (
                self._data[:start]
                + f"<{parent_name}>{node_str}</{parent_name}>"
                + self._data[end:]
            )

        return self

    def grep(
        self,
        pattern: str,
        path: str = "/",
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

    def tree(self, path: str = "/") -> str:
        """Return a tree visualization."""
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

    def find(self, path: str = "/", name: Optional[str] = None, type: Optional[str] = None) -> list[str]:
        """
        Find nodes by name pattern (like find -name).

        Args:
            path: Starting path
            name: Regex pattern to match node names
            type: 'd' for directories (nodes with children), 'f' for files (leaf nodes)
        """
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

    def walk(self, path: str = "/") -> list[tuple[str, list[str], list[str]]]:
        """
        Walk the tree like os.walk().
        Yields (dirpath, dirnames, filenames) tuples.
        Directories = nodes with children, Files = leaf nodes.
        """
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

    def glob(self, pattern: str, path: str = "/") -> list[str]:
        """
        Match paths using glob patterns.
        Supports: * (any chars), ** (any depth), ? (single char)
        Example: /animals/*/dog, /images/**/*.jpg
        """
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
        content = self.cat(path)
        return content[:n]

    def tail(self, path: str, n: int = 10) -> str:
        """Get last n characters of content."""
        content = self.cat(path)
        return content[-n:] if content else ""

    def du(self, path: str = "/", content_size: bool = False) -> int:
        """
        Calculate size: node count or total content bytes.

        Args:
            path: Starting path
            content_size: If True, return total bytes of content. If False, return node count.
        """
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
        """Check if path is a directory (has children)."""
        if not self.exists(path):
            return False
        return len(self.ls(path)) > 0

    def isfile(self, path: str) -> bool:
        """Check if path is a file (leaf node, no children)."""
        if not self.exists(path):
            return False
        return len(self.ls(path)) == 0
