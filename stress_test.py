"""Stress tests and benchmarks for Loopy.

Run:  uv run python stress_test.py
"""

import sys
import time

from loopy import Loopy
from loopy.shell import run


def _fmt(ms: float) -> str:
    if ms < 1:
        return f"{ms*1000:.0f}us"
    if ms < 1000:
        return f"{ms:.1f}ms"
    return f"{ms/1000:.2f}s"


def _size(chars: int) -> str:
    if chars < 1024:
        return f"{chars} B"
    if chars < 1024 * 1024:
        return f"{chars/1024:.0f} KB"
    return f"{chars/1024/1024:.1f} MB"


def bench(label: str, fn, **kwargs):
    t0 = time.perf_counter()
    result = fn()
    elapsed = (time.perf_counter() - t0) * 1000
    extra = " ".join(f"({v})" for v in kwargs.values() if v)
    print(f"  {label:30s} {_fmt(elapsed):>10s}  {extra}")
    return result, elapsed


def bench_wide(n_dirs: int, items_per_dir: int):
    total = n_dirs * items_per_dir
    print(f"\n{'='*60}")
    print(f"WIDE TREE: {n_dirs} dirs x {items_per_dir} items = {total:,} files")
    print(f"{'='*60}")

    tree = Loopy()
    t0 = time.perf_counter()
    for i in range(n_dirs):
        tree.mkdir(f"/cat{i:04d}", parents=True)
        for j in range(items_per_dir):
            tree.touch(
                f"/cat{i:04d}/item{j:04d}",
                f"content for item {j} in category {i}, "
                f"tags: alpha beta gamma delta epsilon",
            )
    build_ms = (time.perf_counter() - t0) * 1000
    print(f"  {'build':30s} {_fmt(build_ms):>10s}")

    raw, _ = bench("serialize (.raw)", lambda: tree.raw)
    print(f"  {'raw size':30s} {_size(len(raw)):>10s}")
    bench("serialize (cached)", lambda: tree.raw)
    bench("parse (from raw)", lambda: Loopy(raw))
    bench("cat (single file)", lambda: run("cat /cat0000/item0000", tree))
    bench(
        "cat (10 files)",
        lambda: run(
            "cat " + " ".join(f"/cat0000/item{j:04d}" for j in range(10)), tree
        ),
    )
    bench("ls (single dir)", lambda: run(f"ls /cat0000", tree))
    bench("grep (full tree)", lambda: run('grep "item 0 in category 0" /', tree))
    out, _ = bench("find -type f", lambda: run("find / -type f", tree))
    bench("du (full tree)", lambda: run("du /", tree))
    bench("tree (single dir)", lambda: run("tree /cat0000", tree))
    bench("grep|sort|head", lambda: run('grep "category 0" / | sort | head -n 5', tree))
    bench("cat 10 files | write", lambda: (
        run("cat " + " ".join(f"/cat0000/item{j:04d}" for j in range(10)) + " | write /combined", tree),
        run("cat /combined", tree),
    ))

    # Roundtrip check
    tree2 = Loopy(raw)
    raw2 = tree2.raw
    assert raw == raw2, "ROUNDTRIP FAILED"
    print(f"  {'roundtrip':30s} {'PASS':>10s}")

    return {
        "label": f"{total:,} files ({n_dirs}x{items_per_dir})",
        "raw_size": _size(len(raw)),
        "build": build_ms,
    }


def bench_deep(depth: int):
    print(f"\n{'='*60}")
    print(f"DEEP TREE: {depth:,} levels")
    print(f"{'='*60}")

    tree = Loopy()
    t0 = time.perf_counter()
    path = ""
    for i in range(depth):
        path += f"/d{i:04d}"
    tree.mkdir(path, parents=True)
    tree.touch(f"{path}/leaf", "deep content here")
    build_ms = (time.perf_counter() - t0) * 1000
    print(f"  {'build':30s} {_fmt(build_ms):>10s}")

    raw, _ = bench("serialize (.raw)", lambda: tree.raw)
    print(f"  {'raw size':30s} {_size(len(raw)):>10s}")
    bench("parse (from raw)", lambda: Loopy(raw))
    bench(f"cat (depth {depth})", lambda: tree.cat(f"{path}/leaf"))
    bench(f"exists (depth {depth})", lambda: tree.exists(f"{path}/leaf"))
    bench("grep (full tree)", lambda: tree.grep("deep", path="/", content=True))
    bench("find -type f", lambda: tree.find("/", type="f"))
    bench("du (full tree)", lambda: tree.du("/"))
    bench("tree (full)", lambda: tree.tree("/"))

    # Roundtrip
    tree2 = Loopy(raw)
    assert tree2.raw == raw, "ROUNDTRIP FAILED"
    print(f"  {'roundtrip':30s} {'PASS':>10s}")

    return {"label": f"{depth:,} levels", "raw_size": _size(len(raw)), "build": build_ms}


def bench_recursion_limit():
    """Verify no RecursionError at depth exceeding Python's default limit."""
    print(f"\n{'='*60}")
    print(f"RECURSION SAFETY (default sys.recursionlimit={sys.getrecursionlimit()})")
    print(f"{'='*60}")

    depth = sys.getrecursionlimit() + 500
    tree = Loopy()
    path = ""
    for i in range(depth):
        path += f"/d{i:05d}"
    tree.mkdir(path, parents=True)
    tree.touch(f"{path}/leaf", "content")

    ops = {
        "serialize (.raw)": lambda: tree.raw,
        "parse (from raw)": lambda: Loopy(tree.raw),
        "cat": lambda: tree.cat(f"{path}/leaf"),
        "grep": lambda: tree.grep("content", path="/", content=True),
        "find": lambda: tree.find("/", type="f"),
        "du": lambda: tree.du("/"),
        "tree": lambda: tree.tree("/"),
        "walk": lambda: tree.walk("/"),
        "glob": lambda: tree.glob("**/leaf"),
        "backlinks": lambda: tree.backlinks("/nonexistent"),
    }

    all_pass = True
    for name, fn in ops.items():
        try:
            fn()
            print(f"  {name:30s} {'PASS':>10s}")
        except RecursionError:
            print(f"  {name:30s} {'FAIL':>10s}  RecursionError!")
            all_pass = False

    return all_pass


def main():
    print("Loopy Stress Test & Benchmarks")
    print(f"Python {sys.version.split()[0]}, recursion limit {sys.getrecursionlimit()}")

    # Wide trees
    bench_wide(10, 1000)      # 10K files
    bench_wide(100, 1000)     # 100K files

    # Deep trees
    bench_deep(100)
    bench_deep(1000)
    bench_deep(5000)
    bench_deep(10000)

    # Recursion safety
    all_pass = bench_recursion_limit()

    print(f"\n{'='*60}")
    if all_pass:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
