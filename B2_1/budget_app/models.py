"""거래 데이터의 모양과 입력 검증 규칙을 정의한다."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
import re
from typing import Any


class AppError(ValueError):
    """사용자에게 원인과 해결 방향을 보여 줄 수 있는 오류."""


def valid_date(value: str) -> str:
    """형식뿐 아니라 실제 존재하는 날짜인지 확인한다."""
    try:
        # fromisoformat만으로는 입력 형식이 느슨할 수 있어 변환 결과도 비교한다.
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise AppError("날짜는 YYYY-MM-DD 형식의 실제 날짜여야 합니다. 예: 2024-01-15") from exc
    return value


def valid_month(value: str) -> str:
    """월별 요약과 예산에서 쓰는 YYYY-MM 형식을 검사한다."""
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
        raise AppError("월은 YYYY-MM 형식이어야 합니다. 예: 2024-01")
    return value


def positive_amount(value: str | int) -> int:
    """거래와 예산의 금액을 0보다 큰 정수로 통일한다."""
    try:
        amount = int(value)
    except (TypeError, ValueError) as exc:
        raise AppError("금액은 양수 정수여야 합니다. 예: 15000") from exc
    # 숫자로 변환 가능하더라도 부호가 붙은 문자열은 입력 규칙에 맞지 않는다.
    if isinstance(value, str) and not re.fullmatch(r"[0-9]+", value.strip()):
        raise AppError("금액은 양수 정수여야 합니다. 예: 15000")
    if amount <= 0:
        raise AppError("금액은 0보다 커야 합니다. 예: 15000")
    return amount


def valid_category(value: str) -> str:
    """빈 이름과 CSV/JSONL 저장을 헷갈리게 할 문자를 막는다."""
    name = value.strip()
    if not name or any(char in name for char in "\r\n,"):
        raise AppError("카테고리명은 빈 값이거나 쉼표/줄바꿈을 포함할 수 없습니다.")
    return name


@dataclass(frozen=True)
class Transaction:
    """거래 한 건. 수정할 때는 원본을 바꾸지 않고 새 객체를 만든다."""
    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """CLI뿐 아니라 파일에서 읽은 거래에도 같은 검증을 적용한다."""
        if not self.id:
            raise AppError("거래 id가 비어 있습니다.")
        valid_date(self.date)
        if self.type not in ("income", "expense"):
            raise AppError("타입은 income 또는 expense여야 합니다.")
        valid_category(self.category)
        positive_amount(self.amount)
        if not isinstance(self.memo, str):
            raise AppError("메모는 문자열이어야 합니다.")
        if any(not tag or "," in tag or "\n" in tag for tag in self.tags):
            raise AppError("태그에는 빈 값, 쉼표 또는 줄바꿈을 사용할 수 없습니다.")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transaction:
        """JSONL 한 줄의 딕셔너리를 검증된 거래 객체로 바꾼다."""
        try:
            tags = data.get("tags", [])
            if not isinstance(tags, list) or not all(isinstance(x, str) for x in tags):
                raise AppError("tags는 문자열 목록이어야 합니다.")
            amount = data["amount"]
            if isinstance(amount, bool) or not isinstance(amount, int):
                raise AppError("amount는 양수 정수여야 합니다.")
            return cls(
                id=data["id"], date=data["date"], type=data["type"],
                category=data["category"], amount=amount,
                memo=data.get("memo", ""), tags=tuple(tags),
            )
        except (KeyError, TypeError) as exc:
            raise AppError("거래 저장 데이터의 필드가 누락되었거나 잘못되었습니다.") from exc

    def changed(self, **updates: Any) -> Transaction:
        """불변 거래에서 일부 필드만 바꾼 새 거래를 반환한다."""
        return replace(self, **updates)


def parse_tags(value: str) -> tuple[str, ...]:
    """입력한 쉼표 구분 태그를 공백을 정리한 튜플로 바꾼다."""
    return tuple(tag.strip() for tag in value.split(",") if tag.strip())
