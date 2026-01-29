# Loopy

A filesystem API over a single Python string.

```python
from loopy import Loopy

tree = (
    Loopy()
    .mkdir("/animals/dogs", parents=True)
    .touch("/animals/dogs/labrador", "friendly, golden")
    .touch("/animals/cats/persian", "fluffy")
)

print(tree.tree())
# root/
# └── animals/
#     ├── dogs/
#     │   └── labrador: friendly, golden
#     └── cats/
#         └── persian: fluffy

print(tree.raw)
# <root><animals><dogs><labrador>friendly, golden</labrador></dogs>...</root>
```

## Why?

- **Agents** need structured memory they can search, edit, and grow organically
- **One string** = easy to serialize, store, pass around
- **Filesystem semantics** = intuitive path-based operations

## Install

```bash
# Single file, no dependencies - just copy it
cp loopy.py /your/project/
```

## API

### Core Operations

| Operation | Example |
|-----------|---------|
| `mkdir(path, parents=True)` | `tree.mkdir("/a/b/c", parents=True)` |
| `touch(path, content)` | `tree.touch("/file", "hello")` |
| `cat(path)` | `tree.cat("/file")` → `"hello"` |
| `ls(path)` | `tree.ls("/a")` → `["b"]` |
| `rm(path)` | `tree.rm("/a/b")` |
| `mv(src, dst)` | `tree.mv("/old", "/new")` |
| `cp(src, dst)` | `tree.cp("/a", "/b")` |
| `exists(path)` | `tree.exists("/a")` → `True` |

### Search & Transform

| Operation | Example |
|-----------|---------|
| `grep(pattern)` | `tree.grep("dog")` → `["/animals/dogs"]` |
| `sed(path, pat, repl)` | `tree.sed("/file", "old", "new")` |
| `glob(pattern)` | `tree.glob("/**/*.py")` |
| `find(path, name, type)` | `tree.find("/", type="f")` |

### Navigation

| Operation | Example |
|-----------|---------|
| `cd(path)` | `tree.cd("/project")` |
| `.cwd` | `tree.cwd` → `"/project"` |

### Inspection

| Operation | Example |
|-----------|---------|
| `tree()` | Pretty print from cwd |
| `du(path)` | Node count |
| `info(path)` | Metadata dict |
| `head(path, n)` | First n chars |
| `tail(path, n)` | Last n chars |
| `isdir(path)` | Has children? |
| `isfile(path)` | Leaf node? |
| `walk(path)` | os.walk() style |
| `.raw` | The underlying string |

All mutating operations return `self` for chaining.

## Relative Paths & cd

```python
tree = (
    Loopy()
    .mkdir("/projects/webapp/src", parents=True)
    .cd("/projects/webapp")      # change directory
    .touch("README.md", "# App") # relative path
    .touch("src/main.py", "...")
    .cd("src")                   # relative cd
    .touch("util.py", "...")
)

tree.cwd        # "/projects/webapp/src"
tree.ls()       # ["main.py", "util.py"] - lists cwd
tree.ls(".")    # same as above
tree.ls("/")    # absolute - always root
```

## Advanced Options

```python
# grep
tree.grep("error", content=True, ignore_case=True, invert=True, count=True)

# sed
tree.sed("/logs", "foo", "bar", recursive=True, count=1, ignore_case=True)

# find
tree.find("/", type="d")  # directories only
tree.find("/", type="f")  # files (leaves) only
tree.find("/", name=r"test_.*")  # regex match

# glob patterns
tree.glob("/**/*.py")     # recursive
tree.glob("/src/*.js")    # single level
tree.glob("/config/??.json")  # ? = single char
```

## Serialization

```python
# Save
db.store("knowledge", tree.raw)

# Load
tree = Loopy(db.get("knowledge"))

# Or initialize with existing XML-like data
tree = Loopy("<root><users><alice>admin</alice></users></root>")
tree.cat("/users/alice")  # "admin"
```

## Text Shell (Pipes)

Loopy includes a small text command runner that supports pipes. The shell is a
thin boundary: commands return text, and pipelines pass stdout to stdin.

```python
from loopy import Loopy
from loopy.shell import run

tree = (
    Loopy()
    .mkdir("/animals/dogs", parents=True)
    .touch("/animals/dogs/lab", "friendly")
)

print(run("ls /animals | grep dog", tree))
print(run("cat /animals/dogs/lab | grep friend", tree))
```

## Special Characters

Content is automatically XML-escaped:

```python
tree.touch("/code", "if (a < b && c > d) { ... }")
tree.cat("/code")  # "if (a < b && c > d) { ... }" - preserved correctly
```

## License

MIT
