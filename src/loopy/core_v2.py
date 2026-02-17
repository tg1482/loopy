"""Core Loopy implementation (node-based)."""

from dataclasses import dataclass, field
import re
from typing import Callable, Optional

# Regex pattern for valid tag names (alphanumeric, underscore, hyphen, dot)
TAG_NAME = r"[\w.\-]+"
_TAG_NAME_RE = re.compile(f"^{TAG_NAME}$")


def _validate_segment(seg: str) -> None:
    """Raise ValueError if segment contains invalid characters."""
    if not _TAG_NAME_RE.match(seg):
        raise ValueError(
            f"Invalid path segment: {seg!r} (only alphanumeric, underscore, hyphen, dot allowed)"
        )


def slugify(value: str) -> str:
    """Convert a string to a valid Loopy path segment.

    Lowercases, replaces non-alphanumeric runs with hyphens,
    strips leading/trailing hyphens. Returns "item" for empty results.

    Example:
        slugify("Hello World!")  # -> "hello-world"
        slugify("  My File (2).txt")  # -> "my-file-2-.txt"
    """
    text = value.strip().lower()
    out: list[str] = []
    prev_sep = False
    for ch in text:
        if ch.isalnum() or ch in ("_", "."):
            out.append(ch)
            prev_sep = False
        else:
            if not prev_sep and out:
                out.append("-")
                prev_sep = True
    result = "".join(out).strip("-")
    return result or "item"


def _escape(text: str) -> str:
    """Escape special characters for storage."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _unescape(text: str) -> str:
    """Unescape special characters when reading."""
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


@dataclass
class Node:
    """A node in the Loopy tree.

    Attributes:
        name: The node's name (tag name in serialization)
        text: Text content of the node
        children: Child nodes
        parent: Parent node reference
        self_closing: If True, serializes as <name/> when empty
        link_target: If set, this node is a symlink pointing to the given path.
                    Symlinks are always self-closing and have no text/children.
    """

    name: str
    text: str = ""
    children: list["Node"] = field(default_factory=list)
    parent: Optional["Node"] = None
    self_closing: bool = False
    link_target: Optional[str] = None


def _parse_symlink_attr(token: str) -> tuple[str, Optional[str]]:
    """Parse a token that may contain a symlink attribute.

    Args:
        token: The tag token (without < >), e.g., 'name @="/path"/' or 'name'

    Returns:
        (name, link_target) where link_target is None if not a symlink
    """
    # Check for symlink syntax: name @="/path"/
    if ' @="' not in token:
        return token, None

    # Extract name and link target
    space_idx = token.index(' @="')
    name = token[:space_idx]

    # Find the closing quote
    quote_start = space_idx + 4  # len(' @="')
    quote_end = token.find('"', quote_start)
    if quote_end == -1:
        raise ValueError(f"Malformed symlink: missing closing quote in {token!r}")

    link_target = token[quote_start:quote_end]

    # Unescape the link target (it may contain escaped characters)
    link_target = _unescape(link_target)

    # The rest should be just "/" for self-closing
    remainder = token[quote_end + 1 :]
    if remainder != "/":
        raise ValueError(f"Symlinks must be self-closing: {token!r}")

    return name, link_target


def parse(data: str) -> Node:
    """Parse raw loopy data into a Node tree.

    Supports symlink syntax: <name @="/target/path"/>
    """
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
            # Check for symlink syntax first
            name, link_target = _parse_symlink_attr(token)

            if link_target is not None:
                # It's a symlink - always self-closing
                if not _TAG_NAME_RE.match(name):
                    raise ValueError(f"Invalid tag name: {name!r}")
                parent = stack[-1] if stack else None
                node = Node(
                    name=name, parent=parent, self_closing=True, link_target=link_target
                )
                if parent:
                    parent.children.append(node)
                if not stack:
                    root = node
            else:
                # Regular node
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
    """Serialize a Node tree to raw loopy data (iterative).

    Symlinks are serialized as: <name @="/target/path"/>
    """
    parts: list[str] = []
    # Stack holds either nodes to open or closing tag strings
    stack: list[Node | str] = [node]

    while stack:
        item = stack.pop()

        if isinstance(item, str):
            # Closing tag
            parts.append(item)
            continue

        if item.link_target is not None:
            escaped_target = _escape(item.link_target)
            parts.append(f'<{item.name} @="{escaped_target}"/>')
            continue

        if item.self_closing and not item.children and not item.text:
            parts.append(f"<{item.name}/>")
            continue

        parts.append(f"<{item.name}>{_escape(item.text)}")
        # Push closing tag first (processed last), then children in reverse
        stack.append(f"</{item.name}>")
        for child in reversed(item.children):
            stack.append(child)

    return "".join(parts)


class Loopy:
    """A lightweight tree structure stored as a string with filesystem operations."""

    def __init__(
        self, data: str = "<root/>", on_mutate: Callable[[], None] | None = None
    ):
        raw = data if data else "<root/>"
        self._raw_cache = raw
        self._root = parse(raw)
        self._cwd = "/"
        self._dirty = False
        self._on_mutate = on_mutate

    @property
    def cwd(self) -> str:
        """Current working directory."""
        return self._cwd

    def _mark_dirty(self) -> None:
        self._dirty = True
        if self._on_mutate is not None:
            self._on_mutate()

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

    def _resolve_through_links(self, path: str, seen: Optional[set] = None) -> Node:
        """Resolve a path, following any symlinks to the final target.

        Args:
            path: The path to resolve
            seen: Set of already-visited paths (for cycle detection)

        Returns:
            The final target Node after following all symlinks

        Raises:
            KeyError: If path or any link target doesn't exist
            ValueError: If a symlink cycle is detected
        """
        if seen is None:
            seen = set()

        path = self._resolve(path)
        if path in seen:
            raise ValueError(f"Symlink cycle detected: {path}")
        seen.add(path)

        node = self._get_node(path)
        if node.link_target is not None:
            # It's a symlink - follow it
            return self._resolve_through_links(node.link_target, seen)
        return node

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

    def ls(
        self, path: str = ".", classify: bool = False, follow_links: bool = True
    ) -> list[str]:
        """List children of a node.

        Args:
            path: Path to list
            classify: If True, append / to directories, @ to symlinks (like ls -F)
            follow_links: If True (default), follow symlinks to directories

        Returns:
            List of child names, optionally with type suffixes
        """
        path = self._resolve(path)
        node = self._get_node(path)

        # If this is a symlink to a directory, list the target's children
        if follow_links and node.link_target is not None:
            node = self._resolve_through_links(path)

        if not node.children:
            return []
        if not classify:
            return [child.name for child in node.children]

        result = []
        for child in node.children:
            if child.link_target is not None:
                # Symlink - append @
                result.append(f"{child.name}@")
            elif self._is_dir_node(child):
                result.append(f"{child.name}/")
            else:
                result.append(child.name)
        return result

    def cat(self, path: str, follow_links: bool = True) -> str:
        """Get the text content of a node (excludes child tags).

        Args:
            path: Path to the node
            follow_links: If True (default), follow symlinks to get target's content

        Returns:
            The text content of the node (or link target if following links)
        """
        path = self._resolve(path)
        if follow_links:
            node = self._resolve_through_links(path)
        else:
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

    def ln(self, source: str, dest: str) -> "Loopy":
        """Create a symbolic link at dest pointing to source.

        Args:
            source: The target path the link will point to (doesn't need to exist)
            dest: The path where the symlink will be created

        Behavior:
            - If dest is an existing directory, create link inside it with source's basename
            - Source doesn't need to exist (dangling links allowed, like Unix)
            - If dest already exists as a file/link, raises FileExistsError

        Returns:
            self for chaining
        """
        source = self._resolve(source)
        dest = self._resolve(dest)

        # If dest is a directory, create link inside it
        if self.exists(dest) and self.isdir(dest):
            source_name = self._normalize_path(source)[-1]
            dest = f"{dest.rstrip('/')}/{source_name}"

        # Check if dest already exists
        if self.exists(dest):
            raise FileExistsError(f"Path already exists: {dest}")

        # Get dest segments and ensure parent exists
        segments = self._normalize_path(dest)
        if not segments:
            raise ValueError("Cannot create symlink at root")

        if len(segments) > 1:
            parent_path = "/" + "/".join(segments[:-1])
            if not self.exists(parent_path):
                self.mkdir(parent_path, parents=True)
            else:
                parent_node = self._get_node(parent_path)
                if self._is_file_node(parent_node) and not self.islink(parent_path):
                    raise NotADirectoryError(
                        f"Cannot create symlink under file: {parent_path}"
                    )

        parent_path = "/" + "/".join(segments[:-1]) if len(segments) > 1 else "/"
        parent_node = self._get_node(parent_path)
        name = segments[-1]

        # Create the symlink node
        new_node = Node(
            name=name,
            parent=parent_node,
            self_closing=True,
            link_target=source,
        )
        parent_node.children.append(new_node)
        parent_node.self_closing = False
        self._mark_dirty()
        return self

    def write(self, path: str, content: str, follow_links: bool = True) -> "Loopy":
        """Write/overwrite content to a node.

        Args:
            path: Path to write to
            content: Content to write
            follow_links: If True (default), follow symlinks and write to target

        Raises:
            IsADirectoryError: If path is a directory
            KeyError: If path doesn't exist (will create via touch)
        """
        path = self._resolve(path)
        try:
            if follow_links:
                node = self._resolve_through_links(path)
            else:
                node = self._get_node(path)
        except KeyError:
            return self.touch(path, content)

        if node.children:
            raise IsADirectoryError(f"Cannot write content to directory: {path}")

        # Don't write to a symlink node itself
        if node.link_target is not None:
            raise ValueError(f"Cannot write to symlink without following: {path}")

        node.text = content
        node.self_closing = False
        self._mark_dirty()
        return self

    def rm(self, path: str, recursive: bool = False) -> "Loopy":
        """Remove a node. Use recursive=True for non-empty directories.

        Note: Removing a symlink removes the link itself, not the target.
        """
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
        """Clone a node and all its children.

        Symlinks are cloned as symlinks (pointing to the same target).
        """
        clone = Node(
            name=node.name,
            parent=parent,
            text=node.text,
            self_closing=node.self_closing,
            link_target=node.link_target,  # Preserve symlink target
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
        """Move a node to a new location. If dst is a directory, moves into it.

        Note: Moving a symlink moves the link itself, not the target.
        """
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
        """Copy a node to a new location. If dst is a directory, copies into it.

        Note: Copying a symlink creates a new symlink pointing to the same target.
        """
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
        lines: bool = False,
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
            lines: If True, search file content line-by-line and return
                   "path:lineno:line" strings (implies content=True).
                   Incompatible with count.

        Returns:
            List of matching paths (or "path:lineno:line" if lines=True),
            or count if count=True
        """
        path = self._resolve(path)
        flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(pattern, flags)
        results: list[str] = []

        start_node = self._get_node(path)

        if lines:
            stack = [(start_node, path)]
            while stack:
                node, current_path = stack.pop()
                node_content = self._cat_node(node)
                if node_content:
                    for lineno, line in enumerate(node_content.splitlines(), 1):
                        matched = bool(regex.search(line))
                        if invert:
                            matched = not matched
                        if matched:
                            results.append(f"{current_path}:{lineno}:{line}")
                for child in reversed(node.children):
                    stack.append((child, self._child_path(current_path, child.name)))
            return results

        stack = [(start_node, path)]
        while stack:
            node, current_path = stack.pop()
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

            for child in reversed(node.children):
                stack.append((child, self._child_path(current_path, child.name)))

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
            stack = [path]
            while stack:
                current = stack.pop()
                for child in self.ls(current):
                    child_path = f"{current.rstrip('/')}/{child}"
                    _apply(child_path)
                    stack.append(child_path)

        return self

    def tree(self, path: str = ".") -> str:
        """Return a tree visualization.

        Symlinks are shown with ` -> /target/path` suffix (like ls -l).
        """
        path = self._resolve(path)
        node = self._get_node(path)
        lines: list[str] = []

        # Iterative tree walk using stack
        # Each entry: (node, path, prefix, is_last, is_root)
        stack: list[tuple[Node, str, str, bool, bool]] = [
            (node, path, "", True, True)
        ]
        while stack:
            current_node, current_path, prefix, is_last, is_root = stack.pop()
            name = "root" if current_path == "/" else current_node.name

            if is_root:
                connector = ""
            else:
                connector = "└── " if is_last else "├── "

            if current_node.link_target is not None:
                lines.append(f"{prefix}{connector}{name} -> {current_node.link_target}")
            else:
                content = self._cat_node(current_node)
                if content:
                    preview = f"{content[:50]}{'...' if len(content) > 50 else ''}"
                    lines.append(f"{prefix}{connector}{name}: {preview}")
                else:
                    lines.append(f"{prefix}{connector}{name}/")

            children = current_node.children
            # Push children in reverse so first child is processed first
            for i in range(len(children) - 1, -1, -1):
                child = children[i]
                child_is_last = i == len(children) - 1
                child_path = self._child_path(current_path, child.name)
                child_prefix = (
                    "" if is_root else prefix + ("    " if is_last else "│   ")
                )
                stack.append((child, child_path, child_prefix, child_is_last, False))
        return "\n".join(lines)

    def find(
        self, path: str = ".", name: Optional[str] = None, type: Optional[str] = None
    ) -> list[str]:
        """
        Find nodes by name pattern (like find -name).

        Args:
            path: Starting path
            name: Regex pattern to match node names
            type: 'd' for directories, 'f' for files, 'l' for symlinks

        Note: type checks the node's own type, not the target type for symlinks.
        """
        path = self._resolve(path)
        start = self._get_node(path)
        results: list[str] = []
        pattern = re.compile(name, re.IGNORECASE) if name else None

        stack = [(start, path)]
        while stack:
            node, current_path = stack.pop()
            node_name = "root" if current_path == "/" else node.name
            children = node.children
            is_link = node.link_target is not None
            is_dir = len(children) > 0 and not is_link

            # Type filtering
            type_matches = True
            if type == "l":
                type_matches = is_link
            elif type == "d":
                type_matches = is_dir
            elif type == "f":
                type_matches = not is_dir and not is_link

            if type_matches and (pattern is None or pattern.search(node_name)):
                results.append(current_path)

            for child in reversed(children):
                stack.append((child, self._child_path(current_path, child.name)))
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

        stack = [(start, path)]
        while stack:
            node, current_path = stack.pop()
            children = node.children
            dirs: list[str] = []
            files: list[str] = []
            for child in children:
                if child.children:
                    dirs.append(child.name)
                else:
                    files.append(child.name)
            results.append((current_path, dirs, files))
            for d in reversed(dirs):
                child = self._get_child(node, d)
                if child is not None:
                    stack.append((child, self._child_path(current_path, d)))
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

        stack = [(start, path)]
        while stack:
            node, current_path = stack.pop()
            if regex.match(current_path):
                results.append(current_path)
            for child in reversed(node.children):
                stack.append((child, self._child_path(current_path, child.name)))
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

        stack = [start]
        while stack:
            node = stack.pop()
            if content_size:
                total += len(self._cat_node(node))
            else:
                total += 1
            for child in node.children:
                stack.append(child)
        return total

    def info(self, path: str = ".", follow_links: bool = True) -> dict:
        """Get metadata about a node.

        Args:
            path: Path to the node
            follow_links: If True (default), info reflects the target for symlinks

        Returns:
            Dict with name, path, type, is_link, link_target, children_count,
            content_length, has_content
        """
        path = self._resolve(path)
        node = self._get_node(path)
        segments = self._normalize_path(path)
        name = segments[-1] if segments else "root"

        is_link = node.link_target is not None
        link_target = node.link_target

        # For type and content info, optionally follow the link
        if follow_links and is_link:
            try:
                target_node = self._resolve_through_links(path)
                children = target_node.children
                text_content = self._cat_node(target_node)
            except (KeyError, ValueError):
                # Dangling or circular link
                children = []
                text_content = ""
        else:
            children = node.children
            text_content = self._cat_node(node)

        if is_link:
            node_type = "link"
        elif children:
            node_type = "directory"
        else:
            node_type = "file"

        return {
            "name": name,
            "path": path,
            "type": node_type,
            "is_link": is_link,
            "link_target": link_target,
            "children_count": len(children),
            "content_length": len(text_content),
            "has_content": bool(text_content),
        }

    def isdir(self, path: str, follow_links: bool = True) -> bool:
        """Check if path is a directory.

        Args:
            path: Path to check
            follow_links: If True (default), follow symlinks to check target type

        Returns:
            True if path is a directory (or symlink to directory if following).
            Returns False for symlinks when follow_links=False.
        """
        path = self._resolve(path)
        try:
            if follow_links:
                node = self._resolve_through_links(path)
            else:
                node = self._get_node(path)
                # If not following links, symlinks are not dirs
                if node.link_target is not None:
                    return False
            return self._is_dir_node(node)
        except (KeyError, ValueError):
            return False

    def isfile(self, path: str, follow_links: bool = True) -> bool:
        """Check if path is a file.

        Args:
            path: Path to check
            follow_links: If True (default), follow symlinks to check target type

        Returns:
            True if path is a file (or symlink to file if following).
            Returns False for symlinks when follow_links=False.
        """
        path = self._resolve(path)
        try:
            if follow_links:
                node = self._resolve_through_links(path)
            else:
                node = self._get_node(path)
                # If not following links, symlinks are not files
                if node.link_target is not None:
                    return False
            return self._is_file_node(node)
        except (KeyError, ValueError):
            return False

    def islink(self, path: str) -> bool:
        """Check if path is a symbolic link."""
        path = self._resolve(path)
        try:
            node = self._get_node(path)
            return node.link_target is not None
        except KeyError:
            return False

    def readlink(self, path: str) -> str:
        """Return the target of a symbolic link.

        Args:
            path: Path to the symlink

        Returns:
            The target path the symlink points to

        Raises:
            KeyError: If path doesn't exist
            ValueError: If path is not a symlink
        """
        path = self._resolve(path)
        node = self._get_node(path)
        if node.link_target is None:
            raise ValueError(f"Not a symlink: {path}")
        return node.link_target

    def backlinks(self, path: str) -> list[str]:
        """Find all symlinks that point to the given path.

        Args:
            path: The target path to search for

        Returns:
            List of paths that are symlinks pointing to the given path
        """
        path = self._resolve(path)
        results: list[str] = []

        stack = [(self._root, "/")]
        while stack:
            node, current_path = stack.pop()
            if node.link_target == path:
                results.append(current_path)
            for child in reversed(node.children):
                stack.append((child, self._child_path(current_path, child.name)))
        return results
