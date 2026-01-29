"""Core Loopy implementation (node-based)."""

from dataclasses import dataclass, field
import re
from typing import Optional

# Regex pattern for valid tag names (alphanumeric, underscore, hyphen, dot)
TAG_NAME = r"[\w.\-]+"
_TAG_NAME_RE = re.compile(f"^{TAG_NAME}$")


def _validate_segment(seg: str) -> None:
    """Raise ValueError if segment contains invalid characters."""
    if not _TAG_NAME_RE.match(seg):
        raise ValueError(
            f"Invalid path segment: {seg!r} (only alphanumeric, underscore, hyphen, dot allowed)"
        )


def _escape(text: str) -> str:
    """Escape special characters for storage."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _unescape(text: str) -> str:
    """Unescape special characters when reading."""
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


@dataclass
class Node:
    name: str
    text: str = ""
    children: list["Node"] = field(default_factory=list)
    parent: Optional["Node"] = None
    self_closing: bool = False


def parse(data: str) -> Node:
    """Parse raw loopy data into a Node tree."""
    if not data:
        data = "<root/>"

    stack: list[Node] = []
    root: Optional[Node] = None
    pos = 0

    while pos < len(data):
        if data[pos] != "<":
            next_tag = data.find("<", pos)
            if next_tag == -1:
                next_tag = len(data)
            if stack:
                stack[-1].text += _unescape(data[pos:next_tag])
            pos = next_tag
            continue

        end = data.find(">", pos + 1)
        if end == -1:
            raise ValueError("Malformed: missing closing '>'")

        token = data[pos + 1 : end]
        if not token:
            raise ValueError("Malformed: empty tag")

        if token.startswith("/"):
            name = token[1:]
            if not stack or stack[-1].name != name:
                raise ValueError(f"Malformed: unexpected closing tag </{name}>")
            node = stack.pop()
            if not stack:
                root = node
        else:
            self_closing = token.endswith("/")
            name = token[:-1] if self_closing else token
            if not _TAG_NAME_RE.match(name):
                raise ValueError(f"Invalid tag name: {name!r}")
            parent = stack[-1] if stack else None
            node = Node(name=name, parent=parent, self_closing=self_closing)
            if parent:
                parent.children.append(node)
            if self_closing:
                if not stack:
                    root = node
            else:
                stack.append(node)

        pos = end + 1

    if stack:
        raise ValueError(f"Malformed: unclosed <{stack[-1].name}>")
    if root is None:
        raise ValueError("Malformed: missing root element")
    return root


def emit(node: Node) -> str:
    """Serialize a Node tree to raw loopy data."""
    if node.self_closing and not node.children and not node.text:
        return f"<{node.name}/>"

    inner = _escape(node.text)
    for child in node.children:
        inner += emit(child)
    return f"<{node.name}>{inner}</{node.name}>"


class Loopy:
    """A lightweight tree structure stored as a string with filesystem operations."""

    def __init__(self, data: str = "<root/>"):
        raw = data if data else "<root/>"
        self._raw_cache = raw
        self._root = parse(raw)
        self._cwd = "/"
        self._dirty = False

    @property
    def cwd(self) -> str:
        """Current working directory."""
        return self._cwd

    def _mark_dirty(self) -> None:
        self._dirty = True

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

        parts = []
        for seg in full.split("/"):
            if seg == "" or seg == ".":
                continue
            if seg == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(seg)
        return "/" + "/".join(parts) if parts else "/"

    @property
    def raw(self) -> str:
        """The raw string representation."""
        if self._dirty:
            self._raw_cache = emit(self._root)
            self._dirty = False
        return self._raw_cache

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        return f"Loopy({self.raw!r})"

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

    def _get_child(self, node: Node, name: str) -> Optional[Node]:
        for child in node.children:
            if child.name == name:
                return child
        return None

    def _get_node_by_segments(self, segments: list[str]) -> Node:
        node = self._root
        for seg in segments:
            child = self._get_child(node, seg)
            if child is None:
                raise KeyError("/" + "/".join(segments))
            node = child
        return node

    def _get_node(self, path: str) -> Node:
        segments = self._normalize_path(path)
        return self._get_node_by_segments(segments)

    def _cat_node(self, node: Node) -> str:
        return node.text.strip()

    def _is_dir_node(self, node: Node) -> bool:
        if node.self_closing:
            return False
        return not self._cat_node(node)

    def _is_file_node(self, node: Node) -> bool:
        if node.self_closing:
            return True
        return bool(self._cat_node(node))

    def _child_path(self, parent_path: str, child_name: str) -> str:
        if parent_path == "/":
            return f"/{child_name}"
        return f"{parent_path}/{child_name}"

    # --- Filesystem Operations ---

    def cd(self, path: str = "/") -> "Loopy":
        """Change working directory. Returns self for chaining."""
        resolved = self._resolve(path)
        if not self.exists(resolved):
            raise KeyError(f"Path does not exist: {resolved}")
        if not self.isdir(resolved):
            raise NotADirectoryError(f"Not a directory: {resolved}")
        self._cwd = resolved
        return self

    def exists(self, path: str) -> bool:
        """Check if a path exists."""
        path = self._resolve(path)
        try:
            self._get_node(path)
            return True
        except KeyError:
            return False

    def ls(self, path: str = ".", classify: bool = False) -> list[str]:
        """List children of a node. Use classify=True to append / to directories (like ls -F)."""
        path = self._resolve(path)
        node = self._get_node(path)
        if not node.children:
            return []
        if not classify:
            return [child.name for child in node.children]
        result = []
        for child in node.children:
            if self._is_dir_node(child):
                result.append(f"{child.name}/")
            else:
                result.append(child.name)
        return result

    def cat(self, path: str) -> str:
        """Get the text content of a node (excludes child tags)."""
        path = self._resolve(path)
        node = self._get_node(path)
        return self._cat_node(node)

    def mkdir(self, path: str, parents: bool = False) -> "Loopy":
        """Create a directory node. Use parents=True for mkdir -p behavior."""
        path = self._resolve(path)
        segments = self._normalize_path(path)
        if not segments:
            return self

        node = self._root
        index = 0
        while index < len(segments):
            child = self._get_child(node, segments[index])
            if child is None:
                break
            node = child
            index += 1

        if index == len(segments):
            return self

        if len(segments) - index > 1 and not parents:
            parent_path = "/" + "/".join(segments[:-1])
            raise KeyError(f"Parent path does not exist: {parent_path}")

        if index > 0 and self._is_file_node(node):
            parent_path = "/" + "/".join(segments[:index])
            raise NotADirectoryError(
                f"Cannot create directory under file: {parent_path}"
            )

        while index < len(segments):
            seg = segments[index]
            new_node = Node(name=seg, parent=node, self_closing=False)
            node.children.append(new_node)
            node.self_closing = False
            node = new_node
            index += 1

        self._mark_dirty()
        return self

    def touch(self, path: str, content: str = "") -> "Loopy":
        """Create a leaf node with optional content."""
        path = self._resolve(path)
        if self.exists(path):
            if content:
                return self.write(path, content)
            return self

        segments = self._normalize_path(path)
        if not segments:
            return self

        if len(segments) > 1:
            parent_path = "/" + "/".join(segments[:-1])
            if not self.exists(parent_path):
                self.mkdir(parent_path, parents=True)
            else:
                parent_node = self._get_node(parent_path)
                if self._is_file_node(parent_node):
                    raise NotADirectoryError(
                        f"Cannot create file under file: {parent_path}"
                    )

        parent_path = "/" + "/".join(segments[:-1]) if len(segments) > 1 else "/"
        parent_node = self._get_node(parent_path)
        name = segments[-1]
        new_node = Node(
            name=name,
            parent=parent_node,
            text=content if content else "",
            self_closing=not bool(content),
        )
        parent_node.children.append(new_node)
        parent_node.self_closing = False
        self._mark_dirty()
        return self

    def write(self, path: str, content: str) -> "Loopy":
        """Write/overwrite content to a node. Raises IsADirectoryError for directories."""
        path = self._resolve(path)
        try:
            node = self._get_node(path)
        except KeyError:
            return self.touch(path, content)

        if node.children:
            raise IsADirectoryError(f"Cannot write content to directory: {path}")

        node.text = content
        node.self_closing = False
        self._mark_dirty()
        return self

    def rm(self, path: str, recursive: bool = False) -> "Loopy":
        """Remove a node. Use recursive=True for non-empty directories."""
        path = self._resolve(path)
        if path == "/" or not path:
            if not recursive:
                raise OSError("Cannot remove root without recursive=True")
            self._root = Node(name="root", self_closing=True)
            self._mark_dirty()
            return self

        segments = self._normalize_path(path)
        parent_segments = segments[:-1]
        parent = self._get_node_by_segments(parent_segments)
        target_name = segments[-1]

        target = None
        for child in parent.children:
            if child.name == target_name:
                target = child
                break
        if target is None:
            raise KeyError(path)

        if target.children and not recursive:
            raise OSError(f"Directory not empty: {path} (use recursive=True)")

        parent.children.remove(target)
        self._mark_dirty()
        return self

    def _clone_node(self, node: Node, parent: Optional[Node] = None) -> Node:
        clone = Node(
            name=node.name,
            parent=parent,
            text=node.text,
            self_closing=node.self_closing,
        )
        for child in node.children:
            clone_child = self._clone_node(child, parent=clone)
            clone.children.append(clone_child)
        return clone

    def _insert_node(self, node: Node, src_name: str, dst: str) -> None:
        dst_segments = self._normalize_path(dst)
        new_name = dst_segments[-1]

        if len(dst_segments) > 1:
            dst_parent = "/" + "/".join(dst_segments[:-1])
            if not self.exists(dst_parent):
                self.mkdir(dst_parent, parents=True)

        dst_parent = "/" + "/".join(dst_segments[:-1]) if len(dst_segments) > 1 else "/"
        parent_node = self._get_node(dst_parent)

        if src_name != new_name:
            node.name = new_name

        node.parent = parent_node
        parent_node.children.append(node)
        parent_node.self_closing = False

    def mv(self, src: str, dst: str) -> "Loopy":
        """Move a node to a new location. If dst is a directory, moves into it."""
        src, dst = self._resolve(src.rstrip("/")), self._resolve(dst.rstrip("/"))

        if src == dst:
            return self

        if self.exists(dst) and self.isdir(dst):
            src_name = self._normalize_path(src)[-1]
            dst = f"{dst.rstrip('/')}/{src_name}"
            if src == dst:
                return self

        src_segments = self._normalize_path(src)
        src_parent = (
            self._get_node_by_segments(src_segments[:-1]) if src_segments else None
        )
        node = self._get_node_by_segments(src_segments)
        src_name = node.name

        if src_parent is not None:
            src_parent.children.remove(node)

        self._insert_node(node, src_name, dst)
        self._mark_dirty()
        return self

    def cp(self, src: str, dst: str) -> "Loopy":
        """Copy a node to a new location. If dst is a directory, copies into it."""
        src, dst = self._resolve(src.rstrip("/")), self._resolve(dst.rstrip("/"))

        if src == dst:
            raise ValueError(f"Cannot copy to self: {src}")

        if self.exists(dst) and self.isdir(dst):
            src_name = self._normalize_path(src)[-1]
            dst = f"{dst.rstrip('/')}/{src_name}"
            if src == dst:
                raise ValueError(f"Cannot copy to self: {src}")

        node = self._get_node(src)
        clone = self._clone_node(node)
        self._insert_node(clone, node.name, dst)
        self._mark_dirty()
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
        results: list[str] = []

        start_node = self._get_node(path)

        def _walk(node: Node, current_path: str) -> None:
            name = "root" if current_path == "/" else current_path.split("/")[-1]
            matches = bool(regex.search(name))

            if not matches and content:
                node_content = self._cat_node(node)
                if node_content and regex.search(node_content):
                    matches = True

            if invert:
                matches = not matches

            if matches:
                results.append(current_path)

            for child in node.children:
                _walk(child, self._child_path(current_path, child.name))

        _walk(start_node, path)
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
            replacement: Replacement string (supports \1, \2 backrefs)
            count: Max replacements (0 = unlimited, like sed default)
            ignore_case: Case insensitive matching
            recursive: Apply to all descendants too

        Returns:
            self for chaining
        """
        path = self._resolve(path)
        flags = re.IGNORECASE if ignore_case else 0

        def _apply(node_path: str) -> None:
            content = self.cat(node_path)
            if content:
                new_content = re.sub(
                    pattern, replacement, content, count=count, flags=flags
                )
                if new_content != content:
                    self.write(node_path, new_content)

        _apply(path)

        if recursive:
            for child in self.ls(path):
                child_path = f"{path.rstrip('/')}/{child}"
                self.sed(
                    child_path, pattern, replacement, count, ignore_case, recursive=True
                )

        return self

    def tree(self, path: str = ".") -> str:
        """Return a tree visualization."""
        path = self._resolve(path)
        node = self._get_node(path)
        lines: list[str] = []

        def _walk(
            current_node: Node,
            current_path: str,
            prefix: str,
            is_last: bool,
            is_root: bool,
        ) -> None:
            name = "root" if current_path == "/" else current_node.name

            if is_root:
                connector = ""
            else:
                connector = "└── " if is_last else "├── "

            content = self._cat_node(current_node)
            if content:
                preview = f"{content[:50]}{'...' if len(content) > 50 else ''}"
                lines.append(f"{prefix}{connector}{name}: {preview}")
            else:
                lines.append(f"{prefix}{connector}{name}/")

            children = current_node.children
            for i, child in enumerate(children):
                child_is_last = i == len(children) - 1
                child_path = self._child_path(current_path, child.name)
                child_prefix = (
                    "" if is_root else prefix + ("    " if is_last else "│   ")
                )
                _walk(child, child_path, child_prefix, child_is_last, False)

        _walk(node, path, "", True, True)
        return "\n".join(lines)

    def find(
        self, path: str = ".", name: Optional[str] = None, type: Optional[str] = None
    ) -> list[str]:
        """
        Find nodes by name pattern (like find -name).

        Args:
            path: Starting path
            name: Regex pattern to match node names
            type: 'd' for directories (nodes with children), 'f' for files (leaf nodes)
        """
        path = self._resolve(path)
        start = self._get_node(path)
        results: list[str] = []
        pattern = re.compile(name, re.IGNORECASE) if name else None

        def _walk(node: Node, current_path: str) -> None:
            node_name = "root" if current_path == "/" else node.name
            children = node.children
            is_dir = len(children) > 0

            if type == "d" and not is_dir:
                pass
            elif type == "f" and is_dir:
                pass
            elif pattern is None or pattern.search(node_name):
                results.append(current_path)

            for child in children:
                _walk(child, self._child_path(current_path, child.name))

        _walk(start, path)
        return results

    def walk(self, path: str = ".") -> list[tuple[str, list[str], list[str]]]:
        """
        Walk the tree like os.walk().
        Yields (dirpath, dirnames, filenames) tuples.
        Directories = nodes with children, Files = leaf nodes.
        """
        path = self._resolve(path)
        start = self._get_node(path)
        results: list[tuple[str, list[str], list[str]]] = []

        def _walk(node: Node, current_path: str) -> None:
            children = node.children
            dirs: list[str] = []
            files: list[str] = []
            for child in children:
                if child.children:
                    dirs.append(child.name)
                else:
                    files.append(child.name)
            results.append((current_path, dirs, files))
            for d in dirs:
                child = self._get_child(node, d)
                if child is not None:
                    _walk(child, self._child_path(current_path, d))

        _walk(start, path)
        return results

    def glob(self, pattern: str, path: str = ".") -> list[str]:
        """
        Match paths using glob patterns.
        Supports: * (any chars), ** (any depth), ? (single char)
        Example: /animals/*/dog, /images/**/*.jpg
        """
        path = self._resolve(path)
        regex_pattern = pattern
        regex_pattern = regex_pattern.replace(".", r"\.")
        regex_pattern = regex_pattern.replace("**", "<<<GLOBSTAR>>>")
        regex_pattern = regex_pattern.replace("*", r"[^/]*")
        regex_pattern = regex_pattern.replace("<<<GLOBSTAR>>>", r".*")
        regex_pattern = regex_pattern.replace("?", r"[^/]")
        regex_pattern = f"^{regex_pattern}$"

        regex = re.compile(regex_pattern)
        results: list[str] = []

        start = self._get_node(path)

        def _walk(node: Node, current_path: str) -> None:
            if regex.match(current_path):
                results.append(current_path)
            for child in node.children:
                _walk(child, self._child_path(current_path, child.name))

        _walk(start, path)
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
        start = self._get_node(path)
        total = 0

        def _walk(node: Node) -> None:
            nonlocal total
            if content_size:
                total += len(self._cat_node(node))
            else:
                total += 1
            for child in node.children:
                _walk(child)

        _walk(start)
        return total

    def info(self, path: str = ".") -> dict:
        """Get metadata about a node."""
        path = self._resolve(path)
        node = self._get_node(path)
        children = self.ls(path)
        text_content = self._cat_node(node)
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
            node = self._get_node(path)
            return self._is_dir_node(node)
        except KeyError:
            return False

    def isfile(self, path: str) -> bool:
        """Check if path is a file (self-closing or has text content)."""
        path = self._resolve(path)
        try:
            node = self._get_node(path)
            return self._is_file_node(node)
        except KeyError:
            return False
