"""JSONL persistence. Large transaction files are read and rewritten in streams."""

from __future__ import annotations

from contextlib import contextmanager
import heapq
import json
import os
from pathlib import Path
import tempfile
from typing import Callable, Iterator

from .models import AppError, Transaction


def _json_line(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


@contextmanager
def _replacement(path: Path) -> Iterator[object]:
    """Write beside the destination, then atomically replace it on success."""
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            yield output
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class LedgerStore:
    DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "other")

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transactions_path = data_dir / "transactions.jsonl"
        self.categories_path = data_dir / "categories.jsonl"
        self.budgets_path = data_dir / "budgets.jsonl"
        for path in (self.transactions_path, self.budgets_path):
            path.touch(exist_ok=True)
        if not self.categories_path.exists() or self.categories_path.stat().st_size == 0:
            self.save_categories(set(self.DEFAULT_CATEGORIES))

    def transactions(self) -> Iterator[Transaction]:
        with self.transactions_path.open(encoding="utf-8") as source:
            for number, line in enumerate(source, 1):
                try:
                    data = json.loads(line)
                    if not isinstance(data, dict):
                        raise ValueError("JSON object expected")
                    yield Transaction.from_dict(data)
                except (ValueError, TypeError) as exc:
                    raise AppError(
                        f"transactions.jsonl {number}행이 손상되었습니다. 파일을 복구한 뒤 다시 실행하세요."
                    ) from exc

    def append(self, transaction: Transaction) -> None:
        with self.transactions_path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(_json_line(transaction.__dict__))
            output.flush()
            os.fsync(output.fileno())

    def rewrite(self, transform: Callable[[Transaction], Transaction | None], *, target_id: str) -> bool:
        found = False
        with _replacement(self.transactions_path) as output:
            for transaction in self.transactions():
                if transaction.id == target_id:
                    found = True
                    replacement = transform(transaction)
                    if replacement is not None:
                        output.write(_json_line(replacement.__dict__))
                else:
                    output.write(_json_line(transaction.__dict__))
        return found

    def append_batch(self, staged_path: Path) -> None:
        with _replacement(self.transactions_path) as output:
            with self.transactions_path.open(encoding="utf-8") as source:
                for line in source:
                    output.write(line)
            with staged_path.open(encoding="utf-8") as source:
                for line in source:
                    output.write(line)

    def categories(self) -> set[str]:
        names: set[str] = set()
        for record in self._records(self.categories_path):
            name = record.get("name")
            if not isinstance(name, str) or not name.strip():
                raise AppError("categories.jsonl의 name이 잘못되었습니다. 파일을 복구하세요.")
            names.add(name)
        return names

    def save_categories(self, categories: set[str]) -> None:
        with _replacement(self.categories_path) as output:
            for name in sorted(categories):
                output.write(_json_line({"name": name}))

    def budgets(self) -> dict[str, int]:
        budgets: dict[str, int] = {}
        for record in self._records(self.budgets_path):
            month, amount = record.get("month"), record.get("amount")
            if not isinstance(month, str) or not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                raise AppError("budgets.jsonl의 month/amount가 잘못되었습니다. 파일을 복구하세요.")
            budgets[month] = amount
        return budgets

    def save_budgets(self, budgets: dict[str, int]) -> None:
        with _replacement(self.budgets_path) as output:
            for month, amount in sorted(budgets.items()):
                output.write(_json_line({"month": month, "amount": amount}))

    @staticmethod
    def _records(path: Path) -> Iterator[dict]:
        with path.open(encoding="utf-8") as source:
            for number, line in enumerate(source, 1):
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError
                    yield record
                except (ValueError, TypeError) as exc:
                    raise AppError(f"{path.name} {number}행이 손상되었습니다. 파일을 복구하세요.") from exc


def newest_first(source: Iterator[Transaction], chunk_size: int = 1000) -> Iterator[Transaction]:
    """External merge sort: memory stays proportional to chunk count and size."""
    with tempfile.TemporaryDirectory(prefix="budget-sort-") as temp_dir:
        paths: list[Path] = []
        chunk: list[Transaction] = []

        def write_chunk() -> None:
            chunk.sort(key=lambda item: (item.date, item.id), reverse=True)
            path = Path(temp_dir) / f"chunk-{len(paths)}.jsonl"
            with path.open("w", encoding="utf-8") as output:
                for item in chunk:
                    output.write(_json_line(item.__dict__))
            paths.append(path)
            chunk.clear()

        for item in source:
            chunk.append(item)
            if len(chunk) >= chunk_size:
                write_chunk()
        if chunk:
            write_chunk()

        def read_chunk(path: Path) -> Iterator[Transaction]:
            with path.open(encoding="utf-8") as input_file:
                for line in input_file:
                    yield Transaction.from_dict(json.loads(line))

        streams = [read_chunk(path) for path in paths]
        try:
            yield from heapq.merge(
                *streams, key=lambda item: (item.date, item.id), reverse=True
            )
        finally:
            for stream in streams:
                stream.close()
