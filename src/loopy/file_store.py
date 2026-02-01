from __future__ import annotations

from pathlib import Path

from .core_v2 import Loopy


def load(path: str | Path) -> Loopy:
    file_path = Path(path)
    data = file_path.read_text() if file_path.exists() else ""
    return Loopy(data)


def save(tree: Loopy, path: str | Path) -> None:
    file_path = Path(path)
    file_path.write_text(tree.raw)


class FileBackedLoopy(Loopy):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        data = self._path.read_text() if self._path.exists() else ""
        super().__init__(data, on_mutate=self.sync)

    @property
    def path(self) -> Path:
        return self._path

    def sync(self) -> None:
        self._path.write_text(self.raw)
