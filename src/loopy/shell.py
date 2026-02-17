"""Text command shell with pipelines for Loopy."""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path
from typing import Callable

from .core_v2 import Loopy
from .file_store import FileBackedLoopy


Command = Callable[[list[str], str, Loopy], str]


def _split_command_chains(command: str) -> list[tuple[str, str]]:
    """Split command on ;, &&, and || into separate chains.

    Returns list of (command, separator) tuples.
    The separator is what comes AFTER this command (';', '&&', '||', or '' for last).
    """
    chains: list[tuple[str, str]] = []
    current: list[str] = []
    in_single = False
    in_double = False
    escape = False
    i = 0

    while i < len(command):
        ch = command[i]

        if escape:
            current.append(ch)
            escape = False
            i += 1
            continue
        if ch == "\\":
            escape = True
            current.append(ch)
            i += 1
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
            i += 1
            continue

        # Check for && (must check before single &)
        if not in_single and not in_double and command[i : i + 2] == "&&":
            segment = "".join(current).strip()
            if not segment:
                raise ValueError("empty command before &&")
            chains.append((segment, "&&"))
            current = []
            i += 2
            continue

        # Check for || (must check before single |)
        if not in_single and not in_double and command[i : i + 2] == "||":
            segment = "".join(current).strip()
            if not segment:
                raise ValueError("empty command before ||")
            chains.append((segment, "||"))
            current = []
            i += 2
            continue

        # Check for ;
        if ch == ";" and not in_single and not in_double:
            segment = "".join(current).strip()
            if not segment:
                raise ValueError("empty command before ;")
            chains.append((segment, ";"))
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    segment = "".join(current).strip()
    if segment:
        chains.append((segment, ""))
    elif chains:
        # Trailing separator with no command
        last_sep = chains[-1][1]
        if last_sep:
            raise ValueError(f"trailing {last_sep} with no command")

    return chains


def _split_pipeline(command: str) -> list[str]:
    """Split a single command on | into pipeline stages."""
    segments: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    escape = False

    for ch in command:
        if escape:
            current.append(ch)
            escape = False
            continue
        if ch == "\\":
            escape = True
            current.append(ch)
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
            continue
        if ch == "|" and not in_single and not in_double:
            segment = "".join(current).strip()
            if not segment:
                raise ValueError("empty command in pipeline")
            segments.append(segment)
            current = []
            continue
        current.append(ch)

    segment = "".join(current).strip()
    if not segment:
        if segments:
            raise ValueError("trailing pipe with no command")
        return []
    segments.append(segment)
    return segments


def _parse_pipeline(command: str) -> list[list[str]]:
    segments = _split_pipeline(command)
    if not segments:
        return []

    parsed: list[list[str]] = []
    for segment in segments:
        tokens = shlex.split(segment, posix=True)
        if not tokens:
            raise ValueError("empty command in pipeline")
        parsed.append(tokens)
    return parsed


def _run_pipeline(command: str, tree: Loopy, stdin: str = "") -> str:
    """Run a single pipeline (commands connected by |)."""
    segments = _parse_pipeline(command)
    output = stdin
    for tokens in segments:
        name = tokens[0]
        args = tokens[1:]
        handler = COMMANDS.get(name)
        if handler is None:
            raise KeyError(f"Unknown command: {name}")
        output = handler(args, output, tree)
    return output


def run(command: str, tree: Loopy, stdin: str = "") -> str:
    """Run a command string, supporting pipes and command chaining.

    - `|`  pipes output from one command to the next
    - `;`  runs commands sequentially, continuing even if one fails
    - `&&` runs commands sequentially, stopping on first failure
    - `||` runs next command only if previous failed
    """
    chains = _split_command_chains(command)
    if not chains:
        return ""

    output = ""
    pending_error: Exception | None = None
    last_succeeded = True

    for i, (cmd, separator) in enumerate(chains):
        prev_sep = chains[i - 1][1] if i > 0 else None

        # Decide whether to run this command based on previous separator and result
        should_run = True

        if prev_sep == "&&" and not last_succeeded:
            # Previous was && and failed - skip this
            should_run = False
        elif prev_sep == "||" and last_succeeded:
            # Previous was || and succeeded - skip this
            should_run = False

        if not should_run:
            # Propagate the skip state but keep pending_error
            # Don't change last_succeeded (carry forward)
            continue

        try:
            output = _run_pipeline(cmd, tree, stdin)
            last_succeeded = True
            pending_error = None
        except Exception as e:
            output = ""
            last_succeeded = False

            if separator == "||":
                # Failed, but || means next command will run
                pending_error = None
            elif separator == "&&":
                # Failed, next && command will be skipped
                pending_error = e
            elif separator == ";":
                # Failed but ; continues, no propagation
                pending_error = None
            else:
                # Last command, propagate error
                raise

    # If chain ended with unhandled error (e.g., a && b where a failed)
    if pending_error is not None:
        raise pending_error

    return output


def demo_tree() -> Loopy:
    return (
        Loopy()
        .mkdir("/animals/dogs", parents=True)
        .mkdir("/animals/cats", parents=True)
        .touch("/animals/dogs/lab", "friendly")
        .touch("/animals/dogs/beagle", "curious")
        .touch("/animals/cats/persian", "fluffy")
        .mkdir("/projects/loopy", parents=True)
        .touch("/projects/loopy/README.md", "notes")
    )


def repl(tree: Loopy | None = None, prompt: str = "loopy> ") -> None:
    if tree is None:
        tree = demo_tree()

    while True:
        try:
            line = input(prompt)
        except EOFError:
            break

        line = line.strip()
        if not line:
            continue
        if line in {"exit", "quit"}:
            break

        try:
            out = run(line, tree)
        except Exception as exc:
            print(f"error: {type(exc).__name__}: {exc}")
        else:
            if out:
                print(out)


def repl_file(path: str | Path, prompt: str = "loopy> ") -> None:
    tree = FileBackedLoopy(path)
    repl(tree, prompt=prompt)


def _display_path(path: str) -> str:
    if path in {"/", ".", ".."}:
        return path
    return path.rstrip("/")


def _ls_recursive(tree: Loopy, path: str, classify: bool) -> str:
    if not tree.isdir(path):
        return _display_path(path)

    lines: list[str] = []

    def _walk(current: str) -> None:
        lines.append(f"{_display_path(current)}:")

        children = tree.ls(current, classify=False)
        if classify:
            entries = []
            for child in children:
                child_path = f"{current.rstrip('/')}/{child}"
                if tree.isdir(child_path):
                    entries.append(f"{child}/")
                else:
                    entries.append(child)
        else:
            entries = children

        lines.extend(entries)

        for child in children:
            child_path = f"{current.rstrip('/')}/{child}"
            if tree.isdir(child_path):
                lines.append("")
                _walk(child_path)

    _walk(path)
    return "\n".join(lines)


def _cmd_ls(args: list[str], _stdin: str, tree: Loopy) -> str:
    classify = True  # Default to showing / for directories
    recursive = False
    path = "."
    for arg in args:
        if arg == "-F":
            classify = True
        elif arg == "--no-classify":
            classify = False
        elif arg in {"-R", "--recursive"}:
            recursive = True
        elif arg.startswith("-"):
            raise ValueError(f"unknown ls option: {arg}")
        elif path != ".":
            raise ValueError("ls takes at most one path")
        else:
            path = arg
    if recursive:
        return _ls_recursive(tree, path, classify=classify)
    return "\n".join(tree.ls(path, classify=classify))


def _cmd_cat(args: list[str], stdin: str, tree: Loopy) -> str:
    path: str | None = None
    start: int | None = None
    length: int | None = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--range":
            if i + 2 >= len(args):
                raise ValueError("--range requires start and length")
            try:
                start = int(args[i + 1])
            except ValueError:
                raise ValueError(
                    f"--range start must be an integer, got: {args[i + 1]}"
                )
            try:
                length = int(args[i + 2])
            except ValueError:
                raise ValueError(
                    f"--range length must be an integer, got: {args[i + 2]}"
                )
            if start < 0:
                raise ValueError("--range start must be non-negative")
            if length < 0:
                raise ValueError("--range length must be non-negative")
            i += 3
            continue
        if arg.startswith("-"):
            raise ValueError(f"unknown cat option: {arg}")
        if path is not None:
            raise ValueError("cat takes at most one path")
        path = arg
        i += 1

    if path is None:
        content = stdin
    else:
        content = tree.cat(path)

    if start is not None and length is not None:
        return content[start : start + length]

    return content


def _parse_grep_args(args: list[str]) -> tuple[str, str | None, bool, bool, bool, bool]:
    ignore_case = False
    invert = False
    count = False
    line_mode = False
    pattern: str | None = None
    path: str | None = None
    flags_done = False

    i = 0
    while i < len(args):
        arg = args[i]

        if not flags_done:
            if arg == "--":
                flags_done = True
                i += 1
                continue
            if arg.startswith("-") and arg != "-":
                for flag in arg[1:]:
                    if flag == "i":
                        ignore_case = True
                    elif flag == "v":
                        invert = True
                    elif flag == "c":
                        count = True
                    elif flag == "n":
                        line_mode = True
                    else:
                        raise ValueError(f"unknown grep flag: -{flag}")
                i += 1
                continue

        if pattern is None:
            pattern = arg
        elif path is None:
            path = arg
        else:
            raise ValueError("grep takes at most one path")
        i += 1

    if pattern is None:
        raise ValueError("grep requires a pattern")

    return pattern, path, ignore_case, invert, count, line_mode


def _cmd_grep(args: list[str], stdin: str, tree: Loopy) -> str:
    pattern, path, ignore_case, invert, count, line_mode = _parse_grep_args(args)
    flags = re.IGNORECASE if ignore_case else 0
    regex = re.compile(pattern, flags)

    if stdin and path is None:
        lines = stdin.splitlines()
        if line_mode:
            matched = []
            for lineno, line in enumerate(lines, 1):
                if bool(regex.search(line)) != invert:
                    matched.append(f"{lineno}:{line}")
            return "\n".join(matched)
        matched = [line for line in lines if bool(regex.search(line)) != invert]
        if count:
            return str(len(matched))
        return "\n".join(matched)

    search_path = path or "."

    if line_mode:
        results = tree.grep(
            pattern,
            path=search_path,
            ignore_case=ignore_case,
            invert=invert,
            lines=True,
        )
        return "\n".join(results)

    results = tree.grep(
        pattern,
        path=search_path,
        content=True,
        ignore_case=ignore_case,
        invert=invert,
        count=count,
    )

    if count:
        return str(results)

    if isinstance(results, int):
        return str(results)

    return "\n".join(results)


def _cmd_find(args: list[str], _stdin: str, tree: Loopy) -> str:
    path = "."
    name = None
    type_ = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-name":
            if i + 1 >= len(args):
                raise ValueError("find -name requires a pattern")
            name = args[i + 1]
            i += 2
            continue
        if arg == "-type":
            if i + 1 >= len(args):
                raise ValueError("find -type requires d or f")
            type_ = args[i + 1]
            i += 2
            continue
        if arg.startswith("-"):
            raise ValueError(f"unknown find option: {arg}")
        if path != ".":
            raise ValueError("find takes at most one path")
        path = arg
        i += 1

    return "\n".join(tree.find(path, name=name, type=type_))


def _cmd_tree(args: list[str], _stdin: str, tree: Loopy) -> str:
    if len(args) > 1:
        raise ValueError("tree takes at most one path")
    path = args[0] if args else "."
    return tree.tree(path)


def _cmd_du(args: list[str], _stdin: str, tree: Loopy) -> str:
    content_size = False
    path = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"-c", "--content"}:
            content_size = True
        elif arg.startswith("-"):
            raise ValueError(f"unknown du option: {arg}")
        elif path is None:
            path = arg
        else:
            raise ValueError("du takes at most one path")
        i += 1

    return str(tree.du(path or ".", content_size=content_size))


def _cmd_pwd(args: list[str], _stdin: str, tree: Loopy) -> str:
    if args:
        raise ValueError("pwd takes no arguments")
    return tree.cwd


def _cmd_cd(args: list[str], _stdin: str, tree: Loopy) -> str:
    if len(args) != 1:
        raise ValueError("cd requires a path")
    tree.cd(args[0])
    return ""


def _cmd_echo(args: list[str], _stdin: str, _tree: Loopy) -> str:
    return " ".join(args)


def _format_printf_once(
    format_str: str, args: list[str], start: int
) -> tuple[str, int, bool]:
    output: list[str] = []
    used = 0
    has_conversion = False
    i = 0

    while i < len(format_str):
        ch = format_str[i]

        if ch == "%":
            if i + 1 >= len(format_str):
                output.append("%")
                i += 1
                continue
            spec = format_str[i + 1]
            if spec == "%":
                output.append("%")
                i += 2
                continue
            if spec == "s":
                has_conversion = True
                if start + used < len(args):
                    output.append(args[start + used])
                    used += 1
                else:
                    output.append("")
                i += 2
                continue
            output.append("%" + spec)
            i += 2
            continue

        if ch == "\\":
            if i + 1 >= len(format_str):
                output.append("\\")
                i += 1
                continue
            nxt = format_str[i + 1]
            if nxt == "n":
                output.append("\n")
                i += 2
                continue
            if nxt == "t":
                output.append("\t")
                i += 2
                continue
            if nxt == "r":
                output.append("\r")
                i += 2
                continue
            if nxt == "\\":
                output.append("\\")
                i += 2
                continue
            if nxt == '"':
                output.append('"')
                i += 2
                continue
            if nxt == "'":
                output.append("'")
                i += 2
                continue
            if nxt in "01234567":
                j = i + 1
                digits: list[str] = []
                while (
                    j < len(format_str)
                    and len(digits) < 3
                    and format_str[j] in "01234567"
                ):
                    digits.append(format_str[j])
                    j += 1
                output.append(chr(int("".join(digits), 8)))
                i = j
                continue
            output.append(nxt)
            i += 2
            continue

        output.append(ch)
        i += 1

    return "".join(output), used, has_conversion


def _cmd_printf(args: list[str], _stdin: str, _tree: Loopy) -> str:
    if not args:
        raise ValueError("printf requires a format")
    format_str = args[0]
    format_args = args[1:]
    rendered, used, has_conversion = _format_printf_once(format_str, format_args, 0)

    if not has_conversion:
        return rendered

    output = [rendered]
    index = used
    while index < len(format_args):
        chunk, used, _ = _format_printf_once(format_str, format_args, index)
        output.append(chunk)
        index += used

    return "".join(output)


def _cmd_mv(args: list[str], _stdin: str, tree: Loopy) -> str:
    if len(args) != 2:
        raise ValueError("mv requires source and destination")
    tree.mv(args[0], args[1])
    return ""


def _cmd_cp(args: list[str], _stdin: str, tree: Loopy) -> str:
    if len(args) != 2:
        raise ValueError("cp requires source and destination")
    tree.cp(args[0], args[1])
    return ""


def _cmd_ln(args: list[str], _stdin: str, tree: Loopy) -> str:
    if len(args) != 2:
        raise ValueError("ln requires target and link path")
    tree.ln(args[0], args[1])
    return ""


def _cmd_readlink(args: list[str], _stdin: str, tree: Loopy) -> str:
    if len(args) != 1:
        raise ValueError("readlink requires a path")
    return tree.readlink(args[0])


def _cmd_rm(args: list[str], _stdin: str, tree: Loopy) -> str:
    recursive = False
    path = None
    for arg in args:
        if arg in ("-r", "-rf", "--recursive"):
            recursive = True
        elif arg.startswith("-"):
            raise ValueError(f"unknown rm option: {arg}")
        elif path is None:
            path = arg
        else:
            raise ValueError("rm takes one path")
    if path is None:
        raise ValueError("rm requires a path")
    tree.rm(path, recursive=recursive)
    return ""


def _cmd_mkdir(args: list[str], _stdin: str, tree: Loopy) -> str:
    parents = False
    path = None
    for arg in args:
        if arg == "-p":
            parents = True
        elif arg.startswith("-"):
            raise ValueError(f"unknown mkdir option: {arg}")
        elif path is None:
            path = arg
        else:
            raise ValueError("mkdir takes one path")
    if path is None:
        raise ValueError("mkdir requires a path")
    tree.mkdir(path, parents=parents)
    return ""


def _cmd_touch(args: list[str], stdin: str, tree: Loopy) -> str:
    if len(args) < 1:
        raise ValueError("touch requires a path")
    path = args[0]
    content = " ".join(args[1:]) if len(args) > 1 else stdin
    tree.touch(path, content)
    return ""


def _cmd_write(args: list[str], stdin: str, tree: Loopy) -> str:
    if len(args) < 1:
        raise ValueError("write requires a path")
    path = args[0]
    content = " ".join(args[1:]) if len(args) > 1 else stdin
    tree.write(path, content)
    return ""


def _cmd_sed(args: list[str], _stdin: str, tree: Loopy) -> str:
    # sed path pattern replacement [-i] [-r] [-c count]
    ignore_case = False
    recursive = False
    count = 0
    positional = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-i":
            ignore_case = True
        elif arg == "-r":
            recursive = True
        elif arg == "-c" and i + 1 < len(args):
            count = int(args[i + 1])
            i += 1
        elif arg.startswith("-"):
            raise ValueError(f"unknown sed option: {arg}")
        else:
            positional.append(arg)
        i += 1

    if len(positional) != 3:
        raise ValueError("sed requires: path pattern replacement")

    path, pattern, replacement = positional
    tree.sed(
        path,
        pattern,
        replacement,
        count=count,
        ignore_case=ignore_case,
        recursive=recursive,
    )
    return ""


def _cmd_info(args: list[str], _stdin: str, tree: Loopy) -> str:
    if len(args) > 1:
        raise ValueError("info takes at most one path")
    path = args[0] if args else "."
    info = tree.info(path)
    return "\n".join(f"{key}: {value}" for key, value in info.items())


def _parse_head_tail_args(args: list[str]) -> tuple[int, str | None]:
    """Parse arguments for head/tail commands. Returns (n_lines, path)."""
    n_lines = 10  # default
    path: str | None = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-n":
            if i + 1 >= len(args):
                raise ValueError("-n requires a number")
            try:
                n_lines = int(args[i + 1])
            except ValueError:
                raise ValueError(f"-n requires a number, got: {args[i + 1]}")
            if n_lines < 0:
                raise ValueError("-n requires a non-negative number")
            i += 2
            continue
        if arg.startswith("-n"):
            # Handle -n5 style (no space)
            try:
                n_lines = int(arg[2:])
            except ValueError:
                raise ValueError(f"-n requires a number, got: {arg[2:]}")
            if n_lines < 0:
                raise ValueError("-n requires a non-negative number")
            i += 1
            continue
        if arg.startswith("-"):
            raise ValueError(f"unknown option: {arg}")
        if path is not None:
            raise ValueError("takes at most one path")
        path = arg
        i += 1

    return n_lines, path


def _cmd_head(args: list[str], stdin: str, tree: Loopy) -> str:
    n_lines, path = _parse_head_tail_args(args)

    if path is None:
        # Read from stdin
        content = stdin
    else:
        content = tree.cat(path)

    lines = content.splitlines()
    return "\n".join(lines[:n_lines])


def _cmd_tail(args: list[str], stdin: str, tree: Loopy) -> str:
    n_lines, path = _parse_head_tail_args(args)

    if path is None:
        # Read from stdin
        content = stdin
    else:
        content = tree.cat(path)

    lines = content.splitlines()
    if n_lines == 0:
        return ""
    return "\n".join(lines[-n_lines:])


def _cmd_wc(args: list[str], stdin: str, tree: Loopy) -> str:
    """Word count: lines, words, chars."""
    count_lines = False
    count_words = False
    count_chars = False
    path: str | None = None

    for arg in args:
        if arg == "-l":
            count_lines = True
        elif arg == "-w":
            count_words = True
        elif arg == "-c" or arg == "-m":
            count_chars = True
        elif arg.startswith("-"):
            # Handle combined flags like -lw
            for flag in arg[1:]:
                if flag == "l":
                    count_lines = True
                elif flag == "w":
                    count_words = True
                elif flag in ("c", "m"):
                    count_chars = True
                else:
                    raise ValueError(f"unknown wc option: -{flag}")
        elif path is None:
            path = arg
        else:
            raise ValueError("wc takes at most one path")

    # Default: show all three
    if not count_lines and not count_words and not count_chars:
        count_lines = count_words = count_chars = True

    if path is not None:
        content = tree.cat(path)
    else:
        content = stdin

    results = []
    if count_lines:
        lines = content.count("\n")
        # Add 1 if content doesn't end with newline but has content
        if content and not content.endswith("\n"):
            lines += 1
        results.append(str(lines))
    if count_words:
        results.append(str(len(content.split())))
    if count_chars:
        results.append(str(len(content)))

    return " ".join(results)


def _cmd_sort(args: list[str], stdin: str, tree: Loopy) -> str:
    """Sort lines."""
    reverse = False
    unique = False
    numeric = False
    path: str | None = None

    for arg in args:
        if arg.startswith("-") and len(arg) > 1 and not arg[1].isdigit():
            # Handle combined flags like -rn
            for flag in arg[1:]:
                if flag == "r":
                    reverse = True
                elif flag == "u":
                    unique = True
                elif flag == "n":
                    numeric = True
                else:
                    raise ValueError(f"unknown sort option: -{flag}")
        elif path is None:
            path = arg
        else:
            raise ValueError("sort takes at most one path")

    if path is not None:
        content = tree.cat(path)
    else:
        content = stdin

    lines = content.splitlines()

    if numeric:

        def sort_key(line: str):
            # Extract leading number, default to 0
            import re

            match = re.match(r"-?\d+", line.strip())
            return int(match.group()) if match else 0

        lines.sort(key=sort_key, reverse=reverse)
    else:
        lines.sort(reverse=reverse)

    if unique:
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        lines = unique_lines

    return "\n".join(lines)


def _cmd_split(args: list[str], stdin: str, tree: Loopy) -> str:
    delimiter: str | None = None
    path: str | None = None
    positional: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"-d", "--delimiter"}:
            if i + 1 >= len(args):
                raise ValueError("split -d requires a delimiter string")
            if delimiter is not None:
                raise ValueError("split delimiter specified twice")
            delimiter = args[i + 1]
            i += 2
            continue
        if arg.startswith("-"):
            raise ValueError(f"unknown split option: {arg}")
        positional.append(arg)
        i += 1

    if delimiter is None:
        if not positional:
            raise ValueError("split requires a delimiter")
        if len(positional) == 1:
            token = positional[0]
            if not stdin and tree.exists(token):
                raise ValueError("split requires a delimiter")
            delimiter = token
        else:
            delimiter = positional[0]
            path = positional[1]
            if len(positional) > 2:
                raise ValueError("split takes at most one path")
    else:
        if len(positional) > 1:
            raise ValueError("split takes at most one path")
        if len(positional) == 1:
            path = positional[0]

    if delimiter == "":
        raise ValueError("split delimiter cannot be empty")

    if path is not None:
        content = tree.cat(path)
    else:
        content = stdin

    return "\n".join(content.split(delimiter))


def _cmd_help(_args: list[str], _stdin: str, _tree: Loopy) -> str:
    return """Available commands:
  ls [path] [-R]      List directory contents
  cd <path>           Change directory
  pwd                 Print working directory
  info [path]         Show node metadata
  cat [path] [--range start length]  Show file contents
  head [path] [-n N]  Show first N lines (default 10)
  tail [path] [-n N]  Show last N lines (default 10)
  wc [-lwc] [path]    Count lines/words/chars
  sort [-rnu] [path]  Sort lines (-r reverse, -n numeric, -u unique)
  split -d <delim> [path]  Split by delimiter
  tree [path]         Show tree structure
  find [path] [-name regex] [-type d|f|l]
  grep <pattern> [path] [-i] [-v] [-c]
  du [path] [-c]      Count nodes or content size

  touch <path> [content]   Create file
  write <path> [content]   Write to file
  mkdir [-p] <path>        Create directory
  rm [-r] <path>           Remove file/directory
  mv <src> <dst>           Move/rename
  cp <src> <dst>           Copy
  ln <target> <link>       Create symlink
  readlink <path>          Show symlink target
  sed <path> <pattern> <replacement> [-i] [-r] [-c n]

  echo <text>         Print text
  printf <fmt> [args]  Print formatted text
  help                Show this help

Command chaining:
  cmd1 | cmd2         Pipe output of cmd1 to cmd2
  cmd1 ; cmd2         Run cmd1 then cmd2 (continue on failure)
  cmd1 && cmd2        Run cmd1 then cmd2 (stop on failure)
  cmd1 || cmd2        Run cmd2 only if cmd1 fails"""


COMMANDS: dict[str, Command] = {
    "ls": _cmd_ls,
    "cat": _cmd_cat,
    "grep": _cmd_grep,
    "find": _cmd_find,
    "tree": _cmd_tree,
    "du": _cmd_du,
    "pwd": _cmd_pwd,
    "cd": _cmd_cd,
    "echo": _cmd_echo,
    "printf": _cmd_printf,
    "split": _cmd_split,
    "mv": _cmd_mv,
    "cp": _cmd_cp,
    "ln": _cmd_ln,
    "readlink": _cmd_readlink,
    "rm": _cmd_rm,
    "mkdir": _cmd_mkdir,
    "touch": _cmd_touch,
    "write": _cmd_write,
    "sed": _cmd_sed,
    "help": _cmd_help,
    "info": _cmd_info,
    "head": _cmd_head,
    "tail": _cmd_tail,
    "wc": _cmd_wc,
    "sort": _cmd_sort,
}


def _main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        repl()
        return
    if len(args) == 1:
        repl_file(args[0])
        return
    raise SystemExit("usage: python -m loopy.shell [path]")


if __name__ == "__main__":
    _main()
