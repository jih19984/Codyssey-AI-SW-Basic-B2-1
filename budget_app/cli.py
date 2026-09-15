"""budget_app CLI: argparse 서브커맨드 정의."""
from __future__ import annotations

import argparse
from pathlib import Path

from budget_app.decorators import handle_errors, log_calls, measure_time
from budget_app.exceptions import ValidationError
from budget_app.models import Transaction
from budget_app.repository import create_repositories
from budget_app.service import BudgetService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget_app", description="나만의 용돈 기입장")
    parser.add_argument("--data-dir", default="./data", help="데이터 저장 폴더 (기본: ./data)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("add", help="거래 추가 (대화형 입력)")

    list_parser = subparsers.add_parser("list", help="거래 목록 조회")
    list_parser.add_argument("--limit", type=int, default=None)

    search_parser = subparsers.add_parser("search", help="조건으로 거래 검색")
    search_parser.add_argument("--from", dest="date_from")
    search_parser.add_argument("--to", dest="date_to")
    search_parser.add_argument("--category")
    search_parser.add_argument("--type")
    search_parser.add_argument("--q")
    search_parser.add_argument("--tag")

    summary_parser = subparsers.add_parser("summary", help="월별 요약")
    summary_parser.add_argument("--month", required=True)
    summary_parser.add_argument("--top", type=int, default=3)

    budget_parser = subparsers.add_parser("budget", help="예산 관리")
    budget_sub = budget_parser.add_subparsers(dest="budget_command", required=True)
    budget_set = budget_sub.add_parser("set", help="월별 예산 설정")
    budget_set.add_argument("--month", required=True)
    budget_set.add_argument("--amount", type=int, required=True)

    category_parser = subparsers.add_parser("category", help="카테고리 관리")
    category_sub = category_parser.add_subparsers(dest="category_command", required=True)
    category_sub.add_parser("list", help="카테고리 목록")
    category_add = category_sub.add_parser("add", help="카테고리 추가")
    category_add.add_argument("--name", required=True)
    category_remove = category_sub.add_parser("remove", help="카테고리 삭제")
    category_remove.add_argument("--name", required=True)
    category_remove.add_argument("--replace", default=None)

    update_parser = subparsers.add_parser("update", help="거래 수정")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--date")
    update_parser.add_argument("--type")
    update_parser.add_argument("--category")
    update_parser.add_argument("--amount", type=int)
    update_parser.add_argument("--memo")
    update_parser.add_argument("--tags")

    delete_parser = subparsers.add_parser("delete", help="거래 삭제")
    delete_parser.add_argument("--id", required=True)

    import_parser = subparsers.add_parser("import", help="CSV에서 가져오기")
    import_parser.add_argument("--from", dest="import_from", required=True)

    export_parser = subparsers.add_parser("export", help="CSV로 내보내기")
    export_parser.add_argument("--out", required=True)
    export_parser.add_argument("--month")
    export_parser.add_argument("--from", dest="date_from")
    export_parser.add_argument("--to", dest="date_to")

    return parser


def _prompt_add(service: BudgetService) -> None:
    date_str = input("날짜(YYYY-MM-DD): ").strip()
    type_str = input("타입(income/expense): ").strip()
    category = input("카테고리: ").strip()
    amount_str = input("금액(양수): ").strip()
    memo = input("메모(선택): ").strip()
    tags_str = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    try:
        amount = int(amount_str)
    except ValueError as e:
        raise ValidationError(f"금액은 숫자여야 합니다: {amount_str}", hint="정수로 입력하세요") from e

    tx = service.add_transaction(
        date_str=date_str,
        type_=type_str,
        category=category,
        amount=amount,
        memo=memo,
        tags=tags,
    )
    print(f"[저장 완료] id={tx.id}")


def _print_transaction(t: Transaction) -> None:
    print(f"{t.id} | {t.date.isoformat()} | {t.type} | {t.category} | {t.amount} | {t.memo}")


@handle_errors
@measure_time
@log_calls
def dispatch(args: argparse.Namespace) -> None:
    data_dir = Path(args.data_dir)
    tx_repo, cat_repo, budget_repo = create_repositories(data_dir)
    service = BudgetService(tx_repo, cat_repo, budget_repo)

    if args.command == "add":
        _prompt_add(service)

    elif args.command == "list":
        for t in service.list_transactions(limit=args.limit):
            _print_transaction(t)

    elif args.command == "search":
        for t in service.search_transactions(
            date_from=args.date_from,
            date_to=args.date_to,
            category=args.category,
            type_=args.type,
            keyword=args.q,
            tag=args.tag,
        ):
            _print_transaction(t)

    elif args.command == "summary":
        result = service.summary(month=args.month, top=args.top)
        if result["count"] == 0:
            print(f"{args.month}에는 거래 내역이 없습니다.")
            return
        print(f"총수입: {result['total_income']}")
        print(f"총지출: {result['total_expense']}")
        print(f"잔액: {result['balance']}")
        print(f"카테고리 TOP {args.top}:")
        for name, amount in result["top_categories"]:
            print(f"  {name}: {amount}")
        if result["budget_amount"] is not None:
            print(f"예산: {result['budget_amount']} (사용률 {result['usage_rate']:.1%})")
            if result["exceeded"]:
                print("경고: 예산을 초과했습니다.")

    elif args.command == "budget":
        if args.budget_command == "set":
            service.set_budget(month=args.month, amount=args.amount)
            print(f"[예산 설정 완료] {args.month} = {args.amount}")

    elif args.command == "category":
        if args.category_command == "list":
            for name in service.list_categories():
                print(name)
        elif args.category_command == "add":
            service.add_category(args.name)
            print(f"[카테고리 추가 완료] {args.name}")
        elif args.category_command == "remove":
            service.remove_category(args.name, replacement=args.replace)
            print(f"[카테고리 삭제 완료] {args.name}")

    elif args.command == "update":
        tags = None
        if args.tags is not None:
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        service.update_transaction(
            args.id,
            date_str=args.date,
            type_=args.type,
            category=args.category,
            amount=args.amount,
            memo=args.memo,
            tags=tags,
        )
        print(f"[수정 완료] id={args.id}")

    elif args.command == "delete":
        service.delete_transaction(args.id)
        print(f"[삭제 완료] id={args.id}")

    elif args.command == "import":
        count = service.import_csv(Path(args.import_from))
        print(f"[가져오기 완료] {count}건 처리")

    elif args.command == "export":
        count = service.export_csv(
            Path(args.out),
            month=args.month,
            date_from=args.date_from,
            date_to=args.date_to,
        )
        print(f"[내보내기 완료] {count}건 처리")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch(args)
    return 0
