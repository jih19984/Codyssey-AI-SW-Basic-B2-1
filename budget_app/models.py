""" budget_app 데이터 모델 정의. """
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any

@dataclass
class Transaction:
  """거래 내역 한 건."""
  id: str
  type: str # "income or expense"
  date: date
  amount: int
  category: str
  memo: str = ""
  tags : list[str] = field(default_factory=list)

  def to_dict(self) -> dict[str, Any]:
        # JSONL 한 줄에 그대로 쓸 수 있도록 date를 문자열로 변환
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date.isoformat(),
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": self.tags,
        }

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> "Transaction":
      return cls(
          id=data["id"],
          type=data["type"],
          date=date.fromisoformat(data["date"]),
          amount=data["amount"],
          category=data["category"],
          memo=data.get("memo", ""),
          tags=data.get("tags", []),
      )

@dataclass
class Category:
  """카테고리 한 건."""
  name: str
  def to_dict(self) -> dict[str, Any]:
    return {"name": self.name}

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> "Category":
    return cls(name=data["name"])

@dataclass
class Budget:
  """월별 예산 한 건."""
  month: str # "YYYY-MM"
  amount: int

  # 객체 -> dict 변환
  def to_dict(self) -> dict[str, Any]:
    return {"month": self.month, "amount": self.amount}

  # JSON 문자열 -> dict 변환
  @classmethod
  def from_dict(cls, data:dict[str, Any]) -> "Budget":
    return cls(month=data["month"], amount=data["amount"])

  # json.load : dict -> json 텍스트
  # json.dump : json 텍스트 -> dict

# 정리
# Transaction 객체 --to_dict()--> dict --json.dump()--> JSON 파일
# JSON 파일 --json.load()--> dict --from_dict()--> Transaction 객체











