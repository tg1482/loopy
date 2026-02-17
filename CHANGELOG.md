# Changelog

## 0.3.1

### New features

- **`cat` multi-path support** — `cat` now accepts multiple paths and concatenates their contents (POSIX-standard behavior). Example: `cat /auth/state /auth/login /auth/logout` outputs all three files joined by newlines. Works with `--range` and piping.

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
