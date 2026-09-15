"""
budget_app 커스텀 예외 정의
CLI 계층에서 이 예외들만 잡아 스택트레이스 대신
'원인 + 해결힌트'를 사용자에게 보여주기 위해 사용한다.
"""
from __future__ import annotations

class BudgetAppError(Exception):
    """Budget_App에서 예상 가능한 모든 예외의 기반 클래스."""

    def __init__(self, message:str, hint:str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\n힌트: {self.hint}"
        return self.message

class ValidationError(BudgetAppError):
    """입력값 검증 실패(잘못된 날짜/금액/타입/카테고리 등)"""

class NotFoundError(BudgetAppError):
    """id 또는 이름으로 찾으려던 대상이 존재하지 않을 때."""

class CategoryInUseError(BudgetAppError):
    """사용 중인 카테고리를 대체 카테고리 지정 없이 삭제하려 할 때."""


