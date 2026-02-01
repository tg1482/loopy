from loopy import Loopy
from loopy.file_store import FileBackedLoopy, load, save


def test_on_mutate_hook_called():
    calls: list[int] = []

    tree = Loopy(on_mutate=lambda: calls.append(1))
    tree.ls("/")
    assert calls == []

    tree.mkdir("/notes", parents=True)
    assert len(calls) == 1


def test_file_backed_loopy_syncs(tmp_path):
    path = tmp_path / "notes.loopy"
    tree = FileBackedLoopy(path)
    tree.touch("/ideas/mcp", "Expose shell with MCP")

    raw = path.read_text()
    assert "Expose shell with MCP" in raw
    assert "<ideas>" in raw


def test_load_and_save(tmp_path):
    path = tmp_path / "notes.loopy"
    tree = load(path)
    tree.touch("/ideas/cli", "Ship a clean CLI")
    save(tree, path)

    raw = path.read_text()
    assert "Ship a clean CLI" in raw
