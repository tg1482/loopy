"""Text command shell with pipelines for Loopy."""

from __future__ import annotations

import re
import shlex
from typing import Callable

from .core_v2 import Loopy


Command = Callable[[list[str], str, Loopy], str]


def _parse_pipeline(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars="|")
    lexer.whitespace_split = True
    lexer.commenters = ""

    tokens = list(lexer)
    if not tokens:
        return []

    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token == "|":
            if not current:
                raise ValueError("empty command in pipeline")
            segments.append(current)
            current = []
        else:
            current.append(token)

    if not current:
        raise ValueError("trailing pipe with no command")

    segments.append(current)
    return segments


def run(command: str, tree: Loopy, stdin: str = "") -> str:
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


def _cmd_ls(args: list[str], _stdin: str, tree: Loopy) -> str:
    classify = True  # Default to showing / for directories
    path = "."
    for arg in args:
        if arg == "-F":
            classify = True
        elif arg == "--no-classify":
            classify = False
        elif arg.startswith("-"):
            raise ValueError(f"unknown ls option: {arg}")
        elif path != ".":
            raise ValueError("ls takes at most one path")
        else:
            path = arg
    return "\n".join(tree.ls(path, classify=classify))


def _cmd_cat(args: list[str], stdin: str, tree: Loopy) -> str:
    if len(args) > 1:
        raise ValueError("cat takes at most one path")
    if not args:
        return stdin
    return tree.cat(args[0])


def _parse_grep_args(args: list[str]) -> tuple[str, str | None, bool, bool, bool]:
    ignore_case = False
    invert = False
    count = False
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

    return pattern, path, ignore_case, invert, count


def _cmd_grep(args: list[str], stdin: str, tree: Loopy) -> str:
    pattern, path, ignore_case, invert, count = _parse_grep_args(args)
    flags = re.IGNORECASE if ignore_case else 0
    regex = re.compile(pattern, flags)

    if stdin and path is None:
        lines = stdin.splitlines()
        matched = [line for line in lines if bool(regex.search(line)) != invert]
        if count:
            return str(len(matched))
        return "\n".join(matched)

    search_path = path or "."
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
    content = " ".join(args[1:]) if len(args) > 1 else stdin.strip()
    tree.touch(path, content)
    return ""


def _cmd_write(args: list[str], stdin: str, tree: Loopy) -> str:
    if len(args) < 1:
        raise ValueError("write requires a path")
    path = args[0]
    content = " ".join(args[1:]) if len(args) > 1 else stdin.strip()
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


def _cmd_help(_args: list[str], _stdin: str, _tree: Loopy) -> str:
    return """Available commands:
  ls [path]           List directory contents
  cd <path>           Change directory
  pwd                 Print working directory
  info [path]         Show node metadata
  cat <path>          Show file contents
  tree [path]         Show tree structure
  find [path] [-name regex] [-type d|f]
  grep <pattern> [path] [-i] [-v] [-c]
  du [path] [-c]      Count nodes or content size

  touch <path> [content]   Create file
  write <path> [content]   Write to file
  mkdir [-p] <path>        Create directory
  rm [-r] <path>           Remove file/directory
  mv <src> <dst>           Move/rename
  cp <src> <dst>           Copy
  sed <path> <pattern> <replacement> [-i] [-r] [-c n]

  echo <text>         Print text
  help                Show this help"""


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
    "mv": _cmd_mv,
    "cp": _cmd_cp,
    "rm": _cmd_rm,
    "mkdir": _cmd_mkdir,
    "touch": _cmd_touch,
    "write": _cmd_write,
    "sed": _cmd_sed,
    "help": _cmd_help,
    "info": _cmd_info,
}


if __name__ == "__main__":
    repl()
