"""Ledger rules independent of terminal input and file layout."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Iterator
from uuid import uuid4

from .models import AppError, Transaction, parse_tags, positive_amount, valid_category, valid_date, valid_month
from .storage import LedgerStore, newest_first


CSV_FIELDS = ("date", "type", "category", "amount", "memo", "tags")


@dataclass(frozen=True)
class Summary:
    count: int
    income: int
    expense: int
    top_categories: list[tuple[str, int]]
    budget: int | None

    @property
    def balance(self) -> int:
        return self.income - self.expense


class BudgetService:
    def __init__(self, store: LedgerStore) -> None:
        self.store = store

    def _transaction(self, *, id: str | None = None, date: str, type: str,
                     category: str, amount: str | int, memo: str = "",
                     tags: str = "") -> Transaction:
        name = valid_category(category)
        if name not in self.store.categories():
            raise AppError(f"등록되지 않은 카테고리 '{name}'입니다. category list/add로 확인하거나 추가하세요.")
        return Transaction(
            id=id or f"TX-{uuid4().hex[:12].upper()}", date=valid_date(date),
            type=type, category=name, amount=positive_amount(amount),
            memo=memo, tags=parse_tags(tags),
        )

    def add(self, **fields: str) -> Transaction:
        item = self._transaction(**fields)
        self.store.append(item)
        return item

    def list(self, limit: int) -> Iterator[Transaction]:
        if limit <= 0:
            raise AppError("--limit은 1 이상이어야 합니다.")
        yield from self._take(newest_first(self.store.transactions()), limit)

    @staticmethod
    def _take(source: Iterator[Transaction], limit: int) -> Iterator[Transaction]:
        try:
            for index, item in enumerate(source):
                if index >= limit:
                    break
                yield item
        finally:
            source.close()

    def search(self, *, from_date: str | None = None, to_date: str | None = None,
               category: str | None = None, type: str | None = None,
               q: str | None = None, tag: str | None = None) -> Iterator[Transaction]:
        if from_date:
            valid_date(from_date)
        if to_date:
            valid_date(to_date)
        if from_date and to_date and from_date > to_date:
            raise AppError("--from은 --to보다 늦을 수 없습니다.")
        if type and type not in ("income", "expense"):
            raise AppError("--type은 income 또는 expense여야 합니다.")

        def matches() -> Iterator[Transaction]:
            for item in self.store.transactions():
                if from_date and item.date < from_date:
                    continue
                if to_date and item.date > to_date:
                    continue
                if category and item.category != category:
                    continue
                if type and item.type != type:
                    continue
                if q and q.casefold() not in item.memo.casefold():
                    continue
                if tag and tag not in item.tags:
                    continue
                yield item

        yield from newest_first(matches())

    def summary(self, month: str, top: int) -> Summary:
        valid_month(month)
        if top <= 0:
            raise AppError("--top은 1 이상이어야 합니다.")
        income = expense = count = 0
        categories: dict[str, int] = {}
        for item in self.store.transactions():
            if item.date[:7] != month:
                continue
            count += 1
            if item.type == "income":
                income += item.amount
            else:
                expense += item.amount
                categories[item.category] = categories.get(item.category, 0) + item.amount
        ranking = sorted(categories.items(), key=lambda pair: (-pair[1], pair[0]))[:top]
        return Summary(count, income, expense, ranking, self.store.budgets().get(month))

    def set_budget(self, month: str, amount: str) -> int:
        valid_month(month)
        value = positive_amount(amount)
        budgets = self.store.budgets()
        budgets[month] = value
        self.store.save_budgets(budgets)
        return value

    def add_category(self, name: str) -> str:
        name = valid_category(name)
        names = self.store.categories()
        if name in names:
            raise AppError(f"'{name}'은 이미 등록되어 있습니다. category list로 확인하세요.")
        names.add(name)
        self.store.save_categories(names)
        return name

    def remove_category(self, name: str) -> None:
        names = self.store.categories()
        if name not in names:
            raise AppError(f"'{name}' 카테고리가 없습니다. category list로 확인하세요.")
        for item in self.store.transactions():
            if item.category == name:
                raise AppError(f"'{name}'을 사용하는 거래가 있어 삭제할 수 없습니다. 거래를 수정/삭제하세요.")
        names.remove(name)
        self.store.save_categories(names)

    def update(self, id: str, **changes: str | None) -> bool:
        changes = {key: value for key, value in changes.items() if value is not None}
        if not changes:
            raise AppError("수정할 옵션을 하나 이상 지정하세요. update --help를 확인하세요.")

        def transform(old: Transaction) -> Transaction:
            fields = dict(date=old.date, type=old.type, category=old.category,
                          amount=old.amount, memo=old.memo, tags=",".join(old.tags))
            fields.update(changes)
            return self._transaction(id=old.id, **fields)

        return self.store.rewrite(transform, target_id=id)

    def delete(self, id: str) -> bool:
        return self.store.rewrite(lambda _: None, target_id=id)

    def import_csv(self, path: Path) -> int:
        if not path.is_file():
            raise AppError(f"CSV 파일이 없습니다: {path}. --from 경로를 확인하세요.")
        count = 0
        with tempfile.TemporaryDirectory(prefix="budget-import-") as temp_dir:
            staged = Path(temp_dir) / "validated.jsonl"
            try:
                with path.open(encoding="utf-8-sig", newline="") as source, staged.open("w", encoding="utf-8") as output:
                    reader = csv.DictReader(source)
                    if not reader.fieldnames or any(field not in reader.fieldnames for field in CSV_FIELDS[:4]):
                        raise AppError("CSV 헤더에 date,type,category,amount가 필요합니다. README 스키마를 확인하세요.")
                    if len(set(reader.fieldnames)) != len(reader.fieldnames):
                        raise AppError("CSV 헤더에 중복 열이 있습니다. 헤더를 수정하세요.")
                    for number, row in enumerate(reader, 2):
                        if None in row:
                            raise AppError(f"CSV {number}행의 열 개수가 헤더보다 많습니다. CSV를 확인하세요.")
                        try:
                            item = self._transaction(
                                date=row["date"], type=row["type"], category=row["category"],
                                amount=row["amount"], memo=row.get("memo") or "",
                                tags=row.get("tags") or "",
                            )
                        except (AppError, TypeError) as exc:
                            raise AppError(f"CSV {number}행: {exc}") from exc
                        output.write(json.dumps(item.__dict__, ensure_ascii=False) + "\n")
                        count += 1
            except UnicodeError as exc:
                raise AppError("CSV 인코딩 오류입니다. UTF-8로 저장하세요.") from exc
            if count:
                self.store.append_batch(staged)
        return count

    def export_csv(self, path: Path, *, month: str | None = None,
                   from_date: str | None = None, to_date: str | None = None) -> int:
        if not month and not from_date and not to_date:
            raise AppError("export에는 --month 또는 --from/--to 조건이 필요합니다.")
        if month:
            valid_month(month)
        if path.resolve() in (self.store.transactions_path.resolve(),
                              self.store.categories_path.resolve(), self.store.budgets_path.resolve()):
            raise AppError("저장 파일을 CSV 출력 경로로 사용할 수 없습니다. 다른 --out 경로를 선택하세요.")
        path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as output:
            temp_path = Path(output.name)
            try:
                writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
                writer.writeheader()
                for item in self.search(from_date=from_date, to_date=to_date):
                    if month and item.date[:7] != month:
                        continue
                    writer.writerow(dict(date=item.date, type=item.type, category=item.category,
                                         amount=item.amount, memo=item.memo, tags=",".join(item.tags)))
                    count += 1
                output.flush()
                os.fsync(output.fileno())
            except BaseException:
                temp_path.unlink(missing_ok=True)
                raise
        temp_path.replace(path)
        return count
