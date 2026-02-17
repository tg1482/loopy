# Changelog

## 0.3.2

### New features

- **`cat` multi-path support** — `cat` now accepts multiple paths and concatenates their contents (POSIX-standard behavior). Example: `cat /auth/state /auth/login /auth/logout` outputs all three files joined by newlines. Works with `--range` and piping.

### Performance

- **Eliminated recursion limits** — Converted all 9 recursive tree-walk functions (`emit`, `grep`, `tree`, `find`, `walk`, `glob`, `du`, `backlinks`, `sed`) to iterative stack-based traversal. Previously, `grep`, `find`, `du`, and `tree` would crash with `RecursionError` on trees deeper than ~1,000 levels. Now handles 10,000+ levels with no issues.

  | Operation | Before (5,000 deep) | After (5,000 deep) |
  |---|---|---|
  | grep | RecursionError | 258ms |
  | find | RecursionError | 2.8ms |
  | du | RecursionError | 0.4ms |
  | tree | RecursionError | 81ms |
  | serialize | RecursionError | 1.8ms |

- **Benchmarked at scale** — 100K files (8.9 MB raw): full-tree grep in 49ms, find in 29ms, cat in 0.06ms. See `stress_test.py`.

### Documentation

- Added Performance section to README with benchmark tables.
- Added `stress_test.py` for reproducible benchmarks.

## 0.3.0

### New features

- **`grep(lines=True)`** — search file content line-by-line and return `path:lineno:line` strings instead of just paths. Works with `ignore_case`, `invert`, and `path` scoping.
- **Shell `grep -n`** — new `-n` flag for the shell `grep` command that activates line-match mode. Composable with existing flags (`grep -ni pattern /path`). Also works on piped stdin.
- **`slugify()`** — new utility (`from loopy import slugify`) that converts any string into a valid Loopy path segment. Lowercases, replaces invalid characters with hyphens, preserves dots and underscores. Returns `"item"` for empty input.

### Documentation

- Updated README with `grep(lines=True)`, `grep -n`, and `slugify()` docs.
- Added this changelog.

## 0.2.3

- Export `FileBackedLoopy`, `load`, `save` from main module.

## 0.2.2

- Add mutation hook (`on_mutate`) and file-backed store.

## 0.2.1

- Shell improvements: `printf`, test fixes.

## 0.2.0

- Initial public release with core filesystem API, shell, symlinks, and file-backed persistence.
