# Loopy

Loopy: a filesystem API over a single Python string.

Loopy is a tiny Python library that exposes filesystem semantics over a single serialized string. Directories become concepts, files become entities, and paths encode relationships. Agents can create, search, reorganize, and evolve ontologies using commands they already understand.

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

# tree.raw
# <root><concepts><ml><supervised><regression>predicts continuous values</regression><classification>predicts categories</classification></supervised><unsupervised><clustering>groups similar items</clustering></unsupervised></ml></concepts></root>
```

## Why?

When an agent processes information, it needs somewhere to put it - somewhere it can search, reorganize, and grow organically. For any type of knowledge base like agent memories, product taxonomies, etc the challenge was enabling recursive interaction without a pile of specialized tools (search, create, delete, etc.) that are added to context.

Recursive Language Models (RLMs) introduced the idea of putting the entire context into a Python variable and let the model recursively interact with it, instead of reasoning over everything in one shot. RLMs: https://alexzhang13.github.io/blog/2025/rlm/. I really liked it, but enabing REPL seemed like a bad tradeoff for generality. 

Loopy imposes a known structure (a tree / filesystem), and replaces the REPL with composable Bash-style commands.

Why this approach:

- simple - a single string can represent the full data
- known structure - stored in a file system format agents already know and love
- composition - compose search commands to quickly navigate the data


## How it works

Loopy keeps an in-memory node tree and exposes filesystem-like operations. The raw string is generated on demand and can be parsed back into the same structure.

```
<root><concepts><ml><supervised>...</supervised></ml></concepts></root>
```

## Install

```bash
# Local install
uv pip install -e .
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

# compose commands with pipes
run("find /topics -type f | grep quantum", tree)  # find files, filter by name
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

Not all commands are supported in the shell format yet. Working towards it.

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


## License

MIT
