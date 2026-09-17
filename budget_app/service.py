"""budget_app 서비스 계층: 검증 / 검색 / 요약 / 예산 로직."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Iterator

from budget_app.exceptions import CategoryInUseError, NotFoundError, ValidationError
from budget_app.models import Budget, Category, Transaction
from budget_app.repository import Repository

REQUIRED_IMPORT_COLUMNS = ("date", "type", "category", "amount")


class BudgetService:
    """Repository 3개를 받아 실제 비즈니스 로직(검증/검색/요약/예산)을 수행한다."""

    def __init__(self, tx_repo: Repository, cat_repo: Repository, budget_repo: Repository) -> None:
        self.tx_repo = tx_repo
        self.cat_repo = cat_repo
        self.budget_repo = budget_repo

    # ---------- 검증 헬퍼 (필드 검증은 서비스 계층 책임) ----------

    @staticmethod
    def _parse_date(value: str) -> date:
        try:
            return date.fromisoformat(value)
        except ValueError as e:
            raise ValidationError(
                f"날짜 형식이 올바르지 않습니다: {value}",
                hint="YYYY-MM-DD 형식으로 입력하세요",
            ) from e

    @staticmethod
    def _parse_amount(value: int) -> int:
        if value <= 0:
            raise ValidationError(
                f"금액은 양수여야 합니다: {value}",
                hint="amount에 양수 정수를 입력하세요",
            )
        return value

    @staticmethod
    def _parse_type(value: str) -> str:
        if value not in ("income", "expense"):
            raise ValidationError(
                f"타입은 income/expense 중 하나여야 합니다: {value}",
                hint="income 또는 expense를 입력하세요",
            )
        return value

    def _validate_category(self, name: str) -> None:
        if name not in self.list_categories():
            raise ValidationError(
                f"등록되지 않은 카테고리입니다: {name}",
                hint="category add로 먼저 등록하거나 category list로 확인하세요",
            )

    # ---------- id 채번 ----------

    def _max_seq(self) -> int:
        max_seq = 0
        for t in self.tx_repo.read_all():
            seq = int(t.id.split("-")[1])
            max_seq = max(max_seq, seq)
        return max_seq

    def _next_id(self) -> str:
        return f"TX-{self._max_seq() + 1:06d}"

    def _find_index(self, tx_id: str, transactions: list[Transaction]) -> int:
        for i, t in enumerate(transactions):
            if t.id == tx_id:
                return i
        raise NotFoundError(
            f"거래를 찾을 수 없습니다: {tx_id}",
            hint="list 명령어로 존재하는 id를 확인하세요",
        )

    # ---------- 카테고리 ----------

    def list_categories(self) -> list[str]:
        return [c.name for c in self.cat_repo.read_all()]

    def add_category(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValidationError("카테고리 이름이 비어 있습니다", hint="카테고리 이름을 입력하세요")
        if name in self.list_categories():
            raise ValidationError(f"이미 존재하는 카테고리입니다: {name}", hint="다른 이름을 사용하세요")
        self.cat_repo.append(Category(name=name))

    def remove_category(self, name: str, replacement: str | None = None) -> None:
        categories = list(self.cat_repo.read_all())
        if name not in [c.name for c in categories]:
            raise NotFoundError(
                f"카테고리를 찾을 수 없습니다: {name}",
                hint="category list로 등록된 카테고리를 확인하세요",
            )

        transactions = list(self.tx_repo.read_all())
        in_use = any(t.category == name for t in transactions)

        if in_use:
            if replacement is None:
                raise CategoryInUseError(
                    f"'{name}' 카테고리를 사용 중인 거래가 있습니다",
                    hint="--replace <다른 카테고리>로 대체 카테고리를 지정하면 삭제할 수 있습니다",
                )
            if replacement not in [c.name for c in categories]:
                raise NotFoundError(f"대체 카테고리를 찾을 수 없습니다: {replacement}")
            for t in transactions:
                if t.category == name:
                    t.category = replacement
            self.tx_repo.rewrite_all(transactions)

        remaining = [c for c in categories if c.name != name]
        self.cat_repo.rewrite_all(remaining)

    # ---------- add ----------

    def add_transaction(
        self,
        date_str: str,
        type_: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: list[str] | None = None,
    ) -> Transaction:
        tx_date = self._parse_date(date_str)
        tx_type = self._parse_type(type_)
        tx_amount = self._parse_amount(amount)
        self._validate_category(category)
        tx = Transaction(
            id=self._next_id(),
            type=tx_type,
            date=tx_date,
            amount=tx_amount,
            category=category,
            memo=memo,
            tags=tags or [],
        )
        self.tx_repo.append(tx)
        return tx

    # ---------- list / search ----------
    # 정렬(최신순)을 위해 read_all() 제너레이터를 sorted()로 한 번 모으긴 하지만,
    # 파일을 직접 여러 번 열거나 별도 캐시에 전체를 들고 있지 않고
    # repository의 스트리밍 read를 그대로 소비한다는 점에서 최소한의 메모리만 쓴다.

    def list_transactions(self, limit: int | None = None) -> Iterator[Transaction]:
        items = sorted(self.tx_repo.read_all(), key=lambda t: t.date, reverse=True)
        if limit is not None:
            items = items[:limit]
        yield from items

    def search_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        type_: str | None = None,
        keyword: str | None = None,
        tag: str | None = None,
    ) -> Iterator[Transaction]:
        parsed_from = self._parse_date(date_from) if date_from else None
        parsed_to = self._parse_date(date_to) if date_to else None

        items = sorted(self.tx_repo.read_all(), key=lambda t: t.date, reverse=True)
        for t in items:
            if parsed_from and t.date < parsed_from:
                continue
            if parsed_to and t.date > parsed_to:
                continue
            if category and t.category != category:
                continue
            if type_ and t.type != type_:
                continue
            if keyword and keyword not in t.memo:
                continue
            if tag and tag not in t.tags:
                continue
            yield t

    # ---------- update / delete ----------

    def update_transaction(
        self,
        tx_id: str,
        *,
        date_str: str | None = None,
        type_: str | None = None,
        category: str | None = None,
        amount: int | None = None,
        memo: str | None = None,
        tags: list[str] | None = None,
    ) -> Transaction:
        transactions = list(self.tx_repo.read_all())
        idx = self._find_index(tx_id, transactions)
        tx = transactions[idx]

        if date_str is not None:
            tx.date = self._parse_date(date_str)
        if type_ is not None:
            tx.type = self._parse_type(type_)
        if category is not None:
            self._validate_category(category)
            tx.category = category
        if amount is not None:
            tx.amount = self._parse_amount(amount)
        if memo is not None:
            tx.memo = memo
        if tags is not None:
            tx.tags = tags

        self.tx_repo.rewrite_all(transactions)
        return tx

    def delete_transaction(self, tx_id: str) -> None:
        transactions = list(self.tx_repo.read_all())
        idx = self._find_index(tx_id, transactions)
        # 파이썬에서 리스트의 해당 요소 삭제할 수 있는 예약어
        del transactions[idx]
        self.tx_repo.rewrite_all(transactions)

    # ---------- summary ----------

    def summary(self, month: str, top: int = 3) -> dict:
        transactions = [t for t in self.tx_repo.read_all() if t.date.strftime("%Y-%m") == month]

        total_income = sum(t.amount for t in transactions if t.type == "income")
        total_expense = sum(t.amount for t in transactions if t.type == "expense")
        balance = total_income - total_expense

        expense_by_category: dict[str, int] = {}
        for t in transactions:
            if t.type == "expense":
                expense_by_category[t.category] = expense_by_category.get(t.category, 0) + t.amount
        top_categories = sorted(expense_by_category.items(), key=lambda kv: kv[1], reverse=True)[:top]

        budget = self.get_budget(month)
        usage_rate = None
        exceeded = None
        if budget is not None and budget.amount:
            usage_rate = total_expense / budget.amount
            exceeded = total_expense > budget.amount

        return {
            "month": month,
            "count": len(transactions),
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "top_categories": top_categories,
            "budget_amount": budget.amount if budget else None,
            "usage_rate": usage_rate,
            "exceeded": exceeded,
        }

    # ---------- budget ----------

    def set_budget(self, month: str, amount: int) -> None:
        self._parse_amount(amount)
        budgets = list(self.budget_repo.read_all())
        for b in budgets:
            if b.month == month:
                b.amount = amount
                self.budget_repo.rewrite_all(budgets)
                return
        self.budget_repo.append(Budget(month=month, amount=amount))

    def get_budget(self, month: str) -> Budget | None:
        for b in self.budget_repo.read_all():
            if b.month == month:
                return b
        return None

    # ---------- import / export ----------

    def import_csv(self, path: Path) -> int:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            missing = [c for c in REQUIRED_IMPORT_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                raise ValidationError(
                    f"CSV 헤더에 필수 컬럼이 없습니다: {missing}",
                    hint="date,type,category,amount 컬럼이 있어야 합니다",
                )
            rows = list(reader)

        validated: list[Transaction] = []
        for line_no, row in enumerate(rows, start=2):  # 1번째 줄은 헤더
            try:
                tx_date = self._parse_date(row["date"])
                tx_type = self._parse_type(row["type"])
                tx_amount = self._parse_amount(int(row["amount"]))
                category = row["category"]
                self._validate_category(category)
            except ValidationError as e:
                raise ValidationError(f"{line_no}번째 줄: {e.message}", hint=e.hint) from e

            tags = [t.strip() for t in row.get("tags", "").split(",") if t.strip()]
            validated.append(
                Transaction(
                    id="",  # 아래에서 일괄 채번
                    type=tx_type,
                    date=tx_date,
                    amount=tx_amount,
                    category=category,
                    memo=row.get("memo", ""),
                    tags=tags,
                )
            )

        base = self._max_seq()
        for offset, tx in enumerate(validated, start=1):
            tx.id = f"TX-{base + offset:06d}"
            self.tx_repo.append(tx)

        return len(validated)

    def export_csv(
        self,
        path: Path,
        month: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        if month is None and date_from is None and date_to is None:
            raise ValidationError(
                "export는 --month 또는 --from/--to 중 하나가 필요합니다",
                hint="--month 2024-01 또는 --from ... --to ... 를 지정하세요",
            )

        if month is not None:
            transactions = [t for t in self.tx_repo.read_all() if t.date.strftime("%Y-%m") == month]
        else:
            transactions = list(self.search_transactions(date_from=date_from, date_to=date_to))

        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "type", "category", "amount", "memo", "tags"])
            writer.writeheader()
            for t in transactions:
                writer.writerow(
                    {
                        "date": t.date.isoformat(),
                        "type": t.type,
                        "category": t.category,
                        "amount": t.amount,
                        "memo": t.memo,
                        "tags": ",".join(t.tags),
                    }
                )
        return len(transactions)
