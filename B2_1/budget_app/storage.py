"""JSONL 영구 저장과 한 줄씩 읽는 스트리밍 처리를 담당한다."""

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
    """객체 한 개를 JSONL의 한 줄로 직렬화한다."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


@contextmanager
def _replacement(path: Path) -> Iterator[object]:
    """같은 폴더의 임시 파일을 완성한 후 원본 파일과 교체한다."""
    # 같은 폴더에 만들어야 os.replace로 한 파일 교체가 가능하다.
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            yield output
            # 디스크 기록을 마친 뒤에만 원본을 교체한다.
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class LedgerStore:
    """거래·카테고리·예산의 세 JSONL 파일을 관리한다."""
    DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "other")

    def __init__(self, data_dir: Path) -> None:
        """첫 실행에는 폴더와 파일, 기본 카테고리를 자동으로 만든다."""
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
        """거래 파일을 통째로 읽지 않고 yield로 한 건씩 전달한다."""
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
        """검증된 거래를 JSONL 끝에 한 줄 추가한다."""
        with self.transactions_path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(_json_line(transaction.__dict__))
            output.flush()
            os.fsync(output.fileno())

    def rewrite(self, transform: Callable[[Transaction], Transaction | None], *, target_id: str) -> bool:
        """수정·삭제에 공통으로 쓰는 재작성. None은 해당 거래 삭제를 뜻한다."""
        found = False
        with _replacement(self.transactions_path) as output:
            # 원본을 직접 고치지 않으므로 변환 도중 오류가 나도 원본이 남는다.
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
        """검증이 끝난 CSV 거래들을 기존 거래 뒤에 한 번에 반영한다."""
        with _replacement(self.transactions_path) as output:
            with self.transactions_path.open(encoding="utf-8") as source:
                for line in source:
                    output.write(line)
            with staged_path.open(encoding="utf-8") as source:
                for line in source:
                    output.write(line)

    def categories(self) -> set[str]:
        """중복 없이 카테고리 이름을 읽는다."""
        names: set[str] = set()
        for record in self._records(self.categories_path):
            name = record.get("name")
            if not isinstance(name, str) or not name.strip():
                raise AppError("categories.jsonl의 name이 잘못되었습니다. 파일을 복구하세요.")
            names.add(name)
        return names

    def save_categories(self, categories: set[str]) -> None:
        """정렬된 카테고리 목록을 임시 파일을 통해 저장한다."""
        with _replacement(self.categories_path) as output:
            for name in sorted(categories):
                output.write(_json_line({"name": name}))

    def budgets(self) -> dict[str, int]:
        """월 문자열을 키로 하는 예산 사전을 읽는다."""
        budgets: dict[str, int] = {}
        for record in self._records(self.budgets_path):
            month, amount = record.get("month"), record.get("amount")
            if not isinstance(month, str) or not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                raise AppError("budgets.jsonl의 month/amount가 잘못되었습니다. 파일을 복구하세요.")
            budgets[month] = amount
        return budgets

    def save_budgets(self, budgets: dict[str, int]) -> None:
        """월 예산 전체를 임시 파일을 통해 저장한다."""
        with _replacement(self.budgets_path) as output:
            for month, amount in sorted(budgets.items()):
                output.write(_json_line({"month": month, "amount": amount}))

    @staticmethod
    def _records(path: Path) -> Iterator[dict]:
        """카테고리·예산 JSONL을 한 줄씩 읽고 손상된 행을 알려 준다."""
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
    """거래를 작은 묶음으로 정렬·병합해 날짜 최신순으로 제공한다."""
    with tempfile.TemporaryDirectory(prefix="budget-sort-") as temp_dir:
        paths: list[Path] = []
        chunk: list[Transaction] = []

        def write_chunk() -> None:
            # 거래 전체 대신 최대 chunk_size건만 메모리에서 정렬한다.
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
            # 각 임시 파일의 맨 앞 거래끼리 비교하며 최신순으로 병합한다.
            yield from heapq.merge(
                *streams, key=lambda item: (item.date, item.id), reverse=True
            )
        finally:
            for stream in streams:
                stream.close()
