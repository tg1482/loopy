# Loopy

A filesystem API over a single Python string. Built for LLMs to organically grow and navigate knowledge structures.

```python
from loopy import Loopy

tree = (
    Loopy()
    .mkdir("/concepts/ml/supervised", parents=True)
    .touch("/concepts/ml/supervised/regression", "predicts continuous values")
    .touch("/concepts/ml/supervised/classification", "predicts categories")
    .mkdir("/concepts/ml/unsupervised")
    .touch("/concepts/ml/unsupervised/clustering", "groups similar items")
)

tree.grep("predicts", content=True)  # find concepts by description
tree.find("/concepts", type="f")  # all leaf concepts
tree.ls("/concepts/ml")  # ['supervised', 'unsupervised']
```

## Why?

**LLMs need structured memory.** When an agent processes information, it needs somewhere to put it—somewhere it can search, reorganize, and grow organically.

Traditional options don't fit:
- **JSON/dicts**: No natural hierarchy, awkward to traverse and modify
- **Databases**: Heavy, require schema, overkill for ephemeral structures
- **Files**: I/O overhead, permissions, cleanup headaches

Loopy gives you:
- **One string** = trivial to serialize, store in context, pass between calls
- **Filesystem semantics** = intuitive paths LLMs already understand
- **Zero dependencies** = pure Python, copy and go

## For Ontologies & Knowledge Graphs

The filesystem metaphor maps naturally to knowledge organization:

| Filesystem | Knowledge Graph |
|------------|-----------------|
| Directories | Categories, concepts, groupings |
| Files | Entities, facts, leaf nodes |
| Paths | Relationships, "is-a" hierarchies |
| Content | Attributes, descriptions, metadata |

```python
# Agent discovers and categorizes information
tree = Loopy()

# Build taxonomy as you learn
tree.mkdir("/animals/mammals/canines", parents=True)
tree.touch("/animals/mammals/canines/dog", "domesticated, loyal, pack animal")
tree.touch("/animals/mammals/canines/wolf", "wild, apex predator, pack hunter")
tree.mkdir("/animals/mammals/felines")
tree.touch("/animals/mammals/felines/cat", "independent, domestic, solitary")

# Query the knowledge
tree.find("/animals", type="f")  # all animals
tree.grep("domestic", content=True)  # find domestic animals
tree.grep("pack", content=True)  # find pack animals

# Reorganize as understanding evolves
tree.mkdir("/pets", parents=True)
tree.mv("/animals/mammals/canines/dog", "/pets/dog")
tree.mv("/animals/mammals/felines/cat", "/pets/cat")
```

## Install

```bash
pip install loopy

# Or just copy - zero dependencies
curl -O https://raw.githubusercontent.com/tg1482/loopy/main/src/loopy/core.py
```

## Shell for Agents

Loopy includes a text shell that agents can use via tool calls:

```python
from loopy.shell import run

tree = Loopy()

# Agent issues text commands
run("mkdir -p /topics/physics/quantum", tree)
run("touch /topics/physics/quantum/entanglement 'spooky action at distance'", tree)
run("find /topics -type f", tree)  # list all facts
run("grep quantum /topics", tree)  # search
run("tree /topics", tree)  # visualize
```

Commands: `ls`, `cd`, `pwd`, `cat`, `tree`, `find`, `grep`, `du`, `touch`, `mkdir`, `rm -r`, `mv`, `cp`, `sed`, `help`

## API

### Core Operations

| Method | Description |
|--------|-------------|
| `mkdir(path, parents=True)` | Create directory (category) |
| `touch(path, content)` | Create file (entity) with content |
| `cat(path)` | Read content |
| `ls(path)` | List children |
| `rm(path, recursive=True)` | Delete node |
| `mv(src, dst)` | Move/rename |
| `cp(src, dst)` | Copy |
| `exists(path)` | Check existence |

### Search

| Method | Description |
|--------|-------------|
| `grep(pattern, content=True)` | Search by regex |
| `find(path, type="f")` | Find by type (f=file, d=dir) |
| `glob(pattern)` | Glob patterns (`**/*.py`) |

### Navigation

| Method | Description |
|--------|-------------|
| `cd(path)` | Change directory |
| `.cwd` | Current directory |
| `..` support | `tree.ls("..")` works |

### Inspection

| Method | Description |
|--------|-------------|
| `tree(path)` | Pretty print hierarchy |
| `du(path)` | Count nodes |
| `info(path)` | Metadata dict |
| `isdir(path)` / `isfile(path)` | Type checks |
| `walk(path)` | os.walk() style |
| `.raw` | The underlying string |

All mutating operations return `self` for chaining.

## Example Databases

Loopy ships with example databases in `examples/`:

```python
from examples import knowledge_graph, product_catalog, bookmarks, recipes, org_chart

# ML/CS concept ontology
tree = knowledge_graph()
tree.cat("/concepts/ml/deep_learning/architectures/transformer")
# "def:Attention-based architecture|prereq:attention,mlp|paper:attention_is_all_you_need"

tree.grep("prereq:.*transformer", content=True)  # what needs transformers?
tree.find("/concepts/ml", type="f")  # all ML concepts

# E-commerce taxonomy
tree = product_catalog()
tree.ls("/clothing/mens/shoes")  # ['loafers_brown']
tree.grep("price:.*99", content=True)  # products ending in .99
```

## Serialization

```python
# Save anywhere - it's just a string
saved = tree.raw
redis.set("agent:memory", saved)
db.store("knowledge", saved)

# Restore
tree = Loopy(redis.get("agent:memory"))

# Initialize from existing structure
tree = Loopy("<root><users><alice>admin</alice></users></root>")
tree.cat("/users/alice")  # "admin"
```

## How It Works

Internally, Loopy stores everything as XML-like tags:

```
<root><concepts><ml><supervised>...</supervised></ml></concepts></root>
```

- Directories = tags with children or empty: `<ml>...</ml>` or `<empty></empty>`
- Files = tags with text content: `<regression>predicts continuous</regression>`
- Content is auto-escaped (`<`, `>`, `&` preserved correctly)

The entire tree is one string—no parsing into objects, no hidden state.

## License

MIT
