"""명령어 해석, 대화형 입력, 결과·오류 출력을 담당한다."""

from __future__ import annotations

import argparse
from functools import wraps
import os
from pathlib import Path
import sys
from time import perf_counter
from typing import Callable, Iterator

from .models import AppError, Transaction
from .service import BudgetService
from .storage import LedgerStore


def timed(func: Callable[..., int]) -> Callable[..., int]:
    """실행 시간 측정을 명령 처리 코드에서 분리한 데코레이터."""
    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> int:
        start = perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            # 평소 출력은 깔끔하게 유지하고 요청할 때만 시간을 표시한다.
            if os.getenv("BUDGET_APP_TIMING") == "1":
                print(f"[실행 시간] {perf_counter() - start:.3f}초", file=sys.stderr)
    return wrapper


def parser() -> argparse.ArgumentParser:
    """모든 명령과 --help, -- 옵션을 한 곳에서 정의한다."""
    root = argparse.ArgumentParser(prog="python -m budget_app", description="나만의 용돈 기입장")
    root.add_argument("--data-dir", type=Path, default=Path("data"), help="저장 폴더 (기본: ./data)")
    # 상위 옵션이므로 --data-dir은 하위 명령 앞에 둔다.
    commands = root.add_subparsers(dest="command", required=True)

    commands.add_parser("add", help="대화형으로 거래 추가")
    listing = commands.add_parser("list", help="날짜 최신순 거래 목록")
    listing.add_argument("--limit", type=int, default=20, help="출력 건수 (기본: 20)")

    search = commands.add_parser("search", help="조건 검색")
    _date_filters(search)
    search.add_argument("--category")
    search.add_argument("--type", choices=("income", "expense"))
    search.add_argument("--q", help="메모 키워드")
    search.add_argument("--tag", help="태그 정확히 일치")

    summary = commands.add_parser("summary", help="월별 합계와 지출 순위")
    summary.add_argument("--month", required=True)
    summary.add_argument("--top", type=int, default=3)

    budget = commands.add_parser("budget", help="월 예산 설정/조회")
    budget_commands = budget.add_subparsers(dest="budget_command", required=True)
    set_budget = budget_commands.add_parser("set", help="월 예산 설정")
    set_budget.add_argument("--month", required=True)
    set_budget.add_argument("--amount", required=True)
    show_budget = budget_commands.add_parser("show", help="월 예산 조회")
    show_budget.add_argument("--month", required=True)

    category = commands.add_parser("category", help="카테고리 관리")
    category_commands = category.add_subparsers(dest="category_command", required=True)
    category_commands.add_parser("add", help="대화형으로 카테고리 추가")
    category_commands.add_parser("list", help="카테고리 목록")
    remove = category_commands.add_parser("remove", help="카테고리 삭제")
    remove.add_argument("--name", required=True)

    update = commands.add_parser("update", help="옵션 방식으로 거래 수정")
    update.add_argument("--id", required=True)
    for name in ("date", "type", "category", "amount", "memo", "tags"):
        update.add_argument(f"--{name}")

    delete = commands.add_parser("delete", help="거래 삭제")
    delete.add_argument("--id", required=True)

    importing = commands.add_parser("import", help="CSV 거래 가져오기")
    importing.add_argument("--from", dest="source", type=Path, required=True)
    exporting = commands.add_parser("export", help="CSV 거래 내보내기")
    exporting.add_argument("--out", type=Path, required=True)
    exporting.add_argument("--month")
    _date_filters(exporting)
    return root


def _date_filters(command: argparse.ArgumentParser) -> None:
    """검색과 내보내기에 공통인 날짜 범위 옵션을 등록한다."""
    command.add_argument("--from", dest="from_date")
    command.add_argument("--to", dest="to_date")


def _print_items(items: Iterator[Transaction]) -> None:
    """제너레이터의 거래를 출력하고 사용한 파일 자원을 닫는다."""
    found = False
    try:
        for item in items:
            found = True
            print(f"{item.id} | {item.date} | {item.type:<7} | {item.category} | "
                  f"{item.amount}원 | {item.memo} | {','.join(item.tags)}")
    finally:
        items.close()
    if not found:
        print("데이터 없음")


def _prompt(label: str) -> str:
    """대화형 입력의 앞뒤 공백을 정리한다."""
    return input(label).strip()


def _run(args: argparse.Namespace) -> int:
    """CLI 요청을 서비스 기능에 연결하고 사용자 메시지를 출력한다."""
    service = BudgetService(LedgerStore(args.data_dir))
    command = args.command
    if command == "add":
        # 과제의 기본 입력 방식: add는 필드를 순서대로 질문한다.
        item = service.add(date=_prompt("날짜(YYYY-MM-DD): "),
                           type=_prompt("타입(income/expense): "),
                           category=_prompt("카테고리: "),
                           amount=_prompt("금액(양수 정수): "),
                           memo=_prompt("메모(선택): "),
                           tags=_prompt("태그(쉼표 구분, 선택): "))
        print(f"[저장 완료] id={item.id}")
    elif command == "list":
        _print_items(service.list(args.limit))
    elif command == "search":
        _print_items(service.search(from_date=args.from_date, to_date=args.to_date,
                                    category=args.category, type=args.type, q=args.q, tag=args.tag))
    elif command == "summary":
        # 서비스는 계산 결과를 돌려주고, 표시 형식과 경고 문구는 CLI가 맡는다.
        result = service.summary(args.month, args.top)
        if result.count == 0:
            print(f"{args.month}: 데이터 없음")
        print(f"총 수입: {result.income}원")
        print(f"총 지출: {result.expense}원")
        print(f"잔액: {result.balance}원")
        if result.budget is not None:
            ratio = result.expense / result.budget * 100
            print(f"예산: {result.budget}원 (사용률 {ratio:.1f}%)")
            if result.expense > result.budget:
                print("[경고] 월 예산을 초과했습니다.")
        print(f"지출 TOP {args.top}")
        if not result.top_categories:
            print("데이터 없음")
        for rank, (name, amount) in enumerate(result.top_categories, 1):
            print(f"{rank}) {name} {amount}원")
    elif command == "budget":
        if args.budget_command == "set":
            amount = service.set_budget(args.month, args.amount)
            print(f"[저장 완료] {args.month} 예산 {amount}원")
        else:
            from .models import valid_month
            valid_month(args.month)
            amount = service.store.budgets().get(args.month)
            print(f"{args.month} 예산: {amount}원" if amount is not None else f"{args.month} 예산: 설정 없음")
    elif command == "category":
        if args.category_command == "add":
            name = service.add_category(_prompt("카테고리명: "))
            print(f"[저장 완료] category={name}")
        elif args.category_command == "list":
            for name in sorted(service.store.categories()):
                print(f"- {name}")
        else:
            service.remove_category(args.name)
            print(f"[삭제 완료] category={args.name}")
    elif command == "update":
        # update는 README에 명시한 옵션 방식으로만 입력받는다.
        changes = {name: getattr(args, name) for name in ("date", "type", "category", "amount", "memo", "tags")}
        if not service.update(args.id, **changes):
            raise AppError(f"id={args.id} 거래가 없습니다. list/search로 id를 확인하세요.")
        print(f"[수정 완료] id={args.id}")
    elif command == "delete":
        if not service.delete(args.id):
            raise AppError(f"id={args.id} 거래가 없습니다. list/search로 id를 확인하세요.")
        print(f"[삭제 완료] id={args.id}")
    elif command == "import":
        print(f"[완료] imported={service.import_csv(args.source)}, skipped=0")
    elif command == "export":
        count = service.export_csv(args.out, month=args.month,
                                   from_date=args.from_date, to_date=args.to_date)
        print(f"[완료] {args.out} ({count} records)")
    return 0


@timed
def main(argv: list[str] | None = None) -> int:
    """사용자 오류를 스택트레이스 대신 메시지와 종료 코드 1로 처리한다."""
    try:
        return _run(parser().parse_args(argv))
    except (AppError, OSError, UnicodeError, EOFError, KeyboardInterrupt) as exc:
        print(f"[오류] {exc}", file=sys.stderr)
        if isinstance(exc, OSError):
            print("[힌트] 파일 경로와 읽기/쓰기 권한을 확인하세요.", file=sys.stderr)
        elif isinstance(exc, (EOFError, KeyboardInterrupt)):
            print("[힌트] 입력을 완료한 뒤 다시 실행하세요.", file=sys.stderr)
        return 1
