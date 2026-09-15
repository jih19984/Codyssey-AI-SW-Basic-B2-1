from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator, Type, TypeVar

from budget_app.models import Budget, Category, Transaction

T = TypeVar("T")

DEFAULT_CATEGORIES = ["food", "transport", "rent", "etc"]

class Repository:
    """하나의 JSONL 파일에 대한 스트리밍 read / 원자적 write를 담당한다."""
    def __init__(self, path: Path, model:Type[T]) -> None:
        self.path = path
        self.model = model
        self.__ensure_file()

    def __ensure_file(self) -> None:
        #파일이 없으면 자동 생성 (README 저장 정책)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def read_all(self) -> Iterator[T]:
        """파일을 한 줄씩 읽어 모델 객체로 변환해 넘긴다. (전체 로드 X, 제너레이터)."""
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield self.model.from_dict(json.loads(line))

    def append(self, item: T) -> None:
        """파일 끝에 한 줄 추가 (add 명령어에서 사용)."""
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

    def rewrite_all(self, items: list[T]) -> None:
        """update/delete처럼 내용 전체를 바꿔야 할 때 : 임시 파일 작성 후 원자적 교체"""
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

        os.replace(tmp_path, self.path) #같은 파일 시스템 내에서 원자적 교체

def create_repositories(data_dir: Path) -> tuple[Repository, Repository, Repository]:
    """data_dir 아래 3개 저장소를 준비하고, 카테고리가 비어 있으면 기본 카테고리를 채운다."""
    tx_repo = Repository(data_dir / "transactions.jsonl", Transaction)
    cat_repo = Repository(data_dir / "categories.jsonl", Category)
    budget_repo = Repository(data_dir / "budgets.jsonl", Budget)

    if not any(True for _ in cat_repo.read_all()):
        for name in DEFAULT_CATEGORIES:
            cat_repo.append(Category(name=name))

    return tx_repo, cat_repo, budget_repo


