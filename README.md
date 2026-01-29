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
# <root><animals><dogs><labrador>friendly, golden</labrador></dogs><cats><persian>fluffy</persian></cats></animals></root>
```

## Why?

- **Agents** need structured memory they can search, edit, and grow organically
- **One string** = easy to serialize, store, pass around
- **Filesystem semantics** = intuitive path-based operations

## Install

```bash
# It's a single file, just copy it
curl -O https://raw.githubusercontent.com/yourname/loopy/main/loopy.py
```

## API

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
| `grep(pattern)` | `tree.grep("dog")` → `["/animals/dogs"]` |
| `sed(path, pat, repl)` | `tree.sed("/file", "old", "new")` |
| `glob(pattern)` | `tree.glob("/**/*.py")` |
| `find(path, name, type)` | `tree.find("/", type="f")` |
| `tree()` | Pretty print |
| `.raw` | Get the underlying string |

All mutating operations return `self` for chaining.

## Advanced

```python
# grep options
tree.grep("error", content=True, ignore_case=True, invert=True, count=True)

# sed options
tree.sed("/logs", "foo", "bar", recursive=True, count=1)

# find by type
tree.find("/", type="d")  # directories only
tree.find("/", type="f")  # files (leaves) only

# stats
tree.du("/")                    # node count
tree.du("/", content_size=True) # total bytes
tree.info("/path")              # metadata dict
```

## Serialization

```python
# Save
db.store("knowledge", tree.raw)

# Load
tree = Loopy(db.get("knowledge"))
```

## License

MIT
