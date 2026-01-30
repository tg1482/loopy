# Loopy

Loopy: a filesystem API over a single Python string.

Loopy is a tiny Python library that exposes filesystem semantics over a string database. It comes with a bash‑style shell so you or your agent can navigate, search, and manipulate a tree‑structured knowledge base with composable commands.

Directories become concepts, files become entities, and paths encode relationships. Agents can create, search, reorganize, and evolve ontologies using commands they already understand.

## Shell

Start a REPL loop with a sample database:

```bash
uv run python -c "from examples import product_catalog; from loopy.shell import repl; repl(product_catalog())"
```

Quick shell example:

```text
loopy> ls -R sports
sports:
fitness/
outdoor/

loopy> find /sports -type f
/sports/fitness/weights/dumbbells_set
/sports/fitness/cardio/yoga_mat
/sports/outdoor/camping/tent_4person
/sports/outdoor/hiking/backpack_40L
```

### Shell Commands

| Command | Description |
|---------|-------------|
| `ls [path] [-R]` | List directory contents |
| `cd <path>` | Change directory |
| `pwd` | Print working directory |
| `cat [path] [--range start len]` | Show file contents |
| `head [path] [-n N]` | Show first N lines (default 10) |
| `tail [path] [-n N]` | Show last N lines (default 10) |
| `tree [path]` | Show tree structure |
| `find [path] [-name pat] [-type d\|f]` | Find files/directories |
| `grep <pat> [path] [-i] [-v] [-c]` | Search by regex |
| `du [path] [-c]` | Count nodes or content size |
| `info [path]` | Show node metadata |
| `touch <path> [content]` | Create file |
| `write <path> [content]` | Write to file (overwrites) |
| `mkdir [-p] <path>` | Create directory |
| `rm [-r] <path>` | Remove file/directory |
| `mv <src> <dst>` | Move/rename |
| `cp <src> <dst>` | Copy |
| `sed <path> <pat> <repl> [-i] [-r]` | Search and replace |
| `split <delim> [path]` | Split content by delimiter (or -d/--delimiter) |
| `echo <text>` | Print text |
| `help` | Show help |

## Why?

When an agent processes information, it needs somewhere to put it - somewhere it can search, reorganize, and grow organically. For any type of knowledge base like agent memories, product taxonomies, etc the challenge was enabling recursive interaction without a pile of specialized tools (search, create, delete, etc.) that are added to context.

Recursive Language Models (RLMs) introduced the idea of putting the entire context into a Python variable and let the model recursively interact with it, instead of reasoning over everything in one shot. RLMs: https://alexzhang13.github.io/blog/2025/rlm/. I really liked it, but enabing a python REPL seemed like a bad tradeoff for generality. 

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

## Install

```bash
# Local install
uv pip install -e .
```

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
